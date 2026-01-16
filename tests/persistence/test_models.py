"""Tests for SQLAlchemy ORM models."""

import json
import pytest
from datetime import datetime

from agentworld.core.models import SimulationStatus
from agentworld.persistence.models import (
    SimulationModel,
    AgentModel,
    MessageModel,
    MemoryModel,
    TopologyEdgeModel,
    TopologyConfigModel,
    MemoryType,
)


class TestSimulationModel:
    """Tests for SimulationModel."""

    def test_to_dict(self):
        """Test converting simulation to dictionary."""
        sim = SimulationModel(
            id="test123",
            name="Test Simulation",
            status=SimulationStatus.RUNNING,
            current_step=5,
            total_steps=10,
        )
        data = sim.to_dict()

        assert data["id"] == "test123"
        assert data["name"] == "Test Simulation"
        assert data["status"] == "running"
        assert data["current_step"] == 5

    def test_from_dict(self):
        """Test creating simulation from dictionary."""
        data = {
            "id": "abc123",
            "name": "New Sim",
            "status": "pending",
            "current_step": 0,
            "total_steps": 20,
        }
        sim = SimulationModel.from_dict(data)

        assert sim.id == "abc123"
        assert sim.name == "New Sim"
        assert sim.status == SimulationStatus.PENDING
        assert sim.total_steps == 20

    def test_from_dict_with_config(self):
        """Test creating simulation with config JSON."""
        data = {
            "id": "test",
            "name": "Test",
            "config": {"steps": 10, "model": "gpt-4"},
        }
        sim = SimulationModel.from_dict(data)

        assert sim.config_json is not None
        config = json.loads(sim.config_json)
        assert config["model"] == "gpt-4"


class TestAgentModel:
    """Tests for AgentModel."""

    def test_to_dict(self):
        """Test converting agent to dictionary."""
        agent = AgentModel(
            id="agent1",
            simulation_id="sim1",
            name="Alice",
            traits_json='{"openness": 0.8}',
            background="A developer",
        )
        data = agent.to_dict()

        assert data["id"] == "agent1"
        assert data["name"] == "Alice"
        assert data["traits"]["openness"] == 0.8
        assert data["background"] == "A developer"

    def test_from_dict(self):
        """Test creating agent from dictionary."""
        data = {
            "id": "agent2",
            "simulation_id": "sim2",
            "name": "Bob",
            "traits": {"extraversion": 0.9},
            "model": "gpt-4o",
        }
        agent = AgentModel.from_dict(data)

        assert agent.id == "agent2"
        assert agent.name == "Bob"
        traits = json.loads(agent.traits_json)
        assert traits["extraversion"] == 0.9


class TestMessageModel:
    """Tests for MessageModel."""

    def test_to_dict(self):
        """Test converting message to dictionary."""
        msg = MessageModel(
            id="msg1",
            simulation_id="sim1",
            sender_id="alice",
            receiver_id="bob",
            content="Hello!",
            step=1,
        )
        data = msg.to_dict()

        assert data["id"] == "msg1"
        assert data["sender_id"] == "alice"
        assert data["content"] == "Hello!"

    def test_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "id": "msg2",
            "simulation_id": "sim2",
            "sender_id": "bob",
            "receiver_id": "alice",
            "content": "Hi there!",
            "step": 2,
        }
        msg = MessageModel.from_dict(data)

        assert msg.id == "msg2"
        assert msg.sender_id == "bob"
        assert msg.content == "Hi there!"

    def test_from_dict_with_timestamp(self):
        """Test creating message with timestamp string."""
        data = {
            "id": "msg3",
            "simulation_id": "sim3",
            "sender_id": "charlie",
            "content": "Test",
            "timestamp": "2024-01-15T10:30:00",
        }
        msg = MessageModel.from_dict(data)

        assert msg.timestamp == datetime.fromisoformat("2024-01-15T10:30:00")


class TestMemoryModel:
    """Tests for MemoryModel."""

    def test_to_dict_observation(self):
        """Test converting observation memory to dictionary."""
        mem = MemoryModel(
            id="mem1",
            agent_id="agent1",
            memory_type=MemoryType.OBSERVATION,
            content="Saw something interesting",
            importance=7.0,
            source="bob",
        )
        data = mem.to_dict()

        assert data["id"] == "mem1"
        assert data["memory_type"] == "observation"
        assert data["importance"] == 7.0
        assert data["source"] == "bob"

    def test_to_dict_reflection(self):
        """Test converting reflection memory to dictionary."""
        mem = MemoryModel(
            id="mem2",
            agent_id="agent1",
            memory_type=MemoryType.REFLECTION,
            content="I think Bob is friendly",
            importance=9.0,
            source_memories='["mem1"]',
            questions_addressed='["Is Bob nice?"]',
        )
        data = mem.to_dict()

        assert data["memory_type"] == "reflection"
        assert data["source_memories"] == ["mem1"]
        assert data["questions_addressed"] == ["Is Bob nice?"]

    def test_from_dict(self):
        """Test creating memory from dictionary."""
        data = {
            "id": "mem3",
            "agent_id": "agent2",
            "memory_type": "observation",
            "content": "Heard a discussion",
            "importance": 5.0,
            "source": "meeting",
        }
        mem = MemoryModel.from_dict(data)

        assert mem.id == "mem3"
        assert mem.memory_type == "observation"
        assert mem.content == "Heard a discussion"


class TestTopologyEdgeModel:
    """Tests for TopologyEdgeModel."""

    def test_to_dict(self):
        """Test converting edge to dictionary."""
        edge = TopologyEdgeModel(
            simulation_id="sim1",
            source_id="alice",
            target_id="bob",
            weight=1.5,
        )
        data = edge.to_dict()

        assert data["simulation_id"] == "sim1"
        assert data["source_id"] == "alice"
        assert data["target_id"] == "bob"
        assert data["weight"] == 1.5

    def test_from_dict(self):
        """Test creating edge from dictionary."""
        data = {
            "simulation_id": "sim2",
            "source_id": "bob",
            "target_id": "charlie",
            "weight": 2.0,
        }
        edge = TopologyEdgeModel.from_dict(data)

        assert edge.source_id == "bob"
        assert edge.target_id == "charlie"
        assert edge.weight == 2.0


class TestTopologyConfigModel:
    """Tests for TopologyConfigModel."""

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = TopologyConfigModel(
            simulation_id="sim1",
            topology_type="mesh",
            directed=0,
            config_json='{"param": "value"}',
        )
        data = config.to_dict()

        assert data["simulation_id"] == "sim1"
        assert data["topology_type"] == "mesh"
        assert data["directed"] is False
        assert data["config"]["param"] == "value"

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "simulation_id": "sim2",
            "topology_type": "hub_spoke",
            "directed": True,
            "config": {"hub_id": "leader"},
        }
        config = TopologyConfigModel.from_dict(data)

        assert config.topology_type == "hub_spoke"
        assert config.directed == 1
        cfg = json.loads(config.config_json)
        assert cfg["hub_id"] == "leader"
