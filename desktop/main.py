"""
desktop/main.py — Lanceur PyWebView pour NkulIA (version corrigée)
====================================================================

Corrige deux des bugs P1 signalés par la revue automatique Codex sur la PR #1 :

  1. Résolution des ressources en mode packagé (PyInstaller onedir 6.10+) :
     `Path(__file__).resolve().parents[1]` ne fonctionne qu'en mode source.
     Une fois figé par PyInstaller, ce script tourne depuis le dossier
     `_internal`, et non plus depuis l'arborescence du dépôt : on utilise
     `sys._MEIPASS` quand il existe (mode packagé), avec repli sur
     l'arborescence source sinon.

  2. Import dynamique de FastAPI non détecté par PyInstaller : le code
     original démarre uvicorn avec la chaîne "app.main:app", qu'aucune
     analyse statique ne peut suivre. On importe explicitement
     `app.main` en haut du fichier et on passe l'objet application
     directement à uvicorn — PyInstaller voit alors l'import comme
     n'importe quel autre.

Corrige aussi le bug P1 sur les chemins Vite (assets en /assets/... non
résolus en fichier local) d'une manière plus robuste que le correctif
proposé par Codex : plutôt que de compter sur un chemin relatif fragile,
on sert le build React directement depuis FastAPI (StaticFiles), et la
fenêtre PyWebView pointe toujours sur une URL http://127.0.0.1, jamais
sur un chemin file://. Cela élimine aussi tout risque de blocage CORS
entre la fenêtre et l'API — les deux partagent désormais la même origine.
"""

import argparse
import os
import sys
import threading
import time
from pathlib import Path

import webview


def get_ressources_dir() -> Path:
    """
    Renvoie le dossier à partir duquel lire 'backend' et 'frontend/dist'.

    - En mode packagé (exécutable PyInstaller), sys._MEIPASS pointe vers
      le dossier où PyInstaller a copié tout ce qui a été déclaré avec
      --add-data (le dossier _internal en mode onedir).
    - En mode développement (python desktop/main.py), il n'existe pas :
      on remonte simplement à la racine du dépôt.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass)
    return Path(__file__).resolve().parents[1]


RESSOURCES = get_ressources_dir()

# La base vit dans le dossier de données de l'utilisateur, JAMAIS à côté de
# l'exécutable. Doit être défini AVANT d'importer l'application : la
# configuration lit cette variable à l'import (voir app/core/config.py).
sys.path.insert(0, str(RESSOURCES / "backend"))
from app.core.bootstrap import apply_migrations, user_data_dir  # noqa: E402

os.environ.setdefault("NKULIA_DB_PATH", str(user_data_dir() / "nkulia.sqlite3"))

# Import explicite (et non plus une chaîne "app.main:app") pour que
# PyInstaller détecte fastapi, starlette, pydantic, etc. comme de vraies
# dépendances de CE script, au lieu de les traiter comme de simples
# fichiers de données copiés sans analyse.
from app.main import app as fastapi_app  # noqa: E402  (import après sys.path, volontaire)

# On monte le build React comme fichiers statiques de la même API : la
# fenêtre PyWebView n'ouvrira donc jamais un chemin file://, seulement
# http://127.0.0.1:8000/. Fini les soucis de chemins d'assets ou de CORS.
from fastapi.staticfiles import StaticFiles  # noqa: E402

FRONTEND_DIST = RESSOURCES / "frontend" / "dist"
if FRONTEND_DIST.exists():
    fastapi_app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


def demarrer_api() -> None:
    """Lance uvicorn dans un thread séparé, avec l'objet app importé directement
    (et non plus une chaîne) — nécessaire pour que PyInstaller embarque bien
    FastAPI et ses dépendances dans l'exécutable final."""
    import uvicorn

    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")


def attendre_que_l_api_reponde(url: str, tentatives: int = 40, delai: float = 0.15) -> bool:
    """
    Remplace le `time.sleep(0.8)` fixe du script d'origine — un délai figé
    est fragile (trop court sur une machine lente, trop long sur une machine
    rapide). On sonde /health jusqu'à obtenir une réponse, ou on abandonne
    après un nombre raisonnable de tentatives.
    """
    import urllib.request

    for _ in range(tentatives):
        try:
            with urllib.request.urlopen(url, timeout=0.5) as reponse:
                if reponse.status == 200:
                    return True
        except Exception:
            time.sleep(delai)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Lanceur desktop NkulIA")
    parser.add_argument("--dev", action="store_true", help="Mode développement (frontend servi par Vite)")
    args = parser.parse_args()

    # Schéma de base à jour avant d'accepter la moindre requête (voir bootstrap.py).
    apply_migrations()

    threading.Thread(target=demarrer_api, daemon=True).start()
    attendre_que_l_api_reponde("http://127.0.0.1:8000/health")

    # En dev, le frontend tourne séparément via `npm run dev` (Vite, port 5173).
    # En production, tout est servi par l'unique serveur FastAPI ci-dessus.
    url = "http://localhost:5173" if args.dev else "http://127.0.0.1:8000"

    webview.create_window("NkulIA", url, width=1440, height=900, min_size=(1024, 700))
    webview.start()


if __name__ == "__main__":
    main()
