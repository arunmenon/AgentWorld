"""Tests for Simulation runner."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentworld.simulation.runner import Simulation
from agentworld.agents.agent import Agent
from agentworld.core.models import Message, SimulationConfig, AgentConfig, SimulationStatus, LLMResponse
from agentworld.personas.traits import TraitVector
from agentworld.persistence.database import init_db


@pytest.fixture
def mock_db():
    """Initialize in-memory database for tests."""
    init_db(in_memory=True)


class TestSimulationCreation:
    """Tests for Simulation creation."""

    def test_creation_basic(self, mock_db):
        """Test creating simulation with basic fields."""
        sim = Simulation(name="Test Simulation")

        assert sim.name == "Test Simulation"
        assert sim.id is not None
        assert len(sim.id) == 8
        assert sim.status == SimulationStatus.PENDING

    def test_creation_with_agents(self, mock_db):
        """Test creating simulation with agents."""
        agent1 = Agent(name="Alice", traits=TraitVector())
        agent2 = Agent(name="Bob", traits=TraitVector())

        sim = Simulation(name="Test", agents=[agent1, agent2])

        assert len(sim.agents) == 2

    def test_from_config(self, mock_db):
        """Test creating simulation from config."""
        config = SimulationConfig(
            name="Config Sim",
            agents=[
                AgentConfig(name="A", traits={"openness": 0.8}),
                AgentConfig(name="B", traits={"extraversion": 0.7}),
            ],
            steps=5,
            initial_prompt="Discuss topic",
            model="gpt-4o-mini",
        )

        sim = Simulation.from_config(config)

        assert sim.name == "Config Sim"
        assert len(sim.agents) == 2
        assert sim.total_steps == 5
        assert sim.initial_prompt == "Discuss topic"


class TestSimulationProperties:
    """Tests for Simulation properties."""

    def test_messages_empty_initially(self, mock_db):
        """Test messages start empty."""
        sim = Simulation(name="Test")
        assert sim.messages == []

    def test_total_tokens_aggregates_agents(self, mock_db):
        """Test that total_tokens aggregates from all agents."""
        agent1 = Agent(name="A", traits=TraitVector())
        agent2 = Agent(name="B", traits=TraitVector())
        agent1._total_tokens = 100
        agent2._total_tokens = 150

        sim = Simulation(name="Test", agents=[agent1, agent2])

        assert sim.total_tokens == 250

    def test_total_cost_aggregates_agents(self, mock_db):
        """Test that total_cost aggregates from all agents."""
        agent1 = Agent(name="A", traits=TraitVector())
        agent2 = Agent(name="B", traits=TraitVector())
        agent1._total_cost = 0.01
        agent2._total_cost = 0.02

        sim = Simulation(name="Test", agents=[agent1, agent2])

        assert sim.total_cost == 0.03


class TestSimulationAgentManagement:
    """Tests for agent management methods."""

    def test_add_agent(self, mock_db):
        """Test adding an agent."""
        sim = Simulation(name="Test")
        agent = Agent(name="Alice", traits=TraitVector())

        sim.add_agent(agent)

        assert len(sim.agents) == 1
        assert agent.simulation_id == sim.id

    def test_get_agent(self, mock_db):
        """Test getting agent by ID."""
        agent = Agent(name="Alice", traits=TraitVector())
        sim = Simulation(name="Test", agents=[agent])

        found = sim.get_agent(agent.id)
        assert found is not None
        assert found.name == "Alice"

    def test_get_agent_not_found(self, mock_db):
        """Test getting non-existent agent."""
        sim = Simulation(name="Test")
        found = sim.get_agent("nonexistent")
        assert found is None

    def test_get_agent_by_name(self, mock_db):
        """Test getting agent by name."""
        agent = Agent(name="Alice", traits=TraitVector())
        sim = Simulation(name="Test", agents=[agent])

        found = sim.get_agent_by_name("alice")  # Case insensitive
        assert found is not None
        assert found.name == "Alice"


class TestSimulationTopology:
    """Tests for topology functionality."""

    def test_default_topology_is_mesh(self, mock_db):
        """Test that default topology is mesh."""
        sim = Simulation(name="Test")
        assert sim.topology_type == "mesh"

    def test_topology_initialized_lazily(self, mock_db):
        """Test topology is created when accessed."""
        agent1 = Agent(name="A", traits=TraitVector())
        agent2 = Agent(name="B", traits=TraitVector())
        sim = Simulation(name="Test", agents=[agent1, agent2])

        # Access topology to trigger initialization
        topology = sim.topology
        assert topology is not None

    def test_can_communicate_mesh(self, mock_db):
        """Test communication check in mesh topology."""
        agent1 = Agent(name="A", traits=TraitVector())
        agent2 = Agent(name="B", traits=TraitVector())
        sim = Simulation(name="Test", agents=[agent1, agent2])

        # In mesh, everyone can communicate
        assert sim.can_communicate(agent1.id, agent2.id)
        assert sim.can_communicate(agent2.id, agent1.id)

    def test_get_valid_recipients(self, mock_db):
        """Test getting valid recipients."""
        agent1 = Agent(name="A", traits=TraitVector())
        agent2 = Agent(name="B", traits=TraitVector())
        agent3 = Agent(name="C", traits=TraitVector())
        sim = Simulation(name="Test", agents=[agent1, agent2, agent3])

        recipients = sim.get_valid_recipients(agent1.id)
        assert len(recipients) >= 1


class TestSimulationCallbacks:
    """Tests for step callbacks."""

    def test_on_step_registers_callback(self, mock_db):
        """Test registering step callback."""
        sim = Simulation(name="Test")

        callback = MagicMock()
        sim.on_step(callback)

        assert callback in sim._step_callbacks


class TestSimulationToDict:
    """Tests for simulation serialization."""

    def test_to_dict(self, mock_db):
        """Test converting simulation to dictionary."""
        agent = Agent(name="Alice", traits=TraitVector())
        sim = Simulation(
            name="Test",
            agents=[agent],
            total_steps=10,
        )
        data = sim.to_dict()

        assert data["name"] == "Test"
        assert data["status"] == "pending"
        assert data["total_steps"] == 10
        assert len(data["agents"]) == 1

    def test_to_dict_includes_topology_info(self, mock_db):
        """Test that to_dict includes topology info when initialized."""
        agent1 = Agent(name="A", traits=TraitVector())
        agent2 = Agent(name="B", traits=TraitVector())
        sim = Simulation(name="Test", agents=[agent1, agent2])

        # Initialize topology
        _ = sim.topology

        data = sim.to_dict()
        assert "topology" in data
        assert data["topology"]["type"] == "mesh"


class TestSimulationRepr:
    """Tests for simulation string representation."""

    def test_repr(self, mock_db):
        """Test simulation string representation."""
        sim = Simulation(name="Test Sim")
        repr_str = repr(sim)

        assert "Simulation" in repr_str
        assert "Test Sim" in repr_str
        assert "pending" in repr_str
