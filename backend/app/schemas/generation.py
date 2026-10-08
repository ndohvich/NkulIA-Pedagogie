"""Schémas HTTP de la génération (issues #12 et #13)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.generation.provenance import Provenance


class CourseSheetRequest(BaseModel):
    teaching_unit_id: int


class GeneratedFieldOut(BaseModel):
    field: str
    label: str
    value: str | None
    provenance: Provenance
    source_ref: str | None
    edited_by_teacher: bool


class GeneratedDocumentOut(BaseModel):
    id: int
    teaching_unit_id: int
    kind: Literal["course_sheet"]
    status: Literal["brouillon", "analyse", "propose", "modifie", "valide"]
    provider_name: str
    created_at: datetime
    updated_at: datetime
    validated_at: datetime | None
    track_schema: str
    fields: list[GeneratedFieldOut]


class GeneratedDocumentSummary(BaseModel):
    id: int
    teaching_unit_id: int
    status: str
    updated_at: datetime


class FieldEditRequest(BaseModel):
    """Modifications de l'enseignant : `{nom_du_champ: nouvelle valeur}`."""

    fields: dict[str, str] = Field(min_length=1)


class ValidateRequest(BaseModel):
    # Valider une fiche qui comporte encore des « informations manquantes »
    # doit être un choix explicite, pas un clic distrait.
    acknowledge_missing: bool = False
