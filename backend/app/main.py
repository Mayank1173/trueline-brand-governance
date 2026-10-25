"""FastAPI application factory and entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import brands, health, reviews
from .citations import CitationValidationError
from .config import Settings, get_settings
from .database import Database
from .errors import NotFoundError, PersistenceError
from .initialization import initialize_database
from .rule_engine import RuleEngineError

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    database = Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            initialize_database(database, settings)
        except Exception as exc:
            logger.error(
                "Database initialization failed; application startup aborted (%s).",
                type(exc).__name__,
            )
            raise RuntimeError(
                "Database initialization failed; application cannot start."
            ) from None
        yield
        database.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Deterministic, explainable brand-governance review API. "
            "Demo rules are illustrative and are not official brand policy."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.settings = settings
    app.state.db = database

    origins = settings.cors_origin_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Accept", "Content-Type"],
        )

    @app.middleware("http")
    async def enforce_request_size(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    size = int(content_length)
                except ValueError:
                    return _error_response(
                        400, "invalid_content_length", "Invalid Content-Length header."
                    )
                if size > settings.max_request_bytes:
                    return _error_response(
                        413,
                        "request_too_large",
                        (
                            "Request body exceeds the configured limit of "
                            f"{settings.max_request_bytes} bytes."
                        ),
                    )
        return await call_next(request)

    _register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(reviews.router)
    app.include_router(brands.router)

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        details = []
        for error in exc.errors():
            details.append(
                {
                    "loc": [str(part) for part in error.get("loc", [])],
                    "msg": str(error.get("msg", "Invalid value")),
                    "type": str(error.get("type", "validation_error")),
                }
            )
        return _error_response(
            422,
            "validation_error",
            "Request validation failed.",
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            code = str(detail.get("code", "http_error"))
            message = str(detail.get("message", detail))
            details = detail.get("details")
        else:
            code = "not_found" if exc.status_code == 404 else "http_error"
            message = str(detail)
            details = None
        return _error_response(
            exc.status_code,
            code,
            message,
            details=details,
            headers=exc.headers,
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        return _error_response(404, "not_found", str(exc))

    @app.exception_handler(PersistenceError)
    async def persistence_handler(_request: Request, exc: PersistenceError):
        logger.error("Persistence failure: %s", exc)
        return _error_response(
            503,
            "database_unavailable",
            "The review database is unavailable. Nothing was saved; try again later.",
        )

    @app.exception_handler(CitationValidationError)
    async def citation_handler(_request: Request, exc: CitationValidationError):
        logger.error("Citation validation failed: %s", exc)
        return _error_response(
            500,
            "citation_validation_failed",
            "The review could not be completed because a citation failed validation.",
        )

    @app.exception_handler(RuleEngineError)
    async def rule_engine_handler(_request: Request, exc: RuleEngineError):
        logger.error("Rule engine failure: %s", exc)
        return _error_response(
            500,
            "rule_engine_error",
            "The review could not be completed because a rule is misconfigured.",
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return _error_response(
            500,
            "internal_error",
            "An unexpected error occurred. No stack trace is exposed.",
        )


def _error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    details=None,
    headers: dict | None = None,
) -> JSONResponse:
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


app = create_app()
