"""Base classes and protocols for simulated applications.

This module defines the SimulatedAppPlugin protocol and supporting
data structures per ADR-017.
"""

from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ==============================================================================
# Data Structures
# ==============================================================================


@dataclass
class ParamSpec:
    """Specification for an action parameter."""

    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str = ""
    required: bool = True
    default: Any = None
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None  # Regex pattern for strings
    enum: list[Any] | None = None  # Allowed values

    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate a value against this parameter spec.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if self.required and self.default is None:
                return False, f"Parameter '{self.name}' is required"
            return True, ""

        # Type validation
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected_type = type_map.get(self.type)
        if expected_type and not isinstance(value, expected_type):
            return False, f"Parameter '{self.name}' must be {self.type}, got {type(value).__name__}"

        # Numeric range validation
        if self.min_value is not None and isinstance(value, (int, float)):
            if value < self.min_value:
                return False, f"Parameter '{self.name}' must be >= {self.min_value}"

        if self.max_value is not None and isinstance(value, (int, float)):
            if value > self.max_value:
                return False, f"Parameter '{self.name}' must be <= {self.max_value}"

        # String length validation
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                return False, f"Parameter '{self.name}' must be at least {self.min_length} characters"
            if self.max_length is not None and len(value) > self.max_length:
                return False, f"Parameter '{self.name}' must be at most {self.max_length} characters"

        # Enum validation
        if self.enum is not None and value not in self.enum:
            return False, f"Parameter '{self.name}' must be one of {self.enum}"

        return True, ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.pattern is not None:
            result["pattern"] = self.pattern
        if self.enum is not None:
            result["enum"] = self.enum
        return result


@dataclass
class AppAction:
    """Definition of an app action."""

    name: str
    description: str
    parameters: dict[str, ParamSpec] = field(default_factory=dict)
    returns: dict[str, Any] = field(default_factory=dict)

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, str]:
        """Validate parameters against this action's spec.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for unknown parameters
        known_params = set(self.parameters.keys())
        provided_params = set(params.keys())
        unknown = provided_params - known_params
        if unknown:
            return False, f"Unknown parameters: {', '.join(unknown)}"

        # Validate each parameter
        for param_name, param_spec in self.parameters.items():
            value = params.get(param_name, param_spec.default)
            is_valid, error = param_spec.validate(value)
            if not is_valid:
                return False, error

        return True, ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {k: v.to_dict() for k, v in self.parameters.items()},
            "returns": self.returns,
        }


@dataclass
class AppResult:
    """Result of executing an action."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }

    @classmethod
    def ok(cls, data: dict[str, Any] | None = None) -> "AppResult":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "AppResult":
        """Create a failed result."""
        return cls(success=False, error=error)


@dataclass
class AppObservation:
    """Observation injected into agent's perception."""

    app_id: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more important
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "message": self.message,
            "data": self.data,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppObservation":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = datetime.now(UTC)

        return cls(
            app_id=data["app_id"],
            message=data["message"],
            data=data.get("data", {}),
            priority=data.get("priority", 0),
            timestamp=timestamp,
        )


@dataclass
class AppActionLogEntry:
    """Entry in the action audit log."""

    id: str
    app_instance_id: str
    agent_id: str
    step: int
    action_name: str
    params: dict[str, Any]
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "app_instance_id": self.app_instance_id,
            "agent_id": self.agent_id,
            "step": self.step,
            "action_name": self.action_name,
            "params": self.params,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "executed_at": self.executed_at.isoformat(),
        }


# ==============================================================================
# Event Types
# ==============================================================================


class AppEventType(str, Enum):
    """Event types for app-related WebSocket events."""

    APP_INITIALIZED = "app.initialized"
    APP_ACTION_REQUESTED = "app.action.requested"
    APP_ACTION_EXECUTED = "app.action.executed"
    APP_ACTION_FAILED = "app.action.failed"
    APP_OBSERVATION_SENT = "app.observation.sent"


# ==============================================================================
# Protocol Definition
# ==============================================================================


@runtime_checkable
class SimulatedAppPlugin(Protocol):
    """Protocol for simulated applications.

    Implement this protocol to create a new simulated app that agents
    can interact with during simulations.
    """

    @property
    def app_id(self) -> str:
        """Unique ID for this app (e.g., 'paypal', 'amazon')."""
        ...

    @property
    def name(self) -> str:
        """Display name for this app (e.g., 'PayPal')."""
        ...

    @property
    def description(self) -> str:
        """Description for agent context."""
        ...

    def get_actions(self) -> list[AppAction]:
        """Get available actions with their schemas."""
        ...

    async def initialize(
        self,
        sim_id: str,
        agents: list[str],
        config: dict[str, Any],
        agent_names: dict[str, str] | None = None,
    ) -> None:
        """Initialize app state for a simulation.

        Args:
            sim_id: Simulation ID
            agents: List of agent IDs participating
            config: App configuration from simulation config
            agent_names: Optional mapping of agent_id -> agent_name for name resolution
        """
        ...

    async def execute(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute an action.

        Args:
            agent_id: ID of the agent performing the action
            action: Action name
            params: Action parameters

        Returns:
            AppResult with success/failure and data
        """
        ...

    async def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Get the agent's view of app state.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with agent-specific state
        """
        ...

    async def get_observations(self, agent_id: str) -> list[AppObservation]:
        """Get pending observations for an agent.

        Called during PERCEIVE phase to get notifications.

        Args:
            agent_id: Agent ID

        Returns:
            List of observations (will be cleared after retrieval)
        """
        ...

    def get_state_snapshot(self) -> bytes:
        """Serialize full app state for checkpoint.

        Returns:
            Serialized state bytes
        """
        ...

    def restore_state(self, snapshot: bytes) -> None:
        """Restore app state from checkpoint.

        Args:
            snapshot: Serialized state bytes from get_state_snapshot
        """
        ...


# ==============================================================================
# Base Implementation
# ==============================================================================


class BaseSimulatedApp(ABC):
    """Base class for simulated apps with common functionality.

    Provides default implementations for common operations while
    requiring subclasses to implement the core business logic.

    Supports optional episode tracking for Gymnasium-style environment semantics.
    See agentworld.apps.environment.AppEnvironmentWrapper for full environment support.
    """

    def __init__(self):
        """Initialize base app."""
        self._sim_id: str | None = None
        self._agents: list[str] = []
        self._config: dict[str, Any] = {}
        self._observations: dict[str, list[AppObservation]] = {}  # agent_id -> observations
        self._action_log: list[AppActionLogEntry] = []
        self._agent_names: dict[str, str] = {}
        self._current_step: int = 0

        # Episode tracking (optional, for environment semantics)
        self._episode_id: str | None = None
        self._episode_step_count: int = 0
        self._episode_active: bool = False

    # ==========================================================================
    # Episode Tracking Properties (for environment semantics)
    # ==========================================================================

    @property
    def episode_id(self) -> str | None:
        """Current episode ID, or None if not in episode mode."""
        return self._episode_id

    @property
    def episode_step_count(self) -> int:
        """Number of steps taken in the current episode."""
        return self._episode_step_count

    @property
    def in_episode(self) -> bool:
        """Whether an episode is currently active."""
        return self._episode_active

    @property
    @abstractmethod
    def app_id(self) -> str:
        """Unique ID for this app."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for this app."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Description for agent context."""
        ...

    @abstractmethod
    def get_actions(self) -> list[AppAction]:
        """Get available actions."""
        ...

    @abstractmethod
    async def _execute_action(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Internal action execution - implement business logic here."""
        ...

    @abstractmethod
    async def _initialize_state(
        self,
        agents: list[str],
        config: dict[str, Any],
    ) -> None:
        """Initialize app-specific state."""
        ...

    @abstractmethod
    def _get_state_dict(self) -> dict[str, Any]:
        """Get app state as dictionary for serialization."""
        ...

    @abstractmethod
    def _restore_state_dict(self, state: dict[str, Any]) -> None:
        """Restore app state from dictionary."""
        ...

    async def initialize(
        self,
        sim_id: str,
        agents: list[str],
        config: dict[str, Any],
        agent_names: dict[str, str] | None = None,
    ) -> None:
        """Initialize app state for a simulation."""
        self._sim_id = sim_id
        self._agents = agents
        self._config = config
        self._agent_names = agent_names or {}
        self._observations = {agent_id: [] for agent_id in agents}
        self._action_log = []

        await self._initialize_state(agents, config)
        logger.info(f"Initialized {self.name} app for simulation {sim_id}")

    async def execute(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute an action with validation and logging."""
        # Find the action definition
        actions = {a.name: a for a in self.get_actions()}
        action_def = actions.get(action)

        if action_def is None:
            error = f"Unknown action: {action}"
            self._log_action(agent_id, action, params, AppResult.fail(error))
            return AppResult.fail(error)

        # Validate parameters
        is_valid, error = action_def.validate_params(params)
        if not is_valid:
            result = AppResult.fail(error)
            self._log_action(agent_id, action, params, result)
            return result

        # Execute the action
        try:
            result = await self._execute_action(agent_id, action, params)
        except Exception as e:
            logger.exception(f"Error executing {action} for {agent_id}")
            result = AppResult.fail(f"Internal error: {str(e)}")

        self._log_action(agent_id, action, params, result)
        return result

    def _log_action(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
        result: AppResult,
    ) -> None:
        """Log an action to the audit trail."""
        # Determine step from simulation context (will be set by runner)
        step = getattr(self, "_current_step", 0)

        entry = AppActionLogEntry(
            id=str(uuid.uuid4())[:8],
            app_instance_id=f"{self._sim_id}_{self.app_id}",
            agent_id=agent_id,
            step=step,
            action_name=action,
            params=params,
            success=result.success,
            result=result.data,
            error=result.error,
        )
        self._action_log.append(entry)

    def add_observation(
        self,
        agent_id: str,
        message: str,
        data: dict[str, Any] | None = None,
        priority: int = 0,
    ) -> None:
        """Add an observation for an agent.

        Args:
            agent_id: Target agent ID
            message: Human-readable message
            data: Structured data
            priority: Priority (higher = more important)
        """
        if agent_id not in self._observations:
            self._observations[agent_id] = []

        observation = AppObservation(
            app_id=self.app_id,
            message=message,
            data=data or {},
            priority=priority,
        )
        self._observations[agent_id].append(observation)

    async def get_observations(self, agent_id: str) -> list[AppObservation]:
        """Get and clear pending observations for an agent."""
        observations = self._observations.get(agent_id, [])
        self._observations[agent_id] = []
        return sorted(observations, key=lambda o: -o.priority)

    @abstractmethod
    async def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Get the agent's view of app state."""
        ...

    def get_action_log(
        self,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[AppActionLogEntry]:
        """Get action log entries.

        Args:
            agent_id: Optional filter by agent
            limit: Maximum entries to return

        Returns:
            List of log entries, newest first
        """
        entries = self._action_log
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        return sorted(entries, key=lambda e: e.executed_at, reverse=True)[:limit]

    def get_state_snapshot(self) -> bytes:
        """Serialize full app state for checkpoint."""
        state = {
            "sim_id": self._sim_id,
            "agents": self._agents,
            "config": self._config,
            "observations": {
                agent_id: [o.to_dict() for o in obs]
                for agent_id, obs in self._observations.items()
            },
            "action_log": [e.to_dict() for e in self._action_log],
            "app_state": self._get_state_dict(),
        }
        return json.dumps(state).encode("utf-8")

    def restore_state(self, snapshot: bytes) -> None:
        """Restore app state from checkpoint."""
        state = json.loads(snapshot.decode("utf-8"))

        self._sim_id = state["sim_id"]
        self._agents = state["agents"]
        self._config = state["config"]
        self._observations = {
            agent_id: [AppObservation.from_dict(o) for o in obs]
            for agent_id, obs in state["observations"].items()
        }
        # Note: action log is typically persisted in DB, not restored here
        self._action_log = []

        self._restore_state_dict(state["app_state"])

    def set_current_step(self, step: int) -> None:
        """Set current simulation step for action logging."""
        self._current_step = step

    def get_full_state(self) -> dict[str, Any]:
        """Get full app state for API responses."""
        state = {
            "app_id": self.app_id,
            "name": self.name,
            "description": self.description,
            "simulation_id": self._sim_id,
            "agents": self._agents,
            "config": self._config,
            "state": self._get_state_dict(),
        }
        # Include episode info if in episode mode
        if self._episode_active:
            state["episode"] = {
                "episode_id": self._episode_id,
                "step_count": self._episode_step_count,
                "active": self._episode_active,
            }
        return state

    # ==========================================================================
    # Episode Methods (for direct environment protocol support)
    # ==========================================================================

    async def env_reset(
        self,
        agents: list[str],
        config: dict[str, Any] | None = None,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Reset for new episode. Override for custom reset logic.

        This method provides direct environment protocol support without
        needing the AppEnvironmentWrapper. The wrapper is still preferred
        for full Gymnasium-style interface with history tracking.

        Args:
            agents: List of agent IDs for this episode
            config: App-specific configuration
            seed: Optional random seed (not used by default)

        Returns:
            Initial observation dictionary
        """
        self._episode_id = str(uuid.uuid4())[:8]
        self._episode_step_count = 0
        self._episode_active = True

        # Initialize the app
        await self.initialize(
            sim_id=f"ep_{self._episode_id}",
            agents=agents,
            config=config or {},
        )

        # Return initial observation
        if agents:
            return await self.get_agent_state(agents[0])
        return {}

    def env_close(self) -> None:
        """End episode. Override for custom cleanup.

        Call this when the episode is complete to clean up episode state.
        """
        self._episode_active = False
        self._episode_id = None
        self._episode_step_count = 0

    def increment_episode_step(self) -> int:
        """Increment and return the episode step counter.

        Call this after each action execution when in episode mode.

        Returns:
            New step count
        """
        self._episode_step_count += 1
        return self._episode_step_count


# ==============================================================================
# App Registry
# ==============================================================================


class AppRegistry:
    """Registry for discovering and instantiating simulated apps.

    Apps are discovered via:
    1. Python plugins registered programmatically
    2. Entry points (agentworld.apps) per ADR-014
    3. Database definitions (DynamicApp) per ADR-018

    Python plugins take precedence over database definitions.
    """

    _instance: "AppRegistry | None" = None
    _apps: dict[str, type[SimulatedAppPlugin]]
    _db_enabled: bool

    def __new__(cls) -> "AppRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._apps = {}
            cls._instance._db_enabled = True
            cls._instance._load_builtin_apps()
        return cls._instance

    def _load_builtin_apps(self) -> None:
        """Load built-in apps."""
        # Built-in apps will be registered here
        # PayPal will be added after implementation
        pass

    def _load_entry_points(self) -> None:
        """Load apps from entry points."""
        try:
            from importlib.metadata import entry_points

            eps = entry_points()
            if hasattr(eps, "select"):
                # Python 3.10+
                app_eps = eps.select(group="agentworld.apps")
            else:
                # Python 3.9
                app_eps = eps.get("agentworld.apps", [])

            for ep in app_eps:
                try:
                    app_class = ep.load()
                    if isinstance(app_class, type):
                        # Instantiate to get app_id
                        instance = app_class()
                        self._apps[instance.app_id] = app_class
                        logger.info(f"Loaded app plugin: {instance.app_id}")
                except Exception as e:
                    logger.warning(f"Failed to load app plugin {ep.name}: {e}")

        except Exception as e:
            logger.warning(f"Failed to load app entry points: {e}")

    def _get_from_db(self, app_id: str) -> SimulatedAppPlugin | None:
        """Try to load an app from the database.

        Args:
            app_id: App ID to look up

        Returns:
            DynamicApp instance or None if not found
        """
        if not self._db_enabled:
            return None

        try:
            from agentworld.persistence.database import init_db
            from agentworld.persistence.repository import Repository
            from agentworld.apps.definition import AppDefinition
            from agentworld.apps.dynamic import DynamicApp

            init_db()
            repo = Repository()
            definition = repo.get_app_definition_by_app_id(app_id)

            if definition:
                full_def = definition.get("definition", {})
                app_def = AppDefinition.from_dict(full_def)
                return DynamicApp(app_def)

        except Exception as e:
            logger.warning(f"Failed to load app from database: {app_id}: {e}")

        return None

    def _list_db_apps(self) -> list[dict[str, str]]:
        """List apps from the database.

        Returns:
            List of app info dicts
        """
        if not self._db_enabled:
            return []

        try:
            from agentworld.persistence.database import init_db
            from agentworld.persistence.repository import Repository

            init_db()
            repo = Repository()
            definitions = repo.list_app_definitions()

            result = []
            for definition in definitions:
                # Skip if Python plugin exists with same ID
                if definition["app_id"] not in self._apps:
                    result.append({
                        "id": definition["app_id"],
                        "name": definition["name"],
                        "description": definition.get("description") or "",
                        "source": "database",
                    })
            return result

        except Exception as e:
            logger.warning(f"Failed to list apps from database: {e}")
            return []

    def register(self, app_class: type[SimulatedAppPlugin]) -> None:
        """Register an app class.

        Args:
            app_class: App class to register
        """
        instance = app_class()
        self._apps[instance.app_id] = app_class
        logger.debug(f"Registered app: {instance.app_id}")

    def get(self, app_id: str) -> SimulatedAppPlugin | None:
        """Get an app instance by ID.

        Looks up apps in order:
        1. Registered Python plugins
        2. Database definitions (DynamicApp)

        Args:
            app_id: App ID

        Returns:
            New app instance or None if not found
        """
        # Check Python plugins first
        app_class = self._apps.get(app_id)
        if app_class:
            return app_class()

        # Fall back to database
        return self._get_from_db(app_id)

    def list_apps(self) -> list[dict[str, str]]:
        """List all available apps.

        Combines Python plugins and database definitions.
        Python plugins take precedence for duplicate IDs.

        Returns:
            List of app info dicts with id, name, description
        """
        result = []

        # Add Python plugins
        for app_id, app_class in self._apps.items():
            instance = app_class()
            result.append({
                "id": instance.app_id,
                "name": instance.name,
                "description": instance.description,
                "source": "plugin",
            })

        # Add database apps (excluding duplicates)
        result.extend(self._list_db_apps())

        return result

    def get_app_ids(self) -> list[str]:
        """Get list of all available app IDs."""
        ids = set(self._apps.keys())

        # Add database app IDs
        for app_info in self._list_db_apps():
            ids.add(app_info["id"])

        return list(ids)

    def reload(self) -> None:
        """Reload apps from entry points."""
        self._apps.clear()
        self._load_builtin_apps()
        self._load_entry_points()

    def set_db_enabled(self, enabled: bool) -> None:
        """Enable or disable database lookups.

        Useful for testing or when database is not available.

        Args:
            enabled: Whether to enable database lookups
        """
        self._db_enabled = enabled

    def is_python_plugin(self, app_id: str) -> bool:
        """Check if an app ID is a registered Python plugin.

        Args:
            app_id: App ID to check

        Returns:
            True if it's a Python plugin, False otherwise
        """
        return app_id in self._apps


def get_app_registry() -> AppRegistry:
    """Get the global app registry instance."""
    return AppRegistry()
