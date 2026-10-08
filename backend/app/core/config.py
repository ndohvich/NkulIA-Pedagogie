"""Configuration de l'API NkulIA.

Tout est lu depuis des variables d'environnement (avec des valeurs par
défaut adaptées au développement local), pour ne jamais coder en dur
un chemin de base de données ou une clé secrète — voir docs/ARCHITECTURE.md,
principe « offline-first » et règle de sécurité sur les clés/API.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# Dossier de données de l'utilisateur (à côté du backend en développement ;
# en production, desktop/main.py pointera vers un dossier utilisateur
# du système d'exploitation — voir docs/ARCHITECTURE.md §Distribution Windows).
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "nkulia.sqlite3"


class Settings:
    """Regroupe les réglages de l'application en un seul endroit.

    Utiliser des variables d'environnement permet de changer la config
    (ex. base de test, base de production) sans toucher au code.
    """

    def __init__(self) -> None:
        db_path = os.environ.get("NKULIA_DB_PATH", str(DEFAULT_DB_PATH))
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.database_url: str = f"sqlite:///{db_path}"

        # Clé utilisée pour signer les jetons de session. En développement,
        # une valeur par défaut évite de bloquer le démarrage ; en
        # production, NKULIA_SECRET_KEY doit être définie explicitement.
        self.secret_key: str = os.environ.get(
            "NKULIA_SECRET_KEY", "dev-secret-key-a-remplacer-en-production"
        )
        self.session_ttl_hours: int = int(os.environ.get("NKULIA_SESSION_TTL_HOURS", "12"))

        # Génération (ADR-0005). « offline » par défaut : aucun réseau requis.
        # La clé API vient UNIQUEMENT de l'environnement — jamais du code, jamais
        # de la base, jamais des logs.
        self.llm_provider: str = os.environ.get("NKULIA_LLM_PROVIDER", "offline")
        self.llm_api_key: str | None = os.environ.get("NKULIA_LLM_API_KEY") or None
        self.llm_model: str = os.environ.get("NKULIA_LLM_MODEL", "claude-sonnet-5-5")
        self.llm_base_url: str = os.environ.get("NKULIA_LLM_BASE_URL", "https://api.anthropic.com")


@lru_cache
def get_settings() -> Settings:
    """Renvoie toujours la même instance de Settings (chargée une seule fois)."""
    return Settings()
