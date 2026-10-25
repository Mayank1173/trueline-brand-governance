"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    settings = request.app.state.settings
    database = request.app.state.db
    database_ok = database.ping()
    payload = HealthResponse(
        status="ok" if database_ok else "degraded",
        database="connected" if database_ok else "unavailable",
        environment=settings.environment,
        version=settings.app_version,
    )
    return JSONResponse(
        status_code=200 if database_ok else 503,
        content=payload.model_dump(),
    )
