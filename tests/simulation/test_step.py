"""Tests for step execution models."""

import pytest
from datetime import datetime

from agentworld.simulation.step import (
    StepPhase,
    StepStatus,
    ActionType,
    AgentAction,
    StepResult,
    StepContext,
    StepEvent,
    StepEventType,
)


class TestStepPhase:
    """Tests for StepPhase enum."""

    def test_phases_exist(self):
        """Test that all phases exist."""
        assert StepPhase.PERCEIVE.value == "perceive"
        assert StepPhase.ACT.value == "act"
        assert StepPhase.COMMIT.value == "commit"

    def test_phase_is_string_enum(self):
        """Test that phases are string enums."""
        assert isinstance(StepPhase.PERCEIVE.value, str)


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_statuses_exist(self):
        """Test that all statuses exist."""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_PROGRESS.value == "in_progress"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.TIMEOUT.value == "timeout"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.CANCELLED.value == "cancelled"


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_types_exist(self):
        """Test that all action types exist."""
        assert ActionType.SPEAK.value == "speak"
        assert ActionType.THINK.value == "think"
        assert ActionType.OBSERVE.value == "observe"
        assert ActionType.IDLE.value == "idle"
        assert ActionType.ERROR.value == "error"


class TestAgentAction:
    """Tests for AgentAction dataclass."""

    def test_creation_minimal(self):
        """Test creating action with minimal params."""
        action = AgentAction(
            agent_id="agent1",
            action_type=ActionType.SPEAK,
        )
        assert action.agent_id == "agent1"
        assert action.action_type == ActionType.SPEAK
        assert action.content == ""

    def test_creation_full(self):
        """Test creating action with all params."""
        action = AgentAction(
            agent_id="agent1",
            action_type=ActionType.SPEAK,
            content="Hello, world!",
            receiver_id="agent2",
            step=5,
            tokens_used=100,
            cost=0.01,
            latency_ms=150.5,
            error=None,
            metadata={"key": "value"},
        )
        assert action.content == "Hello, world!"
        assert action.receiver_id == "agent2"
        assert action.step == 5
        assert action.tokens_used == 100
        assert action.cost == 0.01
        assert action.latency_ms == 150.5
        assert action.metadata["key"] == "value"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        action = AgentAction(
            agent_id="agent1",
            action_type=ActionType.SPEAK,
            content="Test",
            step=1,
        )
        data = action.to_dict()

        assert data["agent_id"] == "agent1"
        assert data["action_type"] == "speak"
        assert data["content"] == "Test"
        assert data["step"] == 1
        assert "timestamp" in data

    def test_error_action(self):
        """Test creating error action."""
        action = AgentAction(
            agent_id="agent1",
            action_type=ActionType.ERROR,
            error="Connection timeout",
        )
        assert action.action_type == ActionType.ERROR
        assert action.error == "Connection timeout"


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_creation_minimal(self):
        """Test creating result with minimal params."""
        result = StepResult(
            step=1,
            status=StepStatus.COMPLETED,
        )
        assert result.step == 1
        assert result.status == StepStatus.COMPLETED
        assert result.actions == []

    def test_creation_with_actions(self):
        """Test creating result with actions."""
        actions = [
            AgentAction(agent_id="a1", action_type=ActionType.SPEAK),
            AgentAction(agent_id="a2", action_type=ActionType.SPEAK),
        ]
        result = StepResult(
            step=1,
            status=StepStatus.COMPLETED,
            actions=actions,
            duration_seconds=1.5,
            messages_sent=2,
            tokens_used=200,
            cost=0.02,
        )
        assert len(result.actions) == 2
        assert result.duration_seconds == 1.5
        assert result.messages_sent == 2
        assert result.tokens_used == 200

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = StepResult(
            step=5,
            status=StepStatus.TIMEOUT,
            errors=["Timeout occurred"],
        )
        data = result.to_dict()

        assert data["step"] == 5
        assert data["status"] == "timeout"
        assert "Timeout occurred" in data["errors"]


class TestStepContext:
    """Tests for StepContext dataclass."""

    def test_creation(self):
        """Test creating context."""
        context = StepContext(
            step_number=10,
            simulation_id="sim123",
            agent_ordering=["a1", "a2", "a3"],
            seed=42,
        )
        assert context.step_number == 10
        assert context.simulation_id == "sim123"
        assert len(context.agent_ordering) == 3

    def test_get_agent_seed_with_seed(self):
        """Test getting agent seed when seed is set."""
        context = StepContext(
            step_number=10,
            simulation_id="sim123",
            agent_ordering=["a1", "a2"],
            seed=42,
        )
        seed1 = context.get_agent_seed("a1")
        seed2 = context.get_agent_seed("a2")

        assert seed1 is not None
        assert seed2 is not None
        assert seed1 != seed2  # Different agents get different seeds
        assert isinstance(seed1, int)

    def test_get_agent_seed_without_seed(self):
        """Test getting agent seed when no seed is set."""
        context = StepContext(
            step_number=10,
            simulation_id="sim123",
            agent_ordering=["a1"],
            seed=None,
        )
        seed = context.get_agent_seed("a1")
        assert seed is None

    def test_deterministic_agent_seed(self):
        """Test that same inputs produce same seed."""
        context1 = StepContext(
            step_number=10,
            simulation_id="sim123",
            agent_ordering=["a1"],
            seed=42,
        )
        context2 = StepContext(
            step_number=10,
            simulation_id="sim123",
            agent_ordering=["a1"],
            seed=42,
        )
        assert context1.get_agent_seed("a1") == context2.get_agent_seed("a1")


class TestStepEvent:
    """Tests for StepEvent dataclass."""

    def test_creation(self):
        """Test creating event."""
        event = StepEvent(
            event_type=StepEventType.STEP_STARTED,
            step=5,
            data={"agents": 3},
        )
        assert event.event_type == StepEventType.STEP_STARTED
        assert event.step == 5
        assert event.data["agents"] == 3

    def test_to_dict(self):
        """Test conversion to dictionary."""
        event = StepEvent(
            event_type=StepEventType.STEP_COMPLETED,
            step=10,
        )
        data = event.to_dict()

        assert data["event_type"] == StepEventType.STEP_COMPLETED
        assert data["step"] == 10
        assert "timestamp" in data


class TestStepEventType:
    """Tests for StepEventType constants."""

    def test_event_types_exist(self):
        """Test that all event types are defined."""
        assert StepEventType.STEP_STARTED == "step_started"
        assert StepEventType.PHASE_STARTED == "phase_started"
        assert StepEventType.PHASE_COMPLETED == "phase_completed"
        assert StepEventType.AGENT_STARTED == "agent_started"
        assert StepEventType.AGENT_COMPLETED == "agent_completed"
        assert StepEventType.AGENT_ERROR == "agent_error"
        assert StepEventType.MESSAGE_SENT == "message_sent"
        assert StepEventType.MESSAGE_DELIVERED == "message_delivered"
        assert StepEventType.STEP_COMPLETED == "step_completed"
        assert StepEventType.STEP_TIMEOUT == "step_timeout"
        assert StepEventType.STEP_CANCELLED == "step_cancelled"
