"""Gymnasium-style environment semantics for AgentWorld apps.

This module provides environment abstractions that enable:
1. Episode abstraction (episode_id, step_count per episode)
2. reset() method - returns app to initial state, returns observation
3. step(action) semantics - execute + return (result, reward, done, truncated, info)
4. close() method - explicit cleanup
5. Uniform interface for both native and OpenEnv apps

Example:
    >>> from agentworld.apps import get_app_registry, AppEnvironmentWrapper
    >>>
    >>> registry = get_app_registry()
    >>> app = registry.get("paypal")
    >>> env = AppEnvironmentWrapper(app, max_steps=100)
    >>>
    >>> # Reset starts a new episode
    >>> result = await env.reset(options={"agents": ["alice", "bob"]})
    >>> print(f"Episode started: {result.info['episode_id']}")
    >>>
    >>> # Step through the episode
    >>> step = await env.step("alice", "get_balance", {})
    >>> print(f"Reward: {step.reward}, Done: {step.terminated}")
    >>>
    >>> # Get episode history for replay/analysis
    >>> history = env.get_episode_history()
    >>> trajectory = history.get_trajectory()  # For RL training
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Callable, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from agentworld.apps.base import SimulatedAppPlugin

logger = logging.getLogger(__name__)


# ==============================================================================
# Data Structures
# ==============================================================================


@dataclass
class StepResult:
    """Gymnasium-style step result.

    Matches the standard Gymnasium API for compatibility with RL frameworks.

    Attributes:
        observation: Current state visible to the agent
        reward: Scalar reward for this step
        terminated: True if episode ended due to reaching goal
        truncated: True if episode ended due to max steps
        info: Additional metadata (episode_id, action_result, etc.)
    """

    observation: dict[str, Any]
    reward: float
    terminated: bool
    truncated: bool
    info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observation": self.observation,
            "reward": self.reward,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "info": self.info,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepResult":
        """Create from dictionary."""
        return cls(
            observation=data.get("observation", {}),
            reward=data.get("reward", 0.0),
            terminated=data.get("terminated", False),
            truncated=data.get("truncated", False),
            info=data.get("info", {}),
        )


@dataclass
class ResetResult:
    """Result from reset() operation.

    Attributes:
        observation: Initial state observation
        info: Episode metadata (episode_id, initial_state_hash, etc.)
    """

    observation: dict[str, Any]
    info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observation": self.observation,
            "info": self.info,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResetResult":
        """Create from dictionary."""
        return cls(
            observation=data.get("observation", {}),
            info=data.get("info", {}),
        )


@dataclass
class StateSnapshot:
    """Snapshot of state at a point in time.

    Used for episode history tracking to enable replay and analysis.

    Attributes:
        step: Step number within the episode
        timestamp: When this snapshot was taken
        state: Full state at this step
        action: Action taken (None for initial state)
        params: Action parameters
        reward: Reward received for this step
    """

    step: int
    timestamp: datetime
    state: dict[str, Any]
    action: str | None = None
    params: dict[str, Any] | None = None
    reward: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state,
            "action": self.action,
            "params": self.params,
            "reward": self.reward,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateSnapshot":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = datetime.now(UTC)

        return cls(
            step=data.get("step", 0),
            timestamp=timestamp,
            state=data.get("state", {}),
            action=data.get("action"),
            params=data.get("params"),
            reward=data.get("reward", 0.0),
        )


@dataclass
class EpisodeHistory:
    """Complete history of an episode for replay/analysis.

    Tracks all state transitions during an episode to support:
    - Replaying episodes for debugging
    - Extracting trajectories for RL training
    - Analyzing agent behavior patterns

    Attributes:
        episode_id: Unique episode identifier
        started_at: When the episode started
        ended_at: When the episode ended (None if still running)
        snapshots: List of state snapshots in order
        terminated: Whether episode ended due to goal completion
        truncated: Whether episode ended due to max steps
        total_reward: Cumulative reward across all steps
    """

    episode_id: str
    started_at: datetime
    ended_at: datetime | None = None
    snapshots: list[StateSnapshot] = field(default_factory=list)
    terminated: bool = False
    truncated: bool = False
    total_reward: float = 0.0

    def get_state_at_step(self, step: int) -> dict[str, Any]:
        """Retrieve state at any step.

        Args:
            step: Step number (0-indexed, 0 is initial state)

        Returns:
            State dictionary at that step

        Raises:
            IndexError: If step is out of range
        """
        if step < 0 or step >= len(self.snapshots):
            raise IndexError(f"Step {step} out of range (0-{len(self.snapshots) - 1})")
        return self.snapshots[step].state

    def get_trajectory(self) -> list[tuple[dict[str, Any], str | None, float]]:
        """Return (state, action, reward) tuples for RL training.

        Returns:
            List of (state, action, reward) tuples. The action for the
            initial state is None.
        """
        return [(s.state, s.action, s.reward) for s in self.snapshots]

    def get_actions(self) -> list[str]:
        """Get list of all actions taken (excluding initial state)."""
        return [s.action for s in self.snapshots if s.action is not None]

    def get_rewards(self) -> list[float]:
        """Get list of all rewards received."""
        return [s.reward for s in self.snapshots]

    def get_cumulative_rewards(self) -> list[float]:
        """Get cumulative reward at each step."""
        cumulative = []
        total = 0.0
        for s in self.snapshots:
            total += s.reward
            cumulative.append(total)
        return cumulative

    @property
    def step_count(self) -> int:
        """Number of actions taken (excludes initial state)."""
        return max(0, len(self.snapshots) - 1)

    @property
    def duration_seconds(self) -> float | None:
        """Episode duration in seconds, or None if still running."""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "episode_id": self.episode_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "terminated": self.terminated,
            "truncated": self.truncated,
            "total_reward": self.total_reward,
            "step_count": self.step_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeHistory":
        """Create from dictionary."""
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        else:
            started_at = datetime.now(UTC)

        ended_at = data.get("ended_at")
        if isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at)

        return cls(
            episode_id=data.get("episode_id", ""),
            started_at=started_at,
            ended_at=ended_at,
            snapshots=[StateSnapshot.from_dict(s) for s in data.get("snapshots", [])],
            terminated=data.get("terminated", False),
            truncated=data.get("truncated", False),
            total_reward=data.get("total_reward", 0.0),
        )


# ==============================================================================
# Environment Protocol
# ==============================================================================


@runtime_checkable
class EnvironmentProtocol(Protocol):
    """Gymnasium-style environment interface.

    This protocol defines the standard interface for all environment-wrapped
    apps, whether native AgentWorld apps or OpenEnv environments.
    """

    @property
    def episode_id(self) -> str | None:
        """Current episode ID, or None if no episode is active."""
        ...

    @property
    def step_count(self) -> int:
        """Number of steps taken in the current episode."""
        ...

    async def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> ResetResult:
        """Reset environment to initial state, start new episode.

        Args:
            seed: Optional random seed for reproducibility
            options: Configuration options including:
                - agents: List of agent IDs
                - config: App-specific configuration

        Returns:
            ResetResult with initial observation and episode info
        """
        ...

    async def step(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> StepResult:
        """Execute an action in the environment.

        Args:
            agent_id: ID of the agent performing the action
            action: Action name
            params: Action parameters

        Returns:
            StepResult with observation, reward, terminated, truncated, info
        """
        ...

    def close(self) -> None:
        """Close the environment and clean up resources."""
        ...


# ==============================================================================
# Reward Functions
# ==============================================================================


def default_reward(
    result: Any,
    observation: dict[str, Any],
    terminated: bool,
    step_count: int,
) -> float:
    """Default reward function with small per-step penalty.

    Encourages efficient task completion by penalizing each step.

    Args:
        result: AppResult from action execution
        observation: Current state observation
        terminated: Whether episode ended due to goal
        step_count: Current step count

    Returns:
        Reward value (default: -0.01 per step, +1.0 on success)
    """
    # Small per-step penalty to encourage efficiency
    reward = -0.01

    # Success bonus
    if terminated:
        reward += 1.0

    # Failure penalty (if result indicates failure)
    if hasattr(result, "success") and not result.success:
        reward -= 0.1

    return reward


def sparse_reward(
    result: Any,
    observation: dict[str, Any],
    terminated: bool,
    step_count: int,
) -> float:
    """Sparse reward function - only rewards on episode completion.

    Args:
        result: AppResult from action execution
        observation: Current state observation
        terminated: Whether episode ended due to goal
        step_count: Current step count

    Returns:
        1.0 on success, 0.0 otherwise
    """
    return 1.0 if terminated else 0.0


def action_cost_reward(
    result: Any,
    observation: dict[str, Any],
    terminated: bool,
    step_count: int,
) -> float:
    """Reward function with action-specific costs.

    More expensive actions (like transfers) have higher costs.

    Args:
        result: AppResult from action execution
        observation: Current state observation
        terminated: Whether episode ended due to goal
        step_count: Current step count

    Returns:
        Reward based on action cost and success
    """
    # Base step cost
    reward = -0.01

    # Success bonus
    if terminated:
        reward += 1.0

    # Check for action-specific costs in result info
    if hasattr(result, "data") and result.data:
        action_cost = result.data.get("action_cost", 0.0)
        reward -= action_cost

    return reward


# ==============================================================================
# App Environment Wrapper
# ==============================================================================


class AppEnvironmentWrapper:
    """Wraps any SimulatedAppPlugin with environment semantics.

    Provides Gymnasium-style interface for native AgentWorld apps,
    enabling RL training and standardized evaluation.

    Example:
        >>> from agentworld.apps import get_app_registry
        >>> from agentworld.apps.environment import AppEnvironmentWrapper
        >>>
        >>> registry = get_app_registry()
        >>> app = registry.get("paypal")
        >>> env = AppEnvironmentWrapper(app, max_steps=100)
        >>>
        >>> # Run an episode
        >>> result = await env.reset(options={"agents": ["alice", "bob"]})
        >>> done = False
        >>> while not done:
        ...     step = await env.step("alice", "get_balance", {})
        ...     done = step.terminated or step.truncated
        ...
        >>> # Get episode history for analysis
        >>> history = env.get_episode_history()
        >>> print(f"Total reward: {history.total_reward}")
    """

    def __init__(
        self,
        app: "SimulatedAppPlugin",
        max_steps: int = 100,
        reward_function: Callable[[Any, dict, bool, int], float] | None = None,
        track_history: bool = True,
        termination_checker: Callable[[dict[str, Any]], bool] | None = None,
        repository: Any | None = None,
        simulation_id: str | None = None,
    ):
        """Initialize the environment wrapper.

        Args:
            app: SimulatedAppPlugin instance to wrap
            max_steps: Maximum steps before truncation
            reward_function: Custom reward function (default: default_reward)
            track_history: Whether to track full state history
            termination_checker: Optional function to check if goal is achieved
            repository: Optional Repository instance for episode persistence
            simulation_id: Simulation ID (required if repository is provided)
        """
        self._app = app
        self._max_steps = max_steps
        self._reward_fn = reward_function or default_reward
        self._track_history = track_history
        self._termination_checker = termination_checker
        self._repository = repository
        self._simulation_id = simulation_id

        # Episode state
        self._episode_id: str | None = None
        self._step_count: int = 0
        self._terminated: bool = False
        self._truncated: bool = False
        self._cumulative_reward: float = 0.0

        # State history tracking (in-memory, synced to DB if repository provided)
        self._current_episode: EpisodeHistory | None = None
        self._episode_history: list[EpisodeHistory] = []

    # ==========================================================================
    # Properties
    # ==========================================================================

    @property
    def app(self) -> "SimulatedAppPlugin":
        """Get the underlying app instance."""
        return self._app

    @property
    def episode_id(self) -> str | None:
        """Current episode ID, or None if no episode is active."""
        return self._episode_id

    @property
    def step_count(self) -> int:
        """Number of steps taken in the current episode."""
        return self._step_count

    @property
    def max_steps(self) -> int:
        """Maximum steps before truncation."""
        return self._max_steps

    @property
    def terminated(self) -> bool:
        """Whether the current episode has terminated (goal achieved)."""
        return self._terminated

    @property
    def truncated(self) -> bool:
        """Whether the current episode was truncated (max steps)."""
        return self._truncated

    @property
    def cumulative_reward(self) -> float:
        """Cumulative reward for the current episode."""
        return self._cumulative_reward

    @property
    def is_active(self) -> bool:
        """Whether an episode is currently active."""
        return self._episode_id is not None and not self._terminated and not self._truncated

    # ==========================================================================
    # Core Methods
    # ==========================================================================

    async def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> ResetResult:
        """Reset to initial state, start new episode.

        Args:
            seed: Optional random seed (not currently used)
            options: Configuration options:
                - agents: List of agent IDs (required)
                - config: App-specific configuration

        Returns:
            ResetResult with initial observation and episode info
        """
        # Save current episode to history before reset
        if self._current_episode and self._track_history:
            self._current_episode.ended_at = datetime.now(UTC)
            self._episode_history.append(self._current_episode)
            # Persist to database if repository available
            self._persist_episode_end(self._current_episode)

        # Generate new episode ID
        self._episode_id = str(uuid.uuid4())[:8]
        self._step_count = 0
        self._terminated = False
        self._truncated = False
        self._cumulative_reward = 0.0

        # Initialize the app
        options = options or {}
        agents = options.get("agents", ["default"])
        config = options.get("config", {})

        await self._app.initialize(
            sim_id=f"ep_{self._episode_id}",
            agents=agents,
            config=config,
        )

        # Build initial observation
        observation = await self._build_observation(agents[0] if agents else "default")

        # Start new episode history
        if self._track_history:
            self._current_episode = EpisodeHistory(
                episode_id=self._episode_id,
                started_at=datetime.now(UTC),
                ended_at=None,
                snapshots=[
                    StateSnapshot(
                        step=0,
                        timestamp=datetime.now(UTC),
                        state=observation,
                        action=None,
                        params=None,
                        reward=0.0,
                    )
                ],
                terminated=False,
                truncated=False,
                total_reward=0.0,
            )

        # Persist new episode to database
        self._persist_episode_start()

        logger.info(f"Started episode {self._episode_id} for app {self._app.app_id}")

        return ResetResult(
            observation=observation,
            info={
                "episode_id": self._episode_id,
                "agents": agents,
            },
        )

    async def step(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> StepResult:
        """Execute action, return Gymnasium-style result.

        Args:
            agent_id: ID of the agent performing the action
            action: Action name
            params: Action parameters

        Returns:
            StepResult with observation, reward, terminated, truncated, info

        Raises:
            RuntimeError: If no episode is active
        """
        if self._episode_id is None:
            raise RuntimeError("No episode active. Call reset() first.")

        if self._terminated or self._truncated:
            raise RuntimeError("Episode has ended. Call reset() to start a new one.")

        self._step_count += 1

        # Execute the action
        result = await self._app.execute(agent_id, action, params)

        # Build observation
        observation = await self._build_observation(agent_id)

        # Check termination conditions
        if self._termination_checker:
            self._terminated = self._termination_checker(observation)
        else:
            # Default: no automatic termination (must be set externally)
            pass

        # Check truncation
        self._truncated = self._step_count >= self._max_steps

        # Calculate reward
        reward = self._reward_fn(result, observation, self._terminated, self._step_count)
        self._cumulative_reward += reward

        # Record snapshot in history
        if self._track_history and self._current_episode:
            self._current_episode.snapshots.append(
                StateSnapshot(
                    step=self._step_count,
                    timestamp=datetime.now(UTC),
                    state=observation,
                    action=action,
                    params=params,
                    reward=reward,
                )
            )
            self._current_episode.total_reward = self._cumulative_reward
            self._current_episode.terminated = self._terminated
            self._current_episode.truncated = self._truncated

        # Persist to database after each step
        self._persist_episode_update()

        logger.debug(
            f"Episode {self._episode_id} step {self._step_count}: "
            f"{action} -> reward={reward:.3f}, term={self._terminated}, trunc={self._truncated}"
        )

        return StepResult(
            observation=observation,
            reward=reward,
            terminated=self._terminated,
            truncated=self._truncated,
            info={
                "action_result": result.to_dict(),
                "episode_id": self._episode_id,
                "step": self._step_count,
                "cumulative_reward": self._cumulative_reward,
            },
        )

    def close(self) -> None:
        """Clean up and finalize history."""
        if self._current_episode and self._track_history:
            self._current_episode.ended_at = datetime.now(UTC)
            self._episode_history.append(self._current_episode)
            # Persist to database
            self._persist_episode_end(self._current_episode)
            logger.info(
                f"Closed episode {self._episode_id}: "
                f"{self._step_count} steps, reward={self._cumulative_reward:.3f}"
            )

        self._episode_id = None
        self._step_count = 0
        self._terminated = False
        self._truncated = False
        self._cumulative_reward = 0.0
        self._current_episode = None

    def mark_terminated(self, terminated: bool = True) -> None:
        """Manually mark the episode as terminated (goal achieved).

        Use this when external logic determines the goal is achieved.

        Args:
            terminated: Whether to mark as terminated
        """
        self._terminated = terminated
        if self._current_episode:
            self._current_episode.terminated = terminated

    # ==========================================================================
    # History Methods
    # ==========================================================================

    def get_episode_history(self, episode_id: str | None = None) -> EpisodeHistory | None:
        """Get history for specific or current episode.

        Args:
            episode_id: Episode ID to retrieve, or None for current

        Returns:
            EpisodeHistory or None if not found
        """
        if episode_id is None:
            return self._current_episode

        for ep in self._episode_history:
            if ep.episode_id == episode_id:
                return ep

        return None

    def get_all_episodes(self) -> list[EpisodeHistory]:
        """Get history of all completed episodes.

        Returns:
            List of EpisodeHistory for completed episodes
        """
        return self._episode_history.copy()

    def get_episode_count(self) -> int:
        """Get total number of completed episodes."""
        return len(self._episode_history)

    def get_trajectory(self, episode_id: str | None = None) -> list[tuple[dict, str | None, float]]:
        """Get trajectory for an episode as (state, action, reward) tuples.

        Args:
            episode_id: Episode ID, or None for current

        Returns:
            List of (state, action, reward) tuples
        """
        history = self.get_episode_history(episode_id)
        if history is None:
            return []
        return history.get_trajectory()

    def clear_history(self) -> None:
        """Clear all episode history (keeps current episode if active)."""
        self._episode_history = []

    # ==========================================================================
    # Internal Methods
    # ==========================================================================

    async def _build_observation(self, agent_id: str) -> dict[str, Any]:
        """Build observation dictionary from app state.

        Args:
            agent_id: Agent ID to get state for

        Returns:
            Observation dictionary
        """
        try:
            agent_state = await self._app.get_agent_state(agent_id)
            return {
                "agent_state": agent_state,
                "app_id": self._app.app_id,
                "step": self._step_count,
            }
        except Exception as e:
            logger.warning(f"Error building observation: {e}")
            return {
                "error": str(e),
                "app_id": self._app.app_id,
                "step": self._step_count,
            }

    # ==========================================================================
    # Persistence Methods
    # ==========================================================================

    def _persist_episode_start(self) -> None:
        """Persist new episode to database."""
        if self._repository is None or self._simulation_id is None:
            return
        if self._episode_id is None:
            return

        try:
            import json
            self._repository.create_episode({
                "id": self._episode_id,
                "simulation_id": self._simulation_id,
                "app_id": self._app.app_id,
                "started_at": datetime.now(UTC),
                "action_count": 0,
                "turn_count": 0,
                "total_reward": 0.0,
                "terminated": False,
                "truncated": False,
                "snapshots_json": json.dumps([
                    self._current_episode.snapshots[0].to_dict()
                ]) if self._current_episode else None,
            })
            logger.debug(f"Persisted episode start: {self._episode_id}")
        except Exception as e:
            logger.warning(f"Failed to persist episode start: {e}")

    def _persist_episode_end(self, episode: EpisodeHistory) -> None:
        """Persist episode end state to database."""
        if self._repository is None or self._simulation_id is None:
            return

        try:
            import json
            self._repository.update_episode(episode.episode_id, {
                "ended_at": episode.ended_at,
                "action_count": episode.step_count,
                "turn_count": episode.step_count,  # For app episodes, turn_count = step_count
                "total_reward": episode.total_reward,
                "terminated": episode.terminated,
                "truncated": episode.truncated,
                "snapshots_json": json.dumps([s.to_dict() for s in episode.snapshots]),
            })
            logger.debug(f"Persisted episode end: {episode.episode_id}")
        except Exception as e:
            logger.warning(f"Failed to persist episode end: {e}")

    def _persist_episode_update(self) -> None:
        """Persist current episode state to database (after each step)."""
        if self._repository is None or self._simulation_id is None:
            return
        if self._episode_id is None or self._current_episode is None:
            return

        try:
            import json
            self._repository.update_episode(self._episode_id, {
                "action_count": self._step_count,
                "turn_count": self._step_count,
                "total_reward": self._cumulative_reward,
                "terminated": self._terminated,
                "truncated": self._truncated,
                "snapshots_json": json.dumps([s.to_dict() for s in self._current_episode.snapshots]),
            })
        except Exception as e:
            logger.warning(f"Failed to persist episode update: {e}")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AppEnvironmentWrapper("
            f"app={self._app.app_id}, "
            f"episode={self._episode_id}, "
            f"step={self._step_count}/{self._max_steps})"
        )
