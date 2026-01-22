"""Tests for logic engine per ADR-018/019."""

import pytest

from agentworld.apps.logic_engine import LogicEngine, ExecutionContext
from agentworld.apps.definition import (
    AppState,
    ValidateBlock,
    UpdateBlock,
    NotifyBlock,
    ReturnBlock,
    ErrorBlock,
    BranchBlock,
    LoopBlock,
    UpdateOperation,
)
from agentworld.apps.base import AppResult


@pytest.fixture
def engine():
    """Create a LogicEngine instance."""
    return LogicEngine()


@pytest.fixture
def basic_context():
    """Create a basic execution context."""
    state = AppState()
    state.set_agent_state("alice", {"balance": 1000, "transactions": []})
    state.set_agent_state("bob", {"balance": 500, "transactions": []})

    return ExecutionContext(
        agent_id="alice",
        params={"to": "bob", "amount": 50, "note": "test"},
        state=state,
        config={"max_transfer": 10000},
    )


class TestValidateBlock:
    """Tests for VALIDATE block execution."""

    @pytest.mark.asyncio
    async def test_validate_pass(self, engine, basic_context):
        """Test that valid condition passes."""
        logic = [
            ValidateBlock(
                condition="params.amount > 0",
                error_message="Amount must be positive",
            ),
            ReturnBlock(value={"status": "ok"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert result.data == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_validate_fail(self, engine, basic_context):
        """Test that invalid condition fails."""
        basic_context.params["amount"] = -10

        logic = [
            ValidateBlock(
                condition="params.amount > 0",
                error_message="Amount must be positive",
            ),
            ReturnBlock(value={"status": "ok"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is False
        assert "Amount must be positive" in result.error

    @pytest.mark.asyncio
    async def test_validate_balance_check(self, engine, basic_context):
        """Test validating sufficient balance."""
        # Alice has 1000, transferring 50 should pass
        logic = [
            ValidateBlock(
                condition="params.amount <= agent.balance",
                error_message="Insufficient funds",
            ),
            ReturnBlock(value={"status": "ok"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True

        # Try transferring more than balance
        basic_context.params["amount"] = 2000
        result = await engine.execute(logic, basic_context)
        assert result.success is False
        assert "Insufficient funds" in result.error


class TestUpdateBlock:
    """Tests for UPDATE block execution."""

    @pytest.mark.asyncio
    async def test_update_set(self, engine, basic_context):
        """Test SET operation."""
        logic = [
            UpdateBlock(
                target="agent.balance",
                operation=UpdateOperation.SET,
                value="500",
            ),
            ReturnBlock(value={"new_balance": "agent.balance"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert basic_context.state.get_agent_state("alice")["balance"] == 500

    @pytest.mark.asyncio
    async def test_update_add(self, engine, basic_context):
        """Test ADD operation."""
        logic = [
            UpdateBlock(
                target="agent.balance",
                operation=UpdateOperation.ADD,
                value="params.amount",
            ),
            ReturnBlock(value={}),
        ]

        await engine.execute(logic, basic_context)
        assert basic_context.state.get_agent_state("alice")["balance"] == 1050

    @pytest.mark.asyncio
    async def test_update_subtract(self, engine, basic_context):
        """Test SUBTRACT operation."""
        logic = [
            UpdateBlock(
                target="agent.balance",
                operation=UpdateOperation.SUBTRACT,
                value="params.amount",
            ),
            ReturnBlock(value={}),
        ]

        await engine.execute(logic, basic_context)
        assert basic_context.state.get_agent_state("alice")["balance"] == 950

    @pytest.mark.asyncio
    async def test_update_append(self, engine, basic_context):
        """Test APPEND operation."""
        logic = [
            UpdateBlock(
                target="agent.transactions",
                operation=UpdateOperation.APPEND,
                value={"type": "sent", "amount": "params.amount"},
            ),
            ReturnBlock(value={}),
        ]

        await engine.execute(logic, basic_context)
        transactions = basic_context.state.get_agent_state("alice")["transactions"]
        assert len(transactions) == 1
        assert transactions[0]["type"] == "sent"
        assert transactions[0]["amount"] == 50

    @pytest.mark.asyncio
    async def test_update_other_agent(self, engine, basic_context):
        """Test updating another agent's state."""
        logic = [
            UpdateBlock(
                target="agents[params.to].balance",
                operation=UpdateOperation.ADD,
                value="params.amount",
            ),
            ReturnBlock(value={}),
        ]

        await engine.execute(logic, basic_context)
        assert basic_context.state.get_agent_state("bob")["balance"] == 550


class TestNotifyBlock:
    """Tests for NOTIFY block execution."""

    @pytest.mark.asyncio
    async def test_notify_creates_observation(self, engine, basic_context):
        """Test that NOTIFY creates an observation."""
        logic = [
            NotifyBlock(
                to="params.to",
                message="You received $${params.amount} from ${agent.id}",
                data={"type": "received", "amount": "params.amount"},
            ),
            ReturnBlock(value={}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True

        # Check observations were created
        assert len(basic_context.observations) == 1
        to_agent, observation = basic_context.observations[0]
        assert to_agent == "bob"
        assert "50" in observation.message
        assert "alice" in observation.message
        assert observation.data["type"] == "received"
        assert observation.data["amount"] == 50


class TestReturnBlock:
    """Tests for RETURN block execution."""

    @pytest.mark.asyncio
    async def test_return_success(self, engine, basic_context):
        """Test RETURN creates success result."""
        logic = [
            ReturnBlock(value={"balance": "agent.balance", "message": "'Transfer complete'"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert result.data["balance"] == 1000
        assert result.data["message"] == "Transfer complete"

    @pytest.mark.asyncio
    async def test_return_stops_execution(self, engine, basic_context):
        """Test RETURN stops further execution."""
        logic = [
            ReturnBlock(value={"step": "1"}),  # "1" evaluates to number 1
            # This should never execute
            UpdateBlock(
                target="agent.balance",
                operation=UpdateOperation.SET,
                value="0",
            ),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.data["step"] == 1  # Number, not string
        assert basic_context.state.get_agent_state("alice")["balance"] == 1000


class TestErrorBlock:
    """Tests for ERROR block execution."""

    @pytest.mark.asyncio
    async def test_error_fails(self, engine, basic_context):
        """Test ERROR creates failure result."""
        logic = [
            ErrorBlock(message="Something went wrong"),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is False
        assert result.error == "Something went wrong"

    @pytest.mark.asyncio
    async def test_error_with_interpolation(self, engine, basic_context):
        """Test ERROR with interpolated message."""
        logic = [
            ErrorBlock(message="Cannot transfer $${params.amount}"),
        ]

        result = await engine.execute(logic, basic_context)
        assert "$50" in result.error


class TestBranchBlock:
    """Tests for BRANCH block execution."""

    @pytest.mark.asyncio
    async def test_branch_true_path(self, engine, basic_context):
        """Test BRANCH takes true path when condition is true."""
        logic = [
            BranchBlock(
                condition="params.amount > 0",
                then_blocks=[ReturnBlock(value={"path": "'then'"})],
                else_blocks=[ReturnBlock(value={"path": "'else'"})],
            ),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.data["path"] == "then"

    @pytest.mark.asyncio
    async def test_branch_false_path(self, engine, basic_context):
        """Test BRANCH takes false path when condition is false."""
        basic_context.params["amount"] = 0

        logic = [
            BranchBlock(
                condition="params.amount > 0",
                then_blocks=[ReturnBlock(value={"path": "'then'"})],
                else_blocks=[ReturnBlock(value={"path": "'else'"})],
            ),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.data["path"] == "else"

    @pytest.mark.asyncio
    async def test_branch_no_else(self, engine, basic_context):
        """Test BRANCH without else continues when condition is false."""
        basic_context.params["amount"] = 0

        logic = [
            BranchBlock(
                condition="params.amount > 0",
                then_blocks=[ErrorBlock(message="Should not reach")],
                else_blocks=None,
            ),
            ReturnBlock(value={"continued": "true"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert result.data["continued"] == True

    @pytest.mark.asyncio
    async def test_nested_branch(self, engine, basic_context):
        """Test nested BRANCH blocks."""
        logic = [
            BranchBlock(
                condition="params.amount > 0",
                then_blocks=[
                    BranchBlock(
                        condition="params.amount <= agent.balance",
                        then_blocks=[ReturnBlock(value={"status": "'valid'"})],
                        else_blocks=[ErrorBlock(message="Insufficient funds")],
                    ),
                ],
                else_blocks=[ErrorBlock(message="Invalid amount")],
            ),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert result.data["status"] == "valid"


class TestLoopBlock:
    """Tests for LOOP block execution."""

    @pytest.mark.asyncio
    async def test_loop_over_array(self, engine, basic_context):
        """Test LOOP iterates over array."""
        basic_context.state.shared["recipients"] = ["bob", "charlie"]

        logic = [
            LoopBlock(
                collection="shared.recipients",  # Use "shared" not "state"
                item="recipient",
                body=[
                    NotifyBlock(
                        to="recipient",
                        message="Hello from ${agent.id}!",
                    ),
                ],
            ),
            ReturnBlock(value={"count": "len(shared.recipients)"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert len(basic_context.observations) == 2

    @pytest.mark.asyncio
    async def test_loop_empty_array(self, engine, basic_context):
        """Test LOOP with empty array."""
        basic_context.state.shared["items"] = []

        logic = [
            LoopBlock(
                collection="shared.items",  # Use "shared" not "state"
                item="item",
                body=[
                    ErrorBlock(message="Should not reach"),
                ],
            ),
            ReturnBlock(value={"status": "'ok'"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is True
        assert result.data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_loop_with_return(self, engine, basic_context):
        """Test LOOP can return early."""
        basic_context.state.shared["numbers"] = [1, 2, 3, 4, 5]

        logic = [
            LoopBlock(
                collection="shared.numbers",  # Use "shared" not "state"
                item="n",
                body=[
                    BranchBlock(
                        condition="n == 3",
                        then_blocks=[ReturnBlock(value={"found": "n"})],
                    ),
                ],
            ),
            ReturnBlock(value={"found": "null"}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.data["found"] == 3


class TestCompleteTransferFlow:
    """Integration tests for a complete transfer action."""

    @pytest.mark.asyncio
    async def test_successful_transfer(self, engine, basic_context):
        """Test a complete successful transfer."""
        logic = [
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
                data={"type": "received", "from": "agent.id", "amount": "params.amount"},
            ),
            # Return success
            ReturnBlock(value={
                "transaction_id": "generate_id()",
                "new_balance": "agent.balance",
            }),
        ]

        result = await engine.execute(logic, basic_context)

        assert result.success is True
        assert "transaction_id" in result.data
        assert result.data["new_balance"] == 950

        # Check state updates
        assert basic_context.state.get_agent_state("alice")["balance"] == 950
        assert basic_context.state.get_agent_state("bob")["balance"] == 550

        # Check notification
        assert len(basic_context.observations) == 1

    @pytest.mark.asyncio
    async def test_failed_transfer_insufficient_funds(self, engine, basic_context):
        """Test transfer fails with insufficient funds."""
        basic_context.params["amount"] = 2000

        logic = [
            ValidateBlock(
                condition="params.amount <= agent.balance",
                error_message="Insufficient funds",
            ),
            ReturnBlock(value={}),
        ]

        result = await engine.execute(logic, basic_context)
        assert result.success is False
        assert "Insufficient funds" in result.error


class TestSafetyLimits:
    """Tests for safety limits."""

    @pytest.mark.asyncio
    async def test_max_nested_depth(self, engine, basic_context):
        """Test max nested depth is enforced."""
        # Create deeply nested branches
        def make_nested(depth: int):
            if depth == 0:
                return [ReturnBlock(value={"depth": f"'{depth}'"})]
            return [BranchBlock(
                condition="true",
                then_blocks=make_nested(depth - 1),
            )]

        logic = make_nested(15)  # Exceeds MAX_NESTED_DEPTH=10

        result = await engine.execute(logic, basic_context)
        assert result.success is False
        assert "depth" in result.error.lower()

    @pytest.mark.asyncio
    async def test_max_loop_iterations(self, engine, basic_context):
        """Test max loop iterations is enforced."""
        # Create a very large array
        basic_context.state.shared["items"] = list(range(2000))

        logic = [
            LoopBlock(
                collection="shared.items",  # Use "shared" not "state"
                item="i",
                body=[
                    UpdateBlock(
                        target="shared.counter",  # Use "shared" not "state"
                        operation=UpdateOperation.SET,
                        value="i",
                    ),
                ],
            ),
            ReturnBlock(value={}),
        ]

        basic_context.state.shared["counter"] = 0
        result = await engine.execute(logic, basic_context)
        assert result.success is False
        assert "iteration" in result.error.lower() or "loop" in result.error.lower()


class TestExecutionContext:
    """Tests for ExecutionContext."""

    def test_context_creation(self):
        """Test ExecutionContext can be created."""
        state = AppState()
        ctx = ExecutionContext(
            agent_id="alice",
            params={},
            state=state,
        )
        assert ctx.agent_id == "alice"

    def test_context_agent_state_access(self):
        """Test agent state access via state object."""
        state = AppState()
        state.set_agent_state("alice", {"balance": 100})

        ctx = ExecutionContext(
            agent_id="alice",
            params={},
            state=state,
        )

        # Access via state object
        assert ctx.state.get_agent_state("alice")["balance"] == 100

    def test_context_agents_state_access(self):
        """Test all agents state access via state object."""
        state = AppState()
        state.set_agent_state("alice", {"balance": 100})
        state.set_agent_state("bob", {"balance": 200})

        ctx = ExecutionContext(
            agent_id="alice",
            params={},
            state=state,
        )

        # Access via state object
        assert ctx.state.per_agent["alice"]["balance"] == 100
        assert ctx.state.per_agent["bob"]["balance"] == 200

    def test_context_to_eval_context(self):
        """Test converting context to evaluation dictionary."""
        state = AppState()
        state.set_agent_state("alice", {"balance": 100})
        state.shared["counter"] = 0

        ctx = ExecutionContext(
            agent_id="alice",
            params={"amount": 50},
            state=state,
            config={"max": 1000},
        )

        eval_ctx = ctx.to_eval_context()

        assert eval_ctx["params"]["amount"] == 50
        assert eval_ctx["agent"]["balance"] == 100
        assert eval_ctx["shared"]["counter"] == 0
        assert eval_ctx["config"]["max"] == 1000
