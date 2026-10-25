"""FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..database import Database
from ..services import ReviewService


def get_session(request: Request) -> Iterator[Session]:
    database: Database = request.app.state.db
    session = database.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_review_service(request: Request) -> ReviewService:
    return ReviewService(request.app.state.settings)


SessionDep = Annotated[Session, Depends(get_session)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
