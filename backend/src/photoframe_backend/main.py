from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import DATABASE_URL, DEFAULT_ROOM_SLUG, engine
from photoframe_backend.api.http.routers import admin, jobs, media, prompts, rooms, settings as settings_router
from photoframe_backend.api.http.routers.auth import router as admin_auth_router
from photoframe_backend.infrastructure.db.bootstrap import bootstrap_default_room
from photoframe_backend.shared.logging import configure_logging

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    configure_logging()
    bootstrap_default_room(engine=engine, database_url=DATABASE_URL, default_room_slug=DEFAULT_ROOM_SLUG)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(settings_router.router)
app.include_router(admin_auth_router)
app.include_router(admin.router)
app.include_router(rooms.router)
app.include_router(prompts.router)
app.include_router(prompts.room_router)
app.include_router(media.router)
app.include_router(jobs.router)
app.include_router(jobs.room_router)
app.include_router(jobs.public_router)
app.mount(
    "/media",
    StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "storage")),
    name="media",
)
