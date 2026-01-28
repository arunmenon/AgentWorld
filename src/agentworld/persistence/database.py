"""Database setup and session management."""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from agentworld.persistence.models import Base


# Default database path
DEFAULT_DB_PATH = Path.home() / ".agentworld" / "agentworld.db"


def get_database_url(path: str | Path | None = None) -> str:
    """Get the database URL.

    Args:
        path: Optional custom database path

    Returns:
        SQLAlchemy database URL
    """
    if path is None:
        path = os.environ.get("AGENTWORLD_DB_PATH", DEFAULT_DB_PATH)

    path = Path(path)

    # Handle in-memory database
    if str(path) == ":memory:":
        return "sqlite:///:memory:"

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{path}"


def create_db_engine(
    path: str | Path | None = None,
    echo: bool = False,
    in_memory: bool = False,
):
    """Create a database engine.

    Args:
        path: Optional custom database path
        echo: Whether to echo SQL statements
        in_memory: Use in-memory database (for testing)

    Returns:
        SQLAlchemy Engine
    """
    if in_memory:
        # In-memory database with shared cache for testing
        engine = create_engine(
            "sqlite:///:memory:",
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        url = get_database_url(path)
        engine = create_engine(
            url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


# Global engine and session factory
_engine = None
_session_factory = None


def _run_migrations(engine) -> None:
    """Run database migrations to add missing columns.

    This handles schema evolution without a full migration framework.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # Migration: Add ADR-020.1 access control columns to app_definitions
    if "app_definitions" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("app_definitions")}

        with engine.connect() as conn:
            # Add access_type column if missing
            if "access_type" not in columns:
                conn.execute(text(
                    "ALTER TABLE app_definitions ADD COLUMN access_type VARCHAR(20) DEFAULT 'shared' NOT NULL"
                ))
                conn.commit()

            # Add allowed_roles_json column if missing
            if "allowed_roles_json" not in columns:
                conn.execute(text(
                    "ALTER TABLE app_definitions ADD COLUMN allowed_roles_json TEXT"
                ))
                conn.commit()

            # Add state_type column if missing
            if "state_type" not in columns:
                conn.execute(text(
                    "ALTER TABLE app_definitions ADD COLUMN state_type VARCHAR(20) DEFAULT 'shared' NOT NULL"
                ))
                conn.commit()


def init_db(
    path: str | Path | None = None,
    echo: bool = False,
    in_memory: bool = False,
) -> None:
    """Initialize the database.

    Creates tables if they don't exist.

    Args:
        path: Optional custom database path
        echo: Whether to echo SQL statements
        in_memory: Use in-memory database (for testing)
    """
    global _engine, _session_factory

    _engine = create_db_engine(path=path, echo=echo, in_memory=in_memory)
    _session_factory = sessionmaker(bind=_engine)

    # Create tables
    Base.metadata.create_all(_engine)

    # Run migrations for existing databases
    _run_migrations(_engine)


def get_engine():
    """Get the database engine, initializing if needed."""
    global _engine
    if _engine is None:
        init_db()
    return _engine


def get_session_factory():
    """Get the session factory, initializing if needed."""
    global _session_factory
    if _session_factory is None:
        init_db()
    return _session_factory


def get_session() -> Session:
    """Get a new database session.

    Returns:
        SQLAlchemy Session
    """
    factory = get_session_factory()
    return factory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Usage:
        with session_scope() as session:
            session.add(obj)
            # automatically committed on exit, rolled back on exception

    Yields:
        SQLAlchemy Session
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_db() -> None:
    """Reset the database (drop and recreate all tables).

    WARNING: This deletes all data!
    """
    global _engine
    if _engine is not None:
        Base.metadata.drop_all(_engine)
        Base.metadata.create_all(_engine)
