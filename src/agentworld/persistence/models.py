"""SQLAlchemy ORM models for AgentWorld."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    LargeBinary,
    Enum as SQLEnum,
)
from sqlalchemy.orm import declarative_base, relationship

from agentworld.core.models import SimulationStatus


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


Base = declarative_base()


class MemoryType:
    """Memory type constants."""
    OBSERVATION = "observation"
    REFLECTION = "reflection"


class SimulationModel(Base):
    """Database model for simulations."""

    __tablename__ = "simulations"

    id = Column(String(8), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(
        SQLEnum(SimulationStatus),
        default=SimulationStatus.PENDING,
        nullable=False,
    )
    config_json = Column(Text, nullable=True)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=10)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    agents = relationship("AgentModel", back_populates="simulation", cascade="all, delete-orphan")
    messages = relationship("MessageModel", back_populates="simulation", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value if self.status else None,
            "config": json.loads(self.config_json) if self.config_json else None,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationModel":
        """Create from dictionary."""
        config_json = json.dumps(data["config"]) if data.get("config") else None
        status = data.get("status")
        if isinstance(status, str):
            status = SimulationStatus(status)

        return cls(
            id=data["id"],
            name=data["name"],
            status=status or SimulationStatus.PENDING,
            config_json=config_json,
            current_step=data.get("current_step", 0),
            total_steps=data.get("total_steps", 10),
            total_tokens=data.get("total_tokens", 0),
            total_cost=data.get("total_cost", 0.0),
        )


class AgentModel(Base):
    """Database model for agents."""

    __tablename__ = "agents"

    id = Column(String(8), primary_key=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    traits_json = Column(Text, nullable=True)
    background = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel", back_populates="agents")
    sent_messages = relationship(
        "MessageModel",
        foreign_keys="MessageModel.sender_id",
        back_populates="sender",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "name": self.name,
            "traits": json.loads(self.traits_json) if self.traits_json else {},
            "background": self.background,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentModel":
        """Create from dictionary."""
        traits_json = json.dumps(data["traits"]) if data.get("traits") else None

        return cls(
            id=data["id"],
            simulation_id=data["simulation_id"],
            name=data["name"],
            traits_json=traits_json,
            background=data.get("background"),
            system_prompt=data.get("system_prompt"),
            model=data.get("model"),
        )


class MessageModel(Base):
    """Database model for messages."""

    __tablename__ = "messages"

    id = Column(String(8), primary_key=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False)
    sender_id = Column(String(8), ForeignKey("agents.id"), nullable=False)
    receiver_id = Column(String(8), ForeignKey("agents.id"), nullable=True)
    content = Column(Text, nullable=False)
    step = Column(Integer, default=0)
    timestamp = Column(DateTime, default=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel", back_populates="messages")
    sender = relationship("AgentModel", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("AgentModel", foreign_keys=[receiver_id])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "step": self.step,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageModel":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            id=data["id"],
            simulation_id=data["simulation_id"],
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            content=data["content"],
            step=data.get("step", 0),
            timestamp=timestamp,
        )


class MemoryModel(Base):
    """Database model for agent memories (observations and reflections)."""

    __tablename__ = "memories"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(8), ForeignKey("agents.id"), nullable=False)
    memory_type = Column(String(20), nullable=False)  # 'observation' or 'reflection'
    content = Column(Text, nullable=False)
    importance = Column(Float, default=5.0)
    embedding = Column(LargeBinary, nullable=True)  # numpy array serialized
    embedding_model = Column(String(100), nullable=True)
    source = Column(String(255), nullable=True)  # For observations
    location = Column(String(255), nullable=True)  # For observations
    source_memories = Column(Text, nullable=True)  # JSON list for reflections
    questions_addressed = Column(Text, nullable=True)  # JSON list for reflections
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    agent = relationship("AgentModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        import numpy as np

        embedding = None
        if self.embedding is not None:
            embedding = np.frombuffer(self.embedding, dtype=np.float32).tolist()

        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "memory_type": self.memory_type,
            "content": self.content,
            "importance": self.importance,
            "embedding": embedding,
            "embedding_model": self.embedding_model,
            "source": self.source,
            "location": self.location,
            "source_memories": json.loads(self.source_memories) if self.source_memories else [],
            "questions_addressed": json.loads(self.questions_addressed) if self.questions_addressed else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryModel":
        """Create from dictionary."""
        import numpy as np

        embedding = None
        if data.get("embedding") is not None:
            embedding = np.array(data["embedding"], dtype=np.float32).tobytes()

        source_memories = json.dumps(data.get("source_memories", []))
        questions_addressed = json.dumps(data.get("questions_addressed", []))

        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            memory_type=data["memory_type"],
            content=data["content"],
            importance=data.get("importance", 5.0),
            embedding=embedding,
            embedding_model=data.get("embedding_model"),
            source=data.get("source"),
            location=data.get("location"),
            source_memories=source_memories,
            questions_addressed=questions_addressed,
        )


class TopologyEdgeModel(Base):
    """Database model for topology edges."""

    __tablename__ = "topology_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False)
    source_id = Column(String(8), nullable=False)
    target_id = Column(String(8), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": self.weight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopologyEdgeModel":
        """Create from dictionary."""
        return cls(
            simulation_id=data["simulation_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            weight=data.get("weight", 1.0),
        )


class TopologyConfigModel(Base):
    """Database model for topology configuration."""

    __tablename__ = "topology_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False, unique=True)
    topology_type = Column(String(50), nullable=False)
    directed = Column(Integer, default=0)  # Boolean as int
    config_json = Column(Text, nullable=True)  # Additional config like hub_id, k, p, etc.
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "topology_type": self.topology_type,
            "directed": bool(self.directed),
            "config": json.loads(self.config_json) if self.config_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopologyConfigModel":
        """Create from dictionary."""
        config_json = json.dumps(data.get("config", {}))

        return cls(
            simulation_id=data["simulation_id"],
            topology_type=data["topology_type"],
            directed=int(data.get("directed", False)),
            config_json=config_json,
        )


class CheckpointModel(Base):
    """Database model for simulation checkpoints."""

    __tablename__ = "checkpoints"

    id = Column(String(8), primary_key=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False)
    step = Column(Integer, nullable=False)
    state_blob = Column(LargeBinary, nullable=False)  # msgpack/JSON serialized state
    reason = Column(String(50), nullable=True)  # manual, auto, shutdown, pause
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (without blob for safety)."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "step": self.step,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_state": self.state_blob is not None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointModel":
        """Create from dictionary."""
        state_blob = data.get("state_blob")
        if isinstance(state_blob, str):
            state_blob = state_blob.encode("utf-8")

        return cls(
            id=data["id"],
            simulation_id=data["simulation_id"],
            step=data["step"],
            state_blob=state_blob,
            reason=data.get("reason"),
        )


class MetricsModel(Base):
    """Database model for simulation metrics time series.

    Stores step-level metrics for analysis and visualization
    per ADR-008.
    """

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False)
    step = Column(Integer, nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "step": self.step,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricsModel":
        """Create from dictionary."""
        return cls(
            simulation_id=data["simulation_id"],
            step=data["step"],
            metric_name=data["metric_name"],
            metric_value=data["metric_value"],
        )


class LLMCacheModel(Base):
    """Database model for LLM response cache.

    Stores cached LLM responses for cost savings and
    reproducibility per ADR-003 and ADR-008.
    """

    __tablename__ = "llm_cache"

    cache_key = Column(String(64), primary_key=True)
    response_content = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=_utc_now)
    expires_at = Column(DateTime, nullable=True)  # NULL = never expires

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cache_key": self.cache_key,
            "response_content": self.response_content,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "model": self.model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMCacheModel":
        """Create from dictionary."""
        expires_at = data.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        return cls(
            cache_key=data["cache_key"],
            response_content=data["response_content"],
            prompt_tokens=data.get("prompt_tokens"),
            completion_tokens=data.get("completion_tokens"),
            model=data["model"],
            expires_at=expires_at,
        )


class PersonaLibraryModel(Base):
    """Database model for reusable persona templates.

    Stores persona definitions that can be reused across
    simulations per ADR-008.
    """

    __tablename__ = "persona_library"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    traits_json = Column(Text, nullable=False)  # TraitVector as JSON
    occupation = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)  # Specific age (ADR-008)
    age_range = Column(String(50), nullable=True)  # e.g., "25-35"
    background = Column(Text, nullable=True)
    goals_json = Column(Text, nullable=True)  # List of goals as JSON
    tags_json = Column(Text, nullable=True)  # List of tags for search

    # ADR-008 required fields
    version = Column(Integer, default=1, nullable=False)  # Schema version
    usage_count = Column(Integer, default=0, nullable=False)  # Times used
    is_template = Column(Integer, default=0, nullable=False)  # Boolean as int
    created_by = Column(String(255), nullable=True)  # Creator identifier
    prompt_preview = Column(Text, nullable=True)  # Generated prompt preview

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "traits": json.loads(self.traits_json) if self.traits_json else {},
            "occupation": self.occupation,
            "age": self.age,
            "age_range": self.age_range,
            "background": self.background,
            "goals": json.loads(self.goals_json) if self.goals_json else [],
            "tags": json.loads(self.tags_json) if self.tags_json else [],
            "version": self.version,
            "usage_count": self.usage_count,
            "is_template": bool(self.is_template),
            "created_by": self.created_by,
            "prompt_preview": self.prompt_preview,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaLibraryModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            traits_json=json.dumps(data.get("traits", {})),
            occupation=data.get("occupation"),
            age=data.get("age"),
            age_range=data.get("age_range"),
            background=data.get("background"),
            goals_json=json.dumps(data.get("goals", [])),
            tags_json=json.dumps(data.get("tags", [])),
            version=data.get("version", 1),
            usage_count=data.get("usage_count", 0),
            is_template=int(data.get("is_template", False)),
            created_by=data.get("created_by"),
            prompt_preview=data.get("prompt_preview"),
        )


class PersonaCollectionModel(Base):
    """Database model for persona collections.

    Groups personas together for reuse across simulations
    per ADR-008 Phase 4.
    """

    __tablename__ = "persona_collections"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True)  # List of tags for search
    is_public = Column(Integer, default=1, nullable=False)  # Boolean as int
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    members = relationship("PersonaCollectionMemberModel", back_populates="collection", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": json.loads(self.tags_json) if self.tags_json else [],
            "is_public": bool(self.is_public),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "member_count": len(self.members) if self.members else 0,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaCollectionModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            tags_json=json.dumps(data.get("tags", [])),
            is_public=int(data.get("is_public", True)),
            created_by=data.get("created_by"),
        )


class PersonaCollectionMemberModel(Base):
    """Database model for persona collection membership.

    Links personas to collections (many-to-many) per ADR-008 Phase 4.
    """

    __tablename__ = "persona_collection_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(String(36), ForeignKey("persona_collections.id"), nullable=False)
    persona_id = Column(String(36), ForeignKey("persona_library.id"), nullable=False)
    added_at = Column(DateTime, default=_utc_now)
    added_by = Column(String(255), nullable=True)

    # Relationships
    collection = relationship("PersonaCollectionModel", back_populates="members")
    persona = relationship("PersonaLibraryModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "persona_id": self.persona_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "added_by": self.added_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaCollectionMemberModel":
        """Create from dictionary."""
        return cls(
            collection_id=data["collection_id"],
            persona_id=data["persona_id"],
            added_by=data.get("added_by"),
        )


class PopulationTemplateModel(Base):
    """Database model for population generation templates.

    Defines demographic distributions and trait distributions
    for generating diverse persona populations per ADR-008 Phase 4.
    """

    __tablename__ = "population_templates"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Demographic configuration
    demographic_config_json = Column(Text, nullable=False, default="{}")
    # Example: {"age": {"min": 18, "max": 65, "distribution": "normal"},
    #           "occupations": ["engineer", "teacher", "artist"],
    #           "education_levels": ["high_school", "bachelors", "masters"]}

    # Trait distributions (Big Five)
    trait_distributions_json = Column(Text, nullable=False, default="{}")
    # Example: {"openness": {"mean": 0.5, "std": 0.2},
    #           "conscientiousness": {"mean": 0.6, "std": 0.15}}

    # Generation settings
    default_count = Column(Integer, default=10, nullable=False)
    seed = Column(Integer, nullable=True)  # For reproducibility

    # Metadata
    tags_json = Column(Text, nullable=True)
    is_public = Column(Integer, default=1, nullable=False)
    created_by = Column(String(255), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "demographic_config": json.loads(self.demographic_config_json) if self.demographic_config_json else {},
            "trait_distributions": json.loads(self.trait_distributions_json) if self.trait_distributions_json else {},
            "default_count": self.default_count,
            "seed": self.seed,
            "tags": json.loads(self.tags_json) if self.tags_json else [],
            "is_public": bool(self.is_public),
            "created_by": self.created_by,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PopulationTemplateModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            demographic_config_json=json.dumps(data.get("demographic_config", {})),
            trait_distributions_json=json.dumps(data.get("trait_distributions", {})),
            default_count=data.get("default_count", 10),
            seed=data.get("seed"),
            tags_json=json.dumps(data.get("tags", [])),
            is_public=int(data.get("is_public", True)),
            created_by=data.get("created_by"),
            usage_count=data.get("usage_count", 0),
        )


class ExperimentModel(Base):
    """Database model for experiment tracking.

    Groups multiple simulation runs for A/B testing and
    comparative analysis per ADR-008.
    """

    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)

    # ADR-008 required fields
    base_config_json = Column(Text, nullable=False, default="{}")  # Base simulation config
    independent_variable_json = Column(Text, nullable=False, default="{}")  # Variable being tested
    dependent_variable = Column(String(255), nullable=False, default="")  # Metric to measure

    # Experiment execution settings
    runs_per_variant = Column(Integer, default=3, nullable=False)
    randomize_order = Column(Integer, default=1, nullable=False)  # Boolean as int
    status = Column(String(50), default="draft")  # draft, running, completed, archived
    current_variant_index = Column(Integer, default=0, nullable=False)
    current_run_index = Column(Integer, default=0, nullable=False)

    # Results and metadata
    results_summary_json = Column(Text, nullable=True)  # Aggregated results
    created_by = Column(String(255), nullable=True)

    # Legacy fields (kept for compatibility)
    config_json = Column(Text, nullable=True)  # General experiment configuration
    variables_json = Column(Text, nullable=True)  # Additional variables

    # Timestamps
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hypothesis": self.hypothesis,
            "base_config": json.loads(self.base_config_json) if self.base_config_json else {},
            "independent_variable": json.loads(self.independent_variable_json) if self.independent_variable_json else {},
            "dependent_variable": self.dependent_variable,
            "runs_per_variant": self.runs_per_variant,
            "randomize_order": bool(self.randomize_order),
            "status": self.status,
            "current_variant_index": self.current_variant_index,
            "current_run_index": self.current_run_index,
            "results_summary": json.loads(self.results_summary_json) if self.results_summary_json else None,
            "created_by": self.created_by,
            "config": json.loads(self.config_json) if self.config_json else {},
            "variables": json.loads(self.variables_json) if self.variables_json else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentModel":
        """Create from dictionary."""
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            hypothesis=data.get("hypothesis"),
            base_config_json=json.dumps(data.get("base_config", {})),
            independent_variable_json=json.dumps(data.get("independent_variable", {})),
            dependent_variable=data.get("dependent_variable", ""),
            runs_per_variant=data.get("runs_per_variant", 3),
            randomize_order=int(data.get("randomize_order", True)),
            status=data.get("status", "draft"),
            current_variant_index=data.get("current_variant_index", 0),
            current_run_index=data.get("current_run_index", 0),
            results_summary_json=json.dumps(data.get("results_summary")) if data.get("results_summary") else None,
            created_by=data.get("created_by"),
            config_json=json.dumps(data.get("config", {})),
            variables_json=json.dumps(data.get("variables", [])),
            started_at=started_at,
            completed_at=completed_at,
        )


class ExperimentVariantModel(Base):
    """Database model for experiment variants.

    Represents different conditions being tested in an A/B experiment
    per ADR-008.
    """

    __tablename__ = "experiment_variants"

    id = Column(String(36), primary_key=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "control", "treatment_a"
    description = Column(Text, nullable=True)
    config_override_json = Column(Text, nullable=False, default="{}")  # Overrides for base_config
    is_control = Column(Integer, default=0, nullable=False)  # Boolean as int
    order_index = Column(Integer, default=0, nullable=False)  # For ordering
    color = Column(String(50), nullable=True)  # UI color for visualization
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    experiment = relationship("ExperimentModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "config_override": json.loads(self.config_override_json) if self.config_override_json else {},
            "is_control": bool(self.is_control),
            "order_index": self.order_index,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentVariantModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            experiment_id=data["experiment_id"],
            name=data["name"],
            description=data.get("description"),
            config_override_json=json.dumps(data.get("config_override", {})),
            is_control=int(data.get("is_control", False)),
            order_index=data.get("order_index", 0),
            color=data.get("color"),
        )


class MessageEvaluationModel(Base):
    """Database model for message evaluations.

    Stores evaluation scores and metadata for messages,
    supporting training data quality filtering and agent benchmarking
    per ADR-010 and ADR-016.
    """

    __tablename__ = "message_evaluations"

    id = Column(String(36), primary_key=True)
    message_id = Column(String(8), ForeignKey("messages.id"), nullable=False)
    evaluator_name = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)  # 0.0 - 1.0
    explanation = Column(Text, nullable=True)  # User-facing rationale

    # Provenance metadata (per ADR-010 amendment)
    evaluator_version = Column(String(50), nullable=False)
    judge_model = Column(String(100), nullable=True)  # If LLM-as-judge
    judge_prompt_hash = Column(String(64), nullable=True)
    input_hash = Column(String(64), nullable=False)  # What was judged

    # Operational metadata
    cost_usd = Column(Float, default=0.0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    message = relationship("MessageModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "evaluator_name": self.evaluator_name,
            "score": self.score,
            "explanation": self.explanation,
            "evaluator_version": self.evaluator_version,
            "judge_model": self.judge_model,
            "judge_prompt_hash": self.judge_prompt_hash,
            "input_hash": self.input_hash,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageEvaluationModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            message_id=data["message_id"],
            evaluator_name=data["evaluator_name"],
            score=data["score"],
            explanation=data.get("explanation"),
            evaluator_version=data["evaluator_version"],
            judge_model=data.get("judge_model"),
            judge_prompt_hash=data.get("judge_prompt_hash"),
            input_hash=data["input_hash"],
            cost_usd=data.get("cost_usd", 0.0),
            latency_ms=data.get("latency_ms", 0),
        )


class ExperimentRunModel(Base):
    """Database model for individual experiment runs.

    Links simulations to experiments for comparative analysis
    per ADR-008.
    """

    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False)
    variant_id = Column(String(36), ForeignKey("experiment_variants.id"), nullable=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=True)  # NULL until sim created
    run_number = Column(Integer, nullable=False)

    # Legacy field (kept for compatibility)
    variant = Column(String(100), nullable=True)  # A, B, control, etc.

    # ADR-008 required status tracking
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)

    # Run parameters and results
    parameters_json = Column(Text, nullable=True)  # Run-specific parameters
    results_json = Column(Text, nullable=True)  # Run results
    metrics_json = Column(Text, nullable=True)  # Computed metrics

    # Performance tracking
    duration_seconds = Column(Float, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=_utc_now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    experiment = relationship("ExperimentModel")
    variant_rel = relationship("ExperimentVariantModel")
    simulation = relationship("SimulationModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "variant_id": self.variant_id,
            "simulation_id": self.simulation_id,
            "run_number": self.run_number,
            "variant": self.variant,
            "status": self.status,
            "error_message": self.error_message,
            "parameters": json.loads(self.parameters_json) if self.parameters_json else {},
            "results": json.loads(self.results_json) if self.results_json else {},
            "metrics": json.loads(self.metrics_json) if self.metrics_json else {},
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentRunModel":
        """Create from dictionary."""
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            experiment_id=data["experiment_id"],
            variant_id=data.get("variant_id"),
            simulation_id=data.get("simulation_id"),
            run_number=data["run_number"],
            variant=data.get("variant"),
            status=data.get("status", "pending"),
            error_message=data.get("error_message"),
            parameters_json=json.dumps(data.get("parameters", {})),
            results_json=json.dumps(data.get("results", {})),
            metrics_json=json.dumps(data.get("metrics", {})) if data.get("metrics") else None,
            duration_seconds=data.get("duration_seconds"),
            total_tokens=data.get("total_tokens"),
            estimated_cost=data.get("estimated_cost"),
            started_at=started_at,
            completed_at=completed_at,
        )


class AppInstanceModel(Base):
    """Database model for app instances per simulation.

    Stores simulated app instances and their state per ADR-017.
    """

    __tablename__ = "app_instances"

    id = Column(String(36), primary_key=True)
    simulation_id = Column(String(8), ForeignKey("simulations.id"), nullable=False)
    app_id = Column(String(50), nullable=False)
    config_json = Column(Text, nullable=False, default="{}")
    state_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    simulation = relationship("SimulationModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "app_id": self.app_id,
            "config": json.loads(self.config_json) if self.config_json else {},
            "state": json.loads(self.state_json) if self.state_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppInstanceModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            simulation_id=data["simulation_id"],
            app_id=data["app_id"],
            config_json=json.dumps(data.get("config", {})),
            state_json=json.dumps(data.get("state", {})),
        )


class AppActionLogModel(Base):
    """Database model for app action audit log.

    Stores all app actions for auditing per ADR-017.
    """

    __tablename__ = "app_action_log"

    id = Column(String(36), primary_key=True)
    app_instance_id = Column(String(36), ForeignKey("app_instances.id"), nullable=False)
    agent_id = Column(String(8), nullable=False)
    step = Column(Integer, nullable=False)
    action_name = Column(String(100), nullable=False)
    params_json = Column(Text, nullable=False, default="{}")
    success = Column(Integer, nullable=False)  # 0 or 1
    result_json = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=_utc_now)

    # Relationships
    app_instance = relationship("AppInstanceModel")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "app_instance_id": self.app_instance_id,
            "agent_id": self.agent_id,
            "step": self.step,
            "action_name": self.action_name,
            "params": json.loads(self.params_json) if self.params_json else {},
            "success": bool(self.success),
            "result": json.loads(self.result_json) if self.result_json else None,
            "error": self.error,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppActionLogModel":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            app_instance_id=data["app_instance_id"],
            agent_id=data["agent_id"],
            step=data["step"],
            action_name=data["action_name"],
            params_json=json.dumps(data.get("params", {})),
            success=int(data.get("success", False)),
            result_json=json.dumps(data.get("result")) if data.get("result") else None,
            error=data.get("error"),
        )


class AppDefinitionModel(Base):
    """Database model for user-created app definitions.

    Stores JSON app definitions that can be loaded as DynamicApps
    per ADR-018.
    """

    __tablename__ = "app_definitions"

    id = Column(String(36), primary_key=True)
    app_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    icon = Column(String(50), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    definition_json = Column(Text, nullable=False)  # Full AppDefinition as JSON
    is_builtin = Column(Integer, default=0, nullable=False)  # Boolean as int
    is_active = Column(Integer, default=1, nullable=False, index=True)  # Boolean as int (soft delete)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    versions = relationship(
        "AppDefinitionVersionModel",
        back_populates="app_definition",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "version": self.version,
            "definition": json.loads(self.definition_json) if self.definition_json else {},
            "is_builtin": bool(self.is_builtin),
            "is_active": bool(self.is_active),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> dict[str, Any]:
        """Convert to summary dictionary (without full definition)."""
        definition = json.loads(self.definition_json) if self.definition_json else {}
        actions = definition.get("actions", [])
        return {
            "id": self.id,
            "app_id": self.app_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "version": self.version,
            "action_count": len(actions),
            "is_builtin": bool(self.is_builtin),
            "is_active": bool(self.is_active),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppDefinitionModel":
        """Create from dictionary."""
        definition = data.get("definition", {})
        if not definition:
            # Build definition from flat data
            definition = {
                "app_id": data["app_id"],
                "name": data["name"],
                "description": data.get("description", ""),
                "category": data["category"],
                "icon": data.get("icon", ""),
                "actions": data.get("actions", []),
                "state_schema": data.get("state_schema", []),
                "initial_config": data.get("initial_config", {}),
                "config_schema": data.get("config_schema", []),
            }

        return cls(
            id=data["id"],
            app_id=data["app_id"],
            name=data["name"],
            description=data.get("description"),
            category=data["category"],
            icon=data.get("icon"),
            version=data.get("version", 1),
            definition_json=json.dumps(definition),
            is_builtin=int(data.get("is_builtin", False)),
            is_active=int(data.get("is_active", True)),
            created_by=data.get("created_by"),
        )


class AppDefinitionVersionModel(Base):
    """Database model for app definition version history.

    Stores previous versions of app definitions for rollback
    per ADR-018.
    """

    __tablename__ = "app_definition_versions"

    id = Column(String(36), primary_key=True)
    app_definition_id = Column(
        String(36),
        ForeignKey("app_definitions.id"),
        nullable=False,
        index=True,
    )
    version = Column(Integer, nullable=False)
    definition_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    app_definition = relationship("AppDefinitionModel", back_populates="versions")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "app_definition_id": self.app_definition_id,
            "version": self.version,
            "definition": json.loads(self.definition_json) if self.definition_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppDefinitionVersionModel":
        """Create from dictionary."""
        definition = data.get("definition", {})
        return cls(
            id=data["id"],
            app_definition_id=data["app_definition_id"],
            version=data["version"],
            definition_json=json.dumps(definition),
        )
