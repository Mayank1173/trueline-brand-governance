"""Database migration and optional demo-data initialization."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, text
from sqlalchemy.orm import Session

from .config import Settings
from .database import Database
from .seed import seed_demo_data

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
MIGRATION_LOCK_KEY = 481_726_203


def _migration_config(connection: Connection) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.attributes["connection"] = connection
    return config


def run_migrations(connection: Connection) -> None:
    """Upgrade the connected database to the latest Alembic revision."""
    command.upgrade(_migration_config(connection), "head")


def _acquire_postgres_lock(connection: Connection) -> None:
    connection.execute(
        text("SELECT pg_advisory_lock(:lock_key)"),
        {"lock_key": MIGRATION_LOCK_KEY},
    )


def _release_postgres_lock(connection: Connection) -> None:
    connection.execute(
        text("SELECT pg_advisory_unlock(:lock_key)"),
        {"lock_key": MIGRATION_LOCK_KEY},
    )


def initialize_database(
    database: Database,
    settings: Settings,
    *,
    migration_runner: Callable[[Connection], None] = run_migrations,
    seed_runner: Callable[[Session], None] = seed_demo_data,
) -> None:
    """Migrate and seed before the application starts serving requests.

    PostgreSQL uses a session-level advisory lock held on the same connection
    used by Alembic. SQLite has no equivalent lock and intentionally skips the
    PostgreSQL-specific statements; its migrations remain safe for the single
    local process used by development and tests.
    """
    connection = database.engine.connect()
    is_postgres = connection.dialect.name == "postgresql"
    lock_acquired = False
    try:
        if is_postgres:
            _acquire_postgres_lock(connection)
            lock_acquired = True
            # pg_advisory_lock is a session-level lock, but its SELECT starts
            # SQLAlchemy's implicit transaction. End that transaction before
            # Alembic starts its own migration transaction; closing the
            # connection with it open would roll the migrations back.
            connection.commit()
        migration_runner(connection)
        with Session(bind=connection) as session:
            if settings.seed_demo_data:
                seed_runner(session)
    finally:
        if is_postgres and lock_acquired:
            try:
                _release_postgres_lock(connection)
            except Exception as exc:
                logger.error(
                    "Could not release the database initialization lock (%s).",
                    type(exc).__name__,
                )
        connection.close()
