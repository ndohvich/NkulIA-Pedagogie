"""Route d'import (issue #9/#11 côté API) — nécessite d'être connecté."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.models import Classroom, SourceDocument, Subject, Teacher
from app.db.session import get_db
from app.ingestion.docx_parser import parse_docx
from app.ingestion.persist import persist_parsed_document
from app.schemas.ingestion import DocumentDetailOut, ImportSummary, SourceDocumentOut

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/import", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
def import_document(
    classroom_id: int = Form(...),
    subject_id: int = Form(...),
    kind: Literal["fiche_progression", "projet_pedagogique"] = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _teacher: Teacher = Depends(get_current_teacher),
) -> ImportSummary:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Seuls les fichiers .docx sont pris en charge pour le moment.",
        )

    # On vérifie que la classe et la matière existent, mais pas encore
    # qu'elles appartiennent à l'enseignant connecté (TeachingAssignment) —
    # simplification MVP assumée, à durcir avant un usage multi-enseignant.
    if db.get(Classroom, classroom_id) is None:
        raise HTTPException(status_code=404, detail="Classe introuvable.")
    if db.get(Subject, subject_id) is None:
        raise HTTPException(status_code=404, detail="Matière introuvable.")

    try:
        parsed = parse_docx(file.file, kind=kind)
    except ValueError as exc:
        # Colonnes obligatoires introuvables (voir track_schema.py) —
        # on refuse clairement plutôt que d'importer une structure fausse.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    document = persist_parsed_document(
        db, parsed, classroom_id=classroom_id, subject_id=subject_id, filename=file.filename
    )

    return ImportSummary(
        document_id=document.id,
        filename=document.filename,
        kind=parsed.kind,
        track_schema=parsed.track_schema,
        module_count=len(parsed.modules),
        learning_unit_count=sum(len(m.learning_units) for m in parsed.modules),
        teaching_unit_count=sum(
            len(lu.teaching_units) for m in parsed.modules for lu in m.learning_units
        ),
        warnings=parsed.warnings,
    )


def _warnings_of(document: SourceDocument) -> list[str]:
    return json.loads(document.warnings_json) if document.warnings_json else []


def _summary_of(document: SourceDocument) -> SourceDocumentOut:
    learning_units = [lu for m in document.modules for lu in m.learning_units]
    return SourceDocumentOut(
        id=document.id,
        filename=document.filename,
        kind=document.kind,
        track_schema=document.track_schema,
        imported_at=document.imported_at,
        module_count=len(document.modules),
        learning_unit_count=len(learning_units),
        teaching_unit_count=sum(len(lu.teaching_units) for lu in learning_units),
        warning_count=len(_warnings_of(document)),
    )


@router.get("/documents", response_model=list[SourceDocumentOut])
def list_documents(
    classroom_id: int,
    db: Session = Depends(get_db),
    _teacher: Teacher = Depends(get_current_teacher),
) -> list[SourceDocumentOut]:
    documents = (
        db.query(SourceDocument)
        .filter(SourceDocument.classroom_id == classroom_id)
        .order_by(SourceDocument.imported_at.desc(), SourceDocument.id.desc())
        .all()
    )
    return [_summary_of(document) for document in documents]


@router.get("/documents/{document_id}", response_model=DocumentDetailOut)
def document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    _teacher: Teacher = Depends(get_current_teacher),
) -> DocumentDetailOut:
    document = db.get(SourceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return DocumentDetailOut(
        **_summary_of(document).model_dump(),
        modules=document.modules,  # type: ignore[arg-type]  # validés via from_attributes
        warnings=_warnings_of(document),
    )


@router.get("/documents/{document_id}/warnings", response_model=list[str])
def document_warnings(
    document_id: int,
    db: Session = Depends(get_db),
    _teacher: Teacher = Depends(get_current_teacher),
) -> list[str]:
    document = db.get(SourceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return _warnings_of(document)
