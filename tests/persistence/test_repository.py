"""Tests for Repository data access class."""

import pytest
from agentworld.core.models import SimulationStatus
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


@pytest.fixture
def repo():
    """Create repository with in-memory database."""
    init_db(in_memory=True)
    return Repository()


class TestSimulationMethods:
    """Tests for simulation CRUD operations."""

    def test_save_simulation(self, repo):
        """Test saving a simulation."""
        sim_data = {
            "id": "sim001",
            "name": "Test Simulation",
            "status": "pending",
            "current_step": 0,
            "total_steps": 10,
        }
        sim_id = repo.save_simulation(sim_data)
        assert sim_id == "sim001"

    def test_get_simulation(self, repo):
        """Test retrieving a simulation."""
        sim_data = {"id": "sim002", "name": "Get Test", "status": "running"}
        repo.save_simulation(sim_data)

        result = repo.get_simulation("sim002")
        assert result is not None
        assert result["name"] == "Get Test"
        assert result["status"] == "running"

    def test_get_simulation_not_found(self, repo):
        """Test getting non-existent simulation."""
        result = repo.get_simulation("nonexistent")
        assert result is None

    def test_list_simulations(self, repo):
        """Test listing simulations."""
        repo.save_simulation({"id": "s1", "name": "Sim 1", "status": "pending"})
        repo.save_simulation({"id": "s2", "name": "Sim 2", "status": "running"})

        results = repo.list_simulations()
        assert len(results) >= 2

    def test_list_simulations_by_status(self, repo):
        """Test filtering simulations by status."""
        repo.save_simulation({"id": "s3", "name": "Pending", "status": "pending"})
        repo.save_simulation({"id": "s4", "name": "Running", "status": "running"})

        pending = repo.list_simulations(status=SimulationStatus.PENDING)
        assert all(s["status"] == "pending" for s in pending)

    def test_update_simulation(self, repo):
        """Test updating a simulation."""
        repo.save_simulation({"id": "s5", "name": "Original", "status": "pending"})

        updated = repo.update_simulation("s5", {"name": "Updated", "current_step": 5})
        assert updated is True

        result = repo.get_simulation("s5")
        assert result["name"] == "Updated"
        assert result["current_step"] == 5

    def test_delete_simulation(self, repo):
        """Test deleting a simulation."""
        repo.save_simulation({"id": "s6", "name": "To Delete", "status": "pending"})

        deleted = repo.delete_simulation("s6")
        assert deleted is True

        result = repo.get_simulation("s6")
        assert result is None


class TestAgentMethods:
    """Tests for agent CRUD operations."""

    def test_save_agent(self, repo):
        """Test saving an agent."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        agent_data = {
            "id": "a1",
            "simulation_id": "sim",
            "name": "Alice",
            "traits": {"openness": 0.8},
        }
        agent_id = repo.save_agent(agent_data)
        assert agent_id == "a1"

    def test_get_agent(self, repo):
        """Test retrieving an agent."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a2", "simulation_id": "sim", "name": "Bob"})

        result = repo.get_agent("a2")
        assert result is not None
        assert result["name"] == "Bob"

    def test_get_agents_for_simulation(self, repo):
        """Test getting all agents for a simulation."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a3", "simulation_id": "sim", "name": "Agent 1"})
        repo.save_agent({"id": "a4", "simulation_id": "sim", "name": "Agent 2"})

        agents = repo.get_agents_for_simulation("sim")
        assert len(agents) == 2


class TestMessageMethods:
    """Tests for message CRUD operations."""

    def test_save_message(self, repo):
        """Test saving a message."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "sender", "simulation_id": "sim", "name": "Sender"})

        msg_data = {
            "id": "m1",
            "simulation_id": "sim",
            "sender_id": "sender",
            "content": "Hello!",
            "step": 1,
        }
        msg_id = repo.save_message(msg_data)
        assert msg_id == "m1"

    def test_get_messages_for_simulation(self, repo):
        """Test getting messages for a simulation."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a", "simulation_id": "sim", "name": "A"})
        repo.save_message({"id": "m1", "simulation_id": "sim", "sender_id": "a", "content": "Hi", "step": 1})
        repo.save_message({"id": "m2", "simulation_id": "sim", "sender_id": "a", "content": "Bye", "step": 2})

        messages = repo.get_messages_for_simulation("sim")
        assert len(messages) == 2

    def test_count_messages(self, repo):
        """Test counting messages."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a", "simulation_id": "sim", "name": "A"})
        repo.save_message({"id": "m1", "simulation_id": "sim", "sender_id": "a", "content": "1"})
        repo.save_message({"id": "m2", "simulation_id": "sim", "sender_id": "a", "content": "2"})

        count = repo.count_messages("sim")
        assert count == 2


class TestMemoryMethods:
    """Tests for memory CRUD operations."""

    def test_save_memory(self, repo):
        """Test saving a memory."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a", "simulation_id": "sim", "name": "A"})

        mem_data = {
            "id": "mem1",
            "agent_id": "a",
            "memory_type": "observation",
            "content": "Saw something",
            "importance": 5.0,
        }
        mem_id = repo.save_memory(mem_data)
        assert mem_id == "mem1"

    def test_get_memories_for_agent(self, repo):
        """Test getting memories for an agent."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a", "simulation_id": "sim", "name": "A"})
        repo.save_memory({"id": "m1", "agent_id": "a", "memory_type": "observation", "content": "1"})
        repo.save_memory({"id": "m2", "agent_id": "a", "memory_type": "reflection", "content": "2"})

        all_memories = repo.get_memories_for_agent("a")
        assert len(all_memories) == 2

        observations = repo.get_memories_for_agent("a", memory_type="observation")
        assert len(observations) == 1

    def test_delete_memories_for_agent(self, repo):
        """Test deleting all memories for an agent."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_agent({"id": "a", "simulation_id": "sim", "name": "A"})
        repo.save_memory({"id": "m1", "agent_id": "a", "memory_type": "observation", "content": "1"})
        repo.save_memory({"id": "m2", "agent_id": "a", "memory_type": "observation", "content": "2"})

        deleted = repo.delete_memories_for_agent("a")
        assert deleted == 2

        remaining = repo.get_memories_for_agent("a")
        assert len(remaining) == 0


class TestTopologyMethods:
    """Tests for topology CRUD operations."""

    def test_save_topology_config(self, repo):
        """Test saving topology configuration."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})

        config_data = {
            "simulation_id": "sim",
            "topology_type": "mesh",
            "directed": False,
            "config": {"param": "value"},
        }
        config_id = repo.save_topology_config(config_data)
        assert config_id is not None

    def test_get_topology_config(self, repo):
        """Test getting topology configuration."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_topology_config({
            "simulation_id": "sim",
            "topology_type": "hub_spoke",
            "config": {"hub_id": "leader"},
        })

        config = repo.get_topology_config("sim")
        assert config is not None
        assert config["topology_type"] == "hub_spoke"

    def test_save_topology_edges(self, repo):
        """Test saving topology edges."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})

        edges = [
            ("a", "b", 1.0),
            ("b", "c", 1.0),
            ("a", "c", 0.5),
        ]
        count = repo.save_topology_edges("sim", edges)
        assert count == 3

    def test_get_topology_edges(self, repo):
        """Test getting topology edges."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_topology_edges("sim", [("a", "b"), ("b", "c")])

        edges = repo.get_topology_edges("sim")
        assert len(edges) == 2

    def test_delete_topology(self, repo):
        """Test deleting topology data."""
        repo.save_simulation({"id": "sim", "name": "Test", "status": "pending"})
        repo.save_topology_config({"simulation_id": "sim", "topology_type": "mesh"})
        repo.save_topology_edges("sim", [("a", "b")])

        edges_deleted, configs_deleted = repo.delete_topology("sim")
        assert edges_deleted == 1
        assert configs_deleted == 1
