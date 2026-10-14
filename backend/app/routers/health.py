"""Endpoints de salud del servicio."""

from fastapi import APIRouter, HTTPException, Request

from ..schemas.system import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthStatus)
def health_live(request: Request) -> HealthStatus:
    return HealthStatus(status="ok", model_ready=False)


@router.get("/health/ready", response_model=HealthStatus)
def health_ready(request: Request) -> HealthStatus:
    settings = request.app.state.settings
    if not settings.database_path.exists():
        raise HTTPException(status_code=503, detail="base de datos no disponible")
    return HealthStatus(status="ready", model_ready=False)
