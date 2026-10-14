import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    get_initiative_engine,
    get_initiative_store,
    get_goal_engine,
    get_goal_store,
    router,
)
from app.application.initiative_autonomy_loop import InitiativeAutonomyLoop
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    autonomy_loop: InitiativeAutonomyLoop | None = None
    autonomy_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal autonomy_loop, autonomy_task
        initiative_engine = get_initiative_engine()
        initiative_store = get_initiative_store()
        if not settings.initiative_autonomy_enabled:
            initiative_engine.state.autonomy_enabled = False
            initiative_store.save_engine(initiative_engine)

        autonomy_loop = InitiativeAutonomyLoop(
            engine=initiative_engine,
            store=initiative_store,
            tick_seconds=settings.initiative_tick_seconds,
            idle_threshold_seconds=settings.initiative_idle_threshold_seconds,
            cooldown_seconds=settings.initiative_cooldown_seconds,
            goal_engine=get_goal_engine(),
            goal_store=get_goal_store(),
        )
        autonomy_task = asyncio.create_task(autonomy_loop.run())
        try:
            yield
        finally:
            if autonomy_loop is not None:
                autonomy_loop.stop()
            if autonomy_task is not None:
                autonomy_task.cancel()
                try:
                    await autonomy_task
                except asyncio.CancelledError:
                    pass

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Aletheia Local MVP API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/health", tags=["System"])
    async def health() -> dict:
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    return app