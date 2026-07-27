from fastapi import FastAPI

from app.configs.env import get_settings
from app.controllers.health_controller import router as health_router
from app.controllers.user_controller import router as user_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        debug=settings.debug,
    )

    app.include_router(health_router)
    app.include_router(user_router)

    return app


app = create_app()
