# ADR-012: API and WebSocket Event Schema

## Status
Accepted

## Dependencies
- **[ADR-007](./ADR-007-visualization.md)**: Event system architecture
- **[ADR-008](./ADR-008-persistence.md)**: Data models for API responses
- **[ADR-011](./ADR-011-simulation-runtime.md)**: Runtime events to expose

## Context

**Critical Gap Identified:**
ADR-007 defines the event bus architecture but leaves undefined:
- REST API endpoints and payloads
- WebSocket message format and protocol
- Event schema versioning strategy
- Pagination for large result sets
- Error response format

**API Requirements:**

| Requirement | Rationale |
|-------------|-----------|
| REST endpoints | CRUD operations, queries, batch operations |
| WebSocket protocol | Real-time event streaming |
| Schema versioning | Backward compatibility as system evolves |
| Pagination | Handle large agent/message lists |
| Error format | Consistent error handling across clients |

**Clients to Support:**
- CLI (via REST for commands, WebSocket for live display)
- Web dashboard (REST + WebSocket)
- External integrations (REST API)
- Programmatic SDK (REST + WebSocket)

## Decision

Implement **versioned REST API with JSON:API-inspired format** and **WebSocket event streaming with typed messages**.

### REST API Design

#### Base URL and Versioning

```
Base URL: /api/v1/
Version header: X-AgentWorld-Version: 2025-01-15
```

**Versioning Strategy:**
- URL path versioning for major changes (`/api/v1/`, `/api/v2/`)
- Date-based header for minor changes within version
- 6-month deprecation window for old versions

#### Endpoint Structure

```
# Simulations
GET     /api/v1/simulations                    # List simulations
POST    /api/v1/simulations                    # Create simulation
GET     /api/v1/simulations/{id}               # Get simulation
PATCH   /api/v1/simulations/{id}               # Update simulation
DELETE  /api/v1/simulations/{id}               # Delete simulation

# Simulation control
POST    /api/v1/simulations/{id}/start         # Start simulation
POST    /api/v1/simulations/{id}/pause         # Pause simulation
POST    /api/v1/simulations/{id}/resume        # Resume simulation
POST    /api/v1/simulations/{id}/step          # Execute single step
POST    /api/v1/simulations/{id}/stop          # Stop simulation

# Agents
GET     /api/v1/simulations/{id}/agents        # List agents
GET     /api/v1/simulations/{id}/agents/{aid}  # Get agent details
GET     /api/v1/simulations/{id}/agents/{aid}/memories  # Agent memories

# Messages
GET     /api/v1/simulations/{id}/messages      # List messages
GET     /api/v1/simulations/{id}/messages/{mid} # Get message

# Checkpoints
GET     /api/v1/simulations/{id}/checkpoints   # List checkpoints
POST    /api/v1/simulations/{id}/checkpoints   # Create checkpoint
POST    /api/v1/simulations/{id}/checkpoints/{cid}/restore  # Restore

# Metrics
GET     /api/v1/simulations/{id}/metrics       # Get metrics
GET     /api/v1/simulations/{id}/metrics/export # Export metrics

# System
GET     /api/v1/health                         # Health check
GET     /api/v1/config                         # Get configuration
```

#### Request/Response Format

**Standard Response Envelope:**
```json
{
  "data": { ... },           // Primary response data
  "meta": {                  // Metadata
    "request_id": "uuid",
    "timestamp": "ISO8601",
    "version": "2025-01-15"
  },
  "links": {                 // HATEOAS links (optional)
    "self": "/api/v1/simulations/123",
    "agents": "/api/v1/simulations/123/agents"
  }
}
```

**Pagination:**
```json
{
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total_pages": 10,
      "total_count": 487
    }
  },
  "links": {
    "self": "/api/v1/simulations/123/messages?page=1",
    "next": "/api/v1/simulations/123/messages?page=2",
    "last": "/api/v1/simulations/123/messages?page=10"
  }
}
```

**Query Parameters:**
```
?page=1&per_page=50          # Pagination
?sort=-created_at            # Sort (- for descending)
?filter[status]=running      # Filter by field
?filter[step][gte]=10        # Filter with operator
?include=agents,messages     # Include related resources
?fields=id,name,status       # Sparse fieldsets
```

#### Error Response Format

```json
{
  "error": {
    "code": "SIMULATION_NOT_FOUND",
    "message": "Simulation with ID '123' not found",
    "details": {
      "simulation_id": "123"
    },
    "request_id": "req-uuid-here"
  },
  "meta": {
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

**Error Codes:**
```python
class ErrorCode(Enum):
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"           # 400
    INVALID_JSON = "INVALID_JSON"                   # 400
    UNAUTHORIZED = "UNAUTHORIZED"                   # 401
    FORBIDDEN = "FORBIDDEN"                         # 403
    NOT_FOUND = "NOT_FOUND"                         # 404
    SIMULATION_NOT_FOUND = "SIMULATION_NOT_FOUND"   # 404
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"             # 404
    CONFLICT = "CONFLICT"                           # 409
    SIMULATION_ALREADY_RUNNING = "SIMULATION_ALREADY_RUNNING"  # 409

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"               # 500
    LLM_PROVIDER_ERROR = "LLM_PROVIDER_ERROR"       # 502
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"    # 503
    TIMEOUT = "TIMEOUT"                             # 504
```

### Resource Schemas

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SimulationStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationResponse(BaseModel):
    """GET /api/v1/simulations/{id}"""
    id: str
    name: str
    description: Optional[str]
    status: SimulationStatus
    current_step: int
    total_steps: Optional[int]
    topology_type: str
    agent_count: int
    created_at: datetime
    updated_at: datetime

    # Computed fields
    progress_percent: Optional[float]
    estimated_completion: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sim-abc123",
                "name": "Product Focus Group",
                "status": "running",
                "current_step": 15,
                "total_steps": 100,
                "topology_type": "hub_spoke",
                "agent_count": 8,
                "progress_percent": 15.0
            }
        }

class AgentResponse(BaseModel):
    """GET /api/v1/simulations/{id}/agents/{aid}"""
    id: str
    name: str
    state: str
    persona_summary: str
    traits: TraitVectorResponse
    memory_count: int
    message_count: int
    current_location: Optional[str]

class TraitVectorResponse(BaseModel):
    """Trait vector (ADR-004) serialization."""
    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)
    custom_traits: dict[str, float] = {}

class MessageResponse(BaseModel):
    """GET /api/v1/simulations/{id}/messages/{mid}"""
    id: str
    step: int
    sender_id: Optional[str]
    sender_name: Optional[str]
    receiver_id: Optional[str]
    receiver_name: Optional[str]
    content: str
    message_type: str  # speech, thought, action
    timestamp: datetime

class MemoryResponse(BaseModel):
    """Memory entry (ADR-006) serialization."""
    id: str
    type: str  # observation, reflection
    content: str
    importance: float
    timestamp: datetime
    source: Optional[str]
    source_memories: Optional[List[str]]  # For reflections

class MetricsResponse(BaseModel):
    """GET /api/v1/simulations/{id}/metrics"""
    simulation_id: str
    current_step: int
    total_messages: int
    total_observations: int
    total_reflections: int
    total_tokens: int
    estimated_cost_usd: float
    messages_per_step: List[int]
    agents_active: int

# Request schemas
class CreateSimulationRequest(BaseModel):
    """POST /api/v1/simulations"""
    name: str
    description: Optional[str]
    config_yaml: str  # Full YAML configuration

class StepRequest(BaseModel):
    """POST /api/v1/simulations/{id}/step"""
    count: int = Field(default=1, ge=1, le=100)
```

### WebSocket Protocol

#### Connection Lifecycle

```
1. Client connects: ws://host/api/v1/ws
2. Server sends: ConnectionAck with session_id
3. Client sends: Subscribe to simulation(s)
4. Server streams: Events for subscribed simulations
5. Client can send: Commands (pause, inject message)
6. Connection closed: Cleanup subscriptions
```

#### Message Format

```python
@dataclass
class WebSocketMessage:
    """Base WebSocket message format."""
    type: str           # Message type identifier
    payload: dict       # Type-specific payload
    timestamp: str      # ISO8601 timestamp
    sequence: int       # Monotonic sequence number
    simulation_id: Optional[str]  # If simulation-specific

# JSON format
{
    "type": "event.step_completed",
    "payload": { ... },
    "timestamp": "2025-01-15T10:30:45.123Z",
    "sequence": 42,
    "simulation_id": "sim-abc123"
}
```

#### Client → Server Messages

```python
class ClientMessageType(Enum):
    # Subscription management
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Commands
    COMMAND_PAUSE = "command.pause"
    COMMAND_RESUME = "command.resume"
    COMMAND_STEP = "command.step"
    COMMAND_INJECT = "command.inject"  # Inject stimulus

    # Heartbeat
    PING = "ping"

# Subscribe to simulation events
{
    "type": "subscribe",
    "payload": {
        "simulation_id": "sim-abc123",
        "events": ["*"]  # Or specific: ["step_completed", "agent_message"]
    }
}

# Inject stimulus into simulation
{
    "type": "command.inject",
    "payload": {
        "simulation_id": "sim-abc123",
        "content": "Moderator asks: What do you think about the pricing?",
        "target_agents": ["agent-1", "agent-2"]  # Optional, null = all
    }
}
```

#### Server → Client Messages

```python
class ServerMessageType(Enum):
    # Connection
    CONNECTION_ACK = "connection.ack"
    SUBSCRIPTION_ACK = "subscription.ack"
    ERROR = "error"

    # Simulation events
    EVENT_SIMULATION_STARTED = "event.simulation_started"
    EVENT_SIMULATION_PAUSED = "event.simulation_paused"
    EVENT_SIMULATION_COMPLETED = "event.simulation_completed"
    EVENT_STEP_STARTED = "event.step_started"
    EVENT_STEP_COMPLETED = "event.step_completed"

    # Agent events
    EVENT_AGENT_MESSAGE = "event.agent_message"
    EVENT_AGENT_THINKING = "event.agent_thinking"
    EVENT_AGENT_REFLECTION = "event.agent_reflection"
    EVENT_AGENT_ERROR = "event.agent_error"

    # System events
    EVENT_CHECKPOINT_SAVED = "event.checkpoint_saved"
    EVENT_METRICS_UPDATE = "event.metrics_update"

    # Heartbeat
    PONG = "pong"

# Step completed event
{
    "type": "event.step_completed",
    "payload": {
        "step": 15,
        "duration_ms": 2340,
        "actions_count": 8,
        "messages_count": 5,
        "reflections_count": 1
    },
    "timestamp": "2025-01-15T10:30:45.123Z",
    "sequence": 42,
    "simulation_id": "sim-abc123"
}

# Agent message event
{
    "type": "event.agent_message",
    "payload": {
        "message_id": "msg-xyz789",
        "step": 15,
        "sender": {
            "id": "agent-lisa",
            "name": "Lisa",
            "traits_summary": "O:0.8 C:0.9 E:0.4"
        },
        "receiver": {
            "id": "agent-bob",
            "name": "Bob"
        },
        "content": "I think the pricing is reasonable for the features offered.",
        "message_type": "speech"
    },
    "timestamp": "2025-01-15T10:30:45.456Z",
    "sequence": 43,
    "simulation_id": "sim-abc123"
}
```

### Event Schema Versioning

```python
class EventSchema:
    """Versioned event schema with migration support."""

    CURRENT_VERSION = "1.0.0"

    @classmethod
    def serialize(cls, event: Event, version: str = None) -> dict:
        """Serialize event to specified version."""
        version = version or cls.CURRENT_VERSION

        if version == "1.0.0":
            return cls._serialize_v1(event)
        else:
            raise ValueError(f"Unknown schema version: {version}")

    @classmethod
    def deserialize(cls, data: dict) -> Event:
        """Deserialize event, auto-detecting version."""
        version = data.get("schema_version", "1.0.0")

        if version == "1.0.0":
            return cls._deserialize_v1(data)
        else:
            raise ValueError(f"Unknown schema version: {version}")

    @classmethod
    def _serialize_v1(cls, event: Event) -> dict:
        return {
            "schema_version": "1.0.0",
            "type": event.type.value,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat(),
            "simulation_id": event.simulation_id
        }
```

### Rate Limiting and Backpressure

```python
class WebSocketManager:
    """Manage WebSocket connections with backpressure."""

    def __init__(self, max_buffer_size: int = 1000):
        self.connections: Dict[str, WebSocket] = {}
        self.buffers: Dict[str, asyncio.Queue] = {}
        self.max_buffer_size = max_buffer_size

    async def send_event(self, conn_id: str, event: dict) -> bool:
        """Send event with backpressure handling."""
        buffer = self.buffers.get(conn_id)
        if not buffer:
            return False

        if buffer.qsize() >= self.max_buffer_size:
            # Backpressure: drop oldest or signal client
            try:
                buffer.get_nowait()  # Drop oldest
                logger.warning(f"Buffer overflow for {conn_id}, dropping event")
            except asyncio.QueueEmpty:
                pass

        await buffer.put(event)
        return True

    async def _sender_loop(self, conn_id: str):
        """Dedicated sender loop per connection."""
        websocket = self.connections[conn_id]
        buffer = self.buffers[conn_id]

        while True:
            event = await buffer.get()
            try:
                await websocket.send_json(event)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Send error for {conn_id}: {e}")
```

### Implementation with FastAPI

```python
from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AgentWorld API",
    version="1.0.0",
    description="Multi-agent simulation platform"
)

# CORS for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/simulations", response_model=PaginatedResponse[SimulationResponse])
async def list_simulations(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: Optional[SimulationStatus] = None,
    sort: str = "-created_at"
):
    """List all simulations with pagination."""
    ...

@app.post("/api/v1/simulations/{sim_id}/step")
async def execute_step(sim_id: str, request: StepRequest):
    """Execute simulation step(s)."""
    simulation = await get_simulation_or_404(sim_id)

    if simulation.status != SimulationStatus.RUNNING:
        raise HTTPException(
            status_code=409,
            detail={"code": "SIMULATION_NOT_RUNNING"}
        )

    results = await simulation.step(count=request.count)
    return {"data": results}

@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events."""
    await websocket.accept()
    conn_id = str(uuid.uuid4())

    try:
        await ws_manager.register(conn_id, websocket)
        await websocket.send_json({
            "type": "connection.ack",
            "payload": {"connection_id": conn_id}
        })

        while True:
            data = await websocket.receive_json()
            await handle_client_message(conn_id, data)

    except WebSocketDisconnect:
        await ws_manager.unregister(conn_id)
```

## Consequences

**Positive:**
- Clear, versioned API contract for all clients
- Consistent error handling across endpoints
- Real-time updates via WebSocket
- Pagination prevents large response issues
- Schema versioning enables evolution

**Negative:**
- More complex than minimal REST
- WebSocket state management complexity
- Version maintenance overhead
- HATEOAS links add response size

**Tradeoffs:**
- Flexibility vs simplicity in query parameters
- Real-time vs polling (WebSocket complexity)
- Schema strictness vs evolution speed

## Related ADRs
- [ADR-007](./ADR-007-visualization.md): Event system
- [ADR-008](./ADR-008-persistence.md): Data models
- [ADR-011](./ADR-011-simulation-runtime.md): Runtime events
- [ADR-013](./ADR-013-security.md): Authentication
