from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, inspect

from app.config import Settings
from app.database import Database
from app.initialization import (
    MIGRATION_LOCK_KEY,
    initialize_database,
)


def test_initialization_runs_migrations_before_seed(tmp_path):
    database = Database(f"sqlite:///{(tmp_path / 'order.db').as_posix()}")
    settings = Settings(_env_file=None, database_url=database.url, seed_demo_data=True)
    calls: list[str] = []

    def migrate(_connection):
        calls.append("migrate")

    def seed(_session):
        calls.append("seed")

    try:
        initialize_database(database, settings, migration_runner=migrate, seed_runner=seed)
    finally:
        database.dispose()

    assert calls == ["migrate", "seed"]


def test_initialization_does_not_seed_when_migration_fails(tmp_path):
    database = Database(f"sqlite:///{(tmp_path / 'failure.db').as_posix()}")
    settings = Settings(_env_file=None, database_url=database.url, seed_demo_data=True)
    seeded = False

    def migrate(_connection):
        raise RuntimeError("migration failed")

    def seed(_session):
        nonlocal seeded
        seeded = True

    try:
        with pytest.raises(RuntimeError, match="migration failed"):
            initialize_database(database, settings, migration_runner=migrate, seed_runner=seed)
    finally:
        database.dispose()

    assert seeded is False


def test_app_does_not_start_when_database_initialization_fails(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app import main
    from app.config import Settings
    from app.main import create_app

    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'startup-failure.db').as_posix()}",
    )

    def fail_initialization(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main, "initialize_database", fail_initialization)
    app = create_app(settings)

    with pytest.raises(RuntimeError, match="Database initialization failed"):
        with TestClient(app):
            pass


def test_seed_command_uses_migration_then_seed_initialization(monkeypatch, tmp_path):
    from app import initialization, seed

    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'seed-command.db').as_posix()}",
        seed_demo_data=True,
    )
    calls: list[str] = []

    def initialize(database, received_settings):
        assert received_settings is settings
        assert database.url == settings.database_url
        calls.append("migrate-and-seed")

    monkeypatch.setattr(seed, "get_settings", lambda: settings)
    monkeypatch.setattr(initialization, "initialize_database", initialize)

    seed.main()

    assert calls == ["migrate-and-seed"]


def test_sqlite_initialization_is_repeatable_and_uses_migrations(tmp_path):
    database = Database(f"sqlite:///{(tmp_path / 'repeat.db').as_posix()}")
    settings = Settings(_env_file=None, database_url=database.url, seed_demo_data=True)
    try:
        initialize_database(database, settings)
        initialize_database(database, settings)
        inspector = inspect(database.engine)
        with database.session_factory() as session:
            from app.models import Brand, Guideline, ApprovedFact

            assert session.query(Brand).count() == 2
            assert session.query(Guideline).count() == 18
            assert session.query(ApprovedFact).count() == 6
        assert "brands" in inspector.get_table_names()
    finally:
        database.dispose()


def test_postgres_lock_uses_same_connection_and_releases_after_seed():
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    engine = MagicMock()
    engine.connect.return_value = connection
    database = MagicMock(engine=engine)
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://redacted", seed_demo_data=True)
    events: list[str] = []

    def execute(statement, params):
        sql = str(statement)
        if "pg_advisory_lock" in sql and "unlock" not in sql:
            events.append(f"lock:{params['lock_key']}")
        elif "pg_advisory_unlock" in sql:
            events.append(f"unlock:{params['lock_key']}")
        return MagicMock()

    connection.execute.side_effect = execute

    def migrate(migration_connection):
        assert migration_connection is connection
        events.append("migrate")

    def seed(session):
        assert session.bind is connection
        events.append("seed")

    initialize_database(database, settings, migration_runner=migrate, seed_runner=seed)

    assert events == [
        f"lock:{MIGRATION_LOCK_KEY}",
        "migrate",
        "seed",
        f"unlock:{MIGRATION_LOCK_KEY}",
    ]
    connection.close.assert_called_once_with()
