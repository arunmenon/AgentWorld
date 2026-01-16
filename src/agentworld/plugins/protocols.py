"""Plugin protocol interfaces per ADR-014."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import networkx as nx

    from agentworld.agents.agent import Agent
    from agentworld.core.message import Message


@dataclass
class ParameterSpec:
    """Specification for a plugin parameter."""

    name: str
    type: str  # "int", "float", "str", "bool", "list", "dict"
    description: str
    required: bool = True
    default: Any = None
    min_value: float | None = None
    max_value: float | None = None
    choices: list[Any] | None = None

    def validate(self, value: Any) -> tuple[bool, str]:
        """
        Validate a value against this parameter spec.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if self.required:
                return False, f"Parameter '{self.name}' is required"
            return True, ""

        # Type validation
        type_map = {
            "int": int,
            "float": (int, float),
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        expected_type = type_map.get(self.type)
        if expected_type and not isinstance(value, expected_type):
            return False, f"Parameter '{self.name}' must be {self.type}, got {type(value).__name__}"

        # Range validation
        if self.min_value is not None and isinstance(value, (int, float)):
            if value < self.min_value:
                return False, f"Parameter '{self.name}' must be >= {self.min_value}"

        if self.max_value is not None and isinstance(value, (int, float)):
            if value > self.max_value:
                return False, f"Parameter '{self.name}' must be <= {self.max_value}"

        # Choices validation
        if self.choices is not None and value not in self.choices:
            return False, f"Parameter '{self.name}' must be one of {self.choices}"

        return True, ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "choices": self.choices,
        }


@dataclass
class ValidationContext:
    """Context for validation operations."""

    simulation_step: int = 0
    agent_id: str = ""
    previous_responses: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result from a validation operation."""

    valid: bool
    score: float  # 0.0 to 1.0
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TopologyPlugin(Protocol):
    """Protocol for topology plugins."""

    @property
    def name(self) -> str:
        """Unique topology name (e.g., 'lattice', 'erdos_renyi')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    def build(self, agent_ids: list[str], **kwargs: Any) -> "nx.Graph":
        """Build the topology graph."""
        ...

    def get_parameters(self) -> list[ParameterSpec]:
        """Describe configurable parameters."""
        ...


@runtime_checkable
class ScenarioPlugin(Protocol):
    """Protocol for scenario plugins."""

    @property
    def name(self) -> str:
        """Unique scenario name."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    async def setup(self, world: Any, config: dict[str, Any]) -> None:
        """Configure world and agents for this scenario."""
        ...

    async def run(self, world: Any) -> Any:
        """Execute the scenario."""
        ...

    def get_config_schema(self) -> dict[str, Any]:
        """JSON Schema for scenario configuration."""
        ...


@runtime_checkable
class ValidatorPlugin(Protocol):
    """Protocol for validator plugins."""

    @property
    def name(self) -> str:
        """Unique validator name."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    async def validate(
        self,
        agent: "Agent",
        response: str,
        context: ValidationContext,
    ) -> ValidationResult:
        """Validate agent response."""
        ...


@runtime_checkable
class ExtractorPlugin(Protocol):
    """Protocol for extractor plugins."""

    @property
    def name(self) -> str:
        """Unique extractor name."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    async def extract(
        self,
        messages: list["Message"],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured data from messages."""
        ...


@runtime_checkable
class AgentToolPlugin(Protocol):
    """Protocol for tools agents can use."""

    @property
    def name(self) -> str:
        """Unique tool name."""
        ...

    @property
    def description(self) -> str:
        """Description for agent's tool selection."""
        ...

    def get_schema(self) -> dict[str, Any]:
        """JSON Schema for tool parameters."""
        ...

    async def execute(self, **params: Any) -> str:
        """Execute the tool and return result."""
        ...


@runtime_checkable
class LLMProviderPlugin(Protocol):
    """Protocol for custom LLM provider plugins."""

    @property
    def name(self) -> str:
        """Unique provider name."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate completion from messages."""
        ...

    def get_models(self) -> list[str]:
        """List available models for this provider."""
        ...


@runtime_checkable
class OutputFormatPlugin(Protocol):
    """Protocol for output format plugins."""

    @property
    def name(self) -> str:
        """Unique format name (e.g., 'parquet', 'arrow')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    @property
    def file_extension(self) -> str:
        """File extension for this format."""
        ...

    def export(self, data: Any, path: str, **kwargs: Any) -> None:
        """Export data to file in this format."""
        ...

    def load(self, path: str, **kwargs: Any) -> Any:
        """Load data from file in this format."""
        ...
