"""Tests for PayPal simulated app per ADR-017."""

import pytest

from agentworld.apps.paypal import PayPalApp


@pytest.fixture
def paypal_app():
    """Create a PayPal app instance."""
    return PayPalApp()


@pytest.fixture
async def initialized_app(paypal_app):
    """Create and initialize a PayPal app."""
    await paypal_app.initialize(
        sim_id="test-sim",
        agents=["alice", "bob", "charlie"],
        config={"initial_balance": 1000.0},
    )
    return paypal_app


class TestPayPalInit:
    """Tests for PayPal initialization."""

    def test_app_properties(self, paypal_app):
        """Test app identity properties."""
        assert paypal_app.app_id == "paypal"
        assert paypal_app.name == "PayPal"
        assert "payment" in paypal_app.description.lower()

    def test_get_actions(self, paypal_app):
        """Test action definitions."""
        actions = paypal_app.get_actions()
        action_names = {a.name for a in actions}

        assert "check_balance" in action_names
        assert "transfer" in action_names
        assert "request_money" in action_names
        assert "view_transactions" in action_names
        assert "pay_request" in action_names
        assert "decline_request" in action_names

    @pytest.mark.asyncio
    async def test_initialize_creates_accounts(self, paypal_app):
        """Test that initialization creates accounts for all agents."""
        await paypal_app.initialize(
            sim_id="test-sim",
            agents=["alice", "bob"],
            config={"initial_balance": 500.0},
        )

        alice_state = await paypal_app.get_agent_state("alice")
        bob_state = await paypal_app.get_agent_state("bob")

        assert alice_state["balance"] == 500.0
        assert bob_state["balance"] == 500.0
        assert "email" in alice_state
        assert "email" in bob_state


class TestCheckBalance:
    """Tests for check_balance action."""

    @pytest.mark.asyncio
    async def test_check_balance_success(self, initialized_app):
        """Test checking balance returns correct amount."""
        result = await initialized_app.execute("alice", "check_balance", {})

        assert result.success is True
        assert result.data["balance"] == 1000.0
        assert "email" in result.data

    @pytest.mark.asyncio
    async def test_check_balance_unknown_agent(self, initialized_app):
        """Test checking balance for unknown agent."""
        result = await initialized_app.execute("unknown", "check_balance", {})

        assert result.success is False
        assert "account" in result.error.lower() or "found" in result.error.lower()


class TestTransfer:
    """Tests for transfer action."""

    @pytest.mark.asyncio
    async def test_transfer_success(self, initialized_app):
        """Test successful transfer."""
        result = await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": 100.0, "note": "Test"}
        )

        assert result.success is True
        assert result.data["new_balance"] == 900.0
        assert "transaction_id" in result.data

        # Verify balances
        alice_state = await initialized_app.get_agent_state("alice")
        bob_state = await initialized_app.get_agent_state("bob")

        assert alice_state["balance"] == 900.0
        assert bob_state["balance"] == 1100.0

    @pytest.mark.asyncio
    async def test_transfer_insufficient_funds(self, initialized_app):
        """Test transfer with insufficient funds."""
        result = await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": 2000.0}
        )

        assert result.success is False
        assert "insufficient" in result.error.lower()

        # Verify balance unchanged
        alice_state = await initialized_app.get_agent_state("alice")
        assert alice_state["balance"] == 1000.0

    @pytest.mark.asyncio
    async def test_transfer_to_self(self, initialized_app):
        """Test transfer to self fails."""
        result = await initialized_app.execute(
            "alice", "transfer", {"to": "alice", "amount": 100.0}
        )

        assert result.success is False
        assert "yourself" in result.error.lower()

    @pytest.mark.asyncio
    async def test_transfer_to_unknown_user(self, initialized_app):
        """Test transfer to unknown user."""
        result = await initialized_app.execute(
            "alice", "transfer", {"to": "unknown", "amount": 100.0}
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_transfer_negative_amount(self, initialized_app):
        """Test transfer with negative amount fails validation."""
        result = await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": -50.0}
        )

        assert result.success is False
        # Validation error from parameter spec

    @pytest.mark.asyncio
    async def test_transfer_creates_observation(self, initialized_app):
        """Test that transfer creates observation for recipient."""
        await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": 50.0, "note": "Lunch"}
        )

        observations = await initialized_app.get_observations("bob")
        assert len(observations) == 1
        assert "received" in observations[0].message.lower()
        assert "$50" in observations[0].message


class TestRequestMoney:
    """Tests for request_money action."""

    @pytest.mark.asyncio
    async def test_request_money_success(self, initialized_app):
        """Test successful money request."""
        result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 75.0, "note": "Dinner"}
        )

        assert result.success is True
        assert "request_id" in result.data

        # Bob should have observation
        observations = await initialized_app.get_observations("bob")
        assert len(observations) == 1
        assert "requested" in observations[0].message.lower()

    @pytest.mark.asyncio
    async def test_request_money_from_self(self, initialized_app):
        """Test request money from self fails."""
        result = await initialized_app.execute(
            "alice", "request_money", {"from": "alice", "amount": 50.0}
        )

        assert result.success is False
        assert "yourself" in result.error.lower()

    @pytest.mark.asyncio
    async def test_request_money_from_unknown(self, initialized_app):
        """Test request from unknown user."""
        result = await initialized_app.execute(
            "alice", "request_money", {"from": "unknown", "amount": 50.0}
        )

        assert result.success is False
        assert "not found" in result.error.lower()


class TestPayRequest:
    """Tests for pay_request action."""

    @pytest.mark.asyncio
    async def test_pay_request_success(self, initialized_app):
        """Test paying a request."""
        # Alice requests from Bob
        request_result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 100.0}
        )
        request_id = request_result.data["request_id"]

        # Clear Bob's observations
        await initialized_app.get_observations("bob")

        # Bob pays the request
        pay_result = await initialized_app.execute(
            "bob", "pay_request", {"request_id": request_id}
        )

        assert pay_result.success is True
        assert pay_result.data["new_balance"] == 900.0
        assert "transaction_id" in pay_result.data

        # Verify balances
        alice_state = await initialized_app.get_agent_state("alice")
        bob_state = await initialized_app.get_agent_state("bob")

        assert alice_state["balance"] == 1100.0
        assert bob_state["balance"] == 900.0

        # Alice should have observation
        observations = await initialized_app.get_observations("alice")
        assert len(observations) == 1
        assert "paid" in observations[0].message.lower()

    @pytest.mark.asyncio
    async def test_pay_request_insufficient_funds(self, initialized_app):
        """Test paying request with insufficient funds."""
        # Alice requests a large amount from Bob
        request_result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 2000.0}
        )
        request_id = request_result.data["request_id"]

        # Bob tries to pay
        pay_result = await initialized_app.execute(
            "bob", "pay_request", {"request_id": request_id}
        )

        assert pay_result.success is False
        assert "insufficient" in pay_result.error.lower()

    @pytest.mark.asyncio
    async def test_pay_request_not_addressed_to_you(self, initialized_app):
        """Test paying request addressed to someone else."""
        # Alice requests from Bob
        request_result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 50.0}
        )
        request_id = request_result.data["request_id"]

        # Charlie tries to pay (not the target)
        pay_result = await initialized_app.execute(
            "charlie", "pay_request", {"request_id": request_id}
        )

        assert pay_result.success is False
        assert "not addressed" in pay_result.error.lower()

    @pytest.mark.asyncio
    async def test_pay_request_not_found(self, initialized_app):
        """Test paying non-existent request."""
        result = await initialized_app.execute(
            "bob", "pay_request", {"request_id": "nonexistent"}
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_pay_already_paid_request(self, initialized_app):
        """Test paying already paid request."""
        # Alice requests from Bob
        request_result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 50.0}
        )
        request_id = request_result.data["request_id"]

        # Bob pays
        await initialized_app.execute("bob", "pay_request", {"request_id": request_id})

        # Bob tries to pay again
        pay_result = await initialized_app.execute(
            "bob", "pay_request", {"request_id": request_id}
        )

        assert pay_result.success is False
        assert "already" in pay_result.error.lower()


class TestDeclineRequest:
    """Tests for decline_request action."""

    @pytest.mark.asyncio
    async def test_decline_request_success(self, initialized_app):
        """Test declining a request."""
        # Alice requests from Bob
        request_result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 100.0}
        )
        request_id = request_result.data["request_id"]

        # Clear observations
        await initialized_app.get_observations("bob")

        # Bob declines
        decline_result = await initialized_app.execute(
            "bob", "decline_request", {"request_id": request_id}
        )

        assert decline_result.success is True

        # Balances unchanged
        alice_state = await initialized_app.get_agent_state("alice")
        bob_state = await initialized_app.get_agent_state("bob")

        assert alice_state["balance"] == 1000.0
        assert bob_state["balance"] == 1000.0

        # Alice should have observation
        observations = await initialized_app.get_observations("alice")
        assert len(observations) == 1
        assert "declined" in observations[0].message.lower()

    @pytest.mark.asyncio
    async def test_decline_already_paid_request(self, initialized_app):
        """Test declining already paid request."""
        # Alice requests from Bob
        request_result = await initialized_app.execute(
            "alice", "request_money", {"from": "bob", "amount": 50.0}
        )
        request_id = request_result.data["request_id"]

        # Bob pays
        await initialized_app.execute("bob", "pay_request", {"request_id": request_id})

        # Bob tries to decline
        decline_result = await initialized_app.execute(
            "bob", "decline_request", {"request_id": request_id}
        )

        assert decline_result.success is False
        assert "already" in decline_result.error.lower()


class TestViewTransactions:
    """Tests for view_transactions action."""

    @pytest.mark.asyncio
    async def test_view_transactions_empty(self, initialized_app):
        """Test viewing transactions when none exist."""
        result = await initialized_app.execute("alice", "view_transactions", {})

        assert result.success is True
        assert result.data["transactions"] == []
        assert result.data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_view_transactions_with_history(self, initialized_app):
        """Test viewing transactions after transfers."""
        # Make some transfers
        await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": 50.0}
        )
        await initialized_app.execute(
            "alice", "transfer", {"to": "charlie", "amount": 25.0}
        )

        result = await initialized_app.execute("alice", "view_transactions", {})

        assert result.success is True
        assert result.data["total_count"] == 2
        assert len(result.data["transactions"]) == 2

        # Verify transaction details
        for tx in result.data["transactions"]:
            assert tx["type"] == "sent"
            assert "counterparty" in tx
            assert "amount" in tx


class TestStateSnapshot:
    """Tests for state snapshot/restore."""

    @pytest.mark.asyncio
    async def test_snapshot_and_restore(self, initialized_app):
        """Test that state can be saved and restored."""
        # Make some changes
        await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": 200.0}
        )
        await initialized_app.execute(
            "bob", "request_money", {"from": "charlie", "amount": 50.0}
        )

        # Snapshot
        snapshot = initialized_app.get_state_snapshot()
        assert isinstance(snapshot, bytes)
        assert len(snapshot) > 0

        # Create new app and restore
        new_app = PayPalApp()
        await new_app.initialize(
            sim_id="test-sim-2",
            agents=["alice", "bob", "charlie"],
            config={"initial_balance": 0},  # Different config
        )

        # Restore
        new_app.restore_state(snapshot)

        # Verify state matches
        alice_state = await new_app.get_agent_state("alice")
        bob_state = await new_app.get_agent_state("bob")

        assert alice_state["balance"] == 800.0
        assert bob_state["balance"] == 1200.0


class TestActionLog:
    """Tests for action audit log."""

    @pytest.mark.asyncio
    async def test_action_log_recorded(self, initialized_app):
        """Test that actions are logged."""
        await initialized_app.execute("alice", "check_balance", {})
        await initialized_app.execute(
            "alice", "transfer", {"to": "bob", "amount": 50.0}
        )

        log = initialized_app.get_action_log()
        assert len(log) == 2

        # Most recent first
        assert log[0].action_name == "transfer"
        assert log[1].action_name == "check_balance"

    @pytest.mark.asyncio
    async def test_action_log_filter_by_agent(self, initialized_app):
        """Test filtering action log by agent."""
        await initialized_app.execute("alice", "check_balance", {})
        await initialized_app.execute("bob", "check_balance", {})

        alice_log = initialized_app.get_action_log(agent_id="alice")
        bob_log = initialized_app.get_action_log(agent_id="bob")

        assert len(alice_log) == 1
        assert len(bob_log) == 1
        assert alice_log[0].agent_id == "alice"
        assert bob_log[0].agent_id == "bob"
