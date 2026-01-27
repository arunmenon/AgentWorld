"""FastAPI dependencies for API routes."""

from typing import Generator

from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


def get_repository() -> Generator[Repository, None, None]:
    """Get a repository instance as a FastAPI dependency.

    This is used with FastAPI's Depends() to inject repository
    instances into route handlers.

    Yields:
        Repository instance
    """
    init_db()
    repo = Repository()
    try:
        yield repo
    finally:
        # Repository cleanup if needed
        pass
