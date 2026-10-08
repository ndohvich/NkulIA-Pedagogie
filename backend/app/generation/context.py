"""Construction du contexte pédagogique d'une unité (la partie « R » du RAG).

Tout ce qui est donné au modèle vient de la base — le référentiel
importé par l'enseignant. Chaque fait reçoit un `source_ref` stable
(`<fichier>#<pointeur>`) que le contrat de provenance sait vérifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.db.models import LearningUnit, Module, SourceDocument, TeachingUnit
from app.generation.retrieval import related_units


@dataclass(frozen=True)
class RelatedUnit:
    title: str
    learning_unit_title: str
    module_title: str


@dataclass
class UnitContext:
    teaching_unit_id: int
    source_document_id: int
    filename: str
    kind: str
    track_schema: str
    # clé de fait (ex. "teaching_unit.title") -> source_ref complet
    refs: dict[str, str] = field(default_factory=dict)
    # source_ref complet -> texte exact du document
    facts: dict[str, str] = field(default_factory=dict)
    previous_titles: list[str] = field(default_factory=list)
    related: list[RelatedUnit] = field(default_factory=list)

    def add_fact(self, key: str, pointer: str, text: str | None) -> None:
        if text is None or not text.strip():
            return  # absent du référentiel : on n'enregistre rien (→ missing_information)
        ref = f"{self.filename}#{pointer}"
        self.refs[key] = ref
        self.facts[ref] = text.strip()

    def fact(self, key: str) -> str | None:
        ref = self.refs.get(key)
        return self.facts[ref] if ref else None


def build_unit_context(db: Session, teaching_unit_id: int) -> UnitContext:
    """Rassemble le contexte d'une unité d'enseignement. `LookupError` si elle n'existe pas."""
    teaching_unit = db.get(TeachingUnit, teaching_unit_id)
    if teaching_unit is None:
        raise LookupError(f"Unité d'enseignement {teaching_unit_id} introuvable.")

    learning_unit: LearningUnit = teaching_unit.learning_unit
    module: Module = learning_unit.module
    document: SourceDocument = module.source_document

    context = UnitContext(
        teaching_unit_id=teaching_unit.id,
        source_document_id=document.id,
        filename=document.filename,
        kind=document.kind,
        track_schema=document.track_schema,
    )

    context.add_fact("module.title", f"module:{module.id}.title", module.title)
    context.add_fact(
        "learning_unit.title", f"learning_unit:{learning_unit.id}.title", learning_unit.title
    )
    prefix = f"teaching_unit:{teaching_unit.id}"
    context.add_fact("teaching_unit.title", f"{prefix}.title", teaching_unit.title)
    context.add_fact("teaching_unit.actions", f"{prefix}.actions", teaching_unit.actions)
    context.add_fact(
        "teaching_unit.essential_knowledge",
        f"{prefix}.essential_knowledge",
        teaching_unit.essential_knowledge,
    )
    context.add_fact("teaching_unit.duration", f"{prefix}.duration", teaching_unit.duration_label)
    context.add_fact(
        "teaching_unit.session_type", f"{prefix}.session_type", teaching_unit.session_type
    )
    if teaching_unit.digitalized is not None:  # None = absent : jamais forcé à NON
        context.add_fact(
            "teaching_unit.digitalized",
            f"{prefix}.digitalized",
            "OUI" if teaching_unit.digitalized else "NON",
        )

    # Unités qui précèdent dans la même unité d'apprentissage : base d'une
    # déduction honnête sur les prérequis.
    siblings = learning_unit.teaching_units
    position = next(i for i, sibling in enumerate(siblings) if sibling.id == teaching_unit.id)
    context.previous_titles = [sibling.title for sibling in siblings[:position]]

    # Unités voisines des documents de la même classe (hors unité courante).
    candidates: list[tuple[int, str]] = []
    by_id: dict[int, RelatedUnit] = {}
    same_class = (
        db.query(SourceDocument).filter(SourceDocument.classroom_id == document.classroom_id).all()
    )
    for other_document in same_class:
        for other_module in other_document.modules:
            for other_lu in other_module.learning_units:
                for other_tu in other_lu.teaching_units:
                    if other_tu.id == teaching_unit.id:
                        continue
                    candidates.append((other_tu.id, f"{other_lu.title} {other_tu.title}"))
                    by_id[other_tu.id] = RelatedUnit(
                        other_tu.title, other_lu.title, other_module.title
                    )
    query = f"{learning_unit.title} {teaching_unit.title}"
    context.related = [by_id[unit_id] for unit_id, _ in related_units(query, candidates, limit=3)]

    return context
