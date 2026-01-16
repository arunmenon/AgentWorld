# ADR-011: Simulation Runtime & Scheduling

## Status
Accepted

## Dependencies
- **[ADR-002](./ADR-002-agent-scale.md)**: Scale constraints inform concurrency model
- **[ADR-003](./ADR-003-llm-architecture.md)**: LLM calls are primary bottleneck
- **[ADR-005](./ADR-005-network-topology.md)**: Topology determines message routing
- **[ADR-006](./ADR-006-dual-memory.md)**: Memory operations during steps

## Context

**Critical Gap Identified:**
The existing ADRs define *what* agents do but not *how* or *when*:
- What constitutes a "step"?
- In what order do agents act within a step?
- Can agents act in parallel?
- How is determinism/reproducibility achieved?
- What happens when a step times out or fails?

**Execution Model Requirements:**

| Requirement | Rationale |
|-------------|-----------|
| Step semantics | Clear definition of simulation unit of time |
| Agent ordering | Fairness, reproducibility, research validity |
| Parallelism | Performance within rate limits |
| Determinism | Reproducible experiments for research |
| Cancellation | Graceful shutdown, timeout handling |
| Error recovery | Resilience to individual agent failures |

**Concurrency Challenges:**

1. **LLM Rate Limits**: Providers limit requests per minute (OpenAI: 500 RPM for GPT-4)
2. **Order Dependencies**: Agent A's output may be input to Agent B
3. **Shared State**: Multiple agents accessing topology, world state
4. **Memory Consistency**: Observations must be ordered within agent

## Decision

Implement a **Step-Based Synchronous Execution Model** with configurable parallelism and deterministic ordering.

### Core Concepts

```python
@dataclass
class StepConfig:
    """Configuration for step execution."""
    # Parallelism
    max_concurrent_agents: int = 5       # Parallel agent processing
    max_concurrent_llm_calls: int = 10   # Total LLM calls in flight

    # Timing
    step_timeout_seconds: float = 60.0   # Max time per step
    agent_timeout_seconds: float = 30.0  # Max time per agent action

    # Ordering
    ordering_strategy: OrderingStrategy = OrderingStrategy.ROUND_ROBIN
    deterministic_seed: Optional[int] = None  # For reproducibility

    # Error handling
    on_agent_error: ErrorStrategy = ErrorStrategy.LOG_AND_CONTINUE
    max_consecutive_failures: int = 3    # Per agent before suspension

class OrderingStrategy(Enum):
    """How agents are ordered within a step."""
    ROUND_ROBIN = "round_robin"      # Fixed order, rotate starting position
    RANDOM = "random"                # Random order each step (with seed)
    PRIORITY = "priority"            # By agent priority attribute
    TOPOLOGY = "topology"            # BFS from hub/central nodes
    SIMULTANEOUS = "simultaneous"    # All at once (parallel only)

class ErrorStrategy(Enum):
    """How to handle agent errors."""
    FAIL_FAST = "fail_fast"          # Stop simulation on any error
    LOG_AND_CONTINUE = "log_and_continue"  # Skip failed agent, continue
    RETRY = "retry"                  # Retry with backoff
    SUSPEND_AGENT = "suspend_agent"  # Disable agent after N failures
```

### Step Execution Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                          SIMULATION STEP N                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  Phase 1:   │───►│  Phase 2:   │───►│  Phase 3:   │             │
│  │  PERCEIVE   │    │    ACT      │    │   COMMIT    │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│                                                                     │
│  All agents see     Agents generate    Messages delivered,          │
│  pending messages   responses          state committed              │
│                     (parallel OK)                                   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Invariants:                                                        │
│  • All perceive happens before any act                              │
│  • Messages from step N visible in step N+1                         │
│  • No agent sees another's step N output within step N              │
└─────────────────────────────────────────────────────────────────────┘
```

**Three-Phase Step:**

1. **PERCEIVE Phase**: All agents receive pending messages and observations
   - Read-only access to world state
   - Messages from previous step delivered
   - Observations added to memory (ADR-006)

2. **ACT Phase**: Agents generate responses (parallelizable)
   - LLM calls for agent decisions
   - Bounded by `max_concurrent_agents`
   - Outputs buffered, not yet visible

3. **COMMIT Phase**: Atomic state update
   - Messages queued for next step
   - Agent states updated
   - Metrics recorded
   - Checkpoint saved (if configured)

### Implementation

```python
class SimulationEngine:
    """Core simulation execution engine."""

    def __init__(self, world: World, config: StepConfig):
        self.world = world
        self.config = config
        self._step_number = 0
        self._rng = random.Random(config.deterministic_seed)
        self._agent_failures: Dict[str, int] = defaultdict(int)
        self._semaphore = asyncio.Semaphore(config.max_concurrent_llm_calls)

    async def run(self, steps: int) -> SimulationResult:
        """Run simulation for specified number of steps."""
        results = []

        for _ in range(steps):
            if self._check_termination():
                break

            step_result = await self.step()
            results.append(step_result)

            await self._emit_event(StepCompletedEvent(
                step=self._step_number,
                result=step_result
            ))

        return SimulationResult(steps=results)

    async def step(self) -> StepResult:
        """Execute a single simulation step."""
        self._step_number += 1
        step_start = time.monotonic()

        try:
            async with asyncio.timeout(self.config.step_timeout_seconds):
                # Phase 1: PERCEIVE
                await self._perceive_phase()

                # Phase 2: ACT
                actions = await self._act_phase()

                # Phase 3: COMMIT
                await self._commit_phase(actions)

                return StepResult(
                    step=self._step_number,
                    actions=actions,
                    duration=time.monotonic() - step_start,
                    status=StepStatus.COMPLETED
                )

        except asyncio.TimeoutError:
            await self._handle_step_timeout()
            return StepResult(
                step=self._step_number,
                status=StepStatus.TIMEOUT
            )

    async def _perceive_phase(self) -> None:
        """Deliver pending messages and observations to all agents."""
        pending_messages = self.world.message_queue.drain()

        for message in pending_messages:
            # Respect topology (ADR-005)
            if self._can_deliver(message):
                receiver = self.world.agents[message.receiver_id]
                await receiver.receive(message)

                # Add to memory as observation (ADR-006)
                await receiver.memory.add_observation(
                    content=f"{message.sender_id} said: {message.content}",
                    source=message.sender_id,
                    importance=await self._rate_importance(message)
                )

    async def _act_phase(self) -> List[AgentAction]:
        """Execute agent actions with controlled parallelism."""
        agents = self._get_ordered_agents()
        actions = []

        if self.config.ordering_strategy == OrderingStrategy.SIMULTANEOUS:
            # Full parallelism
            tasks = [self._agent_act(agent) for agent in agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            actions = self._process_results(results, agents)
        else:
            # Controlled parallelism respecting order
            for batch in self._batch_agents(agents):
                tasks = [self._agent_act(agent) for agent in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                actions.extend(self._process_results(results, batch))

        return actions

    async def _agent_act(self, agent: Agent) -> AgentAction:
        """Execute single agent's action with rate limiting."""
        async with self._semaphore:  # Rate limit LLM calls
            try:
                async with asyncio.timeout(self.config.agent_timeout_seconds):
                    action = await agent.act()
                    self._agent_failures[agent.id] = 0  # Reset on success
                    return action

            except asyncio.TimeoutError:
                return self._handle_agent_timeout(agent)
            except Exception as e:
                return self._handle_agent_error(agent, e)

    async def _commit_phase(self, actions: List[AgentAction]) -> None:
        """Atomically commit step results."""
        # Queue messages for next step
        for action in actions:
            if action.message:
                self.world.message_queue.enqueue(action.message)

        # Update agent states
        for action in actions:
            if action.state_update:
                self.world.agents[action.agent_id].state = action.state_update

        # Trigger reflections if needed (ADR-006)
        for agent in self.world.agents.values():
            await agent.memory.maybe_reflect()

        # Persist checkpoint if configured (ADR-008)
        if self._should_checkpoint():
            await self.world.checkpoint_manager.save(self._step_number)

    def _get_ordered_agents(self) -> List[Agent]:
        """Get agents in execution order based on strategy."""
        agents = list(self.world.agents.values())

        if self.config.ordering_strategy == OrderingStrategy.ROUND_ROBIN:
            # Rotate starting position each step
            rotation = self._step_number % len(agents)
            return agents[rotation:] + agents[:rotation]

        elif self.config.ordering_strategy == OrderingStrategy.RANDOM:
            # Deterministic shuffle with seeded RNG
            shuffled = agents.copy()
            self._rng.shuffle(shuffled)
            return shuffled

        elif self.config.ordering_strategy == OrderingStrategy.TOPOLOGY:
            # BFS from hub/highest centrality
            return self._topology_order(agents)

        elif self.config.ordering_strategy == OrderingStrategy.PRIORITY:
            return sorted(agents, key=lambda a: a.priority, reverse=True)

        return agents  # SIMULTANEOUS uses full list

    def _batch_agents(self, agents: List[Agent]) -> Iterator[List[Agent]]:
        """Yield agent batches for controlled parallelism."""
        batch_size = self.config.max_concurrent_agents
        for i in range(0, len(agents), batch_size):
            yield agents[i:i + batch_size]
```

### Determinism Guarantees

```python
class DeterministicExecution:
    """Ensure reproducible simulations."""

    def __init__(self, seed: int):
        self.seed = seed
        self._step_seeds: Dict[int, int] = {}

    def get_step_seed(self, step: int) -> int:
        """Get deterministic seed for a specific step."""
        if step not in self._step_seeds:
            # Derive step seed from master seed
            self._step_seeds[step] = hash((self.seed, step)) & 0xFFFFFFFF
        return self._step_seeds[step]

    def create_agent_rng(self, step: int, agent_id: str) -> random.Random:
        """Create deterministic RNG for agent at step."""
        agent_seed = hash((self.get_step_seed(step), agent_id)) & 0xFFFFFFFF
        return random.Random(agent_seed)

# Usage in agent
class Agent:
    async def act(self, step_context: StepContext) -> AgentAction:
        # Use deterministic RNG for any random choices
        rng = step_context.get_agent_rng(self.id)

        # LLM calls use temperature=0 for determinism
        response = await self.llm.complete(
            messages=self._build_prompt(),
            temperature=0.0,  # Deterministic
            seed=rng.randint(0, 2**32)  # Provider-specific seeding
        )
```

**Determinism Requirements:**
1. **Same seed** → Same agent ordering
2. **Same seed** → Same random choices within agents
3. **LLM temperature=0** → More consistent (not guaranteed) outputs
4. **No external I/O** → No network time dependencies in logic

> **Note**: Full determinism is impossible with LLM calls. We guarantee *structural* determinism (ordering, routing) while acknowledging LLM output variance.

### Cancellation and Shutdown

```python
class SimulationEngine:
    def __init__(self, ...):
        self._shutdown_event = asyncio.Event()
        self._current_step_task: Optional[asyncio.Task] = None

    async def shutdown(self, graceful: bool = True) -> None:
        """Initiate simulation shutdown."""
        self._shutdown_event.set()

        if graceful and self._current_step_task:
            # Wait for current step to complete
            try:
                await asyncio.wait_for(
                    self._current_step_task,
                    timeout=self.config.step_timeout_seconds
                )
            except asyncio.TimeoutError:
                self._current_step_task.cancel()
        else:
            # Immediate cancellation
            if self._current_step_task:
                self._current_step_task.cancel()

        # Save final checkpoint
        await self.world.checkpoint_manager.save(
            self._step_number,
            reason="shutdown"
        )

    def _check_termination(self) -> bool:
        """Check if simulation should terminate."""
        if self._shutdown_event.is_set():
            return True

        # Check termination conditions
        if self.config.max_steps and self._step_number >= self.config.max_steps:
            return True

        if self.config.termination_condition:
            return self.config.termination_condition(self.world)

        return False
```

### Error Handling

```python
class SimulationEngine:
    def _handle_agent_error(
        self,
        agent: Agent,
        error: Exception
    ) -> AgentAction:
        """Handle agent execution error based on strategy."""
        self._agent_failures[agent.id] += 1

        # Log error
        logger.error(f"Agent {agent.id} failed: {error}")

        if self.config.on_agent_error == ErrorStrategy.FAIL_FAST:
            raise SimulationError(f"Agent {agent.id} failed", cause=error)

        elif self.config.on_agent_error == ErrorStrategy.SUSPEND_AGENT:
            if self._agent_failures[agent.id] >= self.config.max_consecutive_failures:
                agent.state = AgentState.SUSPENDED
                logger.warning(f"Agent {agent.id} suspended after {self._agent_failures[agent.id]} failures")

        # Return no-op action
        return AgentAction(
            agent_id=agent.id,
            action_type=ActionType.ERROR,
            error=str(error)
        )
```

### YAML Configuration

```yaml
simulation:
  name: "Product Focus Group"
  steps: 100

  runtime:
    # Parallelism
    max_concurrent_agents: 5
    max_concurrent_llm_calls: 10

    # Timing
    step_timeout_seconds: 60
    agent_timeout_seconds: 30

    # Ordering
    ordering_strategy: round_robin  # round_robin, random, priority, topology, simultaneous
    deterministic_seed: 42          # For reproducibility (optional)

    # Error handling
    on_agent_error: log_and_continue  # fail_fast, log_and_continue, retry, suspend_agent
    max_consecutive_failures: 3

    # Checkpointing
    checkpoint_every_n_steps: 10

  termination:
    max_steps: 100
    # Or custom condition via code
```

## Consequences

**Positive:**
- Clear step semantics enable reasoning about simulation behavior
- Three-phase model prevents race conditions
- Deterministic ordering enables reproducible research
- Controlled parallelism respects rate limits
- Graceful error handling improves reliability
- Configurable strategies support different use cases

**Negative:**
- Three-phase model adds latency vs fire-and-forget
- Synchronous steps limit real-time interaction patterns
- Full determinism impossible with LLM variance
- Complexity in managing agent ordering

**Tradeoffs:**
- Parallelism vs determinism (configurable)
- Throughput vs rate limit compliance
- Simplicity vs flexibility in ordering

## Related ADRs
- [ADR-002](./ADR-002-agent-scale.md): Scale constraints
- [ADR-003](./ADR-003-llm-architecture.md): Rate limiting integration
- [ADR-005](./ADR-005-network-topology.md): Message routing
- [ADR-006](./ADR-006-dual-memory.md): Memory operations
- [ADR-007](./ADR-007-visualization.md): Event emission
- [ADR-008](./ADR-008-persistence.md): Checkpointing
