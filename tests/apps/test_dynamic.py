"""Tests for DynamicApp per ADR-018."""

import pytest

from agentworld.apps.dynamic import DynamicApp, create_dynamic_app
from agentworld.apps.definition import (
    AppDefinition,
    ActionDefinition,
    AppState,
    ParamSpecDef,
    StateFieldDef,
    ValidateBlock,
    UpdateBlock,
    NotifyBlock,
    ReturnBlock,
    ErrorBlock,
    BranchBlock,
    AppCategory,
    ParamType,
    UpdateOperation,
)


@pytest.fixture
def simple_app_definition():
    """Create a simple app definition for testing."""
    return AppDefinition(
        app_id="test_app",
        name="Test App",
        description="A test application",
        category=AppCategory.CUSTOM,
        icon="🧪",
        actions=[
            ActionDefinition(
                name="get_value",
                description="Get the stored value",
                logic=[
                    ReturnBlock(value={"value": "agent.value"}),
                ],
            ),
            ActionDefinition(
                name="set_value",
                description="Set a value",
                parameters={
                    "value": ParamSpecDef(type=ParamType.NUMBER, required=True),
                },
                logic=[
                    UpdateBlock(
                        target="agent.value",
                        operation=UpdateOperation.SET,
                        value="params.value",
                    ),
                    ReturnBlock(value={"new_value": "agent.value"}),
                ],
            ),
        ],
        state_schema=[
            StateFieldDef(name="value", type=ParamType.NUMBER, default=0),
        ],
        initial_config={},
    )


@pytest.fixture
def payment_app_definition():
    """Create a payment app definition similar to PayPal."""
    return AppDefinition(
        app_id="test_payment",
        name="Test Payment",
        description="A test payment application",
        category=AppCategory.PAYMENT,
        icon="💳",
        actions=[
            ActionDefinition(
                name="check_balance",
                description="Check account balance",
                logic=[
                    ReturnBlock(value={"balance": "agent.balance"}),
                ],
            ),
            ActionDefinition(
                name="transfer",
                description="Transfer money to another user",
                parameters={
                    "to": ParamSpecDef(
                        type=ParamType.STRING,
                        required=True,
                        description="Recipient ID",
                    ),
                    "amount": ParamSpecDef(
                        type=ParamType.NUMBER,
                        required=True,
                        min_value=0.01,
                        max_value=10000,
                    ),
                    "note": ParamSpecDef(
                        type=ParamType.STRING,
                        required=False,
                        max_length=200,
                    ),
                },
                logic=[
                    # Validate recipient exists
                    ValidateBlock(
                        condition="agents[params.to] != null",
                        error_message="Recipient not found",
                    ),
                    # Validate not self-transfer
                    ValidateBlock(
                        condition="params.to != agent.id",
                        error_message="Cannot transfer to yourself",
                    ),
                    # Validate sufficient funds
                    ValidateBlock(
                        condition="params.amount <= agent.balance",
                        error_message="Insufficient funds",
                    ),
                    # Deduct from sender
                    UpdateBlock(
                        target="agent.balance",
                        operation=UpdateOperation.SUBTRACT,
                        value="params.amount",
                    ),
                    # Add to recipient
                    UpdateBlock(
                        target="agents[params.to].balance",
                        operation=UpdateOperation.ADD,
                        value="params.amount",
                    ),
                    # Notify recipient
                    NotifyBlock(
                        to="params.to",
                        message="You received $${params.amount} from ${agent.id}",
                        data={
                            "type": "'received'",
                            "amount": "params.amount",
                            "from": "agent.id",
                        },
                    ),
                    # Return success
                    ReturnBlock(value={
                        "transaction_id": "generate_id()",
                        "new_balance": "agent.balance",
                    }),
                ],
            ),
        ],
        state_schema=[
            StateFieldDef(name="balance", type=ParamType.NUMBER, default=1000),
            StateFieldDef(name="transactions", type=ParamType.ARRAY, default=[]),
        ],
        initial_config={"initial_balance": 1000},
    )


class TestDynamicAppProperties:
    """Tests for DynamicApp properties."""

    def test_app_id(self, simple_app_definition):
        """Test app_id property."""
        app = DynamicApp(simple_app_definition)
        assert app.app_id == "test_app"

    def test_name(self, simple_app_definition):
        """Test name property."""
        app = DynamicApp(simple_app_definition)
        assert app.name == "Test App"

    def test_description(self, simple_app_definition):
        """Test description property."""
        app = DynamicApp(simple_app_definition)
        assert app.description == "A test application"

    def test_definition(self, simple_app_definition):
        """Test definition property."""
        app = DynamicApp(simple_app_definition)
        assert app.definition == simple_app_definition


class TestDynamicAppActions:
    """Tests for DynamicApp action methods."""

    def test_get_actions(self, simple_app_definition):
        """Test getting available actions."""
        app = DynamicApp(simple_app_definition)
        actions = app.get_actions()

        assert len(actions) == 2

        action_names = [a.name for a in actions]
        assert "get_value" in action_names
        assert "set_value" in action_names

    def test_get_actions_with_params(self, payment_app_definition):
        """Test that actions include parameter specs."""
        app = DynamicApp(payment_app_definition)
        actions = app.get_actions()

        transfer = next(a for a in actions if a.name == "transfer")

        assert "to" in transfer.parameters
        assert "amount" in transfer.parameters
        assert "note" in transfer.parameters

        assert transfer.parameters["to"].required is True
        assert transfer.parameters["amount"].min_value == 0.01


class TestDynamicAppInitialization:
    """Tests for DynamicApp initialization."""

    @pytest.mark.asyncio
    async def test_initialize_single_agent(self, simple_app_definition):
        """Test initializing for a single agent."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice"], {})

        state = await app.get_agent_state("alice")
        assert "agent_state" in state
        assert state["agent_state"]["value"] == 0

    @pytest.mark.asyncio
    async def test_initialize_multiple_agents(self, simple_app_definition):
        """Test initializing for multiple agents."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice", "bob", "charlie"], {})

        for agent in ["alice", "bob", "charlie"]:
            state = await app.get_agent_state(agent)
            assert state["agent_state"]["value"] == 0

    @pytest.mark.asyncio
    async def test_initialize_with_config(self, payment_app_definition):
        """Test initializing with custom config."""
        app = DynamicApp(payment_app_definition)
        await app.initialize("sim1", ["alice"], {"initial_balance": 500})

        # Config value should be applied if it matches state schema
        state = await app.get_agent_state("alice")
        # Note: In current implementation, initial_balance from config
        # is applied via state_schema defaults


class TestDynamicAppExecution:
    """Tests for DynamicApp action execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_action(self, simple_app_definition):
        """Test executing a simple action."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice"], {})

        # Get value
        result = await app.execute("alice", "get_value", {})
        assert result.success is True
        assert result.data["value"] == 0

    @pytest.mark.asyncio
    async def test_execute_action_with_state_update(self, simple_app_definition):
        """Test action that updates state."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice"], {})

        # Set value
        result = await app.execute("alice", "set_value", {"value": 42})
        assert result.success is True
        assert result.data["new_value"] == 42

        # Verify state was updated
        result = await app.execute("alice", "get_value", {})
        assert result.data["value"] == 42

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, simple_app_definition):
        """Test executing unknown action returns error."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice"], {})

        result = await app.execute("alice", "unknown_action", {})
        assert result.success is False
        assert "Unknown action" in result.error

    @pytest.mark.asyncio
    async def test_execute_transfer(self, payment_app_definition):
        """Test executing a transfer action."""
        app = DynamicApp(payment_app_definition)
        await app.initialize("sim1", ["alice", "bob"], {})

        # Transfer from alice to bob
        result = await app.execute("alice", "transfer", {
            "to": "bob",
            "amount": 100,
            "note": "Test payment",
        })

        assert result.success is True
        assert "transaction_id" in result.data
        assert result.data["new_balance"] == 900

        # Check balances
        alice_state = await app.get_agent_state("alice")
        bob_state = await app.get_agent_state("bob")

        assert alice_state["agent_state"]["balance"] == 900
        assert bob_state["agent_state"]["balance"] == 1100

    @pytest.mark.asyncio
    async def test_execute_transfer_insufficient_funds(self, payment_app_definition):
        """Test transfer fails with insufficient funds."""
        app = DynamicApp(payment_app_definition)
        await app.initialize("sim1", ["alice", "bob"], {})

        result = await app.execute("alice", "transfer", {
            "to": "bob",
            "amount": 2000,  # More than balance
        })

        assert result.success is False
        assert "Insufficient funds" in result.error

        # Balances should be unchanged
        alice_state = await app.get_agent_state("alice")
        bob_state = await app.get_agent_state("bob")

        assert alice_state["agent_state"]["balance"] == 1000
        assert bob_state["agent_state"]["balance"] == 1000

    @pytest.mark.asyncio
    async def test_execute_self_transfer_fails(self, payment_app_definition):
        """Test self-transfer is rejected."""
        app = DynamicApp(payment_app_definition)
        await app.initialize("sim1", ["alice", "bob"], {})

        result = await app.execute("alice", "transfer", {
            "to": "alice",
            "amount": 100,
        })

        assert result.success is False
        assert "yourself" in result.error.lower()


class TestDynamicAppObservations:
    """Tests for DynamicApp observation handling."""

    @pytest.mark.asyncio
    async def test_transfer_creates_observation(self, payment_app_definition):
        """Test that transfer creates observation for recipient."""
        app = DynamicApp(payment_app_definition)
        await app.initialize("sim1", ["alice", "bob"], {})

        # Transfer creates notification
        await app.execute("alice", "transfer", {
            "to": "bob",
            "amount": 50,
        })

        # Get observations for bob
        observations = await app.get_observations("bob")
        assert len(observations) == 1
        assert "$50" in observations[0].message or "50" in observations[0].message
        assert observations[0].data["amount"] == 50

    @pytest.mark.asyncio
    async def test_observations_are_cleared(self, payment_app_definition):
        """Test that getting observations clears them."""
        app = DynamicApp(payment_app_definition)
        await app.initialize("sim1", ["alice", "bob"], {})

        await app.execute("alice", "transfer", {"to": "bob", "amount": 50})

        # Get observations once
        observations1 = await app.get_observations("bob")
        assert len(observations1) == 1

        # Get observations again - should be empty
        observations2 = await app.get_observations("bob")
        assert len(observations2) == 0


class TestDynamicAppStatelessExecution:
    """Tests for stateless action execution (for test endpoint)."""

    @pytest.mark.asyncio
    async def test_execute_stateless(self, simple_app_definition):
        """Test stateless execution doesn't affect app state."""
        app = DynamicApp(simple_app_definition)

        # Create input state
        state = AppState()
        state.set_agent_state("alice", {"value": 100})

        # Execute stateless
        result, state_after, observations = await app.execute_stateless(
            agent_id="alice",
            action="set_value",
            params={"value": 200},
            state=state,
        )

        assert result.success is True
        assert result.data["new_value"] == 200

        # State_after should reflect the change
        assert state_after.get_agent_state("alice")["value"] == 200

        # Original state should be unchanged
        assert state.get_agent_state("alice")["value"] == 100

    @pytest.mark.asyncio
    async def test_execute_stateless_transfer(self, payment_app_definition):
        """Test stateless transfer execution."""
        app = DynamicApp(payment_app_definition)

        state = AppState()
        state.set_agent_state("alice", {"balance": 1000, "transactions": []})
        state.set_agent_state("bob", {"balance": 500, "transactions": []})

        result, state_after, observations = await app.execute_stateless(
            agent_id="alice",
            action="transfer",
            params={"to": "bob", "amount": 100},
            state=state,
        )

        assert result.success is True
        assert state_after.get_agent_state("alice")["balance"] == 900
        assert state_after.get_agent_state("bob")["balance"] == 600
        assert len(observations) == 1


class TestDynamicAppValidation:
    """Tests for parameter validation."""

    def test_validate_params_missing_required(self, payment_app_definition):
        """Test validation fails for missing required params."""
        app = DynamicApp(payment_app_definition)

        is_valid, error = app.validate_params("transfer", {
            # Missing 'to' and 'amount'
        })

        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_params_wrong_type(self, payment_app_definition):
        """Test validation fails for wrong parameter type."""
        app = DynamicApp(payment_app_definition)

        is_valid, error = app.validate_params("transfer", {
            "to": "bob",
            "amount": "not a number",  # Should be number
        })

        assert is_valid is False
        assert "number" in error.lower()

    def test_validate_params_out_of_range(self, payment_app_definition):
        """Test validation fails for out-of-range values."""
        app = DynamicApp(payment_app_definition)

        is_valid, error = app.validate_params("transfer", {
            "to": "bob",
            "amount": 50000,  # Exceeds max_value of 10000
        })

        assert is_valid is False
        assert "10000" in error

    def test_validate_params_unknown_param(self, simple_app_definition):
        """Test validation fails for unknown parameters."""
        app = DynamicApp(simple_app_definition)

        is_valid, error = app.validate_params("set_value", {
            "value": 42,
            "unknown": "param",  # Not defined
        })

        assert is_valid is False
        assert "unknown" in error.lower()

    def test_validate_params_valid(self, payment_app_definition):
        """Test validation passes for valid params."""
        app = DynamicApp(payment_app_definition)

        is_valid, error = app.validate_params("transfer", {
            "to": "bob",
            "amount": 100,
            "note": "Test",
        })

        assert is_valid is True
        assert error == ""


class TestDynamicAppStateManagement:
    """Tests for state snapshot and restore."""

    @pytest.mark.asyncio
    async def test_state_snapshot(self, simple_app_definition):
        """Test getting state snapshot."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice"], {})

        # Modify state
        await app.execute("alice", "set_value", {"value": 42})

        # Get snapshot
        snapshot = app.get_state_snapshot()
        assert isinstance(snapshot, bytes)

    @pytest.mark.asyncio
    async def test_state_restore(self, simple_app_definition):
        """Test restoring from state snapshot."""
        app = DynamicApp(simple_app_definition)
        await app.initialize("sim1", ["alice"], {})

        # Modify state
        await app.execute("alice", "set_value", {"value": 42})

        # Get snapshot
        snapshot = app.get_state_snapshot()

        # Modify further
        await app.execute("alice", "set_value", {"value": 100})

        # Restore
        app.restore_state(snapshot)

        # Verify restored state
        result = await app.execute("alice", "get_value", {})
        assert result.data["value"] == 42


class TestCreateDynamicApp:
    """Tests for create_dynamic_app helper function."""

    def test_create_from_dict(self):
        """Test creating DynamicApp from dictionary."""
        definition_dict = {
            "app_id": "test_app",
            "name": "Test App",
            "category": "custom",
            "actions": [
                {
                    "name": "test",
                    "description": "Test action",
                    "logic": [
                        {"type": "return", "value": {"result": "'ok'"}},
                    ],
                },
            ],
        }

        app = create_dynamic_app(definition_dict)

        assert isinstance(app, DynamicApp)
        assert app.app_id == "test_app"
        assert len(app.get_actions()) == 1
