"""Integration tests for simulated apps in simulations per ADR-017."""

import pytest

from agentworld.apps import SimulationAppManager, PayPalApp, get_app_registry
from agentworld.apps.parser import parse_message


@pytest.fixture
def app_manager():
    """Create an app manager for testing."""
    return SimulationAppManager(simulation_id="test-sim-001")


@pytest.fixture
async def initialized_manager(app_manager):
    """Create and initialize an app manager with PayPal."""
    await app_manager.initialize_apps(
        app_configs=[
            {"id": "paypal", "config": {"initial_balance": 1000.0}},
        ],
        agent_ids=["alice", "bob", "charlie"],
    )
    return app_manager


class TestAppManagerInitialization:
    """Tests for app manager initialization."""

    @pytest.mark.asyncio
    async def test_initialize_with_paypal(self, app_manager):
        """Test initializing manager with PayPal app."""
        await app_manager.initialize_apps(
            app_configs=[{"id": "paypal", "config": {"initial_balance": 500}}],
            agent_ids=["alice", "bob"],
        )

        assert "paypal" in app_manager.get_app_ids()
        app = app_manager.get_app("paypal")
        assert app is not None

    @pytest.mark.asyncio
    async def test_initialize_with_unknown_app(self, app_manager):
        """Test initializing with unknown app is graceful."""
        await app_manager.initialize_apps(
            app_configs=[{"id": "unknown_app"}],
            agent_ids=["alice"],
        )

        assert "unknown_app" not in app_manager.get_app_ids()

    @pytest.mark.asyncio
    async def test_initialize_multiple_agents(self, initialized_manager):
        """Test that all agents get app state."""
        for agent_id in ["alice", "bob", "charlie"]:
            state = await initialized_manager.get_agent_state("paypal", agent_id)
            assert "balance" in state or "error" not in state


class TestMessageProcessing:
    """Tests for processing agent messages with actions."""

    @pytest.mark.asyncio
    async def test_process_message_with_action(self, initialized_manager):
        """Test processing message containing app action."""
        message = """Sure, let me send you some money.
APP_ACTION: paypal.transfer(to="bob", amount=50)
Done!"""

        cleaned, results = await initialized_manager.process_message("alice", message)

        assert len(results) == 1
        assert results[0].result.success is True
        assert "APP_ACTION" not in cleaned
        assert "send you some money" in cleaned

    @pytest.mark.asyncio
    async def test_process_message_without_action(self, initialized_manager):
        """Test processing message without any actions."""
        message = "Hello, how are you doing today?"

        cleaned, results = await initialized_manager.process_message("alice", message)

        assert len(results) == 0
        assert cleaned == message

    @pytest.mark.asyncio
    async def test_process_message_with_failed_action(self, initialized_manager):
        """Test processing message with action that fails."""
        message = """Let me try to send too much.
APP_ACTION: paypal.transfer(to="bob", amount=5000)
Oops!"""

        cleaned, results = await initialized_manager.process_message("alice", message)

        assert len(results) == 1
        assert results[0].result.success is False
        assert "insufficient" in results[0].result.error.lower()

    @pytest.mark.asyncio
    async def test_process_multiple_actions(self, initialized_manager):
        """Test processing message with multiple actions."""
        message = """Let me do several things.
APP_ACTION: paypal.check_balance()
APP_ACTION: paypal.transfer(to="bob", amount=25)"""

        cleaned, results = await initialized_manager.process_message("alice", message)

        assert len(results) == 2
        assert results[0].action.action == "check_balance"
        assert results[1].action.action == "transfer"


class TestObservations:
    """Tests for app observations."""

    @pytest.mark.asyncio
    async def test_observations_after_transfer(self, initialized_manager):
        """Test that transfer creates observation for recipient."""
        # Alice transfers to Bob
        await initialized_manager.process_message(
            "alice",
            'APP_ACTION: paypal.transfer(to="bob", amount=100)'
        )

        # Bob should have observation
        observations = await initialized_manager.get_agent_observations("bob")
        assert len(observations) >= 1
        assert any("received" in obs.message.lower() for obs in observations)

    @pytest.mark.asyncio
    async def test_observations_cleared_after_retrieval(self, initialized_manager):
        """Test that observations are cleared after retrieval."""
        # Create observation
        await initialized_manager.process_message(
            "alice",
            'APP_ACTION: paypal.transfer(to="bob", amount=50)'
        )

        # Get observations (should clear them)
        obs1 = await initialized_manager.get_agent_observations("bob")
        assert len(obs1) >= 1

        # Get again (should be empty)
        obs2 = await initialized_manager.get_agent_observations("bob")
        assert len(obs2) == 0

    @pytest.mark.asyncio
    async def test_format_observations_for_context(self, initialized_manager):
        """Test formatting observations into context string."""
        # Create observation
        await initialized_manager.process_message(
            "alice",
            'APP_ACTION: paypal.transfer(to="bob", amount=75, note="Lunch")'
        )

        observations = await initialized_manager.get_agent_observations("bob")
        formatted = initialized_manager.format_observations_for_context(observations)

        assert "[App Notifications]" in formatted
        assert "PAYPAL" in formatted
        assert "received" in formatted.lower()


class TestStateManagement:
    """Tests for app state management."""

    @pytest.mark.asyncio
    async def test_get_all_states(self, initialized_manager):
        """Test getting all app states."""
        states = initialized_manager.get_all_states()

        assert "paypal" in states
        assert "state" in states["paypal"]

    @pytest.mark.asyncio
    async def test_state_snapshots(self, initialized_manager):
        """Test snapshot and restore."""
        # Make changes
        await initialized_manager.process_message(
            "alice",
            'APP_ACTION: paypal.transfer(to="bob", amount=200)'
        )

        # Snapshot
        snapshots = initialized_manager.get_state_snapshots()
        assert "paypal" in snapshots
        assert len(snapshots["paypal"]) > 0

    @pytest.mark.asyncio
    async def test_step_tracking(self, initialized_manager):
        """Test that current step is tracked."""
        initialized_manager.set_current_step(5)

        # The step should be passed to apps for action logging
        await initialized_manager.process_message(
            "alice",
            "APP_ACTION: paypal.check_balance()"
        )

        # Verify the action was logged (step would be in log)
        app = initialized_manager.get_app("paypal")
        log = app.get_action_log(limit=1)
        # The step should have been set
        assert len(log) > 0


class TestAvailableAppsPrompt:
    """Tests for generating available apps prompt."""

    @pytest.mark.asyncio
    async def test_available_apps_prompt(self, initialized_manager):
        """Test generating prompt for available apps."""
        prompt = initialized_manager.get_available_apps_prompt()

        assert "## Available Applications" in prompt
        assert "PayPal" in prompt
        assert "paypal" in prompt
        assert "check_balance" in prompt
        assert "transfer" in prompt
        assert "APP_ACTION:" in prompt


class TestAppRegistry:
    """Tests for app registry."""

    def test_registry_has_paypal(self):
        """Test that PayPal is registered."""
        registry = get_app_registry()
        app_ids = registry.get_app_ids()

        assert "paypal" in app_ids

    def test_registry_get_paypal(self):
        """Test getting PayPal from registry."""
        registry = get_app_registry()
        app = registry.get("paypal")

        assert app is not None
        assert app.app_id == "paypal"

    def test_registry_list_apps(self):
        """Test listing available apps."""
        registry = get_app_registry()
        apps = registry.list_apps()

        paypal_info = next((a for a in apps if a["id"] == "paypal"), None)
        assert paypal_info is not None
        assert paypal_info["name"] == "PayPal"


class TestEndToEndScenario:
    """End-to-end test scenarios."""

    @pytest.mark.asyncio
    async def test_bill_splitting_scenario(self, initialized_manager):
        """Test a bill splitting scenario between agents."""
        # Initial state: everyone has $1000

        # Alice pays for dinner ($90 total, splits 3 ways = $30 each)
        # Bob and Charlie owe Alice $30 each

        # Bob sends $30 to Alice
        _, results = await initialized_manager.process_message(
            "bob",
            'Thanks for dinner! APP_ACTION: paypal.transfer(to="alice", amount=30, note="Dinner share")'
        )
        assert results[0].result.success

        # Charlie sends $30 to Alice
        _, results = await initialized_manager.process_message(
            "charlie",
            'Here\'s my share! APP_ACTION: paypal.transfer(to="alice", amount=30, note="Dinner share")'
        )
        assert results[0].result.success

        # Verify final balances
        alice_state = await initialized_manager.get_agent_state("paypal", "alice")
        bob_state = await initialized_manager.get_agent_state("paypal", "bob")
        charlie_state = await initialized_manager.get_agent_state("paypal", "charlie")

        assert alice_state["balance"] == 1060.0  # +30 +30
        assert bob_state["balance"] == 970.0  # -30
        assert charlie_state["balance"] == 970.0  # -30

    @pytest.mark.asyncio
    async def test_money_request_flow(self, initialized_manager):
        """Test the money request flow."""
        # Alice requests $50 from Bob
        _, results = await initialized_manager.process_message(
            "alice",
            'APP_ACTION: paypal.request_money(from="bob", amount=50, note="Movie tickets")'
        )
        assert results[0].result.success
        request_id = results[0].result.data["request_id"]

        # Bob receives observation
        bob_obs = await initialized_manager.get_agent_observations("bob")
        assert len(bob_obs) >= 1
        assert any("requested" in obs.message.lower() for obs in bob_obs)

        # Bob pays the request
        _, results = await initialized_manager.process_message(
            "bob",
            f'Sure thing! APP_ACTION: paypal.pay_request(request_id="{request_id}")'
        )
        assert results[0].result.success

        # Alice receives observation
        alice_obs = await initialized_manager.get_agent_observations("alice")
        assert len(alice_obs) >= 1
        assert any("paid" in obs.message.lower() for obs in alice_obs)

        # Verify final balances
        alice_state = await initialized_manager.get_agent_state("paypal", "alice")
        bob_state = await initialized_manager.get_agent_state("paypal", "bob")

        assert alice_state["balance"] == 1050.0
        assert bob_state["balance"] == 950.0
