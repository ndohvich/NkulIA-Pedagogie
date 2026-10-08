"""Détection des colonnes et du vocabulaire de filière (issue #10).

Le `track_schema` (« ua_ue » vs « chapitre_lecon ») se lit UNIQUEMENT
sur les libellés de l'en-tête du tableau, jamais sur le contenu des
cellules — voir la note de conception en tête de docx_parser.py pour
la raison (en-tête et contenu peuvent diverger dans le corpus réel).

Deux en-têtes réels observés pour la même position de colonne :
  Général  : "UNITES D'APPRENTISSAGE"  / "UNITES D'ENSEIGNEMENT"
  Technique: "N°ET TITRE DES CHAPITRES" / "N°ET TITRE DES LEÇONS"
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.schemas.ingestion import TrackSchema


def _normalize_header(text: str) -> str:
    """Majuscules, sans accents, espaces insécables et doubles espaces
    aplatis — pour comparer des en-têtes robustement, quelle que soit
    la façon dont Word les a enregistrés."""
    text = text.replace("\xa0", " ")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"\s+", " ", text)
    return text.strip().upper()


@dataclass
class HeaderColumns:
    module: int
    learning_unit: int
    teaching_unit: int
    digitalisation: int
    actions: int | None = None
    essential_knowledge: int | None = None
    duration: int | None = None
    session_type: int | None = None


# Chaque motif est cherché avec `in`, pas une égalité stricte : les
# en-têtes réels varient ("N°ET" sans espace, "N° ET" avec espace...).
_MODULE_PATTERNS = ["MODULE"]
_LEARNING_UNIT_UA_PATTERNS = ["UNITE", "UNITES D'APPRENTISSAGE", "APPRENTISSAGE"]
_LEARNING_UNIT_CHAPITRE_PATTERNS = ["CHAPITRE"]
_TEACHING_UNIT_PATTERNS = ["ENSEIGNEMENT", "LECON"]
_DIGITALISATION_PATTERNS = ["DIGITALISATION"]
_ACTIONS_PATTERNS = ["ACTION"]
_ESSENTIAL_KNOWLEDGE_PATTERNS = ["SAVOIR"]
_DURATION_PATTERNS = ["DUREE"]
_SESSION_TYPE_PATTERNS = ["TYPE"]


def _find_column(headers: list[str], patterns: list[str]) -> int | None:
    for index, header in enumerate(headers):
        if any(pattern in header for pattern in patterns):
            return index
    return None


def detect_columns(raw_headers: list[str]) -> tuple[HeaderColumns, TrackSchema]:
    """Analyse la ligne d'en-tête d'un tableau et renvoie l'index de
    chaque colonne reconnue, ainsi que le vocabulaire de filière.

    Lève `ValueError` si une colonne obligatoire (Module, unité
    intermédiaire, unité fine, Digitalisation) est introuvable — on
    préfère un échec explicite à l'import plutôt qu'un import silencieux
    sur de mauvaises colonnes.
    """
    headers = [_normalize_header(h) for h in raw_headers]

    module_index = _find_column(headers, _MODULE_PATTERNS)

    chapitre_index = _find_column(headers, _LEARNING_UNIT_CHAPITRE_PATTERNS)
    ua_index = _find_column(headers, _LEARNING_UNIT_UA_PATTERNS)
    # "CHAPITRE" est vérifié en premier : "UNITE D'ENSEIGNEMENT" contient
    # aussi implicitement le mot "UNITE", donc l'ordre des motifs UA
    # pourrait sinon accrocher la mauvaise colonne sur certains en-têtes.
    learning_unit_index: int | None
    track_schema: TrackSchema
    if chapitre_index is not None:
        learning_unit_index, track_schema = chapitre_index, "chapitre_lecon"
    elif ua_index is not None:
        learning_unit_index, track_schema = ua_index, "ua_ue"
    else:
        learning_unit_index, track_schema = None, "ua_ue"

    teaching_unit_index = _find_column(headers, _TEACHING_UNIT_PATTERNS)
    digitalisation_index = _find_column(headers, _DIGITALISATION_PATTERNS)

    missing = [
        name
        for name, index in [
            ("Module", module_index),
            ("Unité d'apprentissage / Chapitre", learning_unit_index),
            ("Unité d'enseignement / Leçon", teaching_unit_index),
            ("Digitalisation", digitalisation_index),
        ]
        if index is None
    ]
    if missing:
        raise ValueError(
            "Colonnes obligatoires introuvables dans l'en-tête du document : "
            + ", ".join(missing)
            + f". En-têtes lus : {raw_headers!r}"
        )

    columns = HeaderColumns(
        module=module_index,  # type: ignore[arg-type]
        learning_unit=learning_unit_index,  # type: ignore[arg-type]
        teaching_unit=teaching_unit_index,  # type: ignore[arg-type]
        digitalisation=digitalisation_index,  # type: ignore[arg-type]
        actions=_find_column(headers, _ACTIONS_PATTERNS),
        essential_knowledge=_find_column(headers, _ESSENTIAL_KNOWLEDGE_PATTERNS),
        duration=_find_column(headers, _DURATION_PATTERNS),
        session_type=_find_column(headers, _SESSION_TYPE_PATTERNS),
    )
    return columns, track_schema
