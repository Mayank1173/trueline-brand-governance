"""SQLAlchemy engine/session setup for SQLite and PostgreSQL."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Database:
    """Owns an engine and session factory for one application instance."""

    def __init__(self, url: str, *, echo: bool = False) -> None:
        self.url = url
        parsed = make_url(url)
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {}

        if parsed.get_backend_name() == "sqlite":
            connect_args["check_same_thread"] = False
            database = parsed.database
            if database and database != ":memory:":
                Path(database).expanduser().resolve().parent.mkdir(
                    parents=True, exist_ok=True
                )
            else:
                # An in-memory SQLite database is per-connection unless all
                # sessions share one pooled connection.
                engine_kwargs["poolclass"] = StaticPool

        self.engine: Engine = create_engine(
            url,
            echo=echo,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
            **engine_kwargs,
        )

        if parsed.get_backend_name() == "sqlite":
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)

        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            autoflush=False,
            expire_on_commit=False,
        )

    @staticmethod
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    def create_all(self) -> None:
        # Import models so every table is registered on Base.metadata.
        from . import models  # noqa: F401

        Base.metadata.create_all(bind=self.engine)

    def drop_all(self) -> None:
        from . import models  # noqa: F401

        Base.metadata.drop_all(bind=self.engine)

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def dispose(self) -> None:
        self.engine.dispose()
