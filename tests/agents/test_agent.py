"""Tests for Agent class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentworld.agents.agent import Agent
from agentworld.core.models import Message, AgentConfig, LLMResponse
from agentworld.personas.traits import TraitVector


class TestAgentCreation:
    """Tests for Agent creation and initialization."""

    def test_creation_basic(self):
        """Test creating agent with basic fields."""
        traits = TraitVector(openness=0.8)
        agent = Agent(name="Alice", traits=traits)

        assert agent.name == "Alice"
        assert agent.traits.openness == 0.8
        assert agent.id is not None
        assert len(agent.id) == 8

    def test_creation_with_all_fields(self):
        """Test creating agent with all fields."""
        traits = TraitVector(extraversion=0.9)
        agent = Agent(
            name="Bob",
            traits=traits,
            background="A researcher",
            system_prompt="You are helpful",
            model="gpt-4o",
            simulation_id="sim123",
        )

        assert agent.background == "A researcher"
        assert agent.system_prompt == "You are helpful"
        assert agent.model == "gpt-4o"
        assert agent.simulation_id == "sim123"

    def test_auto_generates_system_prompt(self):
        """Test that system prompt is auto-generated if not provided."""
        traits = TraitVector(openness=0.9)
        agent = Agent(name="Creative", traits=traits)

        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0

    def test_from_config(self):
        """Test creating agent from AgentConfig."""
        config = AgentConfig(
            name="Charlie",
            traits={"openness": 0.7, "conscientiousness": 0.8},
            background="An engineer",
            model="gpt-4",
        )
        agent = Agent.from_config(config, simulation_id="sim456")

        assert agent.name == "Charlie"
        assert agent.traits.openness == 0.7
        assert agent.simulation_id == "sim456"


class TestAgentProperties:
    """Tests for Agent properties."""

    def test_message_history_empty(self):
        """Test empty message history."""
        agent = Agent(name="Test", traits=TraitVector())
        assert agent.message_history == []

    def test_total_tokens_starts_zero(self):
        """Test total tokens starts at zero."""
        agent = Agent(name="Test", traits=TraitVector())
        assert agent.total_tokens == 0

    def test_total_cost_starts_zero(self):
        """Test total cost starts at zero."""
        agent = Agent(name="Test", traits=TraitVector())
        assert agent.total_cost == 0.0

    def test_to_dict(self):
        """Test converting agent to dictionary."""
        agent = Agent(
            name="Alice",
            traits=TraitVector(openness=0.8),
            background="A developer",
        )
        data = agent.to_dict()

        assert data["name"] == "Alice"
        assert data["traits"]["openness"] == 0.8
        assert data["background"] == "A developer"
        assert "id" in data


class TestAgentMemory:
    """Tests for Agent memory functionality."""

    def test_memory_property_created_lazily(self):
        """Test that memory is created when first accessed."""
        agent = Agent(name="Test", traits=TraitVector())
        memory = agent.memory

        assert memory is not None

    def test_observations_empty_initially(self):
        """Test that observations start empty."""
        agent = Agent(name="Test", traits=TraitVector())
        assert agent.observations == []

    def test_reflections_empty_initially(self):
        """Test that reflections start empty."""
        agent = Agent(name="Test", traits=TraitVector())
        assert agent.reflections == []

    def test_clear_memory(self):
        """Test clearing memory."""
        agent = Agent(name="Test", traits=TraitVector())
        agent.clear_memory()
        # Should not raise
        assert agent.observations == []


class TestAgentMessageHandling:
    """Tests for Agent message handling."""

    def test_receive_message(self):
        """Test receiving a message."""
        agent = Agent(name="Test", traits=TraitVector())
        msg = Message(sender_id="other", content="Hello")

        agent.receive_message(msg)
        assert len(agent.message_history) == 1
        assert agent.message_history[0].content == "Hello"

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        agent = Agent(name="Test", traits=TraitVector())

        for i in range(15):
            agent.receive_message(Message(sender_id="other", content=f"Msg {i}"))

        recent = agent.get_recent_messages(5)
        assert len(recent) == 5
        assert recent[0].content == "Msg 10"

    def test_clear_history(self):
        """Test clearing message history."""
        agent = Agent(name="Test", traits=TraitVector())
        agent.receive_message(Message(sender_id="other", content="Hello"))

        agent.clear_history()
        assert agent.message_history == []


class TestAgentThink:
    """Tests for Agent think method."""

    @pytest.mark.asyncio
    async def test_think_uses_provider(self):
        """Test that think uses the LLM provider."""
        agent = Agent(name="Test", traits=TraitVector())

        mock_provider = MagicMock()
        mock_response = LLMResponse(
            content="Thinking...",
            tokens_used=50,
            prompt_tokens=30,
            completion_tokens=20,
            cost=0.001,
            model="gpt-4o-mini",
        )
        mock_provider.complete = AsyncMock(return_value=mock_response)
        agent._provider = mock_provider

        result = await agent.think("What do you think?")

        assert result == "Thinking..."
        mock_provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_think_accumulates_tokens(self):
        """Test that think accumulates token usage."""
        agent = Agent(name="Test", traits=TraitVector())

        mock_provider = MagicMock()
        mock_response = LLMResponse(
            content="Response",
            tokens_used=100,
            prompt_tokens=60,
            completion_tokens=40,
            cost=0.002,
            model="gpt-4o-mini",
        )
        mock_provider.complete = AsyncMock(return_value=mock_response)
        agent._provider = mock_provider

        await agent.think("Think 1")
        await agent.think("Think 2")

        assert agent.total_tokens == 200
        assert agent.total_cost == 0.004


class TestAgentGenerateMessage:
    """Tests for Agent generate_message method."""

    @pytest.mark.asyncio
    async def test_generate_message(self):
        """Test generating a message."""
        agent = Agent(name="Test", traits=TraitVector())
        agent.simulation_id = "sim123"

        mock_provider = MagicMock()
        mock_response = LLMResponse(
            content="Generated message",
            tokens_used=30,
            prompt_tokens=20,
            completion_tokens=10,
            cost=0.0005,
            model="gpt-4o-mini",
        )
        mock_provider.complete = AsyncMock(return_value=mock_response)
        agent._provider = mock_provider

        msg = await agent.generate_message("Say hello", receiver_id="bob", step=1)

        assert msg.content == "Generated message"
        assert msg.sender_id == agent.id
        assert msg.receiver_id == "bob"
        assert msg.step == 1
        assert msg.simulation_id == "sim123"


class TestAgentRepr:
    """Tests for Agent string representation."""

    def test_repr(self):
        """Test agent string representation."""
        agent = Agent(name="Alice", traits=TraitVector(openness=0.8))
        repr_str = repr(agent)

        assert "Agent" in repr_str
        assert "Alice" in repr_str
