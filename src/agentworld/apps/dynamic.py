"""Dynamic app implementation that executes JSON definitions.

This module implements the DynamicApp class per ADR-018, which loads
app definitions from JSON and executes them using the LogicEngine.

Example:
    definition = AppDefinition.from_dict({
        "app_id": "my_app",
        "name": "My App",
        "category": "custom",
        "actions": [...],
    })
    app = DynamicApp(definition)
    await app.initialize("sim123", ["alice", "bob"], {})
    result = await app.execute("alice", "some_action", {"param": "value"})
"""

from __future__ import annotations

import copy
import json
import logging
from typing import Any

from agentworld.apps.base import (
    AppAction,
    AppObservation,
    AppResult,
    BaseSimulatedApp,
    ParamSpec,
)
from agentworld.apps.definition import (
    ActionDefinition,
    AppDefinition,
    AppState,
    ParamType,
)
from agentworld.apps.logic_engine import ExecutionContext, LogicEngine

logger = logging.getLogger(__name__)


class DynamicApp(BaseSimulatedApp):
    """App loaded from JSON definition.

    This class implements the SimulatedAppPlugin protocol using a JSON
    definition instead of Python code. The business logic is defined
    in the definition's action logic blocks and executed by the LogicEngine.

    Per ADR-018.
    """

    def __init__(self, definition: AppDefinition):
        """Initialize dynamic app from definition.

        Args:
            definition: The app definition containing actions and logic
        """
        super().__init__()
        self._definition = definition
        self._logic_engine = LogicEngine()
        self._app_state = AppState()

    @property
    def app_id(self) -> str:
        """Unique ID for this app."""
        return self._definition.app_id

    @property
    def name(self) -> str:
        """Display name for this app."""
        return self._definition.name

    @property
    def description(self) -> str:
        """Description for agent context."""
        return self._definition.description

    @property
    def definition(self) -> AppDefinition:
        """Get the underlying definition."""
        return self._definition

    def get_actions(self) -> list[AppAction]:
        """Get available actions with their schemas.

        Converts ActionDefinition to AppAction for compatibility with
        the existing protocol.
        """
        actions = []
        for action_def in self._definition.actions:
            # Convert ParamSpecDef to ParamSpec
            params = {}
            for name, spec_def in action_def.parameters.items():
                params[name] = ParamSpec(
                    name=name,
                    type=spec_def.type.value if isinstance(spec_def.type, ParamType) else spec_def.type,
                    description=spec_def.description,
                    required=spec_def.required,
                    default=spec_def.default,
                    min_value=spec_def.min_value,
                    max_value=spec_def.max_value,
                    min_length=spec_def.min_length,
                    max_length=spec_def.max_length,
                    pattern=spec_def.pattern,
                    enum=spec_def.enum,
                )

            actions.append(AppAction(
                name=action_def.name,
                description=action_def.description,
                parameters=params,
                returns=action_def.returns,
            ))

        return actions

    async def _initialize_state(
        self,
        agents: list[str],
        config: dict[str, Any],
    ) -> None:
        """Initialize app state for all agents.

        Creates per-agent state from state_schema and initializes shared state.
        """
        self._app_state = AppState()

        # Build default per-agent state from schema
        per_agent_defaults = {}
        shared_defaults = {}

        for field_def in self._definition.state_schema:
            default_value = self._get_default_for_type(field_def.type, field_def.default)
            if field_def.per_agent:
                per_agent_defaults[field_def.name] = default_value
            else:
                shared_defaults[field_def.name] = default_value

        # Apply initial_config overrides
        merged_config = {**self._definition.initial_config, **config}

        # Initialize per-agent state
        for agent_id in agents:
            agent_state = copy.deepcopy(per_agent_defaults)
            # Apply any agent-specific config (e.g., initial_balance)
            for key, value in merged_config.items():
                if key in agent_state:
                    agent_state[key] = value
            self._app_state.set_agent_state(agent_id, agent_state)

        # Register agent names for name-to-ID resolution
        if hasattr(self, '_agent_names') and self._agent_names:
            for agent_id, name in self._agent_names.items():
                self._app_state.register_agent_name(agent_id, name)

        # Initialize shared state
        self._app_state.shared = copy.deepcopy(shared_defaults)
        for key, value in merged_config.items():
            if key in self._app_state.shared:
                self._app_state.shared[key] = value

        logger.info(
            f"Initialized DynamicApp '{self.app_id}' for {len(agents)} agents"
        )

    def _get_default_for_type(self, param_type: ParamType, default: Any) -> Any:
        """Get default value for a parameter type."""
        if default is not None:
            return copy.deepcopy(default)

        type_defaults = {
            ParamType.STRING: "",
            ParamType.NUMBER: 0,
            ParamType.BOOLEAN: False,
            ParamType.ARRAY: [],
            ParamType.OBJECT: {},
        }
        return type_defaults.get(param_type, None)

    async def _execute_action(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute an action using the logic engine.

        Args:
            agent_id: ID of the agent performing the action
            action: Action name
            params: Action parameters

        Returns:
            AppResult with success/failure and data
        """
        # Find action definition
        action_def = self._definition.get_action(action)
        if action_def is None:
            return AppResult.fail(f"Unknown action: {action}")

        # Ensure agent has state
        self._app_state.ensure_agent(agent_id)

        # Create execution context
        context = ExecutionContext(
            agent_id=agent_id,
            params=params,
            state=self._app_state,
            config=self._config,
        )

        # Execute logic
        result = await self._logic_engine.execute(action_def.logic, context)

        # Process observations (set app_id and add to internal queue)
        for to_agent, observation in context.observations:
            observation.app_id = self.app_id
            self.add_observation(
                agent_id=to_agent,
                message=observation.message,
                data=observation.data,
                priority=observation.priority,
            )

        return result

    async def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Get the agent's view of app state.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with agent-specific state
        """
        agent_state = self._app_state.get_agent_state(agent_id)
        return {
            "agent_state": agent_state,
            "shared_state": self._app_state.shared,
        }

    def _get_state_dict(self) -> dict[str, Any]:
        """Get app state as dictionary for serialization."""
        return self._app_state.to_dict()

    def _restore_state_dict(self, state: dict[str, Any]) -> None:
        """Restore app state from dictionary."""
        self._app_state = AppState.from_dict(state)

    # =========================================================================
    # Stateless Execution (for /test endpoint per ADR-018)
    # =========================================================================

    async def execute_stateless(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
        state: AppState,
        config: dict[str, Any] | None = None,
    ) -> tuple[AppResult, AppState, list[AppObservation]]:
        """Execute an action without modifying internal state.

        This is used by the /test endpoint for sandbox testing.
        State is passed in and returned, not stored internally.

        Args:
            agent_id: ID of the agent performing the action
            action: Action name
            params: Action parameters
            state: Input state (will be deep-copied)
            config: Optional config override

        Returns:
            Tuple of (result, state_after, observations)
        """
        # Find action definition
        action_def = self._definition.get_action(action)
        if action_def is None:
            return AppResult.fail(f"Unknown action: {action}"), state, []

        # Deep copy state to avoid modifying input
        working_state = state.deep_copy()
        working_state.ensure_agent(agent_id)

        # Create execution context
        context = ExecutionContext(
            agent_id=agent_id,
            params=params,
            state=working_state,
            config=config or self._definition.initial_config,
        )

        # Execute logic
        result = await self._logic_engine.execute(action_def.logic, context)

        # Collect observations as (to_agent, observation) tuples
        observations = []
        for to_agent, observation in context.observations:
            observation.app_id = self.app_id
            observations.append((to_agent, observation))

        return result, working_state, observations

    # =========================================================================
    # Validation
    # =========================================================================

    def validate_params(
        self,
        action: str,
        params: dict[str, Any],
    ) -> tuple[bool, str]:
        """Validate parameters for an action.

        Args:
            action: Action name
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        action_def = self._definition.get_action(action)
        if action_def is None:
            return False, f"Unknown action: {action}"

        # Check for unknown parameters
        known_params = set(action_def.parameters.keys())
        provided_params = set(params.keys())
        unknown = provided_params - known_params
        if unknown:
            return False, f"Unknown parameters: {', '.join(sorted(unknown))}"

        # Validate each parameter
        for param_name, param_spec in action_def.parameters.items():
            value = params.get(param_name)

            # Check required
            if param_spec.required and value is None and param_spec.default is None:
                return False, f"Parameter '{param_name}' is required"

            if value is None:
                continue

            # Type validation
            param_type = param_spec.type
            if isinstance(param_type, ParamType):
                param_type = param_type.value

            type_map = {
                "string": str,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            expected_type = type_map.get(param_type)
            if expected_type and not isinstance(value, expected_type):
                return False, f"Parameter '{param_name}' must be {param_type}, got {type(value).__name__}"

            # Numeric range validation
            if param_spec.min_value is not None and isinstance(value, (int, float)):
                if value < param_spec.min_value:
                    return False, f"Parameter '{param_name}' must be >= {param_spec.min_value}"

            if param_spec.max_value is not None and isinstance(value, (int, float)):
                if value > param_spec.max_value:
                    return False, f"Parameter '{param_name}' must be <= {param_spec.max_value}"

            # String length validation
            if isinstance(value, str):
                if param_spec.min_length is not None and len(value) < param_spec.min_length:
                    return False, f"Parameter '{param_name}' must be at least {param_spec.min_length} characters"
                if param_spec.max_length is not None and len(value) > param_spec.max_length:
                    return False, f"Parameter '{param_name}' must be at most {param_spec.max_length} characters"

            # Enum validation
            if param_spec.enum is not None and value not in param_spec.enum:
                return False, f"Parameter '{param_name}' must be one of {param_spec.enum}"

        return True, ""


def create_dynamic_app(definition_dict: dict[str, Any]) -> DynamicApp:
    """Create a DynamicApp from a definition dictionary.

    Convenience function for creating apps from JSON.

    Args:
        definition_dict: Dictionary representation of AppDefinition

    Returns:
        Configured DynamicApp instance
    """
    definition = AppDefinition.from_dict(definition_dict)
    return DynamicApp(definition)
