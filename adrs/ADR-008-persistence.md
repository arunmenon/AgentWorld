# ADR-008: Persistence and State Management

## Status
Accepted

## Dependencies
- **[ADR-006](./ADR-006-dual-memory.md)**: Memory system data structures to be persisted

## Context

**User Requirement:**
> "SQLite database" for persistence with pause/resume capability

**Persistence Needs:**

| Data Type | Write Frequency | Size per Item | Query Patterns |
|-----------|-----------------|---------------|----------------|
| Simulation config | Once at start | ~1KB | By simulation ID |
| Agent state | Per step | ~500B | By agent ID, simulation ID |
| Messages | Per message | ~1KB | By step, by sender/receiver |
| Memories (ADR-006) | Per observation | ~2KB + embedding | By agent, similarity search |
| Metrics | Per step | ~200B | Time series |
| Checkpoints | Configurable | ~100KB-1MB | Latest per simulation |

**Options Evaluated:**

| Approach | Pros | Cons |
|----------|------|------|
| JSON files | Simple, portable, human-readable | No queries, large files, no ACID |
| SQLite | ACID, SQL queries, single file, zero-config | Schema migrations needed |
| PostgreSQL | Scale, concurrent access, advanced features | Infrastructure overhead |
| In-memory + export | Fast, simple | No pause/resume, data loss risk |

## Decision

Use **SQLite with SQLAlchemy ORM** for persistence.

> **Requirement**: SQLite must be compiled with JSON1 extension (standard in Python 3.9+). Verified at startup.

### Schema Design

```sql
-- Simulation metadata
CREATE TABLE simulations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    config JSON NOT NULL,        -- Full YAML config as JSON
    topology_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_step INTEGER DEFAULT 0,
    status TEXT DEFAULT 'created' -- created, running, paused, completed
);

-- Trigger to update updated_at
CREATE TRIGGER update_simulations_timestamp
AFTER UPDATE ON simulations
BEGIN
    UPDATE simulations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Agent definitions
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    persona_profile JSON NOT NULL,  -- Full PersonaProfile (ADR-004)
    trait_vector JSON NOT NULL,     -- TraitVector from ADR-004
    state TEXT DEFAULT 'idle',      -- idle, thinking, acting, waiting
    current_location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory entries (ADR-006) - MUST match data classes exactly
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    type TEXT NOT NULL,             -- 'observation' or 'reflection'
    content TEXT NOT NULL,
    importance REAL NOT NULL,       -- 1-10 scale
    embedding BLOB,                 -- numpy array, serialized (see below)
    embedding_model TEXT,           -- Model used for embedding (e.g., "text-embedding-3-small")
    embedding_dimensions INTEGER,   -- Vector dimensions for validation
    source TEXT,                    -- For observations: who/what caused this
    source_memories JSON,           -- For reflections: list of memory IDs
    questions_addressed JSON,       -- For reflections: questions this answers
    location TEXT,                  -- Spatial context (optional)
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_memories_agent ON memories(agent_id);
CREATE INDEX idx_memories_type ON memories(agent_id, type);
CREATE INDEX idx_memories_timestamp ON memories(agent_id, timestamp DESC);

-- Messages between agents
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    sender_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
    receiver_id TEXT REFERENCES agents(id) ON DELETE SET NULL,  -- NULL for broadcast
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'speech',      -- speech, thought, action
    timestamp TIMESTAMP NOT NULL
);
CREATE INDEX idx_messages_step ON messages(simulation_id, step);

-- Checkpoints for pause/resume
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    world_state BLOB NOT NULL,      -- Serialized World object (msgpack)
    serialization_format TEXT NOT NULL DEFAULT 'msgpack_v1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_checkpoints_sim ON checkpoints(simulation_id, step DESC);

-- Metrics time series
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_metrics_sim_step ON metrics(simulation_id, step);

-- LLM call cache (ADR-003)
CREATE TABLE llm_cache (
    cache_key TEXT PRIMARY KEY,
    response_content TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- NULL = never expires
);
CREATE INDEX idx_llm_cache_expires ON llm_cache(expires_at);

-- ============================================
-- PERSONA LIBRARY (UI-ADR-006)
-- ============================================

-- Reusable persona definitions (independent of simulations)
CREATE TABLE personas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    occupation TEXT NOT NULL,
    age INTEGER,
    background TEXT,                 -- Rich text description
    traits JSON NOT NULL,            -- {bigFive: {...}, custom: {...}}
    prompt_preview TEXT,             -- Generated system prompt

    -- Metadata
    version INTEGER DEFAULT 1,
    tags JSON,                       -- ["engineer", "tech-savvy", ...]
    usage_count INTEGER DEFAULT 0,   -- Track popularity

    -- Ownership
    created_by TEXT,                 -- User ID (future multi-user)
    is_template BOOLEAN DEFAULT FALSE,  -- System-provided templates

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_personas_name ON personas(name);
CREATE INDEX idx_personas_occupation ON personas(occupation);
CREATE INDEX idx_personas_tags ON personas(tags);

-- Trigger to update updated_at
CREATE TRIGGER update_personas_timestamp
AFTER UPDATE ON personas
BEGIN
    UPDATE personas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Persona collections (folders/groups)
CREATE TABLE persona_collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,                      -- UI display color
    icon TEXT,                       -- Icon identifier

    -- Metadata
    is_smart BOOLEAN DEFAULT FALSE,  -- Smart collection (filter-based)
    smart_filter JSON,               -- Filter criteria for smart collections

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many: personas <-> collections
CREATE TABLE persona_collection_members (
    persona_id TEXT NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    collection_id TEXT NOT NULL REFERENCES persona_collections(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (persona_id, collection_id)
);

-- Population generation templates
CREATE TABLE population_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    config JSON NOT NULL,            -- PopulationConfig from UI-ADR-006

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EXPERIMENTS (UI-ADR-008)
-- ============================================

-- Experiment definitions
CREATE TABLE experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    hypothesis TEXT,                 -- Research hypothesis

    -- Configuration
    base_config JSON NOT NULL,       -- Base simulation config
    independent_variable JSON NOT NULL,  -- {path: "...", type: "categorical|numeric"}
    dependent_variable TEXT NOT NULL,    -- Metric to measure

    -- Execution settings
    runs_per_variant INTEGER DEFAULT 3,
    randomize_order BOOLEAN DEFAULT TRUE,

    -- Status
    status TEXT DEFAULT 'draft',     -- draft, running, paused, completed, failed
    current_variant_index INTEGER DEFAULT 0,
    current_run_index INTEGER DEFAULT 0,

    -- Results summary (computed after completion)
    results_summary JSON,            -- {winner, summary, anova, effectSize, ...}

    -- Metadata
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX idx_experiments_status ON experiments(status);

-- Trigger to update updated_at
CREATE TRIGGER update_experiments_timestamp
AFTER UPDATE ON experiments
BEGIN
    UPDATE experiments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Experiment variants (A/B/C... conditions)
CREATE TABLE experiment_variants (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,              -- e.g., "Control", "Treatment A"
    description TEXT,

    -- Variant configuration
    config_overrides JSON NOT NULL,  -- Overrides to base_config
    color TEXT,                      -- UI display color

    -- Order
    sort_order INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_variants_experiment ON experiment_variants(experiment_id);

-- Individual experiment runs (one per variant per iteration)
CREATE TABLE experiment_runs (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    variant_id TEXT NOT NULL REFERENCES experiment_variants(id) ON DELETE CASCADE,
    run_number INTEGER NOT NULL,     -- 1, 2, 3... for runs_per_variant

    -- Linked simulation
    simulation_id TEXT REFERENCES simulations(id) ON DELETE SET NULL,

    -- Status
    status TEXT DEFAULT 'pending',   -- pending, running, completed, failed
    error_message TEXT,

    -- Results (captured after completion)
    metrics JSON,                    -- {dependent_variable: value, ...}
    duration_seconds REAL,
    total_tokens INTEGER,
    estimated_cost REAL,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_runs_experiment ON experiment_runs(experiment_id);
CREATE INDEX idx_runs_variant ON experiment_runs(variant_id);
CREATE INDEX idx_runs_status ON experiment_runs(status);

-- Experiment tags for organization
CREATE TABLE experiment_tags (
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (experiment_id, tag)
);
CREATE INDEX idx_experiment_tags ON experiment_tags(tag);
```

### Serialization Formats

**Embeddings (BLOB):**
```python
import numpy as np
import struct

def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Serialize numpy array to bytes with dtype header."""
    dtype_str = str(embedding.dtype).encode('utf-8')
    header = struct.pack('I', len(dtype_str)) + dtype_str
    return header + embedding.tobytes()

def deserialize_embedding(data: bytes) -> np.ndarray:
    """Deserialize bytes back to numpy array."""
    dtype_len = struct.unpack('I', data[:4])[0]
    dtype_str = data[4:4+dtype_len].decode('utf-8')
    array_data = data[4+dtype_len:]
    return np.frombuffer(array_data, dtype=np.dtype(dtype_str))
```

**World State (Checkpoint):**
```python
import msgpack
import numpy as np

def serialize_world_state(world: World) -> bytes:
    """
    Serialize World to msgpack with custom type handlers.

    Format: msgpack_v1
    - Handles numpy arrays
    - Handles datetime
    - Handles NetworkX graphs
    """
    def encode_hook(obj):
        if isinstance(obj, np.ndarray):
            return {'__ndarray__': True, 'data': obj.tobytes(),
                    'dtype': str(obj.dtype), 'shape': obj.shape}
        if isinstance(obj, datetime):
            return {'__datetime__': True, 'iso': obj.isoformat()}
        if isinstance(obj, nx.Graph):
            return {'__networkx__': True,
                    'data': nx.node_link_data(obj)}
        return obj

    state = world.to_dict()  # Must implement serializable dict
    return msgpack.packb(state, default=encode_hook, strict_types=False)

def deserialize_world_state(data: bytes) -> dict:
    """Deserialize msgpack to dict with type reconstruction."""
    def decode_hook(obj):
        if isinstance(obj, dict):
            if obj.get('__ndarray__'):
                return np.frombuffer(obj['data'],
                                     dtype=np.dtype(obj['dtype'])).reshape(obj['shape'])
            if obj.get('__datetime__'):
                return datetime.fromisoformat(obj['iso'])
            if obj.get('__networkx__'):
                return nx.node_link_graph(obj['data'])
        return obj

    return msgpack.unpackb(data, object_hook=decode_hook, raw=False)
```

### Pause/Resume Implementation

```python
class CheckpointManager:
    async def save(self, simulation: Simulation) -> Checkpoint:
        """Save simulation state for later resumption."""
        world_bytes = serialize_world_state(simulation.world)

        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            simulation_id=simulation.id,
            step=simulation.current_step,
            world_state=world_bytes,
            serialization_format="msgpack_v1"
        )
        self.session.add(checkpoint)
        await self.session.commit()
        return checkpoint

    async def restore(self, simulation_id: str,
                      step: int = None) -> Simulation:
        """Restore simulation from checkpoint."""
        query = select(Checkpoint).where(
            Checkpoint.simulation_id == simulation_id
        ).order_by(Checkpoint.step.desc())

        if step is not None:
            query = query.where(Checkpoint.step == step)

        checkpoint = await self.session.scalar(query)
        if not checkpoint:
            raise CheckpointNotFoundError(simulation_id, step)

        # Validate format
        if checkpoint.serialization_format != "msgpack_v1":
            raise IncompatibleCheckpointError(
                f"Unknown format: {checkpoint.serialization_format}"
            )

        world_dict = deserialize_world_state(checkpoint.world_state)
        return Simulation.from_dict(world_dict)
```

### Repository Pattern

```python
class AgentRepository:
    """Data access for agents."""

    async def get_by_simulation(self, sim_id: str) -> List[Agent]:
        query = select(AgentModel).where(
            AgentModel.simulation_id == sim_id
        )
        results = await self.session.scalars(query)
        return [self._to_domain(r) for r in results]

    async def update_state(self, agent_id: str, state: AgentState) -> None:
        await self.session.execute(
            update(AgentModel)
            .where(AgentModel.id == agent_id)
            .values(state=state.value)
        )
        await self.session.commit()

class MemoryRepository:
    """Data access for memories (ADR-006)."""

    async def add_observation(self, agent_id: str, obs: Observation) -> None:
        model = MemoryModel(
            id=obs.id,
            agent_id=agent_id,
            type='observation',
            content=obs.content,
            importance=obs.importance,
            embedding=serialize_embedding(obs.embedding),
            embedding_model=obs.embedding_model,
            embedding_dimensions=len(obs.embedding),
            source=obs.source,
            location=obs.location,
            timestamp=obs.timestamp
        )
        self.session.add(model)
        await self.session.commit()

    async def get_recent(self, agent_id: str, limit: int = 100) -> List[Memory]:
        query = (
            select(MemoryModel)
            .where(MemoryModel.agent_id == agent_id)
            .order_by(MemoryModel.timestamp.desc())
            .limit(limit)
        )
        results = await self.session.scalars(query)
        return [self._to_domain(r) for r in results]

    async def search_similar(self, agent_id: str,
                             query_embedding: np.ndarray,
                             embedding_model: str,
                             k: int = 10) -> List[Memory]:
        """
        Similarity search. For MVP, loads and computes in Python.
        Phase 5: Migrate to ChromaDB for efficient vector search.
        """
        # Load all embeddings for this agent
        query = (
            select(MemoryModel)
            .where(MemoryModel.agent_id == agent_id)
            .where(MemoryModel.embedding_model == embedding_model)  # Must match!
        )
        results = await self.session.scalars(query)

        # Compute similarities in Python
        scored = []
        for mem in results:
            embedding = deserialize_embedding(mem.embedding)
            similarity = cosine_similarity(query_embedding, embedding)
            scored.append((mem, similarity))

        # Return top k
        scored.sort(key=lambda x: x[1], reverse=True)
        return [self._to_domain(mem) for mem, _ in scored[:k]]
```

## Consequences

**Positive:**
- Single file deployment (just copy .db file)
- ACID transactions ensure consistency
- SQL queries enable analysis and debugging
- Pause/resume capability via checkpoints
- Easy backup (copy file)
- No external service dependencies
- Schema matches ADR-006 data classes exactly

**Negative:**
- Schema migrations needed for changes (use Alembic)
- Embedding similarity search inefficient in SQLite (O(n))
- Single-writer limitation (fine for our scale per ADR-002)
- JSON fields need JSON1 extension

**Future Enhancement (Phase 5):**
- Optional ChromaDB/Qdrant for vector similarity search
- PostgreSQL adapter for multi-user deployments

**Interactions:**
- Stores memory data structures from **[ADR-006](./ADR-006-dual-memory.md)** (full schema parity)
- Stores agent trait vectors from **[ADR-004](./ADR-004-trait-vector-persona.md)**
- Stores LLM cache from **[ADR-003](./ADR-003-llm-architecture.md)**

## Related ADRs
- [ADR-003](./ADR-003-llm-architecture.md): LLM cache storage
- [ADR-004](./ADR-004-trait-vector-persona.md): Trait vectors stored here
- [ADR-006](./ADR-006-dual-memory.md): Memory data structures persisted (schema must match)
