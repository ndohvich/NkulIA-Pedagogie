"""Schémas Pydantic — la frontière de validation entre l'extérieur
(requêtes HTTP) et le code métier.

Pourquoi séparer ces classes des modèles SQLAlchemy (app/db/models.py) ?
Un modèle SQLAlchemy décrit une table ; un schéma Pydantic décrit une
requête ou une réponse HTTP. Les deux se ressemblent souvent mais pas
toujours (ex. `password` existe en entrée d'inscription, jamais en
sortie) — les garder séparés évite qu'un champ interne (comme
`password_hash`) ne fuite un jour dans une réponse API par accident.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


class TeacherRegister(BaseModel):
    """Données attendues pour créer un compte enseignant."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    last_name: str = Field(min_length=1, max_length=120)
    first_name: str = Field(min_length=1, max_length=120)
    institution_name: str | None = Field(default=None, max_length=200)
    subject_taught: str | None = Field(default=None, max_length=120)

    @field_validator("password")
    @classmethod
    def password_must_have_a_digit(cls, value: str) -> str:
        """Règle simple et honnête pour un outil pédagogique local : au
        moins un chiffre. On évite les règles de complexité excessives
        qui poussent les gens à écrire leur mot de passe sur un post-it."""
        if not any(char.isdigit() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        return value


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str


class TeacherProfileOut(BaseModel):
    """Ce que l'API renvoie pour décrire un enseignant — jamais le mot
    de passe ni son empreinte, même hachée."""

    id: int
    email: str
    last_name: str
    first_name: str
    subject_taught: str | None
    specialty: str | None
    grade: str | None
    function: str | None
    institution_name: str | None

    model_config = {"from_attributes": True}


class TeacherProfileUpdate(BaseModel):
    """Champs modifiables depuis l'écran Profil — tous optionnels,
    seuls les champs envoyés sont mis à jour (voir routes/profile.py)."""

    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    subject_taught: str | None = Field(default=None, max_length=120)
    specialty: str | None = Field(default=None, max_length=120)
    grade: str | None = Field(default=None, max_length=80)
    function: str | None = Field(default=None, max_length=120)
    # Chaîne vide ou null : détache l'enseignant de son établissement.
    institution_name: str | None = Field(default=None, max_length=200)


class SessionOut(BaseModel):
    """Réponse renvoyée après une inscription ou une connexion réussie."""

    token: str
    teacher: TeacherProfileOut
