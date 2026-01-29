"""Goal evaluation engine for dual-control simulations.

Evaluates GoalSpec conditions against simulation state to determine
if goals have been achieved.

Example:
    >>> evaluator = GoalEvaluator()
    >>> result = evaluator.evaluate(
    ...     goal_spec=spec,
    ...     app_states={"paypal_test": {"balance": 450}},
    ...     action_log=[{"app_id": "paypal_test", "action": "dispute_transaction"}],
    ... )
    >>> print(f"Goal achieved: {result.achieved}")
"""

from __future__ import annotations

import logging
import re
from typing import Any

from agentworld.goals.types import (
    GoalType,
    GoalOperator,
    GoalCondition,
    GoalSpec,
    GoalEvaluationResult,
    ConditionResult,
)

logger = logging.getLogger(__name__)


class GoalEvaluator:
    """Evaluates goal conditions against simulation state.

    Thread-safe and stateless - can be reused across evaluations.
    """

    def __init__(self) -> None:
        """Initialize the evaluator."""
        pass

    def evaluate(
        self,
        goal_spec: GoalSpec,
        app_states: dict[str, dict[str, Any]],
        action_log: list[dict[str, Any]] | None = None,
        handoff_log: list[dict[str, Any]] | None = None,
        output_log: list[dict[str, Any]] | None = None,
        current_step: int = 0,
    ) -> GoalEvaluationResult:
        """Evaluate all goal conditions.

        Args:
            goal_spec: Goal specification to evaluate
            app_states: Current app states {app_id: {field: value}}
            action_log: List of executed actions [{app_id, action, success, ...}]
            handoff_log: List of completed handoffs [{handoff_id, ...}]
            output_log: List of agent outputs [{agent_id, content, ...}]
            current_step: Current simulation step number

        Returns:
            GoalEvaluationResult with achieved status and condition details
        """
        if not goal_spec.conditions:
            return GoalEvaluationResult(
                achieved=True,
                condition_results=[],
                details="No conditions to evaluate",
            )

        action_log = action_log or []
        handoff_log = handoff_log or []
        output_log = output_log or []

        results: list[ConditionResult] = []

        for condition in goal_spec.conditions:
            result = self._evaluate_condition(
                condition=condition,
                app_states=app_states,
                action_log=action_log,
                handoff_log=handoff_log,
                output_log=output_log,
                current_step=current_step,
            )
            results.append(result)

        # Determine if goal is achieved based on success_mode
        if goal_spec.success_mode == "all":
            achieved = all(r.met for r in results)
        else:  # "any"
            achieved = any(r.met for r in results)

        step_achieved = current_step if achieved else None

        return GoalEvaluationResult(
            achieved=achieved,
            condition_results=results,
            step_achieved=step_achieved,
            details=self._generate_summary(results, goal_spec.success_mode),
        )

    def _evaluate_condition(
        self,
        condition: GoalCondition,
        app_states: dict[str, dict[str, Any]],
        action_log: list[dict[str, Any]],
        handoff_log: list[dict[str, Any]],
        output_log: list[dict[str, Any]],
        current_step: int,
    ) -> ConditionResult:
        """Evaluate a single goal condition.

        Args:
            condition: The condition to evaluate
            app_states: Current app states
            action_log: Executed actions
            handoff_log: Completed handoffs
            output_log: Agent outputs
            current_step: Current step

        Returns:
            ConditionResult with met status and details
        """
        goal_type = condition.goal_type

        # State-based goals
        if goal_type in (
            GoalType.STATE_EQUALS,
            GoalType.STATE_CONTAINS,
            GoalType.STATE_GREATER,
            GoalType.STATE_LESS,
            GoalType.STATE_EXISTS,
        ):
            return self._evaluate_state_condition(condition, app_states, current_step)

        # Action-based goals
        if goal_type in (GoalType.ACTION_EXECUTED, GoalType.ACTION_SUCCEEDED):
            return self._evaluate_action_condition(condition, action_log, current_step)

        # Coordination-based goals
        if goal_type in (GoalType.HANDOFF_COMPLETED, GoalType.ALL_HANDOFFS_DONE):
            return self._evaluate_handoff_condition(condition, handoff_log, current_step)

        # Output-based goals
        if goal_type == GoalType.OUTPUT_CONTAINS:
            return self._evaluate_output_condition(condition, output_log, current_step)

        # Unknown goal type
        return ConditionResult(
            condition=condition,
            met=False,
            details=f"Unknown goal type: {goal_type}",
        )

    def _evaluate_state_condition(
        self,
        condition: GoalCondition,
        app_states: dict[str, dict[str, Any]],
        current_step: int,
    ) -> ConditionResult:
        """Evaluate a state-based goal condition."""
        app_id = condition.app_id
        if not app_id or app_id not in app_states:
            return ConditionResult(
                condition=condition,
                met=False,
                details=f"App '{app_id}' not found in states",
            )

        app_state = app_states[app_id]
        actual_value = self._get_nested_value(app_state, condition.field_path)

        met = False
        details = ""

        if condition.goal_type == GoalType.STATE_EXISTS:
            met = actual_value is not None
            details = f"Field {'exists' if met else 'does not exist'}"

        elif condition.goal_type == GoalType.STATE_EQUALS:
            met = self._compare_values(actual_value, condition.expected_value, condition.operator)
            details = f"Expected {condition.expected_value}, got {actual_value}"

        elif condition.goal_type == GoalType.STATE_CONTAINS:
            met = self._check_contains(actual_value, condition.expected_value)
            details = f"Checking if {actual_value} contains {condition.expected_value}"

        elif condition.goal_type == GoalType.STATE_GREATER:
            met = self._compare_numeric(actual_value, condition.expected_value, ">")
            details = f"Checking if {actual_value} > {condition.expected_value}"

        elif condition.goal_type == GoalType.STATE_LESS:
            met = self._compare_numeric(actual_value, condition.expected_value, "<")
            details = f"Checking if {actual_value} < {condition.expected_value}"

        return ConditionResult(
            condition=condition,
            met=met,
            actual_value=actual_value,
            step_met=current_step if met else None,
            details=details,
        )

    def _evaluate_action_condition(
        self,
        condition: GoalCondition,
        action_log: list[dict[str, Any]],
        current_step: int,
    ) -> ConditionResult:
        """Evaluate an action-based goal condition."""
        expected_action = condition.expected_value
        app_id = condition.app_id

        matching_actions = [
            a for a in action_log
            if (not app_id or a.get("app_id") == app_id)
            and a.get("action") == expected_action
        ]

        if condition.goal_type == GoalType.ACTION_EXECUTED:
            met = len(matching_actions) > 0
            details = f"Action '{expected_action}' {'was' if met else 'was not'} executed"

        elif condition.goal_type == GoalType.ACTION_SUCCEEDED:
            successful = [a for a in matching_actions if a.get("success", False)]
            met = len(successful) > 0
            details = f"Action '{expected_action}' {'succeeded' if met else 'did not succeed'}"

        else:
            met = False
            details = f"Unknown action goal type"

        return ConditionResult(
            condition=condition,
            met=met,
            actual_value=matching_actions[-1] if matching_actions else None,
            step_met=current_step if met else None,
            details=details,
        )

    def _evaluate_handoff_condition(
        self,
        condition: GoalCondition,
        handoff_log: list[dict[str, Any]],
        current_step: int,
    ) -> ConditionResult:
        """Evaluate a coordination-based goal condition."""
        if condition.goal_type == GoalType.HANDOFF_COMPLETED:
            handoff_id = condition.handoff_id
            matching = [h for h in handoff_log if h.get("handoff_id") == handoff_id]
            successful = [h for h in matching if h.get("success", False)]
            met = len(successful) > 0
            details = f"Handoff '{handoff_id}' {'completed' if met else 'not completed'}"

        elif condition.goal_type == GoalType.ALL_HANDOFFS_DONE:
            # This requires knowing all expected handoffs - typically from task definition
            # For now, check if there are any handoffs marked as required
            required_handoffs = [h for h in handoff_log if h.get("required", True)]
            completed = [h for h in required_handoffs if h.get("success", False)]
            met = len(completed) == len(required_handoffs) if required_handoffs else True
            details = f"Completed {len(completed)}/{len(required_handoffs)} required handoffs"

        else:
            met = False
            details = "Unknown handoff goal type"

        return ConditionResult(
            condition=condition,
            met=met,
            step_met=current_step if met else None,
            details=details,
        )

    def _evaluate_output_condition(
        self,
        condition: GoalCondition,
        output_log: list[dict[str, Any]],
        current_step: int,
    ) -> ConditionResult:
        """Evaluate an output-based goal condition."""
        required_phrase = condition.required_phrase or ""

        # Search for phrase in agent outputs
        for output in output_log:
            content = output.get("content", "")
            if required_phrase.lower() in content.lower():
                return ConditionResult(
                    condition=condition,
                    met=True,
                    actual_value=content[:100] + "..." if len(content) > 100 else content,
                    step_met=output.get("step", current_step),
                    details=f"Found phrase '{required_phrase}' in output",
                )

        return ConditionResult(
            condition=condition,
            met=False,
            details=f"Phrase '{required_phrase}' not found in any output",
        )

    def _get_nested_value(
        self,
        data: dict[str, Any],
        path: str | None,
    ) -> Any:
        """Get a value from nested dict using dot notation.

        Args:
            data: Dictionary to search
            path: Path like "bookings.ABC123.seat" or just "balance"

        Returns:
            Value at path or None if not found
        """
        if not path:
            return None

        parts = path.split(".")
        current = data

        for part in parts:
            if not isinstance(current, dict):
                return None
            if part not in current:
                return None
            current = current[part]

        return current

    def _compare_values(
        self,
        actual: Any,
        expected: Any,
        operator: GoalOperator,
    ) -> bool:
        """Compare two values using the specified operator."""
        if operator == GoalOperator.EQUALS:
            return actual == expected
        elif operator == GoalOperator.NOT_EQUALS:
            return actual != expected
        elif operator == GoalOperator.CONTAINS:
            return self._check_contains(actual, expected)
        elif operator == GoalOperator.NOT_CONTAINS:
            return not self._check_contains(actual, expected)
        elif operator == GoalOperator.GT:
            return self._compare_numeric(actual, expected, ">")
        elif operator == GoalOperator.LT:
            return self._compare_numeric(actual, expected, "<")
        elif operator == GoalOperator.GTE:
            return self._compare_numeric(actual, expected, ">=")
        elif operator == GoalOperator.LTE:
            return self._compare_numeric(actual, expected, "<=")
        elif operator == GoalOperator.EXISTS:
            return actual is not None
        elif operator == GoalOperator.NOT_EXISTS:
            return actual is None
        return False

    def _check_contains(self, container: Any, item: Any) -> bool:
        """Check if container contains item."""
        if container is None:
            return False

        # String contains string
        if isinstance(container, str) and isinstance(item, str):
            return item.lower() in container.lower()

        # List/set contains item
        if isinstance(container, (list, set, tuple)):
            return item in container

        # Dict contains key
        if isinstance(container, dict):
            return item in container

        return False

    def _compare_numeric(self, actual: Any, expected: Any, op: str) -> bool:
        """Compare two values numerically."""
        try:
            actual_num = float(actual) if actual is not None else None
            expected_num = float(expected) if expected is not None else None

            if actual_num is None or expected_num is None:
                return False

            if op == ">":
                return actual_num > expected_num
            elif op == "<":
                return actual_num < expected_num
            elif op == ">=":
                return actual_num >= expected_num
            elif op == "<=":
                return actual_num <= expected_num
            return False

        except (TypeError, ValueError):
            return False

    def _generate_summary(
        self,
        results: list[ConditionResult],
        success_mode: str,
    ) -> str:
        """Generate a summary of the evaluation results."""
        met_count = sum(1 for r in results if r.met)
        total_count = len(results)

        mode_text = "all" if success_mode == "all" else "any"
        return f"{met_count}/{total_count} conditions met (mode: {mode_text})"
