"""Contexte d'enseignement : matières et classes de l'enseignant.

Ces routes comblent un manque réel : l'import (issue #9) exige une
classe et une matière existantes, mais rien ne permettait de les créer
depuis l'interface — les tests les insérant directement en base.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.models import Classroom, SchoolYear, Subject, Teacher
from app.db.session import get_db
from app.schemas.context import ClassroomIn, ClassroomOut, SubjectIn, SubjectOut

router = APIRouter(prefix="/context", tags=["context"])


def current_school_year_label(today: date | None = None) -> str:
    """Année scolaire en cours : elle commence en septembre (calendrier
    camerounais), donc octobre 2026 appartient à « 2026-2027 » et mars
    2027 à « 2026-2027 » également."""
    today = today or date.today()
    start = today.year if today.month >= 9 else today.year - 1
    return f"{start}-{start + 1}"


def _classroom_out(classroom: Classroom, school_year: SchoolYear) -> ClassroomOut:
    return ClassroomOut(
        id=classroom.id,
        label=classroom.label,
        track=classroom.track,
        school_year_label=school_year.label,
    )


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db),
    _teacher: Teacher = Depends(get_current_teacher),
) -> list[Subject]:
    return db.query(Subject).order_by(Subject.name).all()


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectIn,
    db: Session = Depends(get_db),
    _teacher: Teacher = Depends(get_current_teacher),
) -> Subject:
    name = payload.name.strip()
    subject = db.query(Subject).filter(Subject.name == name).first()
    if subject is None:  # idempotent : redéclarer une matière renvoie l'existante
        subject = Subject(name=name)
        db.add(subject)
        db.commit()
        db.refresh(subject)
    return subject


@router.get("/classrooms", response_model=list[ClassroomOut])
def list_classrooms(
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> list[ClassroomOut]:
    if teacher.institution_id is None:
        return []
    rows = (
        db.query(Classroom, SchoolYear)
        .join(SchoolYear, Classroom.school_year_id == SchoolYear.id)
        .filter(Classroom.institution_id == teacher.institution_id)
        .order_by(SchoolYear.label.desc(), Classroom.label)
        .all()
    )
    return [_classroom_out(classroom, school_year) for classroom, school_year in rows]


@router.post("/classrooms", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
def create_classroom(
    payload: ClassroomIn,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> ClassroomOut:
    if teacher.institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Renseignez d'abord votre établissement dans votre profil.",
        )

    label = payload.label.strip()
    year_label = payload.school_year_label or current_school_year_label()

    school_year = (
        db.query(SchoolYear)
        .filter_by(institution_id=teacher.institution_id, label=year_label)
        .first()
    )
    if school_year is None:
        school_year = SchoolYear(institution_id=teacher.institution_id, label=year_label)
        db.add(school_year)
        db.flush()

    already_there = (
        db.query(Classroom)
        .filter_by(
            institution_id=teacher.institution_id, school_year_id=school_year.id, label=label
        )
        .first()
    )
    if already_there is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La classe « {label} » existe déjà pour {year_label}.",
        )

    classroom = Classroom(
        institution_id=teacher.institution_id,
        school_year_id=school_year.id,
        label=label,
        track=payload.track,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return _classroom_out(classroom, school_year)
