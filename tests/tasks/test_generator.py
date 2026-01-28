"""Tests for compositional task generator.

Tests the τ²-bench atomic component and task composition per ADR-020.1.
"""

import pytest
from unittest.mock import MagicMock

from agentworld.tasks.generator import (
    ActionType,
    StateCondition,
    AtomicTaskComponent,
    TaskComposition,
    CompositionalTaskGenerator,
)


class TestStateCondition:
    """Tests for StateCondition."""

    def test_creation(self):
        """Test state condition creation."""
        cond = StateCondition(
            app_id="test_app",
            field_path="balance",
            operator="gte",
            value=100,
        )
        assert cond.app_id == "test_app"
        assert cond.operator == "gte"
        assert cond.value == 100

    def test_serialization(self):
        """Test to_dict and from_dict."""
        cond = StateCondition(
            app_id="app1",
            field_path="status",
            operator="eq",
            value="active",
        )

        data = cond.to_dict()
        restored = StateCondition.from_dict(data)

        assert restored.app_id == cond.app_id
        assert restored.field_path == cond.field_path
        assert restored.operator == cond.operator
        assert restored.value == cond.value

    def test_evaluate_eq(self):
        """Test equality evaluation."""
        cond = StateCondition(
            app_id="app1",
            field_path="status",
            operator="eq",
            value="active",
            agent_relative=False,
        )

        state = {"app1": {"status": "active"}}
        assert cond.evaluate(state) is True

        state = {"app1": {"status": "inactive"}}
        assert cond.evaluate(state) is False

    def test_evaluate_gt(self):
        """Test greater-than evaluation."""
        cond = StateCondition(
            app_id="app1",
            field_path="balance",
            operator="gt",
            value=50,
            agent_relative=False,
        )

        state = {"app1": {"balance": 100}}
        assert cond.evaluate(state) is True

        state = {"app1": {"balance": 50}}
        assert cond.evaluate(state) is False

    def test_evaluate_exists(self):
        """Test exists operator."""
        cond = StateCondition(
            app_id="app1",
            field_path="data",
            operator="exists",
            agent_relative=False,
        )

        state = {"app1": {"data": "something"}}
        assert cond.evaluate(state) is True

        state = {"app1": {}}
        assert cond.evaluate(state) is False


class TestAtomicTaskComponent:
    """Tests for AtomicTaskComponent."""

    def test_creation(self):
        """Test component creation."""
        comp = AtomicTaskComponent(
            component_id="test_check",
            action_type=ActionType.CHECK,
            app_id="test_app",
            action_name="check_balance",
            description="Check account balance",
        )

        assert comp.component_id == "test_check"
        assert comp.action_type == ActionType.CHECK
        assert comp.app_id == "test_app"

    def test_serialization(self):
        """Test to_dict and from_dict."""
        comp = AtomicTaskComponent(
            component_id="comp1",
            action_type=ActionType.UPDATE,
            app_id="app1",
            action_name="update_status",
            required_role="service_agent",
            preconditions=[
                StateCondition(app_id="app1", field_path="active", value=True)
            ],
        )

        data = comp.to_dict()
        restored = AtomicTaskComponent.from_dict(data)

        assert restored.component_id == comp.component_id
        assert restored.action_type == comp.action_type
        assert len(restored.preconditions) == 1

    def test_from_action_definition(self):
        """Test creating component from action definition."""
        from agentworld.apps.definition import (
            ActionDefinition,
            ToolType,
            ParamSpecDef,
            ParamType,
        )

        # Create mock action
        action = ActionDefinition(
            name="check_balance",
            description="Check user balance",
            logic=[],
            parameters={"account_id": ParamSpecDef(type=ParamType.STRING, required=True)},
            tool_type=ToolType.READ,
        )

        comp = AtomicTaskComponent.from_action_definition(
            app_id="paypal",
            action=action,
            required_role="customer",
        )

        assert comp.component_id == "paypal_check_balance"
        assert comp.action_type == ActionType.CHECK
        assert comp.required_role == "customer"


class TestTaskComposition:
    """Tests for TaskComposition."""

    def test_complexity(self):
        """Test complexity calculation."""
        comp1 = AtomicTaskComponent(
            component_id="c1",
            action_type=ActionType.CHECK,
            app_id="app1",
            action_name="check",
        )
        comp2 = AtomicTaskComponent(
            component_id="c2",
            action_type=ActionType.UPDATE,
            app_id="app1",
            action_name="update",
        )

        composition = TaskComposition(components=[comp1, comp2])
        assert composition.complexity == 2

    def test_handoff_count(self):
        """Test handoff count."""
        composition = TaskComposition(
            components=[],
            handoff_points=[1, 3, 5],
        )
        assert composition.handoff_count == 3

    def test_validate_chain_empty(self):
        """Test validation of empty chain."""
        composition = TaskComposition()
        valid, errors = composition.validate_chain()
        assert valid is True
        assert errors == []


class TestCompositionalTaskGenerator:
    """Tests for CompositionalTaskGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a generator instance."""
        return CompositionalTaskGenerator()

    def test_register_component(self, generator):
        """Test component registration."""
        comp = AtomicTaskComponent(
            component_id="test_comp",
            action_type=ActionType.CHECK,
            app_id="test_app",
            action_name="test_action",
            required_role="customer",
        )

        generator.register_component(comp)
        assert "test_comp" in generator._components

    def test_list_components(self, generator):
        """Test listing components with filters."""
        comp1 = AtomicTaskComponent(
            component_id="check1",
            action_type=ActionType.CHECK,
            app_id="app1",
            action_name="check",
            required_role="customer",
        )
        comp2 = AtomicTaskComponent(
            component_id="update1",
            action_type=ActionType.UPDATE,
            app_id="app1",
            action_name="update",
            required_role="service_agent",
        )

        generator.register_component(comp1)
        generator.register_component(comp2)

        # Filter by role
        customer_comps = generator.list_components(role="customer")
        assert len(customer_comps) == 1
        assert customer_comps[0].component_id == "check1"

        # Filter by action type
        check_comps = generator.list_components(action_type=ActionType.CHECK)
        assert len(check_comps) == 1

    def test_register_from_app(self, generator):
        """Test registering components from app definition."""
        from agentworld.apps.definition import (
            AppDefinition,
            AppCategory,
            ActionDefinition,
            ToolType,
        )

        app = AppDefinition(
            app_id="test_airline",
            name="Test Airline",
            category=AppCategory.CUSTOM,
            actions=[
                ActionDefinition(
                    name="lookup_booking",
                    description="Look up booking",
                    logic=[],
                    tool_type=ToolType.READ,
                ),
                ActionDefinition(
                    name="change_seat",
                    description="Change seat",
                    logic=[],
                    tool_type=ToolType.WRITE,
                ),
            ],
        )

        components = generator.register_components_from_app(app, domain="airline")

        assert len(components) == 2
        assert "airline" in generator._components_by_domain

    def test_generate_task(self, generator):
        """Test task generation."""
        # Register some components
        comp1 = AtomicTaskComponent(
            component_id="lookup",
            action_type=ActionType.CHECK,
            app_id="airline",
            action_name="lookup_booking",
            required_role="service_agent",
        )
        comp2 = AtomicTaskComponent(
            component_id="confirm",
            action_type=ActionType.CONFIRM,
            app_id="airline",
            action_name="confirm_change",
            required_role="customer",
        )

        generator.register_component(comp1)
        generator.register_component(comp2)
        generator._components_by_domain["airline"] = ["lookup", "confirm"]

        # Generate task
        task = generator.generate(
            domain="airline",
            complexity=2,
            handoffs=1,
            seed=42,
        )

        assert task.task_id.startswith("gen_")
        assert task.domain == "airline"
        assert "airline" in task.name.lower() or "mixed" in task.name.lower()

    def test_serialization(self, generator):
        """Test generator serialization."""
        comp = AtomicTaskComponent(
            component_id="test",
            action_type=ActionType.CHECK,
            app_id="app",
            action_name="action",
        )
        generator.register_component(comp)

        data = generator.to_dict()
        restored = CompositionalTaskGenerator.from_dict(data)

        assert "test" in restored._components

    def test_calculate_difficulty(self, generator):
        """Test difficulty calculation.

        Formula: score = complexity + (handoffs * 2)
        - score <= 3: easy
        - score <= 6: medium
        - score > 6: hard
        """
        assert generator._calculate_difficulty(1, 0) == "easy"   # 1 + 0 = 1
        assert generator._calculate_difficulty(2, 0) == "easy"   # 2 + 0 = 2
        assert generator._calculate_difficulty(3, 0) == "easy"   # 3 + 0 = 3
        assert generator._calculate_difficulty(2, 1) == "medium" # 2 + 2 = 4
        assert generator._calculate_difficulty(4, 1) == "medium" # 4 + 2 = 6
        assert generator._calculate_difficulty(4, 2) == "hard"   # 4 + 4 = 8
