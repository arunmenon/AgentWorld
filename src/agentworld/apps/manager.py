"""App manager for simulation integration.

This module provides the SimulationAppManager which handles the lifecycle
of simulated apps within a simulation per ADR-017.

Supports environment semantics via get_app_as_env() for Gymnasium-style
episode management and reward tracking.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING

from agentworld.apps.base import (
    AppObservation,
    AppResult,
    SimulatedAppPlugin,
    get_app_registry,
)
from agentworld.apps.parser import parse_message, ParsedAction

if TYPE_CHECKING:
    from agentworld.persistence.repository import Repository
    from agentworld.apps.environment import AppEnvironmentWrapper

logger = logging.getLogger(__name__)


@dataclass
class AppExecutionResult:
    """Result of executing an action from a parsed directive."""

    action: ParsedAction
    result: AppResult
    app_name: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.to_dict(),
            "result": self.result.to_dict(),
            "app_name": self.app_name,
        }


@dataclass
class SimulationAppManager:
    """Manages simulated apps for a simulation.

    Handles app lifecycle (initialization, execution, checkpointing)
    and integrates with the simulation runner.

    Supports environment semantics via get_app_as_env() for Gymnasium-style
    episode management with automatic reward tracking.

    Example:
        >>> manager = SimulationAppManager("sim_123")
        >>> await manager.initialize_apps([{"id": "paypal"}], ["alice"], {})
        >>>
        >>> # Get app with environment wrapper
        >>> env = manager.get_app_as_env("paypal", max_steps=50)
        >>> result = await env.reset(options={"agents": ["alice"]})
        >>> step = await env.step("alice", "get_balance", {})
    """

    simulation_id: str
    _apps: dict[str, SimulatedAppPlugin] = field(default_factory=dict)
    _app_instance_ids: dict[str, str] = field(default_factory=dict)  # app_id -> instance_id
    _repository: "Repository | None" = field(default=None)
    _current_step: int = field(default=0)
    _app_envs: dict[str, "AppEnvironmentWrapper"] = field(default_factory=dict)  # app_id -> wrapper

    async def initialize_apps(
        self,
        app_configs: list[dict[str, Any]],
        agent_ids: list[str],
        agent_names: dict[str, str] | None = None,
    ) -> None:
        """Initialize apps for a simulation.

        Args:
            app_configs: List of app configurations from simulation config
                Each should have 'id' (app_id) and optional 'config' dict
            agent_ids: List of agent IDs in the simulation
            agent_names: Optional mapping of agent_id -> agent_name for name resolution
        """
        registry = get_app_registry()

        for app_config in app_configs:
            app_id = app_config.get("id")
            if not app_id:
                logger.warning("App config missing 'id', skipping")
                continue

            # Get app instance from registry
            app = registry.get(app_id)
            if app is None:
                logger.warning(f"Unknown app: {app_id}, skipping")
                continue

            # Initialize the app
            config = app_config.get("config", {})
            try:
                await app.initialize(
                    sim_id=self.simulation_id,
                    agents=agent_ids,
                    config=config,
                    agent_names=agent_names,
                )
                self._apps[app_id] = app

                # Generate instance ID for DB storage
                instance_id = f"{self.simulation_id}_{app_id}"
                self._app_instance_ids[app_id] = instance_id

                logger.info(f"Initialized app {app_id} for simulation {self.simulation_id}")

                # Persist initial state
                self._save_app_state(app_id)

            except Exception as e:
                logger.exception(f"Failed to initialize app {app_id}: {e}")

    def set_repository(self, repository: "Repository") -> None:
        """Set the repository for persistence."""
        self._repository = repository

    def set_current_step(self, step: int) -> None:
        """Set the current simulation step."""
        self._current_step = step
        for app in self._apps.values():
            if hasattr(app, "set_current_step"):
                app.set_current_step(step)

    def get_app(self, app_id: str) -> SimulatedAppPlugin | None:
        """Get an app by ID."""
        return self._apps.get(app_id)

    def get_app_ids(self) -> list[str]:
        """Get list of active app IDs."""
        return list(self._apps.keys())

    async def get_agent_observations(self, agent_id: str) -> list[AppObservation]:
        """Get all pending observations for an agent from all apps.

        Args:
            agent_id: Agent ID

        Returns:
            List of observations from all apps, sorted by priority
        """
        all_observations: list[AppObservation] = []

        for app in self._apps.values():
            try:
                observations = await app.get_observations(agent_id)
                all_observations.extend(observations)
            except Exception as e:
                logger.warning(f"Error getting observations from {app.app_id}: {e}")

        # Sort by priority (highest first)
        return sorted(all_observations, key=lambda o: -o.priority)

    def format_observations_for_context(
        self,
        observations: list[AppObservation],
    ) -> str:
        """Format observations into a string for agent context.

        Args:
            observations: List of observations

        Returns:
            Formatted string for including in agent prompt
        """
        if not observations:
            return ""

        lines = ["[App Notifications]"]
        for obs in observations:
            lines.append(f"  [{obs.app_id.upper()}] {obs.message}")
        lines.append("")

        return "\n".join(lines)

    async def process_message(
        self,
        agent_id: str,
        message: str,
    ) -> tuple[str, list[AppExecutionResult]]:
        """Process agent message for app actions.

        Parses APP_ACTION directives and executes them.

        Args:
            agent_id: Agent ID
            message: Full message content

        Returns:
            Tuple of (message_without_actions, execution_results)
        """
        parse_result = parse_message(message)

        if not parse_result.has_actions:
            return message, []

        execution_results: list[AppExecutionResult] = []

        for action in parse_result.actions:
            result = await self.execute_action(agent_id, action)
            if result:
                execution_results.append(result)

        # Log any parse errors
        for error in parse_result.errors:
            logger.warning(
                f"Action parse error in message from {agent_id}: {error.message}"
            )

        return parse_result.message_without_actions, execution_results

    async def execute_action(
        self,
        agent_id: str,
        action: ParsedAction,
    ) -> AppExecutionResult | None:
        """Execute a parsed action.

        Args:
            agent_id: Agent ID
            action: Parsed action

        Returns:
            Execution result or None if app not found
        """
        app = self._apps.get(action.app_id)
        if app is None:
            logger.warning(f"Action for unknown app: {action.app_id}")
            return AppExecutionResult(
                action=action,
                result=AppResult.fail(f"Unknown app: {action.app_id}"),
                app_name=action.app_id,
            )

        try:
            result = await app.execute(agent_id, action.action, action.params)
        except Exception as e:
            logger.exception(f"Error executing action {action.action}: {e}")
            result = AppResult.fail(f"Execution error: {str(e)}")

        # Log to database
        self._log_action(action.app_id, agent_id, action, result)

        # Save updated state
        self._save_app_state(action.app_id)

        return AppExecutionResult(
            action=action,
            result=result,
            app_name=app.name,
        )

    def _log_action(
        self,
        app_id: str,
        agent_id: str,
        action: ParsedAction,
        result: AppResult,
    ) -> None:
        """Log an action to the database."""
        if self._repository is None:
            return

        instance_id = self._app_instance_ids.get(app_id)
        if not instance_id:
            return

        try:
            self._repository.save_app_action_log({
                "id": str(uuid.uuid4())[:8],
                "app_instance_id": instance_id,
                "agent_id": agent_id,
                "step": self._current_step,
                "action_name": action.action,
                "params": action.params,
                "success": result.success,
                "result": result.data,
                "error": result.error,
            })
        except Exception as e:
            logger.warning(f"Failed to log action: {e}")

    def _save_app_state(self, app_id: str) -> None:
        """Save app state to database."""
        if self._repository is None:
            return

        app = self._apps.get(app_id)
        if not app:
            return

        instance_id = self._app_instance_ids.get(app_id)
        if not instance_id:
            return

        try:
            # Get state from app
            if hasattr(app, "get_full_state"):
                state = app.get_full_state()
            else:
                state = {}

            self._repository.save_app_instance({
                "id": instance_id,
                "simulation_id": self.simulation_id,
                "app_id": app_id,
                "config": app._config if hasattr(app, "_config") else {},
                "state": state,
            })
        except Exception as e:
            logger.warning(f"Failed to save app state: {e}")

    async def get_agent_state(self, app_id: str, agent_id: str) -> dict[str, Any]:
        """Get an agent's state for a specific app.

        Args:
            app_id: App ID
            agent_id: Agent ID

        Returns:
            Agent's app state or error dict
        """
        app = self._apps.get(app_id)
        if app is None:
            return {"error": f"Unknown app: {app_id}"}

        try:
            return await app.get_agent_state(agent_id)
        except Exception as e:
            logger.exception(f"Error getting agent state: {e}")
            return {"error": str(e)}

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        """Get full state of all apps.

        Returns:
            Dictionary of app_id -> app_state
        """
        states = {}
        for app_id, app in self._apps.items():
            if hasattr(app, "get_full_state"):
                states[app_id] = app.get_full_state()
            else:
                states[app_id] = {}
        return states

    def get_state_snapshots(self) -> dict[str, bytes]:
        """Get state snapshots for all apps (for checkpointing).

        Returns:
            Dictionary of app_id -> serialized_state
        """
        snapshots = {}
        for app_id, app in self._apps.items():
            try:
                snapshots[app_id] = app.get_state_snapshot()
            except Exception as e:
                logger.warning(f"Failed to snapshot app {app_id}: {e}")
        return snapshots

    def restore_state_snapshots(self, snapshots: dict[str, bytes]) -> None:
        """Restore app states from snapshots.

        Args:
            snapshots: Dictionary of app_id -> serialized_state
        """
        for app_id, snapshot in snapshots.items():
            app = self._apps.get(app_id)
            if app is None:
                logger.warning(f"Cannot restore unknown app: {app_id}")
                continue

            try:
                app.restore_state(snapshot)
                logger.info(f"Restored state for app {app_id}")
            except Exception as e:
                logger.exception(f"Failed to restore app {app_id}: {e}")

    async def get_observable_state(
        self,
        agent_id: str,
        app_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get observable state for an agent (τ²-bench state-constrained mode).

        Returns only state fields marked as observable=True in the app's state schema.
        This enables state-constrained user simulation where user agents can only
        report what they actually "see" on their device.

        Args:
            agent_id: Agent ID
            app_ids: Optional list of app IDs to include. If None, includes all apps.

        Returns:
            Dictionary of observable state organized by app_id, e.g.:
            {
                "airline_device": {
                    "boarding_pass_visible": True,
                    "seat_number": "12A",
                    "flight_status": "On Time"
                },
                "paypal_account": {
                    "balance": 150.00,
                    "last_transaction": "$50 to Alice"
                }
            }
        """
        observable_state: dict[str, Any] = {}
        target_apps = app_ids if app_ids else list(self._apps.keys())

        for app_id in target_apps:
            app = self._apps.get(app_id)
            if app is None:
                continue

            try:
                # Get app's state schema to check which fields are observable
                app_state = {}
                if hasattr(app, "get_agent_state"):
                    full_state = await app.get_agent_state(agent_id)
                elif hasattr(app, "get_full_state"):
                    full_state = app.get_full_state()
                    # Extract per-agent state if available
                    per_agent = full_state.get("per_agent", {})
                    full_state = per_agent.get(agent_id, full_state.get("shared", {}))
                else:
                    continue

                # Check if app has state schema with observable fields
                if hasattr(app, "_definition") and hasattr(app._definition, "state_schema"):
                    state_schema = app._definition.state_schema
                    # Filter to only observable fields
                    for field_def in state_schema:
                        if hasattr(field_def, "observable") and field_def.observable:
                            field_name = field_def.name
                            if field_name in full_state:
                                app_state[field_name] = full_state[field_name]
                elif hasattr(app, "state_schema"):
                    # Legacy: state_schema as list of dicts
                    for field_def in app.state_schema:
                        if isinstance(field_def, dict) and field_def.get("observable", True):
                            field_name = field_def.get("name", "")
                            if field_name and field_name in full_state:
                                app_state[field_name] = full_state[field_name]
                else:
                    # Fallback: return all state if no schema defined
                    app_state = full_state

                if app_state:
                    observable_state[app_id] = app_state

            except Exception as e:
                logger.warning(f"Error getting observable state for {app_id}: {e}")

        return observable_state

    def get_available_apps_prompt(self) -> str:
        """Generate prompt text describing available apps.

        Returns:
            Formatted string for agent system prompt
        """
        if not self._apps:
            return ""

        lines = [
            "## Available Applications",
            "",
            "You have access to the following simulated applications. "
            "**IMPORTANT:** To use them, you MUST include APP_ACTION directives in your messages.",
            "",
            "### How to Use Apps",
            "",
            "Include directives on separate lines using this exact format:",
            "```",
            "APP_ACTION: <app_id>.<action>(<params>)",
            "```",
            "",
            "**Examples:**",
            "",
            "To check your balance:",
            "```",
            "APP_ACTION: paypal.check_balance()",
            "```",
            "",
            "To transfer $50 to Bob:",
            "```",
            'APP_ACTION: paypal.transfer(to="bob", amount=50)',
            "```",
            "",
            "To transfer with a note:",
            "```",
            'APP_ACTION: paypal.transfer(to="alice", amount=25, note="thanks!")',
            "```",
            "",
            "**Rules:**",
            "- Always put APP_ACTION on its own line",
            "- Use exact parameter names as shown",
            "- String values must be in quotes",
            "- Number values without quotes",
            "- You can include multiple APP_ACTION directives in one message",
            "",
        ]

        for app_id, app in self._apps.items():
            lines.append(f"### {app.name} ({app_id})")
            lines.append(f"{app.description}")
            lines.append("")
            lines.append("Actions:")

            for action in app.get_actions():
                params_str = ""
                if action.parameters:
                    param_parts = []
                    for name, spec in action.parameters.items():
                        req = "" if spec.required else "optional, "
                        param_parts.append(f"{name}: {spec.type} ({req}{spec.description})")
                    params_str = "; ".join(param_parts)

                lines.append(f"  - {action.name}: {action.description}")
                if params_str:
                    lines.append(f"    Parameters: {params_str}")
            lines.append("")

        return "\n".join(lines)

    # ==========================================================================
    # Environment Wrapper Methods
    # ==========================================================================

    def get_app_as_env(
        self,
        app_id: str,
        max_steps: int = 100,
        reward_function: Callable[[Any, dict, bool, int], float] | None = None,
        track_history: bool = True,
    ) -> "AppEnvironmentWrapper | None":
        """Get app wrapped with environment semantics.

        Returns an AppEnvironmentWrapper that provides Gymnasium-style
        interface (reset, step, close) with automatic reward tracking
        and episode history.

        Args:
            app_id: ID of the app to wrap
            max_steps: Maximum steps per episode before truncation
            reward_function: Optional custom reward function
            track_history: Whether to track full state history

        Returns:
            AppEnvironmentWrapper instance or None if app not found

        Example:
            >>> env = manager.get_app_as_env("paypal", max_steps=50)
            >>> if env:
            ...     result = await env.reset(options={"agents": ["alice"]})
            ...     step = await env.step("alice", "get_balance", {})
        """
        # Return existing wrapper if available
        if app_id in self._app_envs:
            return self._app_envs[app_id]

        # Get underlying app
        app = self._apps.get(app_id)
        if app is None:
            logger.warning(f"Cannot create env wrapper for unknown app: {app_id}")
            return None

        # Import here to avoid circular dependency
        from agentworld.apps.environment import AppEnvironmentWrapper

        # Create wrapper
        env = AppEnvironmentWrapper(
            app=app,
            max_steps=max_steps,
            reward_function=reward_function,
            track_history=track_history,
        )
        self._app_envs[app_id] = env

        logger.info(f"Created environment wrapper for app {app_id} (max_steps={max_steps})")
        return env

    def has_env_wrapper(self, app_id: str) -> bool:
        """Check if an app has an active environment wrapper.

        Args:
            app_id: ID of the app to check

        Returns:
            True if wrapper exists
        """
        return app_id in self._app_envs

    def get_all_env_wrappers(self) -> dict[str, "AppEnvironmentWrapper"]:
        """Get all active environment wrappers.

        Returns:
            Dictionary of app_id -> AppEnvironmentWrapper
        """
        return self._app_envs.copy()

    async def reset_all_envs(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Reset all environment-wrapped apps.

        Useful for starting a new episode across all apps simultaneously.

        Args:
            seed: Optional random seed for reproducibility
            options: Options to pass to each reset (agents, config, etc.)

        Returns:
            Dictionary of app_id -> initial observation
        """
        results = {}
        options = options or {}

        for app_id, env in self._app_envs.items():
            try:
                result = await env.reset(seed=seed, options=options)
                results[app_id] = result.observation
            except Exception as e:
                logger.error(f"Failed to reset env for {app_id}: {e}")
                results[app_id] = {"error": str(e)}

        return results

    def close_all_envs(self) -> None:
        """Close all environment wrappers and finalize their history."""
        for app_id, env in self._app_envs.items():
            try:
                env.close()
            except Exception as e:
                logger.warning(f"Error closing env for {app_id}: {e}")

        self._app_envs.clear()
        logger.info("Closed all environment wrappers")

    def get_env_episode_histories(self) -> dict[str, list[dict[str, Any]]]:
        """Get episode histories from all environment wrappers.

        Returns:
            Dictionary of app_id -> list of episode history dicts
        """
        histories = {}
        for app_id, env in self._app_envs.items():
            episodes = env.get_all_episodes()
            histories[app_id] = [ep.to_dict() for ep in episodes]
            # Include current episode if active
            if env.get_episode_history():
                current = env.get_episode_history()
                if current and current.episode_id not in [ep.episode_id for ep in episodes]:
                    histories[app_id].append(current.to_dict())
        return histories
