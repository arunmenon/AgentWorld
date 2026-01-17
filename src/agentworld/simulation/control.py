"""Simulation control mechanisms: pause, resume, cancel, timeout.

This module provides control mechanisms for managing simulation
execution flow as specified in ADR-011.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable, TYPE_CHECKING
from datetime import UTC, datetime

if TYPE_CHECKING:
    from agentworld.simulation.ordering import OrderingStrategy


class ExecutionPhase(str, Enum):
    """Phases of agent execution within a step per ADR-011.

    The three-phase model ensures deterministic ordering:
    1. PERCEIVE: All agents observe current state
    2. ACT: All agents decide on actions
    3. COMMIT: All actions are applied atomically
    """

    PERCEIVE = "perceive"  # Agents observe state (read-only)
    ACT = "act"  # Agents decide on actions
    COMMIT = "commit"  # Apply all actions atomically


class ErrorStrategy(str, Enum):
    """How to handle agent errors during execution."""

    FAIL_FAST = "fail_fast"  # Stop simulation on any error
    LOG_AND_CONTINUE = "log_and_continue"  # Skip failed agent, continue
    RETRY = "retry"  # Retry with backoff
    SUSPEND_AGENT = "suspend_agent"  # Disable agent after N failures


class ControlSignal(str, Enum):
    """Signals for controlling simulation execution."""

    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    STEP = "step"  # Execute single step then pause


@dataclass
class StepConfig:
    """Configuration for step execution.

    Per ADR-011, controls parallelism, timing, ordering,
    and error handling for simulation steps.
    """

    # Parallelism
    max_concurrent_agents: int = 5  # Parallel agent processing
    max_concurrent_llm_calls: int = 10  # Total LLM calls in flight

    # Timing
    step_timeout_seconds: float = 60.0  # Max time per step
    agent_timeout_seconds: float = 30.0  # Max time per agent action

    # Ordering (per ADR-011)
    ordering_strategy: str = "round_robin"  # round_robin, random, priority, topology, simultaneous
    deterministic_seed: int | None = None  # For reproducibility

    # Error handling
    on_agent_error: ErrorStrategy = ErrorStrategy.LOG_AND_CONTINUE
    max_consecutive_failures: int = 3  # Per agent before suspension

    # Checkpointing
    checkpoint_every_n_steps: int = 0  # 0 = disabled
    auto_checkpoint_on_pause: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_concurrent_agents": self.max_concurrent_agents,
            "max_concurrent_llm_calls": self.max_concurrent_llm_calls,
            "step_timeout_seconds": self.step_timeout_seconds,
            "agent_timeout_seconds": self.agent_timeout_seconds,
            "ordering_strategy": self.ordering_strategy,
            "deterministic_seed": self.deterministic_seed,
            "on_agent_error": self.on_agent_error.value,
            "max_consecutive_failures": self.max_consecutive_failures,
            "checkpoint_every_n_steps": self.checkpoint_every_n_steps,
            "auto_checkpoint_on_pause": self.auto_checkpoint_on_pause,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepConfig":
        """Create from dictionary."""
        error_strategy = data.get("on_agent_error")
        if isinstance(error_strategy, str):
            error_strategy = ErrorStrategy(error_strategy)
        else:
            error_strategy = ErrorStrategy.LOG_AND_CONTINUE

        return cls(
            max_concurrent_agents=data.get("max_concurrent_agents", 5),
            max_concurrent_llm_calls=data.get("max_concurrent_llm_calls", 10),
            step_timeout_seconds=data.get("step_timeout_seconds", 60.0),
            agent_timeout_seconds=data.get("agent_timeout_seconds", 30.0),
            ordering_strategy=data.get("ordering_strategy", "round_robin"),
            deterministic_seed=data.get("deterministic_seed"),
            on_agent_error=error_strategy,
            max_consecutive_failures=data.get("max_consecutive_failures", 3),
            checkpoint_every_n_steps=data.get("checkpoint_every_n_steps", 0),
            auto_checkpoint_on_pause=data.get("auto_checkpoint_on_pause", True),
        )


class SimulationController:
    """Controller for managing simulation execution flow.

    Provides mechanisms for pausing, resuming, canceling,
    and stepping through simulations.
    """

    def __init__(self, config: StepConfig | None = None):
        """Initialize controller.

        Args:
            config: Step configuration
        """
        self.config = config or StepConfig()

        # Control state
        self._paused = asyncio.Event()
        self._paused.set()  # Start in "not paused" state
        self._shutdown = asyncio.Event()
        self._step_once = asyncio.Event()
        self._current_step_task: asyncio.Task | None = None

        # Semaphores for rate limiting
        self._agent_semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)
        self._llm_semaphore = asyncio.Semaphore(self.config.max_concurrent_llm_calls)

        # Agent failure tracking
        self._agent_failures: dict[str, int] = {}
        self._suspended_agents: set[str] = set()

        # Callbacks
        self._on_pause_callbacks: list[Callable[[], Awaitable[None] | None]] = []
        self._on_resume_callbacks: list[Callable[[], Awaitable[None] | None]] = []
        self._on_cancel_callbacks: list[Callable[[], Awaitable[None] | None]] = []

    @property
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return not self._paused.is_set()

    @property
    def is_cancelled(self) -> bool:
        """Check if simulation is cancelled."""
        return self._shutdown.is_set()

    @property
    def suspended_agents(self) -> set[str]:
        """Get set of suspended agent IDs."""
        return self._suspended_agents.copy()

    def on_pause(self, callback: Callable[[], Awaitable[None] | None]) -> None:
        """Register callback for pause events."""
        self._on_pause_callbacks.append(callback)

    def on_resume(self, callback: Callable[[], Awaitable[None] | None]) -> None:
        """Register callback for resume events."""
        self._on_resume_callbacks.append(callback)

    def on_cancel(self, callback: Callable[[], Awaitable[None] | None]) -> None:
        """Register callback for cancel events."""
        self._on_cancel_callbacks.append(callback)

    async def _emit_callbacks(
        self, callbacks: list[Callable[[], Awaitable[None] | None]]
    ) -> None:
        """Emit callbacks."""
        for callback in callbacks:
            result = callback()
            if asyncio.iscoroutine(result):
                await result

    def pause(self) -> None:
        """Pause simulation execution.

        Current step will complete before pausing.
        """
        self._paused.clear()

    async def pause_async(self) -> None:
        """Pause simulation and wait for callbacks."""
        self.pause()
        await self._emit_callbacks(self._on_pause_callbacks)

    def resume(self) -> None:
        """Resume simulation execution."""
        self._paused.set()

    async def resume_async(self) -> None:
        """Resume simulation and trigger callbacks."""
        await self._emit_callbacks(self._on_resume_callbacks)
        self.resume()

    def cancel(self) -> None:
        """Cancel simulation execution.

        This signals the simulation to stop after current step.
        """
        self._shutdown.set()
        # Also resume if paused to allow shutdown
        self._paused.set()

    async def cancel_async(self) -> None:
        """Cancel simulation and trigger callbacks."""
        self.cancel()
        await self._emit_callbacks(self._on_cancel_callbacks)

    def step_once(self) -> None:
        """Execute single step then pause.

        Use this for step-by-step debugging.
        """
        self._step_once.set()
        self._paused.set()  # Temporarily resume for one step

    async def wait_if_paused(self) -> bool:
        """Wait if simulation is paused.

        Returns:
            True if should continue, False if cancelled
        """
        if self._shutdown.is_set():
            return False

        # Wait for resume or cancellation
        while not self._paused.is_set():
            if self._shutdown.is_set():
                return False
            try:
                await asyncio.wait_for(self._paused.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

        return not self._shutdown.is_set()

    async def check_step_once(self) -> None:
        """Check if we should pause after step (for step_once mode)."""
        if self._step_once.is_set():
            self._step_once.clear()
            self.pause()

    def should_terminate(self) -> bool:
        """Check if simulation should terminate."""
        return self._shutdown.is_set()

    def record_agent_success(self, agent_id: str) -> None:
        """Record successful agent action, resetting failure count."""
        self._agent_failures[agent_id] = 0

    def record_agent_failure(self, agent_id: str) -> bool:
        """Record agent failure and check if should suspend.

        Args:
            agent_id: Agent ID

        Returns:
            True if agent was suspended
        """
        self._agent_failures[agent_id] = self._agent_failures.get(agent_id, 0) + 1

        if (
            self.config.on_agent_error == ErrorStrategy.SUSPEND_AGENT
            and self._agent_failures[agent_id] >= self.config.max_consecutive_failures
        ):
            self._suspended_agents.add(agent_id)
            return True

        return False

    def is_agent_suspended(self, agent_id: str) -> bool:
        """Check if agent is suspended."""
        return agent_id in self._suspended_agents

    def unsuspend_agent(self, agent_id: str) -> None:
        """Unsuspend an agent."""
        self._suspended_agents.discard(agent_id)
        self._agent_failures[agent_id] = 0

    def unsuspend_all(self) -> None:
        """Unsuspend all agents."""
        self._suspended_agents.clear()
        self._agent_failures.clear()

    def get_failure_count(self, agent_id: str) -> int:
        """Get failure count for an agent."""
        return self._agent_failures.get(agent_id, 0)

    def agent_semaphore(self) -> asyncio.Semaphore:
        """Get semaphore for agent concurrency control."""
        return self._agent_semaphore

    def llm_semaphore(self) -> asyncio.Semaphore:
        """Get semaphore for LLM call rate limiting."""
        return self._llm_semaphore

    def reset(self) -> None:
        """Reset controller state for reuse."""
        self._paused.set()
        self._shutdown.clear()
        self._step_once.clear()
        self._agent_failures.clear()
        self._suspended_agents.clear()
        self._agent_semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)
        self._llm_semaphore = asyncio.Semaphore(self.config.max_concurrent_llm_calls)


@dataclass
class TimeoutResult:
    """Result of a timed operation."""

    completed: bool
    timed_out: bool
    duration_seconds: float
    error: str | None = None


async def with_timeout(
    coro: Awaitable[Any],
    timeout_seconds: float,
) -> tuple[Any, TimeoutResult]:
    """Execute coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds

    Returns:
        Tuple of (result or None, TimeoutResult)
    """
    start = datetime.now(UTC)
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        duration = (datetime.now(UTC) - start).total_seconds()
        return result, TimeoutResult(
            completed=True,
            timed_out=False,
            duration_seconds=duration,
        )
    except asyncio.TimeoutError:
        duration = (datetime.now(UTC) - start).total_seconds()
        return None, TimeoutResult(
            completed=False,
            timed_out=True,
            duration_seconds=duration,
        )
    except Exception as e:
        duration = (datetime.now(UTC) - start).total_seconds()
        return None, TimeoutResult(
            completed=False,
            timed_out=False,
            duration_seconds=duration,
            error=str(e),
        )


async def retry_with_backoff(
    coro_factory: Callable[[], Awaitable[Any]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> tuple[Any, int]:
    """Retry coroutine with exponential backoff.

    Args:
        coro_factory: Factory function that creates the coroutine
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Tuple of (result, retry_count)
    """
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            result = await coro_factory()
            return result, attempt
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = min(base_delay * (2**attempt), max_delay)
                await asyncio.sleep(delay)

    raise last_error  # type: ignore


@dataclass
class PhaseResult:
    """Result of a single execution phase."""

    phase: ExecutionPhase
    agent_id: str
    success: bool
    data: Any = None
    error: str | None = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase.value,
            "agent_id": self.agent_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class StepPhaseResults:
    """Results from all three phases of a step."""

    step_number: int
    perceive_results: list[PhaseResult] = field(default_factory=list)
    act_results: list[PhaseResult] = field(default_factory=list)
    commit_results: list[PhaseResult] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        """Check if all phases succeeded."""
        all_results = self.perceive_results + self.act_results + self.commit_results
        return all(r.success for r in all_results)

    @property
    def failed_agents(self) -> list[str]:
        """Get list of agents that had failures."""
        failed = set()
        for result in self.perceive_results + self.act_results + self.commit_results:
            if not result.success:
                failed.add(result.agent_id)
        return list(failed)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "perceive_results": [r.to_dict() for r in self.perceive_results],
            "act_results": [r.to_dict() for r in self.act_results],
            "commit_results": [r.to_dict() for r in self.commit_results],
            "all_succeeded": self.all_succeeded,
            "failed_agents": self.failed_agents,
        }


class ThreePhaseExecutor:
    """Executor for three-phase step execution per ADR-011.

    Ensures deterministic ordering by separating perception,
    action decision, and action application into distinct phases.
    """

    def __init__(self, controller: SimulationController | None = None):
        """Initialize executor.

        Args:
            controller: Optional simulation controller for concurrency
        """
        self.controller = controller

    async def execute_perceive(
        self,
        agent_id: str,
        perceive_fn: Callable[[], Awaitable[Any]],
        timeout: float = 30.0,
    ) -> PhaseResult:
        """Execute perceive phase for an agent.

        Args:
            agent_id: Agent ID
            perceive_fn: Function to execute for perception
            timeout: Timeout in seconds

        Returns:
            PhaseResult with perception data
        """
        start = datetime.now(UTC)
        try:
            data, timeout_result = await with_timeout(perceive_fn(), timeout)
            duration = (datetime.now(UTC) - start).total_seconds()

            if timeout_result.timed_out:
                return PhaseResult(
                    phase=ExecutionPhase.PERCEIVE,
                    agent_id=agent_id,
                    success=False,
                    error="Perception timed out",
                    duration_seconds=duration,
                )

            return PhaseResult(
                phase=ExecutionPhase.PERCEIVE,
                agent_id=agent_id,
                success=True,
                data=data,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds()
            return PhaseResult(
                phase=ExecutionPhase.PERCEIVE,
                agent_id=agent_id,
                success=False,
                error=str(e),
                duration_seconds=duration,
            )

    async def execute_act(
        self,
        agent_id: str,
        act_fn: Callable[[Any], Awaitable[Any]],
        perception_data: Any,
        timeout: float = 30.0,
    ) -> PhaseResult:
        """Execute act phase for an agent.

        Args:
            agent_id: Agent ID
            act_fn: Function to execute for action decision
            perception_data: Data from perceive phase
            timeout: Timeout in seconds

        Returns:
            PhaseResult with action decision
        """
        start = datetime.now(UTC)
        try:
            data, timeout_result = await with_timeout(act_fn(perception_data), timeout)
            duration = (datetime.now(UTC) - start).total_seconds()

            if timeout_result.timed_out:
                return PhaseResult(
                    phase=ExecutionPhase.ACT,
                    agent_id=agent_id,
                    success=False,
                    error="Action decision timed out",
                    duration_seconds=duration,
                )

            return PhaseResult(
                phase=ExecutionPhase.ACT,
                agent_id=agent_id,
                success=True,
                data=data,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds()
            return PhaseResult(
                phase=ExecutionPhase.ACT,
                agent_id=agent_id,
                success=False,
                error=str(e),
                duration_seconds=duration,
            )

    async def execute_commit(
        self,
        agent_id: str,
        commit_fn: Callable[[Any], Awaitable[Any]],
        action_data: Any,
        timeout: float = 10.0,
    ) -> PhaseResult:
        """Execute commit phase for an agent.

        Args:
            agent_id: Agent ID
            commit_fn: Function to apply the action
            action_data: Action decision from act phase
            timeout: Timeout in seconds

        Returns:
            PhaseResult with commit result
        """
        start = datetime.now(UTC)
        try:
            data, timeout_result = await with_timeout(commit_fn(action_data), timeout)
            duration = (datetime.now(UTC) - start).total_seconds()

            if timeout_result.timed_out:
                return PhaseResult(
                    phase=ExecutionPhase.COMMIT,
                    agent_id=agent_id,
                    success=False,
                    error="Commit timed out",
                    duration_seconds=duration,
                )

            return PhaseResult(
                phase=ExecutionPhase.COMMIT,
                agent_id=agent_id,
                success=True,
                data=data,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds()
            return PhaseResult(
                phase=ExecutionPhase.COMMIT,
                agent_id=agent_id,
                success=False,
                error=str(e),
                duration_seconds=duration,
            )
