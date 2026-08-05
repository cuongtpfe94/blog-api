from fastapi import FastAPI

from app.configs.env import get_settings
from app.configs.logging import configure_logging
from app.controllers.auth_controller import router as auth_router
from app.controllers.health_controller import router as health_router
from app.controllers.user_controller import router as user_router
from app.core.exceptions.base import BaseAPIError
from app.core.exceptions.exception_handlers import base_api_error_handler


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        debug=settings.debug,
    )

    app.include_router(health_router)
    app.include_router(user_router)
    app.include_router(auth_router)

    # pyrefly: ignore [bad-argument-type]
    app.add_exception_handler(BaseAPIError, base_api_error_handler)

    return app


app = create_app()
