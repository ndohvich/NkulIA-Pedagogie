"""Gabarit de la fiche de cours (issue #13) — premier gabarit.

Les champs « de référence » sont recopiés par le pipeline lui-même
depuis la base (jamais confiés au modèle : une recopie fidèle ne se
délègue pas). Les champs « génératifs » sont ceux qu'un LLM peut
proposer — toujours avec une étiquette de provenance.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    description: str
    fact: str | None = None  # clé du fait source, pour les champs de référence


# Les titres gardent des libellés neutres : le vocabulaire UA/UE ou
# Chapitre/Leçon est appliqué à l'affichage (ADR-0003, principe n°4).
REFERENCE_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("titre_module", "Module", "Titre du module", fact="module.title"),
    FieldSpec(
        "titre_unite_apprentissage",
        "Unité d'apprentissage / Chapitre",
        "Titre de l'unité d'apprentissage ou du chapitre",
        fact="learning_unit.title",
    ),
    FieldSpec(
        "titre_unite_enseignement",
        "Unité d'enseignement / Leçon",
        "Titre de l'unité d'enseignement ou de la leçon",
        fact="teaching_unit.title",
    ),
    FieldSpec("duree", "Durée", "Durée prévue", fact="teaching_unit.duration"),
    FieldSpec("type_seance", "Type de séance", "Type de séance", fact="teaching_unit.session_type"),
    FieldSpec(
        "digitalisation",
        "Digitalisation",
        "Unité digitalisée ou non (OUI/NON)",
        fact="teaching_unit.digitalized",
    ),
    FieldSpec(
        "savoirs_essentiels",
        "Savoirs essentiels",
        "Savoirs essentiels du projet pédagogique",
        fact="teaching_unit.essential_knowledge",
    ),
    FieldSpec(
        "actions", "Actions", "Actions prévues au projet pédagogique", fact="teaching_unit.actions"
    ),
)

GENERATIVE_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("objectifs", "Objectifs", "Objectifs d'apprentissage de la séance"),
    FieldSpec("prerequis", "Prérequis", "Ce que l'élève doit déjà maîtriser"),
    FieldSpec(
        "situation_probleme",
        "Situation-problème",
        "Situation-problème contextualisée, réaliste pour des élèves camerounais",
    ),
    FieldSpec(
        "activites", "Activités", "Déroulement proposé : activités de l'enseignant et de l'élève"
    ),
)

COURSE_SHEET_FIELDS: tuple[FieldSpec, ...] = REFERENCE_FIELDS + GENERATIVE_FIELDS
GENERATIVE_NAMES: frozenset[str] = frozenset(spec.name for spec in GENERATIVE_FIELDS)
