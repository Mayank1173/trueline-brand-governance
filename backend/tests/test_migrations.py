from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_migrations_upgrade_and_downgrade(tmp_path, monkeypatch):
    database_path = (tmp_path / "migrations.db").as_posix()
    url = f"sqlite:///{database_path}"
    monkeypatch.setenv("TRUELINE_DATABASE_URL", url)

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))

    command.upgrade(config, "head")

    engine = create_engine(url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {
        "brands",
        "guidelines",
        "approved_facts",
        "reviews",
        "review_findings",
        "review_events",
        "alembic_version",
    } <= tables

    guideline_columns = {
        column["name"]: column for column in inspector.get_columns("guidelines")
    }
    assert guideline_columns["version"]["nullable"] is True

    fact_columns = {
        column["name"]: column for column in inspector.get_columns("approved_facts")
    }
    assert fact_columns["source_version"]["nullable"] is True

    finding_columns = {
        column["name"]: column for column in inspector.get_columns("review_findings")
    }
    assert finding_columns["ai_label"]["nullable"] is True
    engine.dispose()

    command.downgrade(config, "base")

    engine = create_engine(url)
    remaining = set(inspect(engine).get_table_names())
    assert remaining == {"alembic_version"}
    engine.dispose()
