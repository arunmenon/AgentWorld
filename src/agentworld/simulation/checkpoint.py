"""Checkpoint system for saving and restoring simulation state.

This module implements checkpoint save/restore functionality
as specified in ADR-011 using msgpack serialization.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
import struct

# We use JSON for broader compatibility, but msgpack could be added later
# import msgpack  # Would be preferred for binary state


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""

    id: str
    simulation_id: str
    step: int
    reason: str = ""  # e.g., "manual", "auto", "shutdown", "pause"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "step": self.step,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointMetadata":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now(UTC)

        return cls(
            id=data["id"],
            simulation_id=data["simulation_id"],
            step=data["step"],
            reason=data.get("reason", ""),
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class SimulationState:
    """Complete state of a simulation at a point in time."""

    simulation_id: str
    step: int
    name: str
    status: str
    config: dict[str, Any]
    agents: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    topology_type: str
    topology_edges: list[tuple[str, str, float]]
    agent_memories: dict[str, list[dict[str, Any]]]  # agent_id -> memories
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "simulation_id": self.simulation_id,
            "step": self.step,
            "name": self.name,
            "status": self.status,
            "config": self.config,
            "agents": self.agents,
            "messages": self.messages,
            "topology_type": self.topology_type,
            "topology_edges": self.topology_edges,
            "agent_memories": self.agent_memories,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationState":
        """Create from dictionary."""
        return cls(
            simulation_id=data["simulation_id"],
            step=data["step"],
            name=data["name"],
            status=data["status"],
            config=data.get("config", {}),
            agents=data.get("agents", []),
            messages=data.get("messages", []),
            topology_type=data.get("topology_type", "mesh"),
            topology_edges=data.get("topology_edges", []),
            agent_memories=data.get("agent_memories", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Checkpoint:
    """A simulation checkpoint containing state and metadata."""

    metadata: CheckpointMetadata
    state: SimulationState

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "state": self.state.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            metadata=CheckpointMetadata.from_dict(data["metadata"]),
            state=SimulationState.from_dict(data["state"]),
        )


class CheckpointSerializer(Protocol):
    """Protocol for checkpoint serialization."""

    def serialize(self, checkpoint: Checkpoint) -> bytes:
        """Serialize checkpoint to bytes."""
        ...

    def deserialize(self, data: bytes) -> Checkpoint:
        """Deserialize bytes to checkpoint."""
        ...


class JSONCheckpointSerializer:
    """JSON-based checkpoint serializer."""

    def serialize(self, checkpoint: Checkpoint) -> bytes:
        """Serialize checkpoint to JSON bytes."""
        return json.dumps(checkpoint.to_dict()).encode("utf-8")

    def deserialize(self, data: bytes) -> Checkpoint:
        """Deserialize JSON bytes to checkpoint."""
        return Checkpoint.from_dict(json.loads(data.decode("utf-8")))


class CheckpointManager:
    """Manager for creating, saving, and restoring checkpoints.

    This is an in-memory implementation. The persistence layer
    will handle actual database storage.
    """

    def __init__(self, serializer: CheckpointSerializer | None = None):
        """Initialize checkpoint manager.

        Args:
            serializer: Checkpoint serializer (default: JSON)
        """
        self.serializer = serializer or JSONCheckpointSerializer()
        self._checkpoints: dict[str, Checkpoint] = {}

    def create_checkpoint(
        self,
        simulation_id: str,
        step: int,
        state: SimulationState,
        reason: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """Create a new checkpoint.

        Args:
            simulation_id: Simulation ID
            step: Current step number
            state: Simulation state to checkpoint
            reason: Reason for checkpoint
            metadata: Additional metadata

        Returns:
            Created checkpoint
        """
        checkpoint_id = str(uuid.uuid4())[:8]

        checkpoint_metadata = CheckpointMetadata(
            id=checkpoint_id,
            simulation_id=simulation_id,
            step=step,
            reason=reason,
            metadata=metadata or {},
        )

        checkpoint = Checkpoint(
            metadata=checkpoint_metadata,
            state=state,
        )

        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint or None if not found
        """
        return self._checkpoints.get(checkpoint_id)

    def list_checkpoints(
        self,
        simulation_id: str | None = None,
    ) -> list[CheckpointMetadata]:
        """List checkpoint metadata.

        Args:
            simulation_id: Optional filter by simulation ID

        Returns:
            List of checkpoint metadata
        """
        checkpoints = self._checkpoints.values()
        if simulation_id:
            checkpoints = [
                c for c in checkpoints if c.metadata.simulation_id == simulation_id
            ]
        return sorted(
            [c.metadata for c in checkpoints],
            key=lambda m: m.created_at,
            reverse=True,
        )

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            True if deleted, False if not found
        """
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    def serialize_checkpoint(self, checkpoint_id: str) -> bytes | None:
        """Serialize a checkpoint to bytes.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Serialized bytes or None if not found
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            return None
        return self.serializer.serialize(checkpoint)

    def deserialize_checkpoint(self, data: bytes) -> Checkpoint:
        """Deserialize bytes to a checkpoint.

        Args:
            data: Serialized checkpoint bytes

        Returns:
            Deserialized checkpoint
        """
        return self.serializer.deserialize(data)

    def restore_checkpoint(self, data: bytes) -> Checkpoint:
        """Restore and register a checkpoint from serialized data.

        Args:
            data: Serialized checkpoint bytes

        Returns:
            Restored checkpoint
        """
        checkpoint = self.deserialize_checkpoint(data)
        self._checkpoints[checkpoint.metadata.id] = checkpoint
        return checkpoint

    def clear_checkpoints(self, simulation_id: str | None = None) -> int:
        """Clear checkpoints.

        Args:
            simulation_id: Optional filter by simulation ID

        Returns:
            Number of checkpoints cleared
        """
        if simulation_id is None:
            count = len(self._checkpoints)
            self._checkpoints.clear()
            return count

        to_delete = [
            cid
            for cid, c in self._checkpoints.items()
            if c.metadata.simulation_id == simulation_id
        ]
        for cid in to_delete:
            del self._checkpoints[cid]
        return len(to_delete)


def capture_simulation_state(simulation: Any) -> SimulationState:
    """Capture the current state of a simulation.

    Args:
        simulation: Simulation instance

    Returns:
        SimulationState snapshot
    """
    # Extract agent data with memories
    agents = []
    agent_memories: dict[str, list[dict]] = {}

    for agent in simulation.agents:
        agent_data = agent.to_dict()
        agents.append(agent_data)

        # Capture memories if available
        memories = []
        if hasattr(agent, "memory") and agent._memory is not None:
            for obs in agent.memory.observations:
                memories.append({
                    "type": "observation",
                    "id": obs.id,
                    "content": obs.content,
                    "importance": obs.importance,
                    "source": obs.source,
                    "created_at": obs.created_at.isoformat(),
                })
            for ref in agent.memory.reflections:
                memories.append({
                    "type": "reflection",
                    "id": ref.id,
                    "content": ref.content,
                    "importance": ref.importance,
                    "created_at": ref.created_at.isoformat(),
                })
        agent_memories[agent.id] = memories

    # Extract messages
    messages = [msg.to_dict() for msg in simulation._messages]

    # Extract topology edges
    topology_edges = []
    if simulation._topology is not None:
        for source, target, data in simulation._topology.graph.edges(data=True):
            topology_edges.append((source, target, data.get("weight", 1.0)))

    return SimulationState(
        simulation_id=simulation.id,
        step=simulation.current_step,
        name=simulation.name,
        status=simulation.status.value,
        config=simulation.config.to_dict() if simulation.config else {},
        agents=agents,
        messages=messages,
        topology_type=simulation.topology_type,
        topology_edges=topology_edges,
        agent_memories=agent_memories,
    )
