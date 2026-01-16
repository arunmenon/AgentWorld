"""Tests for base scenario classes."""

import pytest
from datetime import datetime

from agentworld.scenarios.base import (
    ScenarioStatus,
    ScenarioConfig,
    AgentResponse,
    SystemEvent,
    ScenarioResult,
    Scenario,
)


class TestScenarioStatus:
    """Tests for ScenarioStatus enum."""

    def test_statuses_exist(self):
        """Test that all statuses exist."""
        assert ScenarioStatus.PENDING.value == "pending"
        assert ScenarioStatus.SETTING_UP.value == "setting_up"
        assert ScenarioStatus.RUNNING.value == "running"
        assert ScenarioStatus.PAUSED.value == "paused"
        assert ScenarioStatus.COMPLETED.value == "completed"
        assert ScenarioStatus.FAILED.value == "failed"
        assert ScenarioStatus.CANCELLED.value == "cancelled"


class TestScenarioConfig:
    """Tests for ScenarioConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating config with minimal params."""
        config = ScenarioConfig(name="Test")

        assert config.name == "Test"
        assert config.description == ""
        assert config.max_steps == 100
        assert config.seed is None

    def test_creation_full(self):
        """Test creating config with all params."""
        config = ScenarioConfig(
            name="Full Test",
            description="A comprehensive test",
            max_steps=50,
            seed=42,
            metadata={"key": "value"},
        )

        assert config.name == "Full Test"
        assert config.description == "A comprehensive test"
        assert config.max_steps == 50
        assert config.seed == 42
        assert config.metadata["key"] == "value"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ScenarioConfig(name="Test", seed=42)
        data = config.to_dict()

        assert data["name"] == "Test"
        assert data["seed"] == 42
        assert "max_steps" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "From Dict",
            "description": "Test desc",
            "max_steps": 75,
            "seed": 123,
        }
        config = ScenarioConfig.from_dict(data)

        assert config.name == "From Dict"
        assert config.description == "Test desc"
        assert config.max_steps == 75
        assert config.seed == 123


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_creation(self):
        """Test creating response."""
        response = AgentResponse(
            agent_id="agent1",
            content="Hello, world!",
            step=5,
            message_type="speech",
        )

        assert response.agent_id == "agent1"
        assert response.content == "Hello, world!"
        assert response.step == 5
        assert response.message_type == "speech"
        assert isinstance(response.timestamp, datetime)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        response = AgentResponse(
            agent_id="agent1",
            content="Test",
            step=1,
        )
        data = response.to_dict()

        assert data["agent_id"] == "agent1"
        assert data["content"] == "Test"
        assert data["step"] == 1
        assert "timestamp" in data


class TestSystemEvent:
    """Tests for SystemEvent dataclass."""

    def test_creation_minimal(self):
        """Test creating event with minimal params."""
        event = SystemEvent(content="System announcement")

        assert event.content == "System announcement"
        assert event.source == "system"
        assert event.target is None
        assert event.event_type == "announcement"

    def test_creation_targeted(self):
        """Test creating targeted event."""
        event = SystemEvent(
            content="Message to agent1",
            source="moderator",
            target="agent1",
            event_type="prompt",
        )

        assert event.target == "agent1"
        assert event.source == "moderator"
        assert event.event_type == "prompt"

    def test_is_broadcast(self):
        """Test broadcast detection."""
        broadcast = SystemEvent(content="Announcement")
        assert broadcast.is_broadcast

        targeted = SystemEvent(content="Specific", target="agent1")
        assert not targeted.is_broadcast

    def test_to_dict(self):
        """Test conversion to dictionary."""
        event = SystemEvent(
            content="Test",
            source="test",
            event_type="test_event",
        )
        data = event.to_dict()

        assert data["content"] == "Test"
        assert data["source"] == "test"
        assert "timestamp" in data
        assert "id" in data


class TestScenarioResult:
    """Tests for ScenarioResult dataclass."""

    def test_creation(self):
        """Test creating result."""
        config = ScenarioConfig(name="Test")
        result = ScenarioResult(
            scenario_id="sc123",
            scenario_type="test",
            config=config,
            status=ScenarioStatus.COMPLETED,
        )

        assert result.scenario_id == "sc123"
        assert result.scenario_type == "test"
        assert result.status == ScenarioStatus.COMPLETED
        assert result.messages == []

    def test_creation_with_data(self):
        """Test creating result with data."""
        config = ScenarioConfig(name="Test")
        responses = [
            AgentResponse(agent_id="a1", content="Hello", step=1),
            AgentResponse(agent_id="a2", content="Hi", step=1),
        ]
        result = ScenarioResult(
            scenario_id="sc123",
            scenario_type="test",
            config=config,
            status=ScenarioStatus.COMPLETED,
            responses=responses,
            total_steps=10,
            tokens_used=500,
            cost=0.05,
        )

        assert len(result.responses) == 2
        assert result.total_steps == 10
        assert result.tokens_used == 500
        assert result.cost == 0.05

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ScenarioConfig(name="Test")
        result = ScenarioResult(
            scenario_id="sc123",
            scenario_type="test",
            config=config,
            status=ScenarioStatus.COMPLETED,
        )
        data = result.to_dict()

        assert data["scenario_id"] == "sc123"
        assert data["scenario_type"] == "test"
        assert data["status"] == "completed"


class ConcreteScenario(Scenario):
    """Concrete implementation for testing."""

    async def setup(self):
        pass

    async def run(self):
        self._mark_started()
        self.log_response(AgentResponse(
            agent_id="test",
            content="Test message",
            step=1,
        ))
        self._mark_completed()
        return self.build_result()


class TestScenario:
    """Tests for Scenario base class."""

    @pytest.fixture
    def scenario(self):
        """Create scenario instance."""
        config = ScenarioConfig(name="Test Scenario")
        return ConcreteScenario(config)

    def test_creation(self, scenario):
        """Test creating scenario."""
        assert scenario.config.name == "Test Scenario"
        assert scenario.status == ScenarioStatus.PENDING
        assert len(scenario.scenario_id) == 8

    def test_scenario_type(self, scenario):
        """Test scenario type property."""
        assert "concrete" in scenario.scenario_type

    def test_log_message(self, scenario):
        """Test logging messages."""
        scenario.log_message({"id": "m1", "content": "test"})

        assert len(scenario.messages) == 1

    def test_log_event(self, scenario):
        """Test logging events."""
        event = SystemEvent(content="Test event")
        scenario.log_event(event)

        assert len(scenario.events) == 1

    def test_log_response(self, scenario):
        """Test logging responses."""
        response = AgentResponse(agent_id="a1", content="Hello", step=1)
        scenario.log_response(response)

        assert len(scenario.responses) == 1

    def test_add_tokens(self, scenario):
        """Test adding tokens."""
        scenario.add_tokens(100)
        scenario.add_tokens(50)

        assert scenario._total_tokens == 150

    def test_add_cost(self, scenario):
        """Test adding cost."""
        scenario.add_cost(0.01)
        scenario.add_cost(0.02)

        assert scenario._total_cost == 0.03

    def test_extract_responses_all(self, scenario):
        """Test extracting all responses."""
        scenario.log_response(AgentResponse(agent_id="a1", content="1", step=1))
        scenario.log_response(AgentResponse(agent_id="a2", content="2", step=2))

        responses = scenario.extract_responses()

        assert len(responses) == 2

    def test_extract_responses_since_step(self, scenario):
        """Test extracting responses since step."""
        scenario.log_response(AgentResponse(agent_id="a1", content="1", step=1))
        scenario.log_response(AgentResponse(agent_id="a2", content="2", step=2))
        scenario.log_response(AgentResponse(agent_id="a1", content="3", step=3))

        responses = scenario.extract_responses(since_step=2)

        assert len(responses) == 2

    def test_extract_responses_by_type(self, scenario):
        """Test extracting responses by type."""
        scenario.log_response(AgentResponse(
            agent_id="a1", content="1", step=1, message_type="speech"
        ))
        scenario.log_response(AgentResponse(
            agent_id="a2", content="2", step=2, message_type="thought"
        ))

        responses = scenario.extract_responses(filter_type="speech")

        assert len(responses) == 1
        assert responses[0].message_type == "speech"

    def test_extract_responses_by_agent(self, scenario):
        """Test extracting responses by agent."""
        scenario.log_response(AgentResponse(agent_id="a1", content="1", step=1))
        scenario.log_response(AgentResponse(agent_id="a2", content="2", step=2))
        scenario.log_response(AgentResponse(agent_id="a1", content="3", step=3))

        responses = scenario.extract_responses(agent_ids=["a1"])

        assert len(responses) == 2
        assert all(r.agent_id == "a1" for r in responses)

    def test_build_result(self, scenario):
        """Test building result."""
        scenario._mark_started()
        scenario.log_response(AgentResponse(agent_id="a1", content="test", step=1))
        scenario._mark_completed()

        result = scenario.build_result()

        assert result.scenario_id == scenario.scenario_id
        assert result.status == ScenarioStatus.COMPLETED
        assert len(result.responses) == 1

    def test_mark_started(self, scenario):
        """Test marking as started."""
        scenario._mark_started()

        assert scenario.status == ScenarioStatus.RUNNING
        assert scenario._start_time is not None

    def test_mark_completed(self, scenario):
        """Test marking as completed."""
        scenario._mark_started()
        scenario._mark_completed()

        assert scenario.status == ScenarioStatus.COMPLETED
        assert scenario._end_time is not None

    def test_mark_failed(self, scenario):
        """Test marking as failed."""
        scenario._mark_started()
        scenario._mark_failed("Test error")

        assert scenario.status == ScenarioStatus.FAILED
        assert scenario._end_time is not None
        assert scenario.config.metadata["error"] == "Test error"

    def test_duration_seconds(self, scenario):
        """Test duration calculation."""
        assert scenario.duration_seconds == 0.0

        scenario._mark_started()
        # Just check it returns a positive number
        assert scenario.duration_seconds >= 0.0

    @pytest.mark.asyncio
    async def test_run(self, scenario):
        """Test running scenario."""
        result = await scenario.run()

        assert result.status == ScenarioStatus.COMPLETED
        assert len(result.responses) == 1
