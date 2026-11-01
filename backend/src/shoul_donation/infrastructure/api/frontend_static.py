"""Serve the built React app from the same process as the API."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI) -> None:
    dist = frontend_dist()
    if dist is None:
        return
    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")
    _register_spa(app, dist)


def frontend_dist() -> Path | None:
    for candidate in _candidates():
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _candidates() -> list[Path]:
    paths = []
    configured = os.environ.get("FRONTEND_DIST")
    if configured:
        paths.append(Path(configured))
    module = Path(__file__).resolve()
    if len(module.parents) > 5:
        paths.append(module.parents[5] / "frontend" / "dist")
    paths.append(Path("/app/frontend/dist"))
    return paths


def _register_spa(app: FastAPI, dist: Path) -> None:
    @app.get("/")
    def home() -> FileResponse:
        return FileResponse(dist / "index.html")

    @app.get("/{path:path}")
    def spa(path: str) -> FileResponse:
        target = dist / path
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(dist / "index.html")
