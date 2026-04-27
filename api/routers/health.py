"""Health router — public endpoint used by Cloud Run health checks."""
from fastapi import APIRouter

from api.schemas.health import HealthResponse

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Public health endpoint — no auth required.

    :returns: HealthResponse with status "ok".
    """
    return HealthResponse(status="ok")
