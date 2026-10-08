"""Modèles de contexte enseignant.

Ces tables correspondent au schéma de départ décrit dans
docs/ARCHITECTURE.md : teacher, institution, school_year, subject,
classroom, teaching_assignment. On y ajoute `AuthSession`, nécessaire
pour la connexion locale (issue #7) mais absente du schéma initial —
c'est le genre de petit écart qu'on documente plutôt que de cacher.

Notes pédagogiques (niveau 0) :
- `Mapped[str]` etc. sont des annotations de type : elles disent à
  SQLAlchemy (et à vous) quel type Python correspond à quelle colonne.
- `mapped_column(unique=True)` crée une contrainte d'unicité en base :
  la base de données elle-même refusera un deuxième enseignant avec le
  même email, même si le code applicatif avait un bug.
- Les relations (`relationship`) ne créent pas de colonne ; elles
  donnent juste un raccourci Python pratique (ex. `teacher.institution`).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Institution(Base):
    """Un établissement scolaire (ex. Lycée Technique d'Ébolowa)."""

    __tablename__ = "institution"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)

    teachers: Mapped[list[Teacher]] = relationship(back_populates="institution")


class Teacher(Base):
    """Un enseignant — le compte utilisateur principal de NkulIA."""

    __tablename__ = "teacher"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    last_name: Mapped[str] = mapped_column(String(120))
    first_name: Mapped[str] = mapped_column(String(120))
    subject_taught: Mapped[str | None] = mapped_column(String(120), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(80), nullable=True)
    function: Mapped[str | None] = mapped_column(String(120), nullable=True)

    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institution.id"), nullable=True)
    institution: Mapped[Institution | None] = relationship(back_populates="teachers")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan"
    )


class SchoolYear(Base):
    """Une année scolaire (ex. 2025-2026), rattachée à un établissement."""

    __tablename__ = "school_year"
    __table_args__ = (UniqueConstraint("institution_id", "label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institution.id"))
    label: Mapped[str] = mapped_column(String(20))  # ex. "2025-2026"


class Subject(Base):
    """Une matière enseignée (ex. Informatique)."""

    __tablename__ = "subject"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Classroom(Base):
    """Une classe (ex. Seconde C, Niveau 1)."""

    __tablename__ = "classroom"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institution.id"))
    school_year_id: Mapped[int] = mapped_column(ForeignKey("school_year.id"))
    label: Mapped[str] = mapped_column(String(80))  # ex. "Seconde C", "Niveau 1"
    track: Mapped[str] = mapped_column(String(20))  # "generale" | "technique"
    headcount: Mapped[int | None] = mapped_column(nullable=True)


class TeachingAssignment(Base):
    """Le lien entre un enseignant, une classe et une matière."""

    __tablename__ = "teaching_assignment"
    __table_args__ = (UniqueConstraint("teacher_id", "classroom_id", "subject_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"))
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classroom.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"))


class AuthSession(Base):
    """Une session de connexion locale (issue #7).

    Volontairement simple : un jeton opaque stocké côté serveur, avec
    une date d'expiration. Pas de JWT ici — inutile en local, et plus
    facile à révoquer immédiatement (il suffit de supprimer la ligne).
    """

    __tablename__ = "auth_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    teacher: Mapped[Teacher] = relationship(back_populates="sessions")


class SourceDocument(Base):
    """Un document importé — fiche de progression ou projet pédagogique
    (issue #9). Conserve le fichier d'origine par son nom pour la
    traçabilité (un contenu généré doit pouvoir remonter à sa source,
    voir docs/ARCHITECTURE.md, contrat de génération).
    """

    __tablename__ = "source_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classroom.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"))
    filename: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(30))  # "fiche_progression" | "projet_pedagogique"

    # Vocabulaire détecté dans l'EN-TÊTE du document — voir
    # app/ingestion/track_schema.py. Ne préjuge pas du vocabulaire
    # réellement employé à l'intérieur des cellules, qui s'est avéré
    # incohérent avec l'en-tête dans le corpus réel (voir les notes du
    # parseur : un document technique dont l'en-tête dit "Chapitres"
    # peut malgré tout contenir des cellules "UA ...").
    track_schema: Mapped[str] = mapped_column(String(20))  # "ua_ue" | "chapitre_lecon"

    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Avertissements d'extraction, en JSON (ex. lignes "ÉVALUATION"
    # ignorées, valeur de digitalisation illisible) — jamais silencieux,
    # jamais une donnée pédagogique inventée à la place.
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    modules: Mapped[list[Module]] = relationship(
        back_populates="source_document", cascade="all, delete-orphan", order_by="Module.id"
    )


class Module(Base):
    __tablename__ = "module"
    __table_args__ = (UniqueConstraint("source_document_id", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    number: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))

    source_document: Mapped[SourceDocument] = relationship(back_populates="modules")
    learning_units: Mapped[list[LearningUnit]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="LearningUnit.id"
    )


class LearningUnit(Base):
    """Niveau intermédiaire — « Unité d'Apprentissage » ou « Chapitre »
    selon le `track_schema` du document source (voir docs/adr/0003).
    Le nom de la table reste neutre : jamais "ua" ni "chapitre" en dur,
    conformément à la règle non négociable de docs/ARCHITECTURE.md.
    """

    __tablename__ = "learning_unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("module.id"))
    number: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))

    module: Mapped[Module] = relationship(back_populates="learning_units")
    teaching_units: Mapped[list[TeachingUnit]] = relationship(
        back_populates="learning_unit", cascade="all, delete-orphan", order_by="TeachingUnit.id"
    )


class TeachingUnit(Base):
    """Niveau le plus fin — « Unité d'Enseignement » ou « Leçon ».

    `digitalized` est un booléen NULLABLE et non un `str` : `None`
    signifie « absent ou illisible dans le référentiel », jamais
    déduit ni forcé à `False` par défaut — voir docs/adr/0003, §3.3 du
    dossier de cadrage (digitalisation strictement binaire, sans état
    PARTIELLE).
    """

    __tablename__ = "teaching_unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    learning_unit_id: Mapped[int] = mapped_column(ForeignKey("learning_unit.id"))
    number: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    digitalized: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Colonnes optionnelles, présentes uniquement dans un Projet
    # pédagogique (voir §3.2 du dossier de cadrage) — `None` dans une
    # simple Fiche de progression.
    actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    essential_knowledge: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    session_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    learning_unit: Mapped[LearningUnit] = relationship(back_populates="teaching_units")


class GeneratedDocument(Base):
    """Un document produit par la génération (issue #13) — ici, une fiche
    de cours. Son `status` suit le cycle de docs/ARCHITECTURE.md
    (voir app/generation/lifecycle.py)."""

    __tablename__ = "generated_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"))
    teaching_unit_id: Mapped[int] = mapped_column(ForeignKey("teaching_unit.id"))
    kind: Mapped[str] = mapped_column(String(30), default="course_sheet")
    status: Mapped[str] = mapped_column(String(20))
    provider_name: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teaching_unit: Mapped[TeachingUnit] = relationship()
    fields: Mapped[list[GeneratedField]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="GeneratedField.position"
    )


class GeneratedField(Base):
    """Un champ d'un document généré, avec son étiquette de provenance.

    `edited_by_teacher` est ORTHOGONAL à `provenance` (ADR-0004) :
    l'étiquette dit d'où venait la proposition initiale, le booléen dit
    que l'enseignant l'a depuis modifiée ou complétée.
    """

    __tablename__ = "generated_field"
    __table_args__ = (UniqueConstraint("generated_document_id", "field"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    generated_document_id: Mapped[int] = mapped_column(ForeignKey("generated_document.id"))
    position: Mapped[int] = mapped_column()
    field: Mapped[str] = mapped_column(String(60))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance: Mapped[str] = mapped_column(String(30))
    source_ref: Mapped[str | None] = mapped_column(String(400), nullable=True)
    edited_by_teacher: Mapped[bool] = mapped_column(Boolean, default=False)

    document: Mapped[GeneratedDocument] = relationship(back_populates="fields")
