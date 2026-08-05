from app.core.exceptions.base import BaseAPIError
from app.schemas.response.base import ErrorResponse
from fastapi import Request
from fastapi.responses import JSONResponse


async def base_api_error_handler(request: Request, exc: BaseAPIError) -> JSONResponse:
    body = ErrorResponse(
        message=exc.message,
        error_code=exc.error_code,
        extra=exc.extra,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(),
    )
