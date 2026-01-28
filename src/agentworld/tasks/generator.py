"""Compositional task generator for τ²-bench.

This module provides programmatic generation of dual-control tasks from
atomic components, enabling creation of diverse, verifiable tasks with
controlled complexity.

Per τ²-bench requirements (ADR-020.1):
- Atomic task components compose into complex tasks
- Programmatic generation of diverse, verifiable tasks
- Controlled complexity progression
- Automatic ground truth generation

Example:
    >>> from agentworld.tasks.generator import (
    ...     AtomicTaskComponent,
    ...     CompositionalTaskGenerator,
    ... )
    >>>
    >>> generator = CompositionalTaskGenerator()
    >>> generator.register_components_from_app(airline_app)
    >>> task = generator.generate(
    ...     domain="airline",
    ...     complexity=2,
    ...     handoffs=3,
    ... )
"""

from __future__ import annotations

import copy
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agentworld.apps.definition import AppDefinition, ActionDefinition, AgentRole


class ActionType(str, Enum):
    """Type of atomic action for task composition."""
    CHECK = "check"       # Query/read state
    TOGGLE = "toggle"     # Switch boolean state
    TRANSFER = "transfer" # Move value between entities
    CONFIRM = "confirm"   # Acknowledge/verify action
    UPDATE = "update"     # Modify state value


@dataclass
class DualControlAgentConfig:
    """Agent configuration for dual-control tasks.

    Used by the compositional task generator to specify how each
    participant (agent or user) is configured in a task.

    Attributes:
        role: Role identifier (e.g., "service_agent", "customer")
        apps: List of app configurations available to this participant
        initial_message: Optional initial message to start with
    """
    role: str
    apps: list[dict[str, Any]] = field(default_factory=list)
    initial_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "apps": self.apps,
            "initial_message": self.initial_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DualControlAgentConfig":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            apps=data.get("apps", []),
            initial_message=data.get("initial_message", ""),
        )


@dataclass
class StateCondition:
    """A condition on app state for preconditions/postconditions.

    Attributes:
        app_id: App the condition applies to
        field_path: Path to the field (e.g., "per_agent.balance")
        operator: Comparison operator (eq, ne, gt, gte, lt, lte, exists)
        value: Expected value (None for 'exists' operator)
        agent_relative: If True, field_path is relative to acting agent's state
    """
    app_id: str
    field_path: str
    operator: str = "eq"
    value: Any = None
    agent_relative: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "field_path": self.field_path,
            "operator": self.operator,
            "value": self.value,
            "agent_relative": self.agent_relative,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateCondition":
        """Create from dictionary."""
        return cls(
            app_id=data["app_id"],
            field_path=data["field_path"],
            operator=data.get("operator", "eq"),
            value=data.get("value"),
            agent_relative=data.get("agent_relative", True),
        )

    def evaluate(self, state: dict[str, Any], agent_id: str | None = None) -> bool:
        """Evaluate condition against state.

        Args:
            state: Full app state dict
            agent_id: Agent ID if agent_relative is True

        Returns:
            True if condition is satisfied
        """
        # Navigate to the field
        current = state.get(self.app_id, {})

        if self.agent_relative and agent_id:
            # Look in per_agent state
            per_agent = current.get("per_agent", {})
            current = per_agent.get(agent_id, {})

        for part in self.field_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                current = None
                break

        # Apply operator
        if self.operator == "exists":
            return current is not None
        elif self.operator == "eq":
            return current == self.value
        elif self.operator == "ne":
            return current != self.value
        elif self.operator == "gt":
            return current is not None and current > self.value
        elif self.operator == "gte":
            return current is not None and current >= self.value
        elif self.operator == "lt":
            return current is not None and current < self.value
        elif self.operator == "lte":
            return current is not None and current <= self.value

        return False


@dataclass
class AtomicTaskComponent:
    """A single atomic action that can compose into complex tasks.

    Atomic components are extracted from app action definitions and
    represent the smallest unit of work in a task.

    Attributes:
        component_id: Unique identifier for this component
        action_type: Type of action (check, toggle, transfer, confirm, update)
        app_id: App this component operates on
        action_name: Name of the action to execute
        description: Human-readable description
        preconditions: State conditions that must be true before execution
        postconditions: State conditions that will be true after execution
        required_role: Role that must perform this action
        params_template: Template for action parameters
        estimated_steps: Estimated simulation steps for this component
    """
    component_id: str
    action_type: ActionType
    app_id: str
    action_name: str
    description: str = ""
    preconditions: list[StateCondition] = field(default_factory=list)
    postconditions: list[StateCondition] = field(default_factory=list)
    required_role: str = "peer"
    params_template: dict[str, Any] = field(default_factory=dict)
    estimated_steps: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component_id": self.component_id,
            "action_type": self.action_type.value,
            "app_id": self.app_id,
            "action_name": self.action_name,
            "description": self.description,
            "preconditions": [p.to_dict() for p in self.preconditions],
            "postconditions": [p.to_dict() for p in self.postconditions],
            "required_role": self.required_role,
            "params_template": self.params_template,
            "estimated_steps": self.estimated_steps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AtomicTaskComponent":
        """Create from dictionary."""
        return cls(
            component_id=data["component_id"],
            action_type=ActionType(data["action_type"]),
            app_id=data["app_id"],
            action_name=data["action_name"],
            description=data.get("description", ""),
            preconditions=[
                StateCondition.from_dict(p)
                for p in data.get("preconditions", [])
            ],
            postconditions=[
                StateCondition.from_dict(p)
                for p in data.get("postconditions", [])
            ],
            required_role=data.get("required_role", "peer"),
            params_template=data.get("params_template", {}),
            estimated_steps=data.get("estimated_steps", 1),
        )

    @classmethod
    def from_action_definition(
        cls,
        app_id: str,
        action: "ActionDefinition",
        required_role: str = "peer",
    ) -> "AtomicTaskComponent":
        """Create component from an app action definition.

        Analyzes the action's tool_type and logic blocks to infer
        action_type, preconditions, and postconditions.

        Args:
            app_id: ID of the app containing this action
            action: ActionDefinition from app schema
            required_role: Role that should perform this action

        Returns:
            AtomicTaskComponent derived from the action
        """
        from agentworld.apps.definition import ToolType, LogicBlockType

        # Determine action type from tool_type
        if action.tool_type == ToolType.READ:
            action_type = ActionType.CHECK
        else:
            # Analyze logic blocks to determine write type
            has_update = any(
                b.type == LogicBlockType.UPDATE
                for b in action.logic
            )
            action_type = ActionType.UPDATE if has_update else ActionType.CONFIRM

        # Extract preconditions from validate blocks
        preconditions = []
        for block in action.logic:
            if block.type == LogicBlockType.VALIDATE:
                # Parse condition string to create StateCondition
                # This is simplified - full implementation would parse expressions
                preconditions.append(StateCondition(
                    app_id=app_id,
                    field_path="",  # Would parse from block.condition
                    operator="exists",
                ))

        # Extract postconditions from update blocks
        postconditions = []
        for block in action.logic:
            if block.type == LogicBlockType.UPDATE:
                target = getattr(block, "target", "")
                value = getattr(block, "value", None)
                postconditions.append(StateCondition(
                    app_id=app_id,
                    field_path=target,
                    operator="eq",
                    value=value,
                ))

        # Build params template from parameter specs
        params_template = {}
        for param_name, param_spec in action.parameters.items():
            if param_spec.default is not None:
                params_template[param_name] = param_spec.default
            elif param_spec.required:
                # Mark as placeholder
                params_template[param_name] = f"<{param_name}>"

        return cls(
            component_id=f"{app_id}_{action.name}",
            action_type=action_type,
            app_id=app_id,
            action_name=action.name,
            description=action.description,
            preconditions=preconditions,
            postconditions=postconditions,
            required_role=required_role,
            params_template=params_template,
            estimated_steps=1,
        )


@dataclass
class TaskComposition:
    """A sequence of components forming a complete task.

    Attributes:
        components: Ordered list of atomic components
        handoff_points: Indices where control transfers between roles
        initial_state: Starting state for the task
        goal_state: Expected final state
    """
    components: list[AtomicTaskComponent] = field(default_factory=list)
    handoff_points: list[int] = field(default_factory=list)
    initial_state: dict[str, Any] = field(default_factory=dict)
    goal_state: dict[str, Any] = field(default_factory=dict)

    @property
    def complexity(self) -> int:
        """Task complexity based on number of components."""
        return len(self.components)

    @property
    def handoff_count(self) -> int:
        """Number of role handoffs in task."""
        return len(self.handoff_points)

    def validate_chain(self) -> tuple[bool, list[str]]:
        """Validate that components form a valid chain.

        Checks that each component's preconditions are satisfied by
        either the initial state or previous components' postconditions.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        satisfied_conditions: set[str] = set()

        # Add initial state conditions as satisfied
        for app_id, app_state in self.initial_state.items():
            for field, value in self._flatten_state(app_state):
                satisfied_conditions.add(f"{app_id}.{field}")

        # Check each component
        for i, component in enumerate(self.components):
            # Check preconditions
            for pre in component.preconditions:
                condition_key = f"{pre.app_id}.{pre.field_path}"
                if condition_key not in satisfied_conditions and pre.operator != "exists":
                    errors.append(
                        f"Component {i} ({component.component_id}): "
                        f"Unsatisfied precondition {condition_key}"
                    )

            # Add postconditions to satisfied
            for post in component.postconditions:
                satisfied_conditions.add(f"{post.app_id}.{post.field_path}")

        return len(errors) == 0, errors

    def _flatten_state(self, state: dict, prefix: str = "") -> list[tuple[str, Any]]:
        """Flatten nested state dict into list of (path, value) tuples."""
        items = []
        for key, value in state.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                items.extend(self._flatten_state(value, path))
            else:
                items.append((path, value))
        return items


class CompositionalTaskGenerator:
    """Generates complex tasks from atomic components.

    The generator maintains a registry of atomic components extracted from
    app definitions and can compose them into valid task sequences with
    specified complexity and handoff patterns.

    Example:
        >>> generator = CompositionalTaskGenerator()
        >>> generator.register_components_from_app(airline_app)
        >>> generator.register_components_from_app(paypal_app)
        >>>
        >>> task = generator.generate(
        ...     domain="airline",
        ...     complexity=3,
        ...     handoffs=2,
        ... )
    """

    def __init__(self):
        """Initialize the generator."""
        self._components: dict[str, AtomicTaskComponent] = {}
        self._components_by_domain: dict[str, list[str]] = {}
        self._components_by_role: dict[str, list[str]] = {}
        self._components_by_type: dict[ActionType, list[str]] = {
            action_type: [] for action_type in ActionType
        }

    def register_component(self, component: AtomicTaskComponent) -> None:
        """Register a single atomic component.

        Args:
            component: Component to register
        """
        self._components[component.component_id] = component
        self._components_by_type[component.action_type].append(component.component_id)

        role = component.required_role
        if role not in self._components_by_role:
            self._components_by_role[role] = []
        self._components_by_role[role].append(component.component_id)

    def register_components_from_app(
        self,
        app: "AppDefinition",
        domain: str | None = None,
        role_mapping: dict[str, str] | None = None,
    ) -> list[AtomicTaskComponent]:
        """Extract and register components from an app definition.

        Analyzes the app's actions to create atomic components with
        inferred preconditions, postconditions, and action types.

        Args:
            app: AppDefinition to extract components from
            domain: Domain label for these components
            role_mapping: Optional mapping of action names to required roles

        Returns:
            List of created components
        """
        from agentworld.apps.definition import ToolType

        domain = domain or app.category.value
        if domain not in self._components_by_domain:
            self._components_by_domain[domain] = []

        role_mapping = role_mapping or {}
        created = []

        for action in app.actions:
            # Determine role - default to service_agent for WRITE, customer for READ
            if action.name in role_mapping:
                role = role_mapping[action.name]
            elif action.tool_type == ToolType.READ:
                role = "customer"
            else:
                role = "service_agent"

            component = AtomicTaskComponent.from_action_definition(
                app_id=app.app_id,
                action=action,
                required_role=role,
            )

            self.register_component(component)
            self._components_by_domain[domain].append(component.component_id)
            created.append(component)

        return created

    def generate(
        self,
        domain: str | None = None,
        complexity: int = 2,
        handoffs: int = 1,
        seed: int | None = None,
        required_components: list[str] | None = None,
    ) -> "DualControlTaskDefinition":
        """Generate a task from composed components.

        Args:
            domain: Domain to select components from (None = all)
            complexity: Number of atomic components to include
            handoffs: Number of role handoffs to include
            seed: Random seed for reproducibility
            required_components: Component IDs that must be included

        Returns:
            DualControlTaskDefinition ready for evaluation
        """
        from agentworld.tasks.dual_control import (
            DualControlTaskDefinition,
            CoordinationHandoff,
        )

        if seed is not None:
            random.seed(seed)

        # Select component pool
        if domain and domain in self._components_by_domain:
            pool = self._components_by_domain[domain]
        else:
            pool = list(self._components.keys())

        # Ensure required components are included
        selected_ids = list(required_components or [])

        # Add remaining components to reach complexity
        remaining = [c for c in pool if c not in selected_ids]
        additional_needed = max(0, complexity - len(selected_ids))
        if additional_needed > 0 and remaining:
            selected_ids.extend(
                random.sample(remaining, min(additional_needed, len(remaining)))
            )

        # Get component objects
        selected = [self._components[cid] for cid in selected_ids if cid in self._components]

        if not selected:
            raise ValueError(f"No components available for domain={domain}")

        # Sort components to create valid chain (simplified)
        # Full implementation would use precondition/postcondition analysis
        composition = self._compose_chain(selected, handoffs)

        # Generate initial and goal states
        initial_state = self._generate_initial_state(composition)
        goal_state = self._generate_goal_state(composition)

        # Create task definition
        task_id = f"gen_{uuid.uuid4().hex[:8]}"

        # Build app lists
        agent_apps = self._get_apps_for_role("service_agent", composition.components)
        user_apps = self._get_apps_for_role("customer", composition.components)

        # Extract app IDs as strings
        agent_app_ids = [app.get("id", "") for app in agent_apps]
        user_app_ids = [app.get("id", "") for app in user_apps]

        # Build coordination handoffs
        handoff_list = self._build_handoffs(composition)

        from agentworld.apps.definition import AgentRole

        return DualControlTaskDefinition(
            task_id=task_id,
            name=f"Generated Task ({domain or 'mixed'})",
            description=f"Auto-generated task with complexity={complexity}, handoffs={handoffs}",
            domain=domain or "mixed",
            difficulty=self._calculate_difficulty(complexity, handoffs),
            simulation_config={"topology": "direct", "max_turns": 20},
            agent_id="service_agent",
            agent_role=AgentRole.SERVICE_AGENT,
            agent_instruction="Help the user complete the task",
            agent_apps=agent_app_ids,
            agent_initial_state=initial_state,
            agent_goal_state=goal_state,
            user_id="customer",
            user_role=AgentRole.CUSTOMER,
            user_instruction=self._generate_user_request(composition),
            user_apps=user_app_ids,
            user_initial_state=initial_state,
            user_goal_state=goal_state,
            required_handoffs=handoff_list,
            expected_coordination_count=len(handoff_list),
        )

    def _compose_chain(
        self,
        components: list[AtomicTaskComponent],
        target_handoffs: int,
    ) -> TaskComposition:
        """Arrange components into a valid chain with specified handoffs.

        Args:
            components: Components to arrange
            target_handoffs: Target number of role handoffs

        Returns:
            TaskComposition with ordered components and handoff points
        """
        if not components:
            return TaskComposition()

        # Sort by action type (CHECK before UPDATE before CONFIRM)
        type_order = {
            ActionType.CHECK: 0,
            ActionType.UPDATE: 1,
            ActionType.TOGGLE: 2,
            ActionType.TRANSFER: 3,
            ActionType.CONFIRM: 4,
        }
        sorted_components = sorted(
            components,
            key=lambda c: type_order.get(c.action_type, 5)
        )

        # Identify handoff points (role changes)
        handoff_points = []
        current_role = sorted_components[0].required_role if sorted_components else None

        for i, comp in enumerate(sorted_components[1:], 1):
            if comp.required_role != current_role:
                handoff_points.append(i)
                current_role = comp.required_role

        return TaskComposition(
            components=sorted_components,
            handoff_points=handoff_points[:target_handoffs],
        )

    def _generate_initial_state(self, composition: TaskComposition) -> dict[str, Any]:
        """Generate initial state that satisfies first component's preconditions."""
        initial = {}

        for component in composition.components:
            if component.app_id not in initial:
                initial[component.app_id] = {"per_agent": {}, "shared": {}}

            # Satisfy preconditions
            for pre in component.preconditions:
                if pre.field_path and pre.value is not None:
                    self._set_nested(initial[component.app_id], pre.field_path, pre.value)

        return initial

    def _generate_goal_state(self, composition: TaskComposition) -> dict[str, Any]:
        """Generate goal state from final postconditions."""
        goal = copy.deepcopy(composition.initial_state)

        for component in composition.components:
            for post in component.postconditions:
                if post.app_id not in goal:
                    goal[post.app_id] = {"per_agent": {}, "shared": {}}
                if post.field_path and post.value is not None:
                    self._set_nested(goal[post.app_id], post.field_path, post.value)

        return goal

    def _set_nested(self, d: dict, path: str, value: Any) -> None:
        """Set a value in a nested dict by path."""
        parts = path.split(".")
        current = d
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        if parts:
            current[parts[-1]] = value

    def _get_apps_for_role(
        self,
        role: str,
        components: list[AtomicTaskComponent],
    ) -> list[dict[str, Any]]:
        """Get app configs for components matching a role."""
        apps = {}
        for comp in components:
            if comp.required_role == role and comp.app_id not in apps:
                apps[comp.app_id] = {"id": comp.app_id}
        return list(apps.values())

    def _generate_user_request(self, composition: TaskComposition) -> str:
        """Generate initial user request based on task components."""
        if not composition.components:
            return "I need help with something."

        # Use first component's description
        first = composition.components[0]
        return f"I need help with: {first.description or first.action_name}"

    def _build_handoffs(
        self,
        composition: TaskComposition,
    ) -> list["CoordinationHandoff"]:
        """Build CoordinationHandoff objects from composition."""
        from agentworld.tasks.dual_control import CoordinationHandoff, InstructionTemplate
        from agentworld.apps.definition import AgentRole

        handoffs = []
        for i, comp in enumerate(composition.components):
            if i in composition.handoff_points or comp.required_role == "customer":
                # Create instruction template with keywords from component
                keywords = comp.action_name.replace("_", " ").split()
                template = InstructionTemplate(
                    template_id=f"gen_{comp.component_id}",
                    keywords=keywords[:2] if keywords else ["do"],
                    target_keywords=[comp.app_id.replace("_", " ")],
                    canonical_instruction=f"Please {comp.description or comp.action_name}",
                )
                handoffs.append(CoordinationHandoff(
                    handoff_id=f"handoff_{i}_{comp.component_id}",
                    from_role=AgentRole.SERVICE_AGENT,
                    to_role=AgentRole.CUSTOMER,
                    expected_action=f"{comp.app_id}.{comp.action_name}",
                    description=comp.description,
                    instruction_template=template,
                ))
        return handoffs

    def _calculate_difficulty(self, complexity: int, handoffs: int) -> str:
        """Calculate difficulty label from task parameters."""
        score = complexity + (handoffs * 2)
        if score <= 3:
            return "easy"
        elif score <= 6:
            return "medium"
        else:
            return "hard"

    def list_components(
        self,
        domain: str | None = None,
        role: str | None = None,
        action_type: ActionType | None = None,
    ) -> list[AtomicTaskComponent]:
        """List registered components with optional filtering.

        Args:
            domain: Filter by domain
            role: Filter by required role
            action_type: Filter by action type

        Returns:
            List of matching components
        """
        result = list(self._components.values())

        if domain and domain in self._components_by_domain:
            domain_ids = set(self._components_by_domain[domain])
            result = [c for c in result if c.component_id in domain_ids]

        if role and role in self._components_by_role:
            role_ids = set(self._components_by_role[role])
            result = [c for c in result if c.component_id in role_ids]

        if action_type:
            type_ids = set(self._components_by_type.get(action_type, []))
            result = [c for c in result if c.component_id in type_ids]

        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize generator state to dictionary."""
        return {
            "components": {
                cid: comp.to_dict()
                for cid, comp in self._components.items()
            },
            "domains": self._components_by_domain,
            "roles": self._components_by_role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompositionalTaskGenerator":
        """Create generator from serialized state."""
        generator = cls()

        for cid, comp_data in data.get("components", {}).items():
            component = AtomicTaskComponent.from_dict(comp_data)
            generator.register_component(component)

        # Restore domain mappings
        for domain, comp_ids in data.get("domains", {}).items():
            generator._components_by_domain[domain] = comp_ids

        return generator
