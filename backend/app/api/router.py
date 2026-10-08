from fastapi import APIRouter

from app.api.routes import auth, context, generation, ingestion, profile

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(context.router)
api_router.include_router(ingestion.router)
api_router.include_router(generation.router)


@api_router.get("/readiness", tags=["system"])
def readiness() -> dict[str, str]:
    """Distincte de /health (racine) : confirme que le routeur applicatif
    complet (auth, profil, ...) est chargé, pas seulement le process."""
    return {"status": "ready"}
