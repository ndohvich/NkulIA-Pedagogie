"""Représentation intermédiaire d'un document importé, avant
persistance en base (voir app/ingestion/docx_parser.py, qui produit
ces objets, et app/ingestion/persist.py, qui les enregistre).

Séparer cette étape de la persistance permet de tester le parseur seul
(donner un fichier, vérifier la structure obtenue) sans avoir besoin
d'une base de données — voir tests/unit/test_docx_parser.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TrackSchema = Literal["ua_ue", "chapitre_lecon"]


class ParsedTeachingUnit(BaseModel):
    number: str
    title: str
    digitalized: bool | None = None

    # Colonnes optionnelles (Projet pédagogique uniquement — §3.2 du
    # dossier de cadrage). `None` dans une simple Fiche de progression.
    actions: str | None = None
    essential_knowledge: str | None = None
    duration_label: str | None = None
    session_type: str | None = None


class ParsedLearningUnit(BaseModel):
    number: str
    title: str
    teaching_units: list[ParsedTeachingUnit] = []


class ParsedModule(BaseModel):
    number: str
    title: str
    learning_units: list[ParsedLearningUnit] = []


class ParsedDocument(BaseModel):
    """Résultat complet de l'extraction d'un fichier .docx.

    `warnings` n'est jamais vide « par défaut » dans un vrai corpus —
    voir la découverte faite sur le corpus réel (lignes ÉVALUATION /
    REMEDIATION, coquilles comme "NION"). Une liste vide signifie
    « extraction propre », pas « warnings non implémentés ».
    """

    kind: Literal["fiche_progression", "projet_pedagogique"]
    track_schema: TrackSchema
    modules: list[ParsedModule] = []
    warnings: list[str] = []


class ImportSummary(BaseModel):
    """Réponse renvoyée après un import réussi — un résumé, pas la
    hiérarchie complète (récupérable ensuite via GET /documents/{id})."""

    document_id: int
    filename: str
    kind: Literal["fiche_progression", "projet_pedagogique"]
    track_schema: TrackSchema
    module_count: int
    learning_unit_count: int
    teaching_unit_count: int
    warnings: list[str] = []


class SourceDocumentOut(BaseModel):
    """Une ligne de la liste « documents importés » (écran Import)."""

    id: int
    filename: str
    kind: str
    track_schema: str
    imported_at: datetime
    module_count: int = 0
    learning_unit_count: int = 0
    teaching_unit_count: int = 0
    warning_count: int = 0


class TeachingUnitOut(BaseModel):
    id: int
    number: str
    title: str
    digitalized: bool | None
    actions: str | None
    essential_knowledge: str | None
    duration_label: str | None
    session_type: str | None

    model_config = {"from_attributes": True}


class LearningUnitOut(BaseModel):
    id: int
    number: str
    title: str
    teaching_units: list[TeachingUnitOut]

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: int
    number: str
    title: str
    learning_units: list[LearningUnitOut]

    model_config = {"from_attributes": True}


class DocumentDetailOut(SourceDocumentOut):
    """Hiérarchie complète détectée — aperçu de l'écran Import (#11)."""

    modules: list[ModuleOut]
    warnings: list[str]
