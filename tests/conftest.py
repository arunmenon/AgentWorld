"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path

from agentworld.persistence.database import init_db, reset_db
from agentworld.persistence.repository import Repository
from agentworld.personas.traits import TraitVector
from agentworld.agents.agent import Agent


@pytest.fixture(scope="function")
def db():
    """Initialize an in-memory database for testing."""
    init_db(in_memory=True)
    yield
    reset_db()


@pytest.fixture
def repository(db):
    """Get a repository instance."""
    return Repository()


@pytest.fixture
def sample_traits():
    """Create sample trait vector."""
    return TraitVector(
        openness=0.8,
        conscientiousness=0.6,
        extraversion=0.7,
        agreeableness=0.5,
        neuroticism=0.3,
    )


@pytest.fixture
def sample_agent(sample_traits):
    """Create a sample agent."""
    return Agent(
        name="TestAgent",
        traits=sample_traits,
        background="A test agent for unit testing.",
    )


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def example_config_path(project_root):
    """Get the path to the example config."""
    return project_root / "examples" / "two_agents.yaml"
