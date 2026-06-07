from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logger import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Aletheia Local MVP API",
    )

    @app.get("/health", tags=["System"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    app.include_router(router)
    return app
