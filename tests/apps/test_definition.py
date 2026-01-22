"""Tests for app definition dataclasses per ADR-018/019."""

import pytest

from agentworld.apps.definition import (
    AppDefinition,
    ActionDefinition,
    AppState,
    ParamSpecDef,
    StateFieldDef,
    ConfigFieldDef,
    LogicBlock,
    ValidateBlock,
    UpdateBlock,
    NotifyBlock,
    ReturnBlock,
    ErrorBlock,
    BranchBlock,
    LoopBlock,
    AppCategory,
    ParamType,
    LogicBlockType,
    UpdateOperation,
)


class TestAppCategory:
    """Tests for AppCategory enum."""

    def test_valid_categories(self):
        """Test all valid categories."""
        assert AppCategory.PAYMENT.value == "payment"
        assert AppCategory.SHOPPING.value == "shopping"
        assert AppCategory.COMMUNICATION.value == "communication"
        assert AppCategory.CALENDAR.value == "calendar"
        assert AppCategory.SOCIAL.value == "social"
        assert AppCategory.CUSTOM.value == "custom"

    def test_category_from_string(self):
        """Test creating category from string."""
        assert AppCategory("payment") == AppCategory.PAYMENT


class TestParamType:
    """Tests for ParamType enum."""

    def test_valid_types(self):
        """Test all valid types."""
        assert ParamType.STRING.value == "string"
        assert ParamType.NUMBER.value == "number"
        assert ParamType.BOOLEAN.value == "boolean"
        assert ParamType.ARRAY.value == "array"
        assert ParamType.OBJECT.value == "object"


class TestParamSpecDef:
    """Tests for ParamSpecDef dataclass."""

    def test_basic_param(self):
        """Test basic parameter creation."""
        param = ParamSpecDef(
            type=ParamType.STRING,
            description="User name",
            required=True,
        )
        assert param.type == ParamType.STRING
        assert param.description == "User name"
        assert param.required is True

    def test_param_with_constraints(self):
        """Test parameter with value constraints."""
        param = ParamSpecDef(
            type=ParamType.NUMBER,
            required=True,
            min_value=0.01,
            max_value=10000,
        )
        assert param.min_value == 0.01
        assert param.max_value == 10000

    def test_param_to_dict(self):
        """Test converting parameter to dictionary."""
        param = ParamSpecDef(
            type=ParamType.STRING,
            description="Test",
            required=True,
            min_length=1,
            max_length=100,
        )
        d = param.to_dict()

        assert d["type"] == "string"
        assert d["description"] == "Test"
        assert d["required"] is True
        assert d["minLength"] == 1
        assert d["maxLength"] == 100

    def test_param_from_dict(self):
        """Test creating parameter from dictionary."""
        d = {
            "type": "number",
            "description": "Amount",
            "required": True,
            "minValue": 0,
            "maxValue": 1000,
        }
        param = ParamSpecDef.from_dict(d)

        assert param.type == ParamType.NUMBER
        assert param.min_value == 0
        assert param.max_value == 1000


class TestStateFieldDef:
    """Tests for StateFieldDef dataclass."""

    def test_per_agent_field(self):
        """Test per-agent state field."""
        field = StateFieldDef(
            name="balance",
            type=ParamType.NUMBER,
            default=1000,
            per_agent=True,
        )
        assert field.name == "balance"
        assert field.per_agent is True
        assert field.default == 1000

    def test_shared_field(self):
        """Test shared state field."""
        field = StateFieldDef(
            name="counter",
            type=ParamType.NUMBER,
            default=0,
            per_agent=False,
        )
        assert field.per_agent is False

    def test_field_to_dict(self):
        """Test converting state field to dictionary."""
        field = StateFieldDef(
            name="items",
            type=ParamType.ARRAY,
            default=[],
            per_agent=True,
        )
        d = field.to_dict()

        assert d["name"] == "items"
        assert d["type"] == "array"
        assert d["default"] == []

    def test_field_from_dict(self):
        """Test creating state field from dictionary."""
        d = {
            "name": "balance",
            "type": "number",
            "default": 0,
            "perAgent": False,
        }
        field = StateFieldDef.from_dict(d)

        assert field.name == "balance"
        assert field.type == ParamType.NUMBER
        assert field.per_agent is False


class TestLogicBlocks:
    """Tests for logic block dataclasses."""

    def test_validate_block(self):
        """Test ValidateBlock creation."""
        block = ValidateBlock(
            condition="params.amount > 0",
            error_message="Amount must be positive",
        )
        assert block.type == LogicBlockType.VALIDATE
        assert block.condition == "params.amount > 0"

    def test_update_block(self):
        """Test UpdateBlock creation."""
        block = UpdateBlock(
            target="agent.balance",
            operation=UpdateOperation.SUBTRACT,
            value="params.amount",
        )
        assert block.type == LogicBlockType.UPDATE
        assert block.operation == UpdateOperation.SUBTRACT

    def test_notify_block(self):
        """Test NotifyBlock creation."""
        block = NotifyBlock(
            to="params.to",
            message="Hello!",
            data={"type": "greeting"},
        )
        assert block.type == LogicBlockType.NOTIFY
        assert block.data == {"type": "greeting"}

    def test_return_block(self):
        """Test ReturnBlock creation."""
        block = ReturnBlock(value={"status": "ok"})
        assert block.type == LogicBlockType.RETURN
        assert block.value == {"status": "ok"}

    def test_error_block(self):
        """Test ErrorBlock creation."""
        block = ErrorBlock(message="Something went wrong")
        assert block.type == LogicBlockType.ERROR
        assert block.message == "Something went wrong"

    def test_branch_block(self):
        """Test BranchBlock creation."""
        block = BranchBlock(
            condition="x > 0",
            then_blocks=[ReturnBlock(value={"result": "positive"})],
            else_blocks=[ReturnBlock(value={"result": "negative"})],
        )
        assert block.type == LogicBlockType.BRANCH
        assert len(block.then_blocks) == 1
        assert len(block.else_blocks) == 1

    def test_loop_block(self):
        """Test LoopBlock creation."""
        block = LoopBlock(
            collection="items",
            item="item",
            body=[
                NotifyBlock(to="item.user", message="Hello"),
            ],
        )
        assert block.type == LogicBlockType.LOOP
        assert block.item == "item"

    def test_logic_block_from_dict(self):
        """Test creating logic blocks from dict."""
        validate_dict = {
            "type": "validate",
            "condition": "x > 0",
            "errorMessage": "Must be positive",
        }
        block = LogicBlock.from_dict(validate_dict)
        assert isinstance(block, ValidateBlock)
        assert block.condition == "x > 0"

    def test_logic_block_to_dict(self):
        """Test converting logic blocks to dict."""
        block = UpdateBlock(
            target="agent.balance",
            operation=UpdateOperation.ADD,
            value="100",
        )
        d = block.to_dict()

        assert d["type"] == "update"
        assert d["target"] == "agent.balance"
        assert d["operation"] == "add"

    def test_nested_logic_blocks_serialization(self):
        """Test serializing nested logic blocks."""
        block = BranchBlock(
            condition="x > 0",
            then_blocks=[
                UpdateBlock(
                    target="result",
                    operation=UpdateOperation.SET,
                    value="'positive'",
                ),
                ReturnBlock(value={"done": "true"}),
            ],
            else_blocks=None,
        )

        d = block.to_dict()
        assert len(d["then"]) == 2
        assert d["then"][0]["type"] == "update"
        assert d["then"][1]["type"] == "return"


class TestActionDefinition:
    """Tests for ActionDefinition dataclass."""

    def test_basic_action(self):
        """Test basic action creation."""
        action = ActionDefinition(
            name="check_balance",
            description="Check account balance",
            logic=[ReturnBlock(value={"balance": "agent.balance"})],
        )
        assert action.name == "check_balance"
        assert len(action.logic) == 1

    def test_action_with_params(self):
        """Test action with parameters."""
        action = ActionDefinition(
            name="transfer",
            description="Transfer money",
            parameters={
                "to": ParamSpecDef(type=ParamType.STRING, required=True),
                "amount": ParamSpecDef(
                    type=ParamType.NUMBER,
                    required=True,
                    min_value=0.01,
                ),
            },
            logic=[],
        )
        assert "to" in action.parameters
        assert action.parameters["amount"].min_value == 0.01

    def test_action_to_dict(self):
        """Test converting action to dictionary."""
        action = ActionDefinition(
            name="test_action",
            description="Test",
            parameters={
                "param1": ParamSpecDef(type=ParamType.STRING),
            },
            logic=[ReturnBlock(value={})],
        )
        d = action.to_dict()

        assert d["name"] == "test_action"
        assert "param1" in d["parameters"]
        assert len(d["logic"]) == 1

    def test_action_from_dict(self):
        """Test creating action from dictionary."""
        d = {
            "name": "my_action",
            "description": "My action",
            "parameters": {
                "x": {"type": "number", "required": True},
            },
            "logic": [
                {"type": "return", "value": {"result": "x * 2"}},
            ],
        }
        action = ActionDefinition.from_dict(d)

        assert action.name == "my_action"
        assert "x" in action.parameters
        assert len(action.logic) == 1
        assert isinstance(action.logic[0], ReturnBlock)


class TestAppDefinition:
    """Tests for AppDefinition dataclass."""

    def test_valid_app_id(self):
        """Test valid app_id formats."""
        # Valid IDs
        app = AppDefinition(
            app_id="my_app",
            name="My App",
            category=AppCategory.CUSTOM,
            actions=[],
        )
        assert app.app_id == "my_app"

        app2 = AppDefinition(
            app_id="payment_app_v2",
            name="Payment App",
            category=AppCategory.PAYMENT,
            actions=[],
        )
        assert app2.app_id == "payment_app_v2"

    def test_invalid_app_id(self):
        """Test invalid app_id formats."""
        # Must start with letter
        with pytest.raises(ValueError):
            AppDefinition(
                app_id="1app",
                name="App",
                category=AppCategory.CUSTOM,
                actions=[],
            )

        # No uppercase
        with pytest.raises(ValueError):
            AppDefinition(
                app_id="MyApp",
                name="App",
                category=AppCategory.CUSTOM,
                actions=[],
            )

        # Too short
        with pytest.raises(ValueError):
            AppDefinition(
                app_id="a",
                name="App",
                category=AppCategory.CUSTOM,
                actions=[],
            )

    def test_full_app_definition(self):
        """Test creating a full app definition."""
        app = AppDefinition(
            app_id="test_payment",
            name="Test Payment",
            description="A test payment app",
            category=AppCategory.PAYMENT,
            icon="💳",
            actions=[
                ActionDefinition(
                    name="check_balance",
                    description="Check balance",
                    logic=[ReturnBlock(value={"balance": "agent.balance"})],
                ),
                ActionDefinition(
                    name="transfer",
                    description="Transfer money",
                    parameters={
                        "to": ParamSpecDef(type=ParamType.STRING, required=True),
                        "amount": ParamSpecDef(type=ParamType.NUMBER, required=True),
                    },
                    logic=[],
                ),
            ],
            state_schema=[
                StateFieldDef(name="balance", type=ParamType.NUMBER, default=1000),
                StateFieldDef(name="transactions", type=ParamType.ARRAY, default=[]),
            ],
            initial_config={"max_transfer": 10000},
        )

        assert app.app_id == "test_payment"
        assert len(app.actions) == 2
        assert len(app.state_schema) == 2

    def test_get_action(self):
        """Test getting action by name."""
        app = AppDefinition(
            app_id="test_app",
            name="Test",
            category=AppCategory.CUSTOM,
            actions=[
                ActionDefinition(name="action_a", description="A", logic=[]),
                ActionDefinition(name="action_b", description="B", logic=[]),
            ],
        )

        assert app.get_action("action_a").name == "action_a"
        assert app.get_action("action_b").description == "B"
        assert app.get_action("nonexistent") is None

    def test_get_action_names(self):
        """Test getting list of action names."""
        app = AppDefinition(
            app_id="test_app",
            name="Test",
            category=AppCategory.CUSTOM,
            actions=[
                ActionDefinition(name="a", description="A", logic=[]),
                ActionDefinition(name="b", description="B", logic=[]),
                ActionDefinition(name="c", description="C", logic=[]),
            ],
        )

        names = app.get_action_names()
        assert names == ["a", "b", "c"]

    def test_app_to_dict(self):
        """Test converting app to dictionary."""
        app = AppDefinition(
            app_id="test_app",
            name="Test App",
            description="A test app",
            category=AppCategory.CUSTOM,
            icon="🔧",
            actions=[
                ActionDefinition(name="test", description="Test", logic=[]),
            ],
            state_schema=[
                StateFieldDef(name="counter", type=ParamType.NUMBER, default=0),
            ],
            initial_config={"setting": "value"},
        )

        d = app.to_dict()

        assert d["app_id"] == "test_app"
        assert d["name"] == "Test App"
        assert d["description"] == "A test app"
        assert d["category"] == "custom"
        assert d["icon"] == "🔧"
        assert len(d["actions"]) == 1
        assert len(d["state_schema"]) == 1
        assert d["initial_config"]["setting"] == "value"

    def test_app_from_dict(self):
        """Test creating app from dictionary."""
        d = {
            "app_id": "my_app",
            "name": "My App",
            "description": "My description",
            "category": "payment",
            "icon": "💰",
            "actions": [
                {
                    "name": "action1",
                    "description": "Action 1",
                    "parameters": {
                        "x": {"type": "number"},
                    },
                    "logic": [
                        {"type": "return", "value": {"result": "x"}},
                    ],
                },
            ],
            "state_schema": [
                {"name": "balance", "type": "number", "default": 0},
            ],
            "initial_config": {"max": 1000},
        }

        app = AppDefinition.from_dict(d)

        assert app.app_id == "my_app"
        assert app.category == AppCategory.PAYMENT
        assert len(app.actions) == 1
        assert len(app.state_schema) == 1
        assert app.initial_config["max"] == 1000

    def test_app_roundtrip(self):
        """Test that app can be converted to dict and back."""
        original = AppDefinition(
            app_id="test_app",
            name="Test",
            category=AppCategory.CUSTOM,
            actions=[
                ActionDefinition(
                    name="test",
                    description="Test action",
                    parameters={
                        "x": ParamSpecDef(type=ParamType.NUMBER, required=True),
                    },
                    logic=[
                        ValidateBlock(
                            condition="x > 0",
                            error_message="Must be positive",
                        ),
                        ReturnBlock(value={"result": "x"}),
                    ],
                ),
            ],
        )

        d = original.to_dict()
        restored = AppDefinition.from_dict(d)

        assert restored.app_id == original.app_id
        assert len(restored.actions) == len(original.actions)
        assert restored.actions[0].name == original.actions[0].name


class TestAppState:
    """Tests for AppState dataclass."""

    def test_empty_state(self):
        """Test empty state creation."""
        state = AppState()
        assert state.per_agent == {}
        assert state.shared == {}

    def test_get_set_agent_state(self):
        """Test getting and setting agent state."""
        state = AppState()
        state.set_agent_state("alice", {"balance": 100})

        assert state.get_agent_state("alice") == {"balance": 100}
        assert state.get_agent_state("bob") == {}

    def test_ensure_agent(self):
        """Test ensuring agent has state."""
        state = AppState()
        state.ensure_agent("alice", {"balance": 0})

        assert state.get_agent_state("alice") == {"balance": 0}

        # Should not overwrite existing
        state.set_agent_state("alice", {"balance": 100})
        state.ensure_agent("alice", {"balance": 0})
        assert state.get_agent_state("alice") == {"balance": 100}

    def test_shared_state(self):
        """Test shared state access."""
        state = AppState()
        state.shared = {"counter": 0}

        assert state.shared["counter"] == 0

    def test_deep_copy(self):
        """Test deep copying state."""
        state = AppState()
        state.set_agent_state("alice", {"balance": 100, "items": [1, 2]})
        state.shared = {"counter": 0}

        copy = state.deep_copy()

        # Modify original
        state.get_agent_state("alice")["balance"] = 200
        state.get_agent_state("alice")["items"].append(3)
        state.shared["counter"] = 1

        # Copy should be unchanged
        assert copy.get_agent_state("alice")["balance"] == 100
        assert copy.get_agent_state("alice")["items"] == [1, 2]
        assert copy.shared["counter"] == 0

    def test_to_dict(self):
        """Test converting state to dictionary."""
        state = AppState()
        state.set_agent_state("alice", {"balance": 100})
        state.shared = {"counter": 0}

        d = state.to_dict()

        assert d["per_agent"]["alice"]["balance"] == 100
        assert d["shared"]["counter"] == 0

    def test_from_dict(self):
        """Test creating state from dictionary."""
        d = {
            "per_agent": {"alice": {"balance": 100}},
            "shared": {"counter": 0},
        }

        state = AppState.from_dict(d)

        assert state.get_agent_state("alice")["balance"] == 100
        assert state.shared["counter"] == 0


class TestConfigFieldDef:
    """Tests for ConfigFieldDef dataclass."""

    def test_string_config_field(self):
        """Test string config field."""
        field = ConfigFieldDef(
            name="api_key",
            label="API Key",
            type="string",
            required=True,
        )
        assert field.name == "api_key"
        assert field.type == "string"

    def test_number_config_field(self):
        """Test number config field with constraints."""
        field = ConfigFieldDef(
            name="max_amount",
            label="Maximum Amount",
            type="number",
            default=1000,
            min_value=0,
            max_value=10000,
            step=100,
        )
        assert field.min_value == 0
        assert field.step == 100

    def test_select_config_field(self):
        """Test select config field."""
        field = ConfigFieldDef(
            name="mode",
            label="Mode",
            type="select",
            options=[
                {"value": "fast", "label": "Fast"},
                {"value": "safe", "label": "Safe"},
            ],
        )
        assert len(field.options) == 2

    def test_config_field_roundtrip(self):
        """Test config field to/from dict."""
        original = ConfigFieldDef(
            name="test",
            label="Test",
            type="number",
            default=50,
            min_value=0,
            max_value=100,
        )

        d = original.to_dict()
        restored = ConfigFieldDef.from_dict(d)

        assert restored.name == original.name
        assert restored.min_value == original.min_value
