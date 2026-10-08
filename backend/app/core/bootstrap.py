"""Préparation de la base au démarrage de l'application desktop.

Sans ceci, l'exécutable packagé démarrerait sur une base VIDE : aucune
table, donc la première inscription échouerait. En développement on
lance `make migrate` à la main ; sur le poste d'un enseignant, personne
ne le fera — l'application applique donc elle-même les migrations.
"""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[2]


def user_data_dir(platform: str | None = None, env: dict[str, str] | None = None) -> Path:
    """Dossier de données par utilisateur : jamais dans le dossier de l'exécutable
    (en lecture seule ou écrasé à chaque mise à jour)."""
    platform = platform or os.name
    env = env if env is not None else dict(os.environ)
    if platform == "nt":
        base = Path(env.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(env.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "NkulIA"


def apply_migrations() -> None:
    """Amène la base configurée (NKULIA_DB_PATH) au dernier schéma. Idempotent."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(config, "head")
