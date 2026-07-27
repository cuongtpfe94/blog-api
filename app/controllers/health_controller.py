from app.configs.env import get_settings
from app.dependencies.db import get_db
from app.schemas.response.database_health_out_schema import DatabaseHealthResponse
from app.schemas.response.health_out_schema import HealthResponse
from app.services.database_health_service import DatabaseHealthService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="health check",
)
async def health_check() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="database health check",
)
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> DatabaseHealthResponse:
    service = DatabaseHealthService(db)

    is_connected = await service.check_database_connection()

    return DatabaseHealthResponse(
        status="ok" if is_connected else "error",
        database="connected" if is_connected else "disconnected",
    )
