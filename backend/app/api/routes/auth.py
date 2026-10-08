"""Routes d'authentification locale (issue #6).

Trois routes volontairement simples : pas de OAuth, pas de fournisseur
d'identité externe — cohérent avec l'authentification locale décidée
pour une application offline-first (docs/adr/0001).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.security import (
    generate_session_token,
    hash_password,
    session_expiry,
    verify_password,
)
from app.db.models import AuthSession, Teacher
from app.db.session import get_db
from app.schemas.teacher import SessionOut, TeacherLogin, TeacherProfileOut, TeacherRegister
from app.services.institutions import get_or_create_institution

router = APIRouter(prefix="/auth", tags=["auth"])


def _profile_out(teacher: Teacher) -> TeacherProfileOut:
    """Construit la réponse publique à partir du modèle interne — voir
    schemas/teacher.py pour pourquoi ces deux représentations diffèrent."""
    return TeacherProfileOut(
        id=teacher.id,
        email=teacher.email,
        last_name=teacher.last_name,
        first_name=teacher.first_name,
        subject_taught=teacher.subject_taught,
        specialty=teacher.specialty,
        grade=teacher.grade,
        function=teacher.function,
        institution_name=teacher.institution.name if teacher.institution else None,
    )


def _create_session(db: Session, teacher: Teacher) -> str:
    token = generate_session_token()
    db.add(AuthSession(token=token, teacher_id=teacher.id, expires_at=session_expiry()))
    db.commit()
    return token


@router.post("/register", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def register(payload: TeacherRegister, db: Session = Depends(get_db)) -> SessionOut:
    institution = (
        get_or_create_institution(db, payload.institution_name)
        if payload.institution_name
        else None
    )

    teacher = Teacher(
        email=payload.email,
        password_hash=hash_password(payload.password),
        last_name=payload.last_name,
        first_name=payload.first_name,
        subject_taught=payload.subject_taught,
        institution=institution,
    )
    db.add(teacher)
    try:
        db.commit()
    except IntegrityError as exc:
        # La contrainte unique sur `email` (voir app/db/models.py) est la
        # dernière ligne de défense si deux requêtes arrivent en même
        # temps — le message reste volontairement générique.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email.",
        ) from exc

    db.refresh(teacher)
    token = _create_session(db, teacher)
    return SessionOut(token=token, teacher=_profile_out(teacher))


@router.post("/login", response_model=SessionOut)
def login(payload: TeacherLogin, db: Session = Depends(get_db)) -> SessionOut:
    teacher = db.query(Teacher).filter(Teacher.email == payload.email).first()

    # Message identique que l'email soit inconnu ou le mot de passe faux :
    # ne jamais révéler laquelle des deux informations est incorrecte.
    erreur = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou mot de passe incorrect.",
    )
    if teacher is None:
        raise erreur
    if not verify_password(payload.password, teacher.password_hash):
        raise erreur

    token = _create_session(db, teacher)
    return SessionOut(token=token, teacher=_profile_out(teacher))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
) -> None:
    # On supprime toutes les sessions de cet enseignant plutôt qu'une
    # seule : un "déconnecter partout" simple et prévisible, adapté à
    # un compte local où la notion de "cet appareil" n'a pas de sens.
    db.query(AuthSession).filter(AuthSession.teacher_id == teacher.id).delete()
    db.commit()
