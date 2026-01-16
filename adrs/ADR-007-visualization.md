# ADR-007: Visualization Strategy

## Status
Accepted

## Dependencies
- **[ADR-001](./ADR-001-framework-inspiration.md)**: Framework visualization approaches surveyed

## Context

**User Requirement:**
> "Both Web UI and CLI" for observing simulations

**Visualization Needs Analysis:**

| Need | CLI Capability | Web Capability |
|------|---------------|----------------|
| Quick iteration | Instant startup | Server startup |
| Real-time monitoring | Text-based | Rich dashboards |
| Remote access | Local only | Browser anywhere |
| Scripting/CI | Pipe-friendly | Needs API |
| Network visualization | ASCII art only | Interactive graphs |
| Agent detail inspection | Verbose output | Click to expand |

**Framework Visualization Approaches (from ADR-001):**

| Framework | Approach |
|-----------|----------|
| TinyTroupe | Jupyter notebooks, logging, no built-in UI |
| AI Town | Full 2D game-like visual sandbox |
| AgentSociety | Web dashboards with metrics |
| CrewAI | CLI output and logs |
| AgentVerse | Web UI for demos |
| CAMEL | AgentOps integration for observability |

## Decision

Implement **both Rich CLI (Phase 1) and FastAPI Web Dashboard (Phase 4)** sharing a common event system.

### CLI Interface (Phase 1)

**Interactive Mode:**
```
┌──────────────────────────────────────────────────────────────────┐
│ AgentWorld - Product Focus Group                        [Step 15]│
├──────────────────────────────────────────────────────────────────┤
│ Progress: ████████████░░░░░░░░░░░░░░░░░░░░  15/100  15%         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Lisa (Engineer, O:0.8 C:0.9 E:0.4)                              │
│    "I think the new feature would be useful, but the learning   │
│     curve might be steep for non-technical users..."            │
│                                                                  │
│ Bob (Designer, O:0.7 C:0.6 E:0.8)                               │
│    "From a UX perspective, we should consider progressive       │
│     disclosure to reduce initial complexity."                   │
│                                                                  │
│ Carol (Manager, O:0.5 C:0.9 E:0.6)                              │
│    "What about the timeline implications? Can we ship an MVP    │
│     first and iterate?"                                         │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ Messages: 45 | Reflections: 3 | Tokens: 12,450 | Cost: $0.23    │
└──────────────────────────────────────────────────────────────────┘
```

**Non-Interactive Mode (CI/Logging):**
```python
class OutputMode(Enum):
    INTERACTIVE = "interactive"  # Rich live display
    LOG = "log"                  # Line-by-line logging (CI-friendly)
    JSON = "json"                # Structured JSON output
    QUIET = "quiet"              # Minimal output, only errors

# Usage
agentworld run config.yaml --output-mode log
agentworld run config.yaml --output-mode json > results.jsonl
```

**Log Mode Output:**
```
[2025-01-15 10:30:45] STEP 1/100
[2025-01-15 10:30:46] Lisa: "I think the new feature would be useful..."
[2025-01-15 10:30:47] Bob: "From a UX perspective..."
[2025-01-15 10:30:48] STEP 2/100
...
[2025-01-15 10:35:22] COMPLETE: 100 steps, 450 messages, $2.34
```

### Web Dashboard (Phase 4)

```
┌────────────────────────────────────────────────────────────────────┐
│  AgentWorld Dashboard                              [Read-Only Mode]│
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐│
│  │   Network Graph     │  │       Agent Activity Feed            ││
│  │   (D3.js)           │  │                                      ││
│  │                     │  │  [2s] Lisa: "I think the new..."     ││
│  │    (Lisa)──(Bob)    │  │  [5s] Bob: "From a UX perspective..."││
│  │      │  ╲   │       │  │  [8s] Carol: "What about the..."     ││
│  │      │   ╲  │       │  │                                      ││
│  │   (Carol)──(Dan)    │  │  ──────────────────────────────────  ││
│  │                     │  │  Lisa reflected: "The team seems     ││
│  │  [Click node for    │  │     concerned about complexity..."   ││
│  │   agent details]    │  │                                      ││
│  └─────────────────────┘  └──────────────────────────────────────┘│
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐│
│  │  Simulation Metrics │  │       Selected: Lisa                 ││
│  │                     │  │                                      ││
│  │  Messages: 45       │  │  Traits:                             ││
│  │  Reflections: 3     │  │    O: ████████░░ 0.8                 ││
│  │  Tokens: 12,450     │  │    C: █████████░ 0.9                 ││
│  │  Est. Cost: $0.23   │  │    E: ████░░░░░░ 0.4                 ││
│  │                     │  │                                      ││
│  │  Topology: Mesh     │  │  Memories: 34 obs, 5 reflections     ││
│  │  Clustering: 1.0    │  │  Last action: "Responded to Bob"     ││
│  └─────────────────────┘  └──────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
```

**Graph Rendering:**
- Use **D3.js force-directed layout** via react-force-graph (consistent with UI-ADR-004)
- Canvas rendering for performance with 50+ nodes
- Web Worker offloading for force simulation (see UI-ADR-004 performance optimizations)
- Performance target: Smooth rendering for 50 nodes

**Access Control (Phase 4+):**
```yaml
# Web dashboard config
web:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  auth:
    enabled: true  # Enable for remote access
    method: basic  # basic | token | none
    users:
      - username: admin
        password_hash: "..."  # bcrypt hash
  mode: read_only  # read_only | interactive (future)
```

### Event System Architecture

```python
from abc import ABC, abstractmethod
from asyncio import Queue
from typing import List
import asyncio

class Event:
    """Base event type."""
    timestamp: datetime
    event_type: str
    data: dict

class EventSubscriber(ABC):
    """Interface for event consumers."""

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """Handle an event. Must not block."""
        pass

class SimulationEventBus:
    """
    Publish events to all subscribers with isolation.

    Features:
    - Async fan-out to all subscribers
    - Per-subscriber queues prevent blocking
    - Backpressure handling
    - Event buffering for late subscribers
    """

    def __init__(self, buffer_size: int = 1000):
        self.subscribers: List[EventSubscriber] = []
        self._queues: dict[EventSubscriber, Queue] = {}
        self._buffer: List[Event] = []
        self._buffer_size = buffer_size

    def subscribe(self, subscriber: EventSubscriber,
                  replay_buffer: bool = False) -> None:
        """Add subscriber. Optionally replay buffered events."""
        self.subscribers.append(subscriber)
        self._queues[subscriber] = Queue(maxsize=100)

        if replay_buffer:
            for event in self._buffer:
                asyncio.create_task(subscriber.on_event(event))

        # Start worker for this subscriber
        asyncio.create_task(self._subscriber_worker(subscriber))

    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers (non-blocking)."""
        # Buffer for late subscribers
        self._buffer.append(event)
        if len(self._buffer) > self._buffer_size:
            self._buffer.pop(0)

        # Fan out to subscriber queues
        for subscriber, queue in self._queues.items():
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Backpressure: drop oldest event for slow subscriber
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except:
                    pass  # Best effort

    async def _subscriber_worker(self, subscriber: EventSubscriber) -> None:
        """Process events for a single subscriber."""
        queue = self._queues[subscriber]
        while True:
            event = await queue.get()
            try:
                await asyncio.wait_for(
                    subscriber.on_event(event),
                    timeout=5.0  # Prevent hung subscribers
                )
            except asyncio.TimeoutError:
                pass  # Log warning, continue
            except Exception as e:
                pass  # Log error, continue
```

### Subscriber Implementations

```python
class CLISubscriber(EventSubscriber):
    """Updates Rich Live display on events."""

    def __init__(self, console: Console, mode: OutputMode):
        self.console = console
        self.mode = mode

    async def on_event(self, event: Event) -> None:
        if self.mode == OutputMode.INTERACTIVE:
            # Update Rich live display
            self._update_display(event)
        elif self.mode == OutputMode.LOG:
            # Simple line output
            self.console.print(self._format_log_line(event))
        elif self.mode == OutputMode.JSON:
            # Structured output
            print(json.dumps(event.data))

class WebSocketSubscriber(EventSubscriber):
    """Broadcasts to connected WebSocket clients."""

    def __init__(self, connections: List[WebSocket]):
        self.connections = connections

    async def on_event(self, event: Event) -> None:
        message = json.dumps(event.data)
        # Fan out to all connections
        await asyncio.gather(*[
            self._safe_send(conn, message)
            for conn in self.connections
        ], return_exceptions=True)
```

### Tech Stack

- **CLI**: `rich` (progress bars, tables, live display, panels) + `typer` (commands)
- **Web Backend**: `FastAPI` (REST + WebSocket)
- **Web Frontend** (aligned with UI-ADR-004):
  - `React` (component framework)
  - `react-force-graph` / `D3.js` (network visualization)
  - `Zustand` (UI state management)
  - `React Query` (server state)
  - `Framer Motion` (animations)
  - `react-window` (virtualized lists)

## Consequences

**Positive:**
- CLI enables rapid iteration during development
- Web enables remote monitoring and team collaboration
- Both share same event system (single source of truth)
- CLI works in CI/CD pipelines (log/json modes)
- Web provides richer interaction (click agents, hover for details)
- Isolated subscribers prevent cascading failures

**Negative:**
- Two UIs to maintain
- Web adds deployment complexity (need to serve static files)
- Real-time web requires WebSocket infrastructure
- Buffer memory overhead for event replay

**Implementation Order:**
1. Phase 1: Rich CLI only (interactive + log modes)
2. Phase 4: Add web dashboard (after core simulation stable)

## Related ADRs
- [ADR-001](./ADR-001-framework-inspiration.md): Framework visualization approaches
- [UI-ADR-004](./UI-ADR-004-realtime-visualization.md): Detailed real-time visualization specification (defines React + D3.js tech stack)
