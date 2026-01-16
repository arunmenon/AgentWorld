"""Tests for core data models."""

import pytest
from datetime import datetime

from agentworld.core.models import (
    SimulationStatus,
    Message,
    AgentConfig,
    SimulationConfig,
    LLMResponse,
)


class TestSimulationStatus:
    """Tests for SimulationStatus enum."""

    def test_all_statuses_exist(self):
        """Test that all expected statuses exist."""
        assert SimulationStatus.PENDING
        assert SimulationStatus.RUNNING
        assert SimulationStatus.PAUSED
        assert SimulationStatus.COMPLETED
        assert SimulationStatus.FAILED
        assert SimulationStatus.CANCELLED

    def test_status_values(self):
        """Test status string values."""
        assert SimulationStatus.PENDING.value == "pending"
        assert SimulationStatus.RUNNING.value == "running"
        assert SimulationStatus.COMPLETED.value == "completed"


class TestMessage:
    """Tests for Message dataclass."""

    def test_creation_minimal(self):
        """Test creating message with minimal fields."""
        msg = Message(sender_id="alice", content="Hello")

        assert msg.sender_id == "alice"
        assert msg.content == "Hello"
        assert msg.receiver_id is None
        assert msg.id is not None
        assert len(msg.id) == 8

    def test_creation_full(self):
        """Test creating message with all fields."""
        msg = Message(
            sender_id="alice",
            receiver_id="bob",
            content="Hello Bob!",
            step=3,
            simulation_id="sim123",
        )

        assert msg.receiver_id == "bob"
        assert msg.step == 3
        assert msg.simulation_id == "sim123"

    def test_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message(sender_id="alice", content="Hi", receiver_id="bob")
        data = msg.to_dict()

        assert data["sender_id"] == "alice"
        assert data["content"] == "Hi"
        assert data["receiver_id"] == "bob"
        assert "timestamp" in data
        assert "id" in data

    def test_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "sender_id": "bob",
            "content": "Hello!",
            "receiver_id": "alice",
            "step": 2,
        }
        msg = Message.from_dict(data)

        assert msg.sender_id == "bob"
        assert msg.content == "Hello!"
        assert msg.step == 2

    def test_from_dict_with_timestamp(self):
        """Test creating message with timestamp string."""
        data = {
            "sender_id": "alice",
            "content": "Test",
            "timestamp": "2024-01-15T12:00:00",
        }
        msg = Message.from_dict(data)

        assert msg.timestamp == datetime.fromisoformat("2024-01-15T12:00:00")


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating config with minimal fields."""
        config = AgentConfig(name="Alice")

        assert config.name == "Alice"
        assert config.traits == {}
        assert config.background == ""
        assert config.system_prompt is None

    def test_creation_full(self):
        """Test creating config with all fields."""
        config = AgentConfig(
            name="Bob",
            traits={"openness": 0.8, "extraversion": 0.6},
            background="A software engineer",
            system_prompt="You are helpful",
            model="gpt-4o",
        )

        assert config.traits["openness"] == 0.8
        assert config.background == "A software engineer"
        assert config.model == "gpt-4o"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = AgentConfig(name="Test", traits={"openness": 0.5})
        data = config.to_dict()

        assert data["name"] == "Test"
        assert data["traits"]["openness"] == 0.5

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "name": "Charlie",
            "traits": {"conscientiousness": 0.9},
            "model": "gpt-4",
        }
        config = AgentConfig.from_dict(data)

        assert config.name == "Charlie"
        assert config.traits["conscientiousness"] == 0.9
        assert config.model == "gpt-4"


class TestSimulationConfig:
    """Tests for SimulationConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating simulation config with minimal fields."""
        agent = AgentConfig(name="Agent1")
        config = SimulationConfig(name="Test Sim", agents=[agent])

        assert config.name == "Test Sim"
        assert len(config.agents) == 1
        assert config.steps == 10
        assert config.temperature == 0.7

    def test_creation_full(self):
        """Test creating simulation config with all fields."""
        agents = [AgentConfig(name="A"), AgentConfig(name="B")]
        config = SimulationConfig(
            name="Full Sim",
            agents=agents,
            steps=20,
            initial_prompt="Discuss AI",
            model="gpt-4o",
            seed=42,
            temperature=0.9,
        )

        assert len(config.agents) == 2
        assert config.steps == 20
        assert config.initial_prompt == "Discuss AI"
        assert config.seed == 42

    def test_to_dict(self):
        """Test converting simulation config to dictionary."""
        config = SimulationConfig(
            name="Test",
            agents=[AgentConfig(name="A")],
            steps=5,
        )
        data = config.to_dict()

        assert data["name"] == "Test"
        assert len(data["agents"]) == 1
        assert data["steps"] == 5

    def test_from_dict(self):
        """Test creating simulation config from dictionary."""
        data = {
            "name": "From Dict",
            "agents": [{"name": "Agent1"}, {"name": "Agent2"}],
            "steps": 15,
            "model": "gpt-4o-mini",
        }
        config = SimulationConfig.from_dict(data)

        assert config.name == "From Dict"
        assert len(config.agents) == 2
        assert config.agents[0].name == "Agent1"
        assert config.steps == 15


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_creation(self):
        """Test creating LLM response."""
        response = LLMResponse(
            content="Hello!",
            tokens_used=50,
            prompt_tokens=30,
            completion_tokens=20,
            cost=0.001,
            model="gpt-4o-mini",
        )

        assert response.content == "Hello!"
        assert response.tokens_used == 50
        assert response.cost == 0.001
        assert response.cached is False

    def test_to_dict(self):
        """Test converting response to dictionary."""
        response = LLMResponse(
            content="Test",
            tokens_used=100,
            prompt_tokens=60,
            completion_tokens=40,
            cost=0.002,
            model="gpt-4",
            cached=True,
        )
        data = response.to_dict()

        assert data["content"] == "Test"
        assert data["tokens_used"] == 100
        assert data["cached"] is True
