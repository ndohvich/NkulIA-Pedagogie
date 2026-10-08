"""Schémas du contexte d'enseignement : matières et classes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SubjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class SubjectOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ClassroomIn(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    track: Literal["generale", "technique"]
    # « 2025-2026 ». Omis : année scolaire en cours (voir routes/context.py).
    school_year_label: str | None = Field(default=None, pattern=r"^\d{4}-\d{4}$")


class ClassroomOut(BaseModel):
    id: int
    label: str
    track: str
    school_year_label: str
