"""App definition dataclasses for dynamic apps.

This module defines the JSON-serializable data structures for app definitions
that can be stored in a database and executed by the DynamicApp engine.

Per ADR-018 and ADR-019.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


# ==============================================================================
# Enums
# ==============================================================================


class AppCategory(str, Enum):
    """Valid app categories."""

    PAYMENT = "payment"
    SHOPPING = "shopping"
    COMMUNICATION = "communication"
    CALENDAR = "calendar"
    SOCIAL = "social"
    CUSTOM = "custom"


class AppAccessType(str, Enum):
    """Who can access this app.

    Per ADR-020.1 for τ²-bench dual-control support.
    """
    SHARED = "shared"                    # All agents (current default)
    ROLE_RESTRICTED = "role_restricted"  # Only specific roles
    PER_AGENT = "per_agent"              # Each agent has their own instance


class AppStateType(str, Enum):
    """How state is managed.

    Per ADR-020.1 for τ²-bench dual-control support.
    """
    SHARED = "shared"       # Single state for all agents
    PER_AGENT = "per_agent" # Each agent has isolated state


class ToolType(str, Enum):
    """Tool classification for analysis and policy.

    Per ADR-020.1 for τ²-bench dual-control support.
    """
    READ = "read"   # Queries state, no modifications
    WRITE = "write" # Modifies state


class AgentRole(str, Enum):
    """Built-in agent roles for dual-control scenarios.

    Per ADR-020.1 for τ²-bench dual-control support.
    """
    PEER = "peer"                    # Default: equal access to shared apps
    SERVICE_AGENT = "service_agent"  # Backend access, guides users
    CUSTOMER = "customer"            # Device access, follows instructions


class ParamType(str, Enum):
    """Valid parameter types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class LogicBlockType(str, Enum):
    """Valid logic block types."""

    VALIDATE = "validate"
    UPDATE = "update"
    NOTIFY = "notify"
    RETURN = "return"
    ERROR = "error"
    BRANCH = "branch"
    LOOP = "loop"


class UpdateOperation(str, Enum):
    """Valid update operations."""

    SET = "set"
    ADD = "add"
    SUBTRACT = "subtract"
    APPEND = "append"
    REMOVE = "remove"
    MERGE = "merge"


# ==============================================================================
# Parameter Specification
# ==============================================================================


@dataclass
class ParamSpecDef:
    """Parameter specification for an action.

    Matches ADR-019 ParamSpec schema.
    """

    type: ParamType
    description: str = ""
    required: bool = False
    default: Any = None
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "type": self.type.value if isinstance(self.type, ParamType) else self.type,
        }
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = self.required
        if self.default is not None:
            result["default"] = self.default
        if self.min_value is not None:
            result["minValue"] = self.min_value
        if self.max_value is not None:
            result["maxValue"] = self.max_value
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.pattern is not None:
            result["pattern"] = self.pattern
        if self.enum is not None:
            result["enum"] = self.enum
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParamSpecDef":
        """Create from dictionary."""
        return cls(
            type=ParamType(data["type"]) if isinstance(data["type"], str) else data["type"],
            description=data.get("description", ""),
            required=data.get("required", False),
            default=data.get("default"),
            min_value=data.get("minValue"),
            max_value=data.get("maxValue"),
            min_length=data.get("minLength"),
            max_length=data.get("maxLength"),
            pattern=data.get("pattern"),
            enum=data.get("enum"),
        )


# ==============================================================================
# State Field Specification
# ==============================================================================


@dataclass
class StateFieldDef:
    """State field definition.

    Defines a field in the app state schema.

    Per τ²-bench integration (ADR-020.1):
    - observable: Whether user agents can see this field in state-constrained mode.
      When True, the field value is included in the user's observable state,
      allowing state-constrained user simulators to respond only based on
      what they can actually "see" on their device.
    """

    name: str
    type: ParamType
    default: Any = None
    per_agent: bool = True  # If False, it's shared state
    description: str = ""
    observable: bool = True  # NEW: Whether user can see this field (τ²-bench)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type.value if isinstance(self.type, ParamType) else self.type,
        }
        if self.default is not None:
            result["default"] = self.default
        if not self.per_agent:
            result["perAgent"] = self.per_agent
        if self.description:
            result["description"] = self.description
        # Always include observable for τ²-bench state-constrained mode
        result["observable"] = self.observable
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateFieldDef":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type=ParamType(data["type"]) if isinstance(data["type"], str) else data["type"],
            default=data.get("default"),
            per_agent=data.get("perAgent", True),
            description=data.get("description", ""),
            observable=data.get("observable", True),  # Default True for backward compat
        )


# ==============================================================================
# Logic Blocks
# ==============================================================================


@dataclass
class LogicBlock:
    """Base class for logic blocks.

    Logic blocks define the business logic executed when an action is called.
    """

    type: LogicBlockType

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"type": self.type.value if isinstance(self.type, LogicBlockType) else self.type}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogicBlock":
        """Create appropriate LogicBlock subclass from dictionary."""
        block_type = data.get("type")

        if block_type == "validate":
            return ValidateBlock.from_dict(data)
        elif block_type == "update":
            return UpdateBlock.from_dict(data)
        elif block_type == "notify":
            return NotifyBlock.from_dict(data)
        elif block_type == "return":
            return ReturnBlock.from_dict(data)
        elif block_type == "error":
            return ErrorBlock.from_dict(data)
        elif block_type == "branch":
            return BranchBlock.from_dict(data)
        elif block_type == "loop":
            return LoopBlock.from_dict(data)
        else:
            raise ValueError(f"Unknown logic block type: {block_type}")


@dataclass
class ValidateBlock(LogicBlock):
    """Validation block - checks a condition.

    If condition is false, returns an error.
    """

    condition: str  # Expression that must be true
    error_message: str  # Message if validation fails

    def __init__(self, condition: str, error_message: str):
        super().__init__(type=LogicBlockType.VALIDATE)
        self.condition = condition
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["condition"] = self.condition
        result["errorMessage"] = self.error_message
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidateBlock":
        return cls(
            condition=data["condition"],
            error_message=data.get("errorMessage", data.get("error_message", "")),
        )


@dataclass
class UpdateBlock(LogicBlock):
    """Update block - modifies state.

    Operations: set, add, subtract, append, remove, merge
    """

    target: str  # State path to update (e.g., "agent.balance")
    operation: UpdateOperation
    value: Any  # Expression or literal value

    def __init__(self, target: str, operation: UpdateOperation | str, value: Any):
        super().__init__(type=LogicBlockType.UPDATE)
        self.target = target
        self.operation = UpdateOperation(operation) if isinstance(operation, str) else operation
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["target"] = self.target
        result["operation"] = self.operation.value if isinstance(self.operation, UpdateOperation) else self.operation
        result["value"] = self.value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdateBlock":
        return cls(
            target=data["target"],
            operation=UpdateOperation(data["operation"]),
            value=data["value"],
        )


@dataclass
class NotifyBlock(LogicBlock):
    """Notify block - sends observation to an agent."""

    to: str  # Expression for target agent ID
    message: str  # Message template (supports interpolation)
    data: dict[str, Any] | None = None  # Optional structured data

    def __init__(self, to: str, message: str, data: dict[str, Any] | None = None):
        super().__init__(type=LogicBlockType.NOTIFY)
        self.to = to
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["to"] = self.to
        result["message"] = self.message
        if self.data:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotifyBlock":
        return cls(
            to=data["to"],
            message=data["message"],
            data=data.get("data"),
        )


@dataclass
class ReturnBlock(LogicBlock):
    """Return block - returns success with data."""

    value: dict[str, Any]  # Return value (expressions evaluated)

    def __init__(self, value: dict[str, Any]):
        super().__init__(type=LogicBlockType.RETURN)
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["value"] = self.value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReturnBlock":
        return cls(value=data["value"])


@dataclass
class ErrorBlock(LogicBlock):
    """Error block - returns failure with message."""

    message: str  # Error message (may contain expressions)

    def __init__(self, message: str):
        super().__init__(type=LogicBlockType.ERROR)
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["message"] = self.message
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorBlock":
        return cls(message=data["message"])


@dataclass
class BranchBlock(LogicBlock):
    """Branch block - conditional execution."""

    condition: str  # Boolean expression
    then_blocks: list[LogicBlock]  # Blocks if true
    else_blocks: list[LogicBlock] | None = None  # Blocks if false (optional)

    def __init__(
        self,
        condition: str,
        then_blocks: list[LogicBlock],
        else_blocks: list[LogicBlock] | None = None,
    ):
        super().__init__(type=LogicBlockType.BRANCH)
        self.condition = condition
        self.then_blocks = then_blocks
        self.else_blocks = else_blocks

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["condition"] = self.condition
        result["then"] = [b.to_dict() for b in self.then_blocks]
        if self.else_blocks:
            result["else"] = [b.to_dict() for b in self.else_blocks]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BranchBlock":
        then_blocks = [LogicBlock.from_dict(b) for b in data.get("then", [])]
        else_data = data.get("else")
        else_blocks = [LogicBlock.from_dict(b) for b in else_data] if else_data else None
        return cls(
            condition=data["condition"],
            then_blocks=then_blocks,
            else_blocks=else_blocks,
        )


@dataclass
class LoopBlock(LogicBlock):
    """Loop block - iterate over collection."""

    collection: str  # Expression for array to iterate
    item: str  # Variable name for current item
    body: list[LogicBlock]  # Blocks to execute per item

    def __init__(self, collection: str, item: str, body: list[LogicBlock]):
        super().__init__(type=LogicBlockType.LOOP)
        self.collection = collection
        self.item = item
        self.body = body

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["collection"] = self.collection
        result["item"] = self.item
        result["body"] = [b.to_dict() for b in self.body]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoopBlock":
        body = [LogicBlock.from_dict(b) for b in data.get("body", [])]
        return cls(
            collection=data["collection"],
            item=data["item"],
            body=body,
        )


# ==============================================================================
# Action Definition
# ==============================================================================


@dataclass
class ActionDefinition:
    """Definition of a single action.

    Contains the action's parameters, return schema, and business logic.

    Per ADR-020.1, includes tool_type annotation for τ²-bench compatibility:
    - READ: Queries state, no modifications
    - WRITE: Modifies state
    """

    name: str
    description: str
    logic: list[LogicBlock]
    parameters: dict[str, ParamSpecDef] = field(default_factory=dict)
    returns: dict[str, Any] = field(default_factory=dict)
    tool_type: ToolType = ToolType.WRITE  # Default to WRITE for safety

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "description": self.description,
            "parameters": {k: v.to_dict() for k, v in self.parameters.items()},
            "returns": self.returns,
            "logic": [b.to_dict() for b in self.logic],
        }
        # Only include tool_type if not default (for backward compatibility)
        if self.tool_type != ToolType.WRITE:
            result["toolType"] = self.tool_type.value
        else:
            result["toolType"] = self.tool_type.value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionDefinition":
        """Create from dictionary."""
        parameters = {}
        for k, v in data.get("parameters", {}).items():
            parameters[k] = ParamSpecDef.from_dict(v)

        logic = [LogicBlock.from_dict(b) for b in data.get("logic", [])]

        # Parse tool_type with backward compatibility
        tool_type_str = data.get("toolType") or data.get("tool_type")
        tool_type = ToolType(tool_type_str) if tool_type_str else ToolType.WRITE

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=parameters,
            returns=data.get("returns", {}),
            logic=logic,
            tool_type=tool_type,
        )


# ==============================================================================
# Config Field Definition (for UI config forms)
# ==============================================================================


@dataclass
class ConfigFieldDef:
    """Configuration field definition for dynamic config forms."""

    name: str
    label: str
    type: Literal["string", "number", "boolean", "select"]
    description: str = ""
    default: Any = None
    required: bool = False
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    options: list[dict[str, str]] | None = None  # For select type: [{value, label}]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
        }
        if self.description:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        if self.required:
            result["required"] = self.required
        if self.min_value is not None:
            result["min"] = self.min_value
        if self.max_value is not None:
            result["max"] = self.max_value
        if self.step is not None:
            result["step"] = self.step
        if self.options is not None:
            result["options"] = self.options
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigFieldDef":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            label=data["label"],
            type=data["type"],
            description=data.get("description", ""),
            default=data.get("default"),
            required=data.get("required", False),
            min_value=data.get("min"),
            max_value=data.get("max"),
            step=data.get("step"),
            options=data.get("options"),
        )


# ==============================================================================
# App Definition
# ==============================================================================


# App ID pattern: snake_case, starts with letter, 2-50 chars
APP_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,49}$")


@dataclass
class AppDefinition:
    """JSON-serializable app definition.

    This is the complete definition of a dynamic app that can be
    stored in a database and executed by the DynamicApp engine.

    Per ADR-018 and ADR-019, extended per ADR-020.1 for τ²-bench support:
    - access_type: Who can access this app (SHARED, ROLE_RESTRICTED, PER_AGENT)
    - allowed_roles: Roles that can access when role_restricted (e.g., ["service_agent"])
    - allowed_role_tags: Additional tag-based access (e.g., ["supervisor", "admin"])
    - state_type: How state is managed (SHARED, PER_AGENT)
    """

    app_id: str
    name: str
    category: AppCategory
    actions: list[ActionDefinition]
    description: str = ""
    icon: str = ""  # Emoji or icon key
    state_schema: list[StateFieldDef] = field(default_factory=list)
    initial_config: dict[str, Any] = field(default_factory=dict)
    config_schema: list[ConfigFieldDef] = field(default_factory=list)  # For UI config forms

    # NEW: Access control (ADR-020.1, defaults for backward compatibility)
    access_type: AppAccessType = AppAccessType.SHARED
    allowed_roles: list[str] | None = None  # e.g., ["service_agent", "customer"]
    allowed_role_tags: list[str] | None = None  # e.g., ["supervisor", "admin"]

    # NEW: State management (ADR-020.1, defaults for backward compatibility)
    state_type: AppStateType = AppStateType.SHARED

    def __post_init__(self):
        """Validate app_id format and access/state combinations."""
        if not APP_ID_PATTERN.match(self.app_id):
            raise ValueError(
                f"Invalid app_id '{self.app_id}'. Must be snake_case, "
                "start with a letter, and be 2-50 characters."
            )

        # Validate access/state combinations per ADR-020.1
        if self.access_type == AppAccessType.PER_AGENT and self.state_type == AppStateType.SHARED:
            raise ValueError(
                "Invalid combination: access_type=PER_AGENT requires state_type=PER_AGENT. "
                "If each agent has own instance, state must be isolated."
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "app_id": self.app_id,
            "name": self.name,
            "category": self.category.value if isinstance(self.category, AppCategory) else self.category,
            "actions": [a.to_dict() for a in self.actions],
        }
        if self.description:
            result["description"] = self.description
        if self.icon:
            result["icon"] = self.icon
        if self.state_schema:
            result["state_schema"] = [s.to_dict() for s in self.state_schema]
        if self.initial_config:
            result["initial_config"] = self.initial_config
        if self.config_schema:
            result["config_schema"] = [c.to_dict() for c in self.config_schema]

        # NEW: Access control fields (always include for clarity)
        result["access_type"] = self.access_type.value if isinstance(self.access_type, AppAccessType) else self.access_type
        if self.allowed_roles:
            result["allowed_roles"] = self.allowed_roles
        if self.allowed_role_tags:
            result["allowed_role_tags"] = self.allowed_role_tags
        result["state_type"] = self.state_type.value if isinstance(self.state_type, AppStateType) else self.state_type

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppDefinition":
        """Create from dictionary."""
        actions = [ActionDefinition.from_dict(a) for a in data.get("actions", [])]
        state_schema = [StateFieldDef.from_dict(s) for s in data.get("state_schema", [])]
        config_schema = [ConfigFieldDef.from_dict(c) for c in data.get("config_schema", [])]

        # Parse access_type with backward compatibility (defaults to SHARED)
        access_type_str = data.get("access_type") or data.get("accessType")
        access_type = AppAccessType(access_type_str) if access_type_str else AppAccessType.SHARED

        # Parse state_type with backward compatibility (defaults to SHARED)
        state_type_str = data.get("state_type") or data.get("stateType")
        state_type = AppStateType(state_type_str) if state_type_str else AppStateType.SHARED

        return cls(
            app_id=data["app_id"],
            name=data["name"],
            category=AppCategory(data["category"]) if isinstance(data["category"], str) else data["category"],
            actions=actions,
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            state_schema=state_schema,
            initial_config=data.get("initial_config", {}),
            config_schema=config_schema,
            access_type=access_type,
            allowed_roles=data.get("allowed_roles") or data.get("allowedRoles"),
            allowed_role_tags=data.get("allowed_role_tags") or data.get("allowedRoleTags"),
            state_type=state_type,
        )

    def get_action(self, action_name: str) -> ActionDefinition | None:
        """Get an action definition by name."""
        for action in self.actions:
            if action.name == action_name:
                return action
        return None

    def get_action_names(self) -> list[str]:
        """Get list of action names."""
        return [a.name for a in self.actions]

    def can_agent_access(self, agent_role: str | AgentRole, agent_role_tags: list[str] | None = None) -> bool:
        """Check if an agent with given role can access this app.

        Per ADR-020.1 access control logic:
        - SHARED: All agents can access
        - ROLE_RESTRICTED: Only agents with matching role or role_tags
        - PER_AGENT: All agents can access (each gets own instance)

        Args:
            agent_role: Agent's primary role (AgentRole enum or string)
            agent_role_tags: Agent's additional role tags

        Returns:
            True if agent can access this app
        """
        # Normalize role to string
        if isinstance(agent_role, AgentRole):
            role_str = agent_role.value
        else:
            role_str = agent_role

        # SHARED and PER_AGENT always allow access
        if self.access_type in (AppAccessType.SHARED, AppAccessType.PER_AGENT):
            return True

        # ROLE_RESTRICTED: check primary role and role_tags
        if self.access_type == AppAccessType.ROLE_RESTRICTED:
            # Check primary role
            if self.allowed_roles and role_str in self.allowed_roles:
                return True

            # Check role tags
            if self.allowed_role_tags and agent_role_tags:
                if set(agent_role_tags) & set(self.allowed_role_tags):
                    return True

            return False

        return True  # Default allow for unknown access types


# ==============================================================================
# App State (canonical format per ADR-018)
# ==============================================================================


class AgentStateProxy(dict):
    """Dict-like wrapper that resolves agent names to IDs.

    Allows accessing agents by name (case-insensitive) or ID.
    When accessed by name, resolves to the actual agent ID's state.
    """

    def __init__(self, per_agent: dict[str, dict[str, Any]], name_to_id: dict[str, str]):
        super().__init__(per_agent)
        self._name_to_id = {k.lower(): v for k, v in name_to_id.items()}
        self._per_agent = per_agent

    def __getitem__(self, key: str) -> dict[str, Any]:
        # First try direct ID lookup
        if key in self._per_agent:
            return self._per_agent[key]
        # Then try name resolution (case-insensitive)
        resolved_id = self._name_to_id.get(key.lower())
        if resolved_id and resolved_id in self._per_agent:
            return self._per_agent[resolved_id]
        # Return empty dict for unknown agents (will be created on write)
        return {}

    def __setitem__(self, key: str, value: dict[str, Any]) -> None:
        # Resolve name to ID if possible
        resolved_id = self._name_to_id.get(key.lower(), key)
        self._per_agent[resolved_id] = value

    def get(self, key: str, default: Any = None) -> Any:
        try:
            result = self.__getitem__(key)
            return result if result else default
        except KeyError:
            return default


@dataclass
class AppState:
    """Canonical app state format.

    Per ADR-018:
    {
        "per_agent": {
            "agent_id": { ...agent-specific state... }
        },
        "shared": { ...shared state... }
    }
    """

    per_agent: dict[str, dict[str, Any]] = field(default_factory=dict)
    shared: dict[str, Any] = field(default_factory=dict)
    name_to_id: dict[str, str] = field(default_factory=dict)  # Maps agent names to IDs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "per_agent": self.per_agent,
            "shared": self.shared,
            "name_to_id": self.name_to_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppState":
        """Create from dictionary."""
        return cls(
            per_agent=data.get("per_agent", {}),
            shared=data.get("shared", {}),
            name_to_id=data.get("name_to_id", {}),
        )

    def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Get state for a specific agent."""
        return self.per_agent.get(agent_id, {})

    def set_agent_state(self, agent_id: str, state: dict[str, Any]) -> None:
        """Set state for a specific agent."""
        self.per_agent[agent_id] = state

    def ensure_agent(self, agent_id: str, defaults: dict[str, Any] | None = None) -> None:
        """Ensure agent has state entry, initializing with defaults if needed."""
        if agent_id not in self.per_agent:
            self.per_agent[agent_id] = dict(defaults or {})

    def register_agent_name(self, agent_id: str, name: str) -> None:
        """Register an agent name to ID mapping."""
        self.name_to_id[name.lower()] = agent_id

    def resolve_agent_id(self, key: str) -> str:
        """Resolve a name or ID to the actual agent ID."""
        # Try direct lookup first
        if key in self.per_agent:
            return key
        # Try name resolution (case-insensitive)
        return self.name_to_id.get(key.lower(), key)

    def get_agents_proxy(self) -> AgentStateProxy:
        """Get a proxy dict that resolves names to IDs."""
        return AgentStateProxy(self.per_agent, self.name_to_id)

    def deep_copy(self) -> "AppState":
        """Create a deep copy of the state."""
        import copy
        return AppState(
            per_agent=copy.deepcopy(self.per_agent),
            shared=copy.deepcopy(self.shared),
            name_to_id=copy.deepcopy(self.name_to_id),
        )
