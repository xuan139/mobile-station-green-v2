from fastapi import APIRouter

from green_v2.application.health import get_service_status
from green_v2.config import Settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = Settings.from_env()
    return get_service_status(settings.app_version).to_dict()


@router.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/api/v1/ping")
def ping() -> dict[str, str]:
    return {"message": "pong", "service": "green-v2-api"}

