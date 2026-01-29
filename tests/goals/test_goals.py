"""Tests for the goal evaluation system."""

import pytest
from agentworld.goals.types import (
    GoalType,
    GoalOperator,
    GoalCondition,
    GoalSpec,
    GoalEvaluationResult,
)
from agentworld.goals.evaluator import GoalEvaluator


class TestGoalType:
    """Test GoalType enum."""

    def test_state_goal_types(self):
        """Test state-based goal types exist."""
        assert GoalType.STATE_EQUALS.value == "state_equals"
        assert GoalType.STATE_CONTAINS.value == "state_contains"
        assert GoalType.STATE_GREATER.value == "state_greater"
        assert GoalType.STATE_EXISTS.value == "state_exists"

    def test_action_goal_types(self):
        """Test action-based goal types exist."""
        assert GoalType.ACTION_EXECUTED.value == "action_executed"
        assert GoalType.ACTION_SUCCEEDED.value == "action_succeeded"

    def test_coordination_goal_types(self):
        """Test coordination-based goal types exist."""
        assert GoalType.HANDOFF_COMPLETED.value == "handoff_completed"
        assert GoalType.ALL_HANDOFFS_DONE.value == "all_handoffs_done"

    def test_output_goal_types(self):
        """Test output-based goal types exist."""
        assert GoalType.OUTPUT_CONTAINS.value == "output_contains"


class TestGoalCondition:
    """Test GoalCondition dataclass."""

    def test_state_equals_condition(self):
        """Test creating a state_equals condition."""
        condition = GoalCondition(
            goal_type=GoalType.STATE_EQUALS,
            description="Balance should be 450",
            app_id="paypal",
            field_path="balance",
            operator=GoalOperator.EQUALS,
            expected_value=450,
        )
        assert condition.goal_type == GoalType.STATE_EQUALS
        assert condition.app_id == "paypal"
        assert condition.expected_value == 450

    def test_action_executed_condition(self):
        """Test creating an action_executed condition."""
        condition = GoalCondition(
            goal_type=GoalType.ACTION_EXECUTED,
            description="Dispute action should be called",
            app_id="paypal",
            expected_value="dispute_transaction",
        )
        assert condition.goal_type == GoalType.ACTION_EXECUTED
        assert condition.expected_value == "dispute_transaction"

    def test_to_dict(self):
        """Test serializing condition to dict."""
        condition = GoalCondition(
            goal_type=GoalType.STATE_EQUALS,
            description="Test",
            app_id="test_app",
            field_path="field1",
            expected_value=100,
        )
        d = condition.to_dict()
        assert d["goal_type"] == "state_equals"
        assert d["app_id"] == "test_app"
        assert d["expected_value"] == 100

    def test_from_dict(self):
        """Test deserializing condition from dict."""
        data = {
            "goal_type": "action_executed",
            "description": "Action test",
            "app_id": "test_app",
            "expected_value": "do_something",
        }
        condition = GoalCondition.from_dict(data)
        assert condition.goal_type == GoalType.ACTION_EXECUTED
        assert condition.expected_value == "do_something"


class TestGoalSpec:
    """Test GoalSpec dataclass."""

    def test_empty_spec(self):
        """Test creating empty goal spec."""
        spec = GoalSpec()
        assert spec.conditions == []
        assert spec.success_mode == "all"

    def test_spec_with_conditions(self):
        """Test creating spec with conditions."""
        conditions = [
            GoalCondition(
                goal_type=GoalType.STATE_EQUALS,
                description="Test 1",
                app_id="app1",
                expected_value=1,
            ),
            GoalCondition(
                goal_type=GoalType.ACTION_EXECUTED,
                description="Test 2",
                app_id="app2",
                expected_value="action1",
            ),
        ]
        spec = GoalSpec(conditions=conditions, success_mode="any")
        assert len(spec.conditions) == 2
        assert spec.success_mode == "any"

    def test_to_dict_and_from_dict(self):
        """Test serialization round trip."""
        original = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Test",
                    app_id="app1",
                    expected_value=100,
                )
            ],
            success_mode="all",
            description="Test goal",
        )
        d = original.to_dict()
        restored = GoalSpec.from_dict(d)
        assert len(restored.conditions) == 1
        assert restored.success_mode == "all"
        assert restored.description == "Test goal"

    def test_from_legacy_goal_state(self):
        """Test converting legacy goal_state format."""
        legacy = {
            "paypal": {"balance": 450, "status": "active"},
            "booking": {"confirmed": True},
        }
        spec = GoalSpec.from_legacy_goal_state(legacy, "Test conversion")
        assert len(spec.conditions) == 3
        assert spec.success_mode == "all"
        assert spec.description == "Test conversion"


class TestGoalEvaluator:
    """Test GoalEvaluator class."""

    def test_empty_spec_achieves(self):
        """Test that empty spec is considered achieved."""
        evaluator = GoalEvaluator()
        spec = GoalSpec()
        result = evaluator.evaluate(spec, {})
        assert result.achieved is True

    def test_state_equals_met(self):
        """Test state_equals condition met."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Balance check",
                    app_id="paypal",
                    field_path="balance",
                    expected_value=450,
                )
            ]
        )
        app_states = {"paypal": {"balance": 450}}
        result = evaluator.evaluate(spec, app_states)
        assert result.achieved is True
        assert result.met_count == 1

    def test_state_equals_not_met(self):
        """Test state_equals condition not met."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Balance check",
                    app_id="paypal",
                    field_path="balance",
                    expected_value=450,
                )
            ]
        )
        app_states = {"paypal": {"balance": 500}}
        result = evaluator.evaluate(spec, app_states)
        assert result.achieved is False
        assert result.met_count == 0

    def test_state_contains_string(self):
        """Test state_contains with string."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_CONTAINS,
                    description="Status contains disputed",
                    app_id="paypal",
                    field_path="status",
                    expected_value="disputed",
                )
            ]
        )
        app_states = {"paypal": {"status": "Transaction disputed successfully"}}
        result = evaluator.evaluate(spec, app_states)
        assert result.achieved is True

    def test_state_greater(self):
        """Test state_greater comparison."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_GREATER,
                    description="Balance > 100",
                    app_id="paypal",
                    field_path="balance",
                    expected_value=100,
                )
            ]
        )
        app_states = {"paypal": {"balance": 150}}
        result = evaluator.evaluate(spec, app_states)
        assert result.achieved is True

    def test_state_exists(self):
        """Test state_exists condition."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EXISTS,
                    description="Dispute ID exists",
                    app_id="paypal",
                    field_path="dispute_id",
                )
            ]
        )
        app_states = {"paypal": {"dispute_id": "DSP123"}}
        result = evaluator.evaluate(spec, app_states)
        assert result.achieved is True

        # Test when field doesn't exist
        app_states_no_field = {"paypal": {}}
        result2 = evaluator.evaluate(spec, app_states_no_field)
        assert result2.achieved is False

    def test_action_executed(self):
        """Test action_executed condition."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.ACTION_EXECUTED,
                    description="Dispute was called",
                    app_id="paypal",
                    expected_value="dispute_transaction",
                )
            ]
        )
        action_log = [
            {"app_id": "paypal", "action": "dispute_transaction", "success": True}
        ]
        result = evaluator.evaluate(spec, {}, action_log=action_log)
        assert result.achieved is True

    def test_action_succeeded(self):
        """Test action_succeeded requires success flag."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.ACTION_SUCCEEDED,
                    description="Dispute succeeded",
                    app_id="paypal",
                    expected_value="dispute_transaction",
                )
            ]
        )
        # Action failed
        action_log_fail = [
            {"app_id": "paypal", "action": "dispute_transaction", "success": False}
        ]
        result1 = evaluator.evaluate(spec, {}, action_log=action_log_fail)
        assert result1.achieved is False

        # Action succeeded
        action_log_success = [
            {"app_id": "paypal", "action": "dispute_transaction", "success": True}
        ]
        result2 = evaluator.evaluate(spec, {}, action_log=action_log_success)
        assert result2.achieved is True

    def test_output_contains(self):
        """Test output_contains condition."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.OUTPUT_CONTAINS,
                    description="Agent said refund",
                    required_phrase="your refund",
                )
            ]
        )
        output_log = [
            {"agent_id": "agent1", "content": "Your refund has been initiated."}
        ]
        result = evaluator.evaluate(spec, {}, output_log=output_log)
        assert result.achieved is True

    def test_success_mode_all(self):
        """Test success_mode='all' requires all conditions."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Cond 1",
                    app_id="app1",
                    field_path="a",
                    expected_value=1,
                ),
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Cond 2",
                    app_id="app1",
                    field_path="b",
                    expected_value=2,
                ),
            ],
            success_mode="all",
        )
        # Only first met
        result1 = evaluator.evaluate(spec, {"app1": {"a": 1, "b": 0}})
        assert result1.achieved is False
        assert result1.met_count == 1

        # Both met
        result2 = evaluator.evaluate(spec, {"app1": {"a": 1, "b": 2}})
        assert result2.achieved is True
        assert result2.met_count == 2

    def test_success_mode_any(self):
        """Test success_mode='any' requires at least one condition."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Cond 1",
                    app_id="app1",
                    field_path="a",
                    expected_value=1,
                ),
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Cond 2",
                    app_id="app1",
                    field_path="b",
                    expected_value=2,
                ),
            ],
            success_mode="any",
        )
        # First met
        result1 = evaluator.evaluate(spec, {"app1": {"a": 1, "b": 0}})
        assert result1.achieved is True

        # Neither met
        result2 = evaluator.evaluate(spec, {"app1": {"a": 0, "b": 0}})
        assert result2.achieved is False

    def test_nested_field_path(self):
        """Test accessing nested fields via dot notation."""
        evaluator = GoalEvaluator()
        spec = GoalSpec(
            conditions=[
                GoalCondition(
                    goal_type=GoalType.STATE_EQUALS,
                    description="Nested field",
                    app_id="booking",
                    field_path="bookings.ABC123.seat",
                    expected_value="12A",
                )
            ]
        )
        app_states = {
            "booking": {
                "bookings": {
                    "ABC123": {"seat": "12A", "status": "confirmed"}
                }
            }
        }
        result = evaluator.evaluate(spec, app_states)
        assert result.achieved is True


class TestGoalEvaluationResult:
    """Test GoalEvaluationResult."""

    def test_conditions_met_property(self):
        """Test conditions_met tuple list."""
        from agentworld.goals.types import ConditionResult

        result = GoalEvaluationResult(
            achieved=True,
            condition_results=[
                ConditionResult(
                    condition=GoalCondition(
                        goal_type=GoalType.STATE_EQUALS,
                        description="Cond 1",
                    ),
                    met=True,
                ),
                ConditionResult(
                    condition=GoalCondition(
                        goal_type=GoalType.STATE_EQUALS,
                        description="Cond 2",
                    ),
                    met=False,
                ),
            ],
        )
        assert result.conditions_met == [("Cond 1", True), ("Cond 2", False)]
        assert result.met_count == 1
        assert result.total_count == 2

    def test_to_dict(self):
        """Test serialization."""
        result = GoalEvaluationResult(
            achieved=True,
            step_achieved=5,
            details="All conditions met",
        )
        d = result.to_dict()
        assert d["achieved"] is True
        assert d["step_achieved"] == 5
