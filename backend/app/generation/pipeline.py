"""Pipeline de génération d'une fiche de cours (issues #12 et #13).

    contexte (base) ──► champs de RÉFÉRENCE recopiés par le pipeline
                   └──► fournisseur ──► champs GÉNÉRATIFS ──► contrat de provenance
                                                          └──► fusion ──► sortie vérifiée

Garanties, toutes testées (tests/unit/test_generation_pipeline.py) :
- une sortie sans étiquette valide est rejetée (`GenerationRejected`) ;
- le fournisseur ne peut pas écrire un champ de référence ni un champ
  hors gabarit ;
- tout champ du gabarit est présent dans le résultat : un champ non
  produit devient « information manquante », jamais silencieusement absent.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.generation.context import UnitContext, build_unit_context
from app.generation.provenance import (
    GenerationOutput,
    ProvenancedField,
    ProvenanceError,
    parse_generation_output,
    verify_references,
)
from app.generation.providers import LLMProvider
from app.generation.template import COURSE_SHEET_FIELDS, GENERATIVE_NAMES, REFERENCE_FIELDS

MAX_ATTEMPTS = 2  # une première tentative + une seconde avec la raison du rejet


class GenerationRejected(RuntimeError):
    """Le fournisseur n'a pas produit de sortie conforme au contrat, même après relance."""


def reference_fields(context: UnitContext) -> list[ProvenancedField]:
    """Champs recopiés du référentiel — ou « information manquante » s'ils n'y sont pas."""
    fields: list[ProvenancedField] = []
    for spec in REFERENCE_FIELDS:
        value = context.fact(spec.fact) if spec.fact else None
        if spec.fact is None or value is None:
            fields.append(ProvenancedField(field=spec.name, provenance="missing_information"))
        else:
            fields.append(
                ProvenancedField(
                    field=spec.name,
                    value=value,
                    provenance="reference",
                    source_ref=context.refs[spec.fact],
                )
            )
    return fields


def _generative_fields(provider: LLMProvider, context: UnitContext) -> list[ProvenancedField]:
    feedback: str | None = None
    last_error = ""
    for _ in range(MAX_ATTEMPTS):
        raw = provider.generate(context, feedback)
        try:
            produced = parse_generation_output(raw)
            outside = [f.field for f in produced.fields if f.field not in GENERATIVE_NAMES]
            if outside:
                raise ProvenanceError(
                    "Champs non autorisés (la structure est fixée par l'application) : "
                    + ", ".join(outside)
                )
            verify_references(produced, context.facts)
            if any(f.provenance == "reference" for f in produced.fields):
                raise ProvenanceError(
                    "Les champs génératifs ne peuvent pas être étiquetés « reference »."
                )
            return produced.fields
        except ProvenanceError as exc:
            last_error = str(exc)
            feedback = last_error
    raise GenerationRejected(f"Sortie rejetée après {MAX_ATTEMPTS} tentatives : {last_error}")


def generate_course_sheet(
    db: Session, teaching_unit_id: int, provider: LLMProvider
) -> GenerationOutput:
    """Produit une fiche de cours complète et vérifiée pour une unité d'enseignement.

    `LookupError` si l'unité n'existe pas ; `GenerationRejected` si la
    sortie du fournisseur viole le contrat ; `ProviderError` (module
    providers) si le fournisseur est indisponible.
    """
    context = build_unit_context(db, teaching_unit_id)

    by_name = {f.field: f for f in reference_fields(context)}
    for field in _generative_fields(provider, context):
        by_name[field.field] = field

    # Complétude : tout champ du gabarit existe, dans l'ordre du gabarit.
    ordered: list[ProvenancedField] = []
    for spec in COURSE_SHEET_FIELDS:
        ordered.append(
            by_name.get(spec.name)
            or ProvenancedField(field=spec.name, provenance="missing_information")
        )

    result = GenerationOutput(fields=ordered)
    verify_references(result, context.facts)  # dernier filet avant toute persistance
    return result
