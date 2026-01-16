"""Tests for checkpoint system."""

import pytest
from datetime import datetime

from agentworld.simulation.checkpoint import (
    CheckpointMetadata,
    SimulationState,
    Checkpoint,
    CheckpointManager,
    JSONCheckpointSerializer,
)


class TestCheckpointMetadata:
    """Tests for CheckpointMetadata dataclass."""

    def test_creation(self):
        """Test creating metadata."""
        metadata = CheckpointMetadata(
            id="chk123",
            simulation_id="sim456",
            step=10,
            reason="manual",
        )
        assert metadata.id == "chk123"
        assert metadata.simulation_id == "sim456"
        assert metadata.step == 10
        assert metadata.reason == "manual"
        assert isinstance(metadata.created_at, datetime)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = CheckpointMetadata(
            id="chk123",
            simulation_id="sim456",
            step=10,
            reason="auto",
        )
        data = metadata.to_dict()

        assert data["id"] == "chk123"
        assert data["simulation_id"] == "sim456"
        assert data["step"] == 10
        assert data["reason"] == "auto"
        assert "created_at" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "chk123",
            "simulation_id": "sim456",
            "step": 15,
            "reason": "shutdown",
            "created_at": "2024-01-15T10:30:00",
        }
        metadata = CheckpointMetadata.from_dict(data)

        assert metadata.id == "chk123"
        assert metadata.simulation_id == "sim456"
        assert metadata.step == 15
        assert metadata.reason == "shutdown"


class TestSimulationState:
    """Tests for SimulationState dataclass."""

    def test_creation_minimal(self):
        """Test creating state with minimal params."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test Sim",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )
        assert state.simulation_id == "sim123"
        assert state.step == 5
        assert state.name == "Test Sim"

    def test_creation_with_data(self):
        """Test creating state with full data."""
        agents = [{"id": "a1", "name": "Alice"}]
        messages = [{"id": "m1", "content": "Hello"}]
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test Sim",
            status="running",
            config={"steps": 100},
            agents=agents,
            messages=messages,
            topology_type="hub_spoke",
            topology_edges=[("a1", "hub", 1.0)],
            agent_memories={"a1": [{"type": "observation", "content": "saw something"}]},
            metadata={"key": "value"},
        )

        assert len(state.agents) == 1
        assert len(state.messages) == 1
        assert state.topology_type == "hub_spoke"
        assert len(state.topology_edges) == 1
        assert "a1" in state.agent_memories

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )
        data = state.to_dict()

        assert data["simulation_id"] == "sim123"
        assert data["step"] == 5
        assert data["topology_type"] == "mesh"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "simulation_id": "sim123",
            "step": 10,
            "name": "Restored",
            "status": "paused",
            "config": {"steps": 50},
            "agents": [],
            "messages": [],
            "topology_type": "mesh",
            "topology_edges": [],
            "agent_memories": {},
        }
        state = SimulationState.from_dict(data)

        assert state.simulation_id == "sim123"
        assert state.step == 10
        assert state.name == "Restored"
        assert state.status == "paused"


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""

    @pytest.fixture
    def checkpoint(self):
        """Create a checkpoint instance."""
        metadata = CheckpointMetadata(
            id="chk123",
            simulation_id="sim456",
            step=10,
            reason="test",
        )
        state = SimulationState(
            simulation_id="sim456",
            step=10,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )
        return Checkpoint(metadata=metadata, state=state)

    def test_creation(self, checkpoint):
        """Test creating checkpoint."""
        assert checkpoint.metadata.id == "chk123"
        assert checkpoint.state.step == 10

    def test_to_dict(self, checkpoint):
        """Test conversion to dictionary."""
        data = checkpoint.to_dict()

        assert "metadata" in data
        assert "state" in data
        assert data["metadata"]["id"] == "chk123"
        assert data["state"]["step"] == 10

    def test_from_dict(self, checkpoint):
        """Test creation from dictionary."""
        data = checkpoint.to_dict()
        restored = Checkpoint.from_dict(data)

        assert restored.metadata.id == checkpoint.metadata.id
        assert restored.state.step == checkpoint.state.step


class TestJSONCheckpointSerializer:
    """Tests for JSONCheckpointSerializer."""

    @pytest.fixture
    def serializer(self):
        """Create serializer instance."""
        return JSONCheckpointSerializer()

    @pytest.fixture
    def checkpoint(self):
        """Create a checkpoint instance."""
        metadata = CheckpointMetadata(
            id="chk123",
            simulation_id="sim456",
            step=10,
            reason="test",
        )
        state = SimulationState(
            simulation_id="sim456",
            step=10,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )
        return Checkpoint(metadata=metadata, state=state)

    def test_serialize(self, serializer, checkpoint):
        """Test serialization."""
        data = serializer.serialize(checkpoint)

        assert isinstance(data, bytes)
        assert b"chk123" in data

    def test_deserialize(self, serializer, checkpoint):
        """Test deserialization."""
        serialized = serializer.serialize(checkpoint)
        restored = serializer.deserialize(serialized)

        assert restored.metadata.id == checkpoint.metadata.id
        assert restored.state.step == checkpoint.state.step

    def test_roundtrip(self, serializer, checkpoint):
        """Test serialization roundtrip."""
        serialized = serializer.serialize(checkpoint)
        restored = serializer.deserialize(serialized)

        assert restored.to_dict() == checkpoint.to_dict()


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return CheckpointManager()

    def test_create_checkpoint(self, manager):
        """Test creating a checkpoint."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        checkpoint = manager.create_checkpoint(
            simulation_id="sim123",
            step=5,
            state=state,
            reason="manual",
        )

        assert checkpoint.metadata.simulation_id == "sim123"
        assert checkpoint.metadata.step == 5
        assert checkpoint.metadata.reason == "manual"

    def test_get_checkpoint(self, manager):
        """Test getting a checkpoint."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        created = manager.create_checkpoint(
            simulation_id="sim123",
            step=5,
            state=state,
        )

        retrieved = manager.get_checkpoint(created.metadata.id)

        assert retrieved is not None
        assert retrieved.metadata.id == created.metadata.id

    def test_get_nonexistent_checkpoint(self, manager):
        """Test getting nonexistent checkpoint."""
        retrieved = manager.get_checkpoint("nonexistent")
        assert retrieved is None

    def test_list_checkpoints(self, manager):
        """Test listing checkpoints."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        manager.create_checkpoint(simulation_id="sim123", step=1, state=state)
        manager.create_checkpoint(simulation_id="sim123", step=2, state=state)
        manager.create_checkpoint(simulation_id="sim456", step=1, state=state)

        # All checkpoints
        all_checkpoints = manager.list_checkpoints()
        assert len(all_checkpoints) == 3

        # Filtered by simulation
        sim123_checkpoints = manager.list_checkpoints(simulation_id="sim123")
        assert len(sim123_checkpoints) == 2

    def test_delete_checkpoint(self, manager):
        """Test deleting a checkpoint."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        created = manager.create_checkpoint(
            simulation_id="sim123",
            step=5,
            state=state,
        )

        deleted = manager.delete_checkpoint(created.metadata.id)
        assert deleted

        retrieved = manager.get_checkpoint(created.metadata.id)
        assert retrieved is None

    def test_delete_nonexistent_checkpoint(self, manager):
        """Test deleting nonexistent checkpoint."""
        deleted = manager.delete_checkpoint("nonexistent")
        assert not deleted

    def test_clear_checkpoints(self, manager):
        """Test clearing all checkpoints."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        manager.create_checkpoint(simulation_id="sim123", step=1, state=state)
        manager.create_checkpoint(simulation_id="sim456", step=1, state=state)

        cleared = manager.clear_checkpoints()
        assert cleared == 2
        assert len(manager.list_checkpoints()) == 0

    def test_clear_checkpoints_by_simulation(self, manager):
        """Test clearing checkpoints for specific simulation."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        manager.create_checkpoint(simulation_id="sim123", step=1, state=state)
        manager.create_checkpoint(simulation_id="sim123", step=2, state=state)
        manager.create_checkpoint(simulation_id="sim456", step=1, state=state)

        cleared = manager.clear_checkpoints(simulation_id="sim123")
        assert cleared == 2
        assert len(manager.list_checkpoints()) == 1

    def test_serialize_checkpoint(self, manager):
        """Test serializing a checkpoint."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        created = manager.create_checkpoint(
            simulation_id="sim123",
            step=5,
            state=state,
        )

        serialized = manager.serialize_checkpoint(created.metadata.id)

        assert serialized is not None
        assert isinstance(serialized, bytes)

    def test_restore_checkpoint(self, manager):
        """Test restoring from serialized data."""
        state = SimulationState(
            simulation_id="sim123",
            step=5,
            name="Test",
            status="running",
            config={},
            agents=[],
            messages=[],
            topology_type="mesh",
            topology_edges=[],
            agent_memories={},
        )

        created = manager.create_checkpoint(
            simulation_id="sim123",
            step=5,
            state=state,
        )

        serialized = manager.serialize_checkpoint(created.metadata.id)
        manager.clear_checkpoints()  # Clear all

        restored = manager.restore_checkpoint(serialized)

        assert restored.metadata.id == created.metadata.id
        assert manager.get_checkpoint(restored.metadata.id) is not None
