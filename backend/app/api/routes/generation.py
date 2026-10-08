"""Routes de génération de fiches de cours (issues #12 et #13)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.config import get_settings
from app.db.models import GeneratedDocument, GeneratedField, Teacher
from app.db.session import get_db
from app.export.pdf import NotValidated, render_course_sheet_pdf
from app.generation import lifecycle
from app.generation.pipeline import GenerationRejected, generate_course_sheet
from app.generation.providers import LLMProvider, ProviderError, build_provider
from app.generation.template import COURSE_SHEET_FIELDS
from app.schemas.generation import (
    CourseSheetRequest,
    FieldEditRequest,
    GeneratedDocumentOut,
    GeneratedDocumentSummary,
    GeneratedFieldOut,
    ValidateRequest,
)

router = APIRouter(prefix="/generation", tags=["generation"])

_LABELS = {spec.name: spec.label for spec in COURSE_SHEET_FIELDS}


def get_provider() -> LLMProvider:
    """Dépendance FastAPI : les tests la remplacent par un faux fournisseur."""
    try:
        return build_provider(get_settings())
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def _to_out(document: GeneratedDocument) -> GeneratedDocumentOut:
    source = document.teaching_unit.learning_unit.module.source_document
    return GeneratedDocumentOut(
        id=document.id,
        teaching_unit_id=document.teaching_unit_id,
        kind="course_sheet",
        status=document.status,  # type: ignore[arg-type]  # valeurs fixées par lifecycle.py
        provider_name=document.provider_name,
        created_at=document.created_at,
        updated_at=document.updated_at,
        validated_at=document.validated_at,
        track_schema=source.track_schema,
        fields=[
            GeneratedFieldOut(
                field=item.field,
                label=_LABELS.get(item.field, item.field),
                value=item.value,
                provenance=item.provenance,  # type: ignore[arg-type]
                source_ref=item.source_ref,
                edited_by_teacher=item.edited_by_teacher,
            )
            for item in document.fields
        ],
    )


def _owned_document(db: Session, document_id: int, teacher: Teacher) -> GeneratedDocument:
    document = db.get(GeneratedDocument, document_id)
    # Même réponse « introuvable » qu'il n'existe pas ou qu'il appartienne à un autre.
    if document is None or document.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Document généré introuvable.")
    return document


@router.post(
    "/course-sheets", response_model=GeneratedDocumentOut, status_code=status.HTTP_201_CREATED
)
def create_course_sheet(
    payload: CourseSheetRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
    provider: LLMProvider = Depends(get_provider),
) -> GeneratedDocumentOut:
    try:
        output = generate_course_sheet(db, payload.teaching_unit_id, provider)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Unité d'enseignement introuvable.") from exc
    except GenerationRejected as exc:
        # Rien n'est enregistré ni affiché : une sortie hors contrat n'atteint jamais l'interface.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    # brouillon → analysé → proposé, enchaînés : le contexte a été analysé et la
    # proposition produite dans la même requête.
    current = lifecycle.BROUILLON
    for target in (lifecycle.ANALYSE, lifecycle.PROPOSE):
        lifecycle.check_transition(current, target)
        current = target

    document = GeneratedDocument(
        teacher_id=teacher.id,
        teaching_unit_id=payload.teaching_unit_id,
        status=current,
        provider_name=provider.name,
    )
    for position, item in enumerate(output.fields):
        document.fields.append(
            GeneratedField(
                position=position,
                field=item.field,
                value=item.value,
                provenance=item.provenance,
                source_ref=item.source_ref,
            )
        )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _to_out(document)


@router.get("/documents", response_model=list[GeneratedDocumentSummary])
def list_generated_documents(
    teaching_unit_id: int,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> list[GeneratedDocument]:
    return (
        db.query(GeneratedDocument)
        .filter_by(teacher_id=teacher.id, teaching_unit_id=teaching_unit_id)
        .order_by(GeneratedDocument.id.desc())
        .all()
    )


@router.get("/documents/{document_id}", response_model=GeneratedDocumentOut)
def read_generated_document(
    document_id: int,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> GeneratedDocumentOut:
    return _to_out(_owned_document(db, document_id, teacher))


@router.patch("/documents/{document_id}", response_model=GeneratedDocumentOut)
def edit_generated_document(
    document_id: int,
    payload: FieldEditRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> GeneratedDocumentOut:
    document = _owned_document(db, document_id, teacher)
    by_name = {item.field: item for item in document.fields}

    for name, new_value in payload.fields.items():
        item = by_name.get(name)
        if item is None:
            raise HTTPException(status_code=422, detail=f"Champ inconnu : « {name} ».")
        if item.provenance == "reference":
            # Une référence EST le document source : pour la changer, on corrige
            # le document importé, pas la fiche (sinon l'étiquette mentirait).
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Le champ « {name} » est une référence du document importé et "
                    "ne se modifie pas ici."
                ),
            )
        item.value = new_value.strip() or None
        item.edited_by_teacher = item.value is not None

    try:
        lifecycle.check_transition(document.status, lifecycle.MODIFIE)
    except lifecycle.InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    document.status = lifecycle.MODIFIE
    document.validated_at = None
    db.commit()
    db.refresh(document)
    return _to_out(document)


@router.post("/documents/{document_id}/validate", response_model=GeneratedDocumentOut)
def validate_generated_document(
    document_id: int,
    payload: ValidateRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> GeneratedDocumentOut:
    document = _owned_document(db, document_id, teacher)

    try:
        lifecycle.check_transition(document.status, lifecycle.VALIDE)
    except lifecycle.InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    missing = [
        _LABELS.get(item.field, item.field)
        for item in document.fields
        if not (item.value and item.value.strip())
    ]
    if missing and not payload.acknowledge_missing:
        raise HTTPException(
            status_code=409,
            detail=(
                "Informations manquantes : "
                + ", ".join(missing)
                + ". Complétez-les ou confirmez la validation malgré ces manques."
            ),
        )

    document.status = lifecycle.VALIDE
    document.validated_at = datetime.now(UTC)
    db.commit()
    db.refresh(document)
    return _to_out(document)


@router.get("/documents/{document_id}/pdf")
def export_generated_document_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> Response:
    """Export PDF définitif — réservé aux fiches validées (principe n°3)."""
    document = _owned_document(db, document_id, teacher)
    try:
        content = render_course_sheet_pdf(document, teacher)
    except NotValidated as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Validez la fiche avant de l'exporter en PDF.",
        ) from exc
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="fiche-{document.id}.pdf"'},
    )
