from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend import database
from backend.api.router import api_router
from backend.config import get_settings
from backend.seed import seed_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("maslobox")


def _ensure_sqlite_parent(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    raw = database_url.removeprefix("sqlite:///")
    # sqlite:////data/file.db → /data/file.db ; sqlite:///./local.db → ./local.db
    path = Path(raw)
    if path.parent and str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)


def _resolve_static_dir() -> Path | None:
    candidates = [
        os.getenv("STATIC_DIR"),
        str(Path(__file__).resolve().parents[3] / "static"),  # /app/static in Docker layout
        str(Path(__file__).resolve().parents[3]),  # repo root for local: .../maslobox
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        if (path / "index.html").exists():
            return path
    return None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    _ensure_sqlite_parent(settings.database_url)
    database.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MasloBox API",
        version="0.1.0",
        description="Приём заявок с лендинга и передача администраторам точек",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/admin")
    def admin_redirect() -> RedirectResponse:
        return RedirectResponse(url="/admin/", status_code=307)

    static_dir = _resolve_static_dir()
    if static_dir is not None:
        logger.info("Serving static files from %s", static_dir)
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    else:
        logger.warning("STATIC_DIR not found — API only mode")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    run()
