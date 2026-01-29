"""Goal type definitions for dual-control simulations.

Provides a structured taxonomy of goal types for defining success criteria
in τ²-bench style evaluations per ADR-020.1.

Goal Types:
    - State-based: Check app data (equals, contains, greater, exists)
    - Action-based: Check what actions were executed
    - Coordination-based: Check agent-user handoffs
    - Output-based: Check what agent said

Example:
    >>> from agentworld.goals.types import GoalType, GoalCondition, GoalSpec
    >>> condition = GoalCondition(
    ...     goal_type=GoalType.ACTION_EXECUTED,
    ...     description="User must call the dispute action",
    ...     app_id="paypal_test",
    ...     expected_value="dispute_transaction",
    ... )
    >>> spec = GoalSpec(conditions=[condition], success_mode="all")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class GoalType(str, Enum):
    """Taxonomy of goal types for dual-control tasks.

    Categories:
        State Goals: Check app data values
        Action Goals: Check what user did
        Coordination Goals: Check agent-user interaction
        Output Goals: Check what agent said
    """

    # State-based goals (checking app data)
    STATE_EQUALS = "state_equals"       # App field equals expected value
    STATE_CONTAINS = "state_contains"   # App field contains substring/item
    STATE_GREATER = "state_greater"     # Numeric comparison (>)
    STATE_LESS = "state_less"           # Numeric comparison (<)
    STATE_EXISTS = "state_exists"       # Field exists (not None)

    # Action-based goals (checking what user did)
    ACTION_EXECUTED = "action_executed"   # Specific app action was called
    ACTION_SUCCEEDED = "action_succeeded" # Action was called AND returned success

    # Coordination-based goals (checking agent-user interaction)
    HANDOFF_COMPLETED = "handoff_completed"   # Specific handoff happened
    ALL_HANDOFFS_DONE = "all_handoffs_done"   # All required handoffs done

    # Output-based goals (checking what agent said)
    OUTPUT_CONTAINS = "output_contains"  # Agent said specific phrase


class GoalOperator(str, Enum):
    """Comparison operators for goal conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


@dataclass
class GoalCondition:
    """A single goal condition to check.

    Represents one atomic success criterion that can be evaluated
    against simulation state.

    Attributes:
        goal_type: Type of goal (state, action, coordination, output)
        description: Human-readable description of the condition
        app_id: App ID for state/action goals
        field_path: Path to field in app state (e.g., "balance" or "bookings.ABC123.seat")
        operator: Comparison operator for state goals
        expected_value: Expected value for comparison
        handoff_id: Handoff ID for coordination goals
        required_phrase: Required phrase for output goals
    """

    goal_type: GoalType
    description: str

    # For state/action goals
    app_id: str | None = None
    field_path: str | None = None
    operator: GoalOperator = GoalOperator.EQUALS
    expected_value: Any = None

    # For handoff goals
    handoff_id: str | None = None

    # For output goals
    required_phrase: str | None = None

    # Internal tracking
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "goal_type": self.goal_type.value,
            "description": self.description,
            "app_id": self.app_id,
            "field_path": self.field_path,
            "operator": self.operator.value,
            "expected_value": self.expected_value,
            "handoff_id": self.handoff_id,
            "required_phrase": self.required_phrase,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalCondition":
        """Create from dictionary."""
        goal_type = data.get("goal_type", GoalType.STATE_EQUALS)
        if isinstance(goal_type, str):
            goal_type = GoalType(goal_type)

        operator = data.get("operator", GoalOperator.EQUALS)
        if isinstance(operator, str):
            operator = GoalOperator(operator)

        return cls(
            id=data.get("id"),
            goal_type=goal_type,
            description=data.get("description", ""),
            app_id=data.get("app_id"),
            field_path=data.get("field_path"),
            operator=operator,
            expected_value=data.get("expected_value"),
            handoff_id=data.get("handoff_id"),
            required_phrase=data.get("required_phrase"),
        )


@dataclass
class GoalSpec:
    """Complete goal specification for a task.

    Contains all goal conditions and the success mode (all/any).

    Attributes:
        conditions: List of goal conditions to evaluate
        success_mode: "all" requires all conditions, "any" requires at least one
        description: Overall goal description
    """

    conditions: list[GoalCondition] = field(default_factory=list)
    success_mode: Literal["all", "any"] = "all"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "success_mode": self.success_mode,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalSpec":
        """Create from dictionary."""
        conditions_data = data.get("conditions", [])
        conditions = [
            GoalCondition.from_dict(c) if isinstance(c, dict) else c
            for c in conditions_data
        ]

        return cls(
            conditions=conditions,
            success_mode=data.get("success_mode", "all"),
            description=data.get("description", ""),
        )

    @classmethod
    def from_legacy_goal_state(
        cls,
        goal_state: dict[str, Any],
        description: str = "",
    ) -> "GoalSpec":
        """Convert legacy goal_state dict to GoalSpec.

        Used for backwards compatibility with existing tasks that use
        the unstructured goal_state format.

        Args:
            goal_state: Legacy format like {"app_id": {"field": value}}
            description: Goal description

        Returns:
            Equivalent GoalSpec with state_equals conditions
        """
        conditions = []

        for app_id, fields in goal_state.items():
            if isinstance(fields, dict):
                for field_name, expected_value in fields.items():
                    conditions.append(GoalCondition(
                        goal_type=GoalType.STATE_EQUALS,
                        description=f"{app_id}.{field_name} should equal {expected_value}",
                        app_id=app_id,
                        field_path=field_name,
                        operator=GoalOperator.EQUALS,
                        expected_value=expected_value,
                    ))

        return cls(
            conditions=conditions,
            success_mode="all",
            description=description,
        )


@dataclass
class ConditionResult:
    """Result of evaluating a single goal condition."""

    condition: GoalCondition
    met: bool
    actual_value: Any = None
    step_met: int | None = None
    details: str = ""


@dataclass
class GoalEvaluationResult:
    """Result of evaluating all goal conditions.

    Attributes:
        achieved: Whether the goal was achieved (per success_mode)
        conditions_met: List of (condition_description, was_met) tuples
        step_achieved: Step number when goal was achieved (if achieved)
        details: Additional details about the evaluation
    """

    achieved: bool
    condition_results: list[ConditionResult] = field(default_factory=list)
    step_achieved: int | None = None
    details: str = ""

    @property
    def conditions_met(self) -> list[tuple[str, bool]]:
        """Get list of (description, met) tuples for backwards compatibility."""
        return [
            (r.condition.description, r.met)
            for r in self.condition_results
        ]

    @property
    def met_count(self) -> int:
        """Count of conditions that are met."""
        return sum(1 for r in self.condition_results if r.met)

    @property
    def total_count(self) -> int:
        """Total number of conditions."""
        return len(self.condition_results)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "achieved": self.achieved,
            "conditions_met": self.conditions_met,
            "met_count": self.met_count,
            "total_count": self.total_count,
            "step_achieved": self.step_achieved,
            "details": self.details,
        }
