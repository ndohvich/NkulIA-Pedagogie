"""Persiste un `ParsedDocument` (voir docx_parser.py) dans les tables
SourceDocument / Module / LearningUnit / TeachingUnit.

Séparé du parseur (docx_parser.py ne connaît pas SQLAlchemy) : on peut
tester l'extraction seule sans base de données, et changer un jour de
moteur de persistance sans toucher au parseur — voir tests/unit/
test_docx_parser.py vs tests/integration/test_ingestion.py.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import LearningUnit, Module, SourceDocument, TeachingUnit
from app.schemas.ingestion import ParsedDocument


def persist_parsed_document(
    db: Session,
    parsed: ParsedDocument,
    *,
    classroom_id: int,
    subject_id: int,
    filename: str,
) -> SourceDocument:
    """Enregistre un document déjà extrait. Ne fait AUCUNE validation
    métier supplémentaire (elle a eu lieu dans le parseur) : cette
    fonction traduit fidèlement la structure Pydantic en lignes SQL."""
    source_document = SourceDocument(
        classroom_id=classroom_id,
        subject_id=subject_id,
        filename=filename,
        kind=parsed.kind,
        track_schema=parsed.track_schema,
        warnings_json=json.dumps(parsed.warnings, ensure_ascii=False),
    )

    for parsed_module in parsed.modules:
        module = Module(number=parsed_module.number, title=parsed_module.title)
        for parsed_lu in parsed_module.learning_units:
            learning_unit = LearningUnit(number=parsed_lu.number, title=parsed_lu.title)
            for parsed_tu in parsed_lu.teaching_units:
                learning_unit.teaching_units.append(
                    TeachingUnit(
                        number=parsed_tu.number,
                        title=parsed_tu.title,
                        digitalized=parsed_tu.digitalized,
                        actions=parsed_tu.actions,
                        essential_knowledge=parsed_tu.essential_knowledge,
                        duration_label=parsed_tu.duration_label,
                        session_type=parsed_tu.session_type,
                    )
                )
            module.learning_units.append(learning_unit)
        source_document.modules.append(module)

    db.add(source_document)
    db.commit()
    db.refresh(source_document)
    return source_document
