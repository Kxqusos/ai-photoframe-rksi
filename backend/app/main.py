from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth import router as admin_auth_router
from app.config import configure_logging, settings
from app.db import init_db
from app.routers import jobs, media, prompts, settings as settings_router

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    configure_logging()
    init_db()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(settings_router.router)
app.include_router(admin_auth_router)
app.include_router(prompts.router)
app.include_router(media.router)
app.include_router(jobs.router)
app.include_router(jobs.public_router)
app.mount("/media", StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "storage")), name="media")
