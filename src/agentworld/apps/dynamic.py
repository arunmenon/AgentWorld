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
    AgentRole,
    AppAccessType,
    AppDefinition,
    AppState,
    AppStateType,
    ParamType,
    ToolType,
)
from agentworld.apps.logic_engine import ExecutionContext, LogicEngine

logger = logging.getLogger(__name__)


class DynamicApp(BaseSimulatedApp):
    """App loaded from JSON definition.

    This class implements the SimulatedAppPlugin protocol using a JSON
    definition instead of Python code. The business logic is defined
    in the definition's action logic blocks and executed by the LogicEngine.

    Per ADR-018, extended per ADR-020.1 for τ²-bench support:
    - Access control checking before action execution
    - Per-agent state isolation when state_type=PER_AGENT
    - Agent role tracking for role-restricted apps
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

        # NEW: Agent role tracking for access control (ADR-020.1)
        self._agent_roles: dict[str, str] = {}  # agent_id -> role
        self._agent_role_tags: dict[str, list[str]] = {}  # agent_id -> role_tags

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

    @property
    def access_type(self) -> AppAccessType:
        """Get app access type."""
        return self._definition.access_type

    @property
    def state_type(self) -> AppStateType:
        """Get app state type."""
        return self._definition.state_type

    # =========================================================================
    # Access Control (ADR-020.1)
    # =========================================================================

    def set_agent_role(
        self,
        agent_id: str,
        role: str | AgentRole,
        role_tags: list[str] | None = None
    ) -> None:
        """Set an agent's role for access control.

        Args:
            agent_id: ID of the agent
            role: Agent's primary role
            role_tags: Additional role tags for fine-grained access
        """
        if isinstance(role, AgentRole):
            self._agent_roles[agent_id] = role.value
        else:
            self._agent_roles[agent_id] = role

        if role_tags:
            self._agent_role_tags[agent_id] = role_tags

    def get_agent_role(self, agent_id: str) -> str:
        """Get an agent's role.

        Returns:
            Agent's role string, defaults to 'peer' if not set
        """
        return self._agent_roles.get(agent_id, AgentRole.PEER.value)

    def can_agent_access(self, agent_id: str) -> bool:
        """Check if an agent can access this app.

        Per ADR-020.1 access control:
        - SHARED: All agents can access
        - ROLE_RESTRICTED: Only agents with matching role
        - PER_AGENT: All agents can access (each gets own instance)

        Args:
            agent_id: ID of the agent to check

        Returns:
            True if agent can access this app
        """
        role = self.get_agent_role(agent_id)
        role_tags = self._agent_role_tags.get(agent_id)
        return self._definition.can_agent_access(role, role_tags)

    def check_access(self, agent_id: str) -> tuple[bool, str]:
        """Check access and return detailed result.

        Args:
            agent_id: ID of the agent to check

        Returns:
            Tuple of (can_access, error_message)
        """
        if self.can_agent_access(agent_id):
            return True, ""

        role = self.get_agent_role(agent_id)
        allowed = self._definition.allowed_roles or []
        return False, (
            f"Access denied: Agent '{agent_id}' with role '{role}' "
            f"cannot access app '{self.app_id}'. "
            f"Allowed roles: {allowed}"
        )

    def get_actions(self, agent_id: str | None = None) -> list[AppAction]:
        """Get available actions with their schemas.

        Converts ActionDefinition to AppAction for compatibility with
        the existing protocol.

        Args:
            agent_id: Optional agent ID for access control filtering.
                     If provided and agent cannot access this app,
                     returns empty list.

        Returns:
            List of available actions (may include tool_type metadata)
        """
        # Check access control if agent_id provided
        if agent_id and not self.can_agent_access(agent_id):
            logger.debug(
                f"Agent '{agent_id}' cannot access app '{self.app_id}', "
                f"returning empty action list"
            )
            return []

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

            # Include tool_type in returns metadata (ADR-020.1)
            returns_with_metadata = dict(action_def.returns)
            returns_with_metadata["_tool_type"] = action_def.tool_type.value

            actions.append(AppAction(
                name=action_def.name,
                description=action_def.description,
                parameters=params,
                returns=returns_with_metadata,
            ))

        return actions

    async def _initialize_state(
        self,
        agents: list[str],
        config: dict[str, Any],
    ) -> None:
        """Initialize app state for all agents.

        Creates per-agent state from state_schema and initializes shared state.

        Per ADR-020.1:
        - If state_type=SHARED, all agents share state
        - If state_type=PER_AGENT, each agent has isolated state
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

        # Determine which agents get state based on state_type
        if self.state_type == AppStateType.PER_AGENT:
            # PER_AGENT state: Each agent gets isolated state
            for agent_id in agents:
                agent_state = copy.deepcopy(per_agent_defaults)
                # Apply any agent-specific config
                for key, value in merged_config.items():
                    if key in agent_state:
                        agent_state[key] = value
                self._app_state.set_agent_state(agent_id, agent_state)

            logger.debug(
                f"Initialized PER_AGENT state for app '{self.app_id}' "
                f"with {len(agents)} isolated instances"
            )
        else:
            # SHARED state: Initialize per-agent state for all agents
            for agent_id in agents:
                agent_state = copy.deepcopy(per_agent_defaults)
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
            f"Initialized DynamicApp '{self.app_id}' for {len(agents)} agents "
            f"(access={self.access_type.value}, state={self.state_type.value})"
        )

    async def initialize_with_roles(
        self,
        simulation_id: str,
        agents: list[str],
        config: dict[str, Any],
        agent_roles: dict[str, str | AgentRole] | None = None,
        agent_role_tags: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize app with agent role information.

        Extended initialization method for ADR-020.1 dual-control support.

        Args:
            simulation_id: ID of the simulation
            agents: List of agent IDs to initialize
            config: App configuration
            agent_roles: Mapping of agent_id -> role
            agent_role_tags: Mapping of agent_id -> role_tags
        """
        # Set agent roles before initialization
        if agent_roles:
            for agent_id, role in agent_roles.items():
                role_tags = agent_role_tags.get(agent_id) if agent_role_tags else None
                self.set_agent_role(agent_id, role, role_tags)

        # Call standard initialization
        await self.initialize(simulation_id, agents, config)

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

        Per ADR-020.1, checks access control before execution.

        Args:
            agent_id: ID of the agent performing the action
            action: Action name
            params: Action parameters

        Returns:
            AppResult with success/failure and data
        """
        # Check access control (ADR-020.1)
        can_access, error_msg = self.check_access(agent_id)
        if not can_access:
            logger.warning(f"Access denied for agent '{agent_id}' on app '{self.app_id}'")
            return AppResult.fail(error_msg)

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

        # Log action with tool_type for analysis (ADR-020.1)
        logger.debug(
            f"Executed {action_def.tool_type.value.upper()} action '{action}' "
            f"for agent '{agent_id}' on app '{self.app_id}'"
        )

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
