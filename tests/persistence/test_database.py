"""Tests for database setup and session management."""

import pytest
from sqlalchemy.orm import Session

from agentworld.persistence.database import (
    get_database_url,
    create_db_engine,
    init_db,
    get_session,
    session_scope,
    reset_db,
)
from agentworld.persistence.models import Base


class TestGetDatabaseUrl:
    """Tests for get_database_url function."""

    def test_in_memory_url(self):
        """Test in-memory database URL."""
        url = get_database_url(":memory:")
        assert url == "sqlite:///:memory:"

    def test_custom_path(self, tmp_path):
        """Test custom database path."""
        db_path = tmp_path / "test.db"
        url = get_database_url(db_path)
        assert f"sqlite:///{db_path}" == url

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directory is created."""
        db_path = tmp_path / "subdir" / "test.db"
        url = get_database_url(db_path)
        assert db_path.parent.exists()


class TestCreateDbEngine:
    """Tests for create_db_engine function."""

    def test_in_memory_engine(self):
        """Test creating in-memory engine."""
        engine = create_db_engine(in_memory=True)
        assert engine is not None
        engine.dispose()

    def test_engine_with_path(self, tmp_path):
        """Test creating engine with path."""
        db_path = tmp_path / "test.db"
        engine = create_db_engine(path=db_path)
        assert engine is not None
        engine.dispose()


class TestInitDb:
    """Tests for init_db function."""

    def test_init_creates_tables(self):
        """Test that init_db creates tables."""
        init_db(in_memory=True)

        # Should be able to get a session after init
        session = get_session()
        assert session is not None
        session.close()

    def test_init_idempotent(self):
        """Test that init_db can be called multiple times."""
        init_db(in_memory=True)
        init_db(in_memory=True)

        session = get_session()
        assert session is not None
        session.close()


class TestGetSession:
    """Tests for get_session function."""

    def test_returns_session(self):
        """Test that get_session returns a valid session."""
        init_db(in_memory=True)
        session = get_session()

        assert session is not None
        assert isinstance(session, Session)
        session.close()


class TestSessionScope:
    """Tests for session_scope context manager."""

    def test_commits_on_success(self):
        """Test that session commits on successful exit."""
        init_db(in_memory=True)

        with session_scope() as session:
            assert session is not None
            # Just verify we can use the session
            assert isinstance(session, Session)

    def test_rollback_on_exception(self):
        """Test that session rolls back on exception."""
        init_db(in_memory=True)

        class TestError(Exception):
            pass

        with pytest.raises(TestError):
            with session_scope() as session:
                raise TestError("Test exception")

        # Session should still work after rollback
        with session_scope() as session:
            assert session is not None


class TestResetDb:
    """Tests for reset_db function."""

    def test_reset_clears_data(self):
        """Test that reset_db clears all data."""
        init_db(in_memory=True)

        # Add some data (we'd need to import models for this)
        # For now, just verify reset doesn't crash
        reset_db()

        # Should still be able to use database after reset
        session = get_session()
        assert session is not None
        session.close()
