from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.schemas.common import DataResponse
from backend.app.schemas.health import HealthStatus, ReadinessStatus
from backend.app.services.health_service import HealthService

router = APIRouter()


@router.get("/health", response_model=DataResponse[HealthStatus], summary="Basic Health Check")
def get_health():
    """
    Returns basic service health status, timestamp, and environment.
    """
    return {"data": HealthService.get_live_status()}


@router.get("/health/ready", summary="Readiness Check")
@router.get("/health/readiness", summary="Readiness Check Alias")
def get_readiness():
    """
    Readiness check verifying database connectivity and dependent services.
    Returns HTTP 200 when ready, HTTP 503 Service Unavailable when DB is unreachable.
    """
    status_data = HealthService.get_readiness_status()
    is_ready = status_data["status"] == "ready"
    http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=http_status, content={"data": status_data})
