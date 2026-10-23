from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.database import Database
from app.errors import PersistenceError
from app.models import Review
from app.schemas import ReviewRequest
from app.seed import seed_demo_data
from app.services import ReviewService


def test_commit_failure_is_not_reported_as_success(tmp_path, monkeypatch):
    database_path = (tmp_path / "failure.db").as_posix()
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{database_path}",
        seed_demo_data=False,
        auto_create_tables=True,
    )
    database = Database(settings.database_url)
    database.create_all()

    with database.session_factory() as session:
        seed_demo_data(session)

    session = database.session_factory()

    def failing_commit():
        raise SQLAlchemyError("simulated database failure")

    monkeypatch.setattr(session, "commit", failing_commit)
    service = ReviewService(settings)

    with pytest.raises(PersistenceError):
        service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Cheapest. Terms apply.",
                purpose="marketing",
            ),
        )

    monkeypatch.undo()
    assert session.scalar(select(func.count()).select_from(Review)) == 0
    session.close()
    database.dispose()
