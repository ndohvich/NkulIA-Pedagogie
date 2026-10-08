"""Gestion partagée des établissements (inscription et profil).

Un établissement est identifié par son nom : le saisir deux fois à
l'identique (inscription, puis modification du profil) doit désigner
la même ligne en base, jamais créer un doublon.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Institution


def get_or_create_institution(db: Session, name: str) -> Institution:
    """Renvoie l'établissement de ce nom, en le créant s'il n'existe pas.

    Utilise `flush()` et non `commit()` : l'appelant garde la maîtrise
    de la transaction (il peut encore l'annuler en cas d'erreur).
    """
    institution = db.query(Institution).filter_by(name=name).first()
    if institution is None:
        institution = Institution(name=name)
        db.add(institution)
        db.flush()
    return institution
