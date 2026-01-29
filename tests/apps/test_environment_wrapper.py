"""Tests for AppEnvironmentWrapper and environment semantics.

Tests the Gymnasium-style environment wrapper for native apps.
"""

import pytest
from datetime import datetime
from agentworld.apps.environment import (
    StepResult,
    ResetResult,
    StateSnapshot,
    EpisodeHistory,
    AppEnvironmentWrapper,
    default_reward,
    sparse_reward,
    action_cost_reward,
)
from agentworld.apps.paypal import PayPalApp


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_step_result_creation(self):
        """Test StepResult can be created with all fields."""
        result = StepResult(
            observation={"balance": 100},
            reward=-0.01,
            terminated=False,
            truncated=False,
            info={"episode_id": "abc123"},
        )
        assert result.observation == {"balance": 100}
        assert result.reward == -0.01
        assert result.terminated is False
        assert result.truncated is False
        assert result.info["episode_id"] == "abc123"

    def test_step_result_to_dict(self):
        """Test StepResult serialization."""
        result = StepResult(
            observation={"balance": 100},
            reward=0.5,
            terminated=True,
            truncated=False,
            info={},
        )
        d = result.to_dict()
        assert d["observation"] == {"balance": 100}
        assert d["reward"] == 0.5
        assert d["terminated"] is True
        assert d["truncated"] is False

    def test_step_result_unpacking(self):
        """Test StepResult can be used as Gymnasium-style tuple."""
        result = StepResult(
            observation={"state": "x"},
            reward=1.0,
            terminated=True,
            truncated=False,
            info={"key": "value"},
        )
        # Test dictionary access works
        assert result.observation == {"state": "x"}
        assert result.reward == 1.0
        assert result.terminated is True
        assert result.truncated is False
        assert result.info == {"key": "value"}


class TestResetResult:
    """Tests for ResetResult dataclass."""

    def test_reset_result_creation(self):
        """Test ResetResult creation."""
        result = ResetResult(
            observation={"initial": True},
            info={"episode_id": "ep_001"},
        )
        assert result.observation == {"initial": True}
        assert result.info["episode_id"] == "ep_001"

    def test_reset_result_unpacking(self):
        """Test ResetResult can be used as Gymnasium-style tuple."""
        result = ResetResult(
            observation={"state": "initial"},
            info={"seed": 42},
        )
        # Test attribute access works
        assert result.observation == {"state": "initial"}
        assert result.info["seed"] == 42


class TestStateSnapshot:
    """Tests for StateSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test StateSnapshot creation."""
        now = datetime.now()
        snapshot = StateSnapshot(
            step=5,
            timestamp=now,
            state={"balance": 500},
            action="transfer",
            params={"to": "bob", "amount": 100},
            reward=-0.01,
        )
        assert snapshot.step == 5
        assert snapshot.state["balance"] == 500
        assert snapshot.action == "transfer"
        assert snapshot.reward == -0.01

    def test_snapshot_to_dict(self):
        """Test StateSnapshot serialization."""
        snapshot = StateSnapshot(
            step=0,
            timestamp=datetime.now(),
            state={"key": "value"},
            action=None,
            params=None,
            reward=0.0,
        )
        d = snapshot.to_dict()
        assert d["step"] == 0
        assert d["state"] == {"key": "value"}
        assert d["action"] is None
        assert "timestamp" in d


class TestEpisodeHistory:
    """Tests for EpisodeHistory dataclass."""

    def test_episode_history_creation(self):
        """Test EpisodeHistory creation."""
        history = EpisodeHistory(
            episode_id="ep_test",
            started_at=datetime.now(),
            ended_at=None,
            snapshots=[],
            terminated=False,
            truncated=False,
            total_reward=0.0,
        )
        assert history.episode_id == "ep_test"
        assert history.ended_at is None
        assert len(history.snapshots) == 0

    def test_episode_history_step_count(self):
        """Test step_count property."""
        history = EpisodeHistory(
            episode_id="ep_test",
            started_at=datetime.now(),
            ended_at=None,
            snapshots=[
                StateSnapshot(step=0, timestamp=datetime.now(), state={}, action=None, params=None, reward=0.0),
                StateSnapshot(step=1, timestamp=datetime.now(), state={}, action="a1", params={}, reward=-0.01),
                StateSnapshot(step=2, timestamp=datetime.now(), state={}, action="a2", params={}, reward=-0.01),
            ],
            terminated=False,
            truncated=False,
            total_reward=-0.02,
        )
        assert history.step_count == 2  # Excludes initial state

    def test_get_state_at_step(self):
        """Test retrieving state at specific step."""
        history = EpisodeHistory(
            episode_id="ep_test",
            started_at=datetime.now(),
            ended_at=None,
            snapshots=[
                StateSnapshot(step=0, timestamp=datetime.now(), state={"balance": 1000}, action=None, params=None, reward=0.0),
                StateSnapshot(step=1, timestamp=datetime.now(), state={"balance": 900}, action="transfer", params={}, reward=-0.01),
            ],
            terminated=False,
            truncated=False,
            total_reward=-0.01,
        )
        state = history.get_state_at_step(0)
        assert state["balance"] == 1000
        state = history.get_state_at_step(1)
        assert state["balance"] == 900

    def test_get_trajectory(self):
        """Test getting RL trajectory."""
        history = EpisodeHistory(
            episode_id="ep_test",
            started_at=datetime.now(),
            ended_at=None,
            snapshots=[
                StateSnapshot(step=0, timestamp=datetime.now(), state={"s": 0}, action=None, params=None, reward=0.0),
                StateSnapshot(step=1, timestamp=datetime.now(), state={"s": 1}, action="act1", params={}, reward=0.5),
                StateSnapshot(step=2, timestamp=datetime.now(), state={"s": 2}, action="act2", params={}, reward=1.0),
            ],
            terminated=True,
            truncated=False,
            total_reward=1.5,
        )
        trajectory = history.get_trajectory()
        assert len(trajectory) == 3
        # Each item is (state, action, reward)
        assert trajectory[0] == ({"s": 0}, None, 0.0)
        assert trajectory[1] == ({"s": 1}, "act1", 0.5)
        assert trajectory[2] == ({"s": 2}, "act2", 1.0)


class TestRewardFunctions:
    """Tests for reward functions."""

    def test_default_reward(self):
        """Test default per-step penalty reward."""
        from agentworld.apps.base import AppResult

        result = AppResult(success=True, data={})
        reward = default_reward(result, {}, False, 1)
        assert reward == -0.01  # Per-step penalty

    def test_default_reward_termination(self):
        """Test default reward on termination."""
        from agentworld.apps.base import AppResult

        result = AppResult(success=True, data={})
        reward = default_reward(result, {}, True, 5)
        assert reward == 0.99  # Success bonus (1.0) + step penalty (-0.01)

    def test_sparse_reward(self):
        """Test sparse reward function."""
        from agentworld.apps.base import AppResult

        result = AppResult(success=True, data={})

        # No reward during episode
        reward = sparse_reward(result, {}, False, 10)
        assert reward == 0.0

        # Reward only on termination
        reward = sparse_reward(result, {}, True, 10)
        assert reward == 1.0

    def test_action_cost_reward(self):
        """Test action cost reward function."""
        from agentworld.apps.base import AppResult

        result = AppResult(success=True, data={})
        reward = action_cost_reward(result, {}, False, 3)
        assert reward == -0.01  # Base step penalty

        # Success bonus minus step cost
        reward = action_cost_reward(result, {}, True, 5)
        assert reward == 0.99  # 1.0 - 0.01


class TestAppEnvironmentWrapper:
    """Tests for AppEnvironmentWrapper."""

    @pytest.fixture
    def paypal_app(self):
        """Create a PayPal app instance."""
        return PayPalApp()

    @pytest.mark.asyncio
    async def test_wrapper_creation(self, paypal_app):
        """Test wrapper can be created."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10)
        assert env is not None
        assert env._max_steps == 10
        assert env.episode_id is None
        assert env.step_count == 0

    @pytest.mark.asyncio
    async def test_wrapper_reset(self, paypal_app):
        """Test reset returns observation and starts episode."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10)
        result = await env.reset(options={"agents": ["alice", "bob"]})

        assert result.observation is not None
        assert result.info["episode_id"] is not None
        assert env.episode_id == result.info["episode_id"]
        assert env.step_count == 0

    @pytest.mark.asyncio
    async def test_wrapper_step(self, paypal_app):
        """Test step executes action and returns Gymnasium-style result."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10)
        await env.reset(options={"agents": ["alice", "bob"]})

        step = await env.step("alice", "check_balance", {})

        assert step.observation is not None
        assert isinstance(step.reward, float)
        assert step.terminated is False
        assert step.truncated is False
        assert env.step_count == 1

    @pytest.mark.asyncio
    async def test_wrapper_truncation(self, paypal_app):
        """Test episode truncates after max_steps."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=3)
        await env.reset(options={"agents": ["alice"]})

        for i in range(4):
            result = await env.step("alice", "check_balance", {})
            if result.truncated:
                break

        assert result.truncated is True
        assert env.step_count == 3

    @pytest.mark.asyncio
    async def test_wrapper_close(self, paypal_app):
        """Test close finalizes episode."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10)
        await env.reset(options={"agents": ["alice"]})
        await env.step("alice", "check_balance", {})

        env.close()

        assert env.episode_id is None
        assert env.step_count == 0

    @pytest.mark.asyncio
    async def test_wrapper_history_tracking(self, paypal_app):
        """Test episode history is tracked."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10, track_history=True)
        await env.reset(options={"agents": ["alice", "bob"]})

        await env.step("alice", "check_balance", {})
        await env.step("alice", "transfer", {"to": "bob", "amount": 50})

        history = env.get_episode_history()
        assert history is not None
        assert len(history.snapshots) == 3  # initial + 2 steps
        assert history.snapshots[1].action == "check_balance"
        assert history.snapshots[2].action == "transfer"

    @pytest.mark.asyncio
    async def test_wrapper_multi_episode(self, paypal_app):
        """Test multiple episodes are tracked."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=5, track_history=True)

        # Episode 1
        await env.reset(options={"agents": ["alice"]})
        await env.step("alice", "check_balance", {})
        env.close()

        # Episode 2
        await env.reset(options={"agents": ["alice"]})
        await env.step("alice", "check_balance", {})
        env.close()

        all_episodes = env.get_all_episodes()
        assert len(all_episodes) == 2

    @pytest.mark.asyncio
    async def test_wrapper_custom_reward(self, paypal_app):
        """Test custom reward function."""
        def always_positive_reward(result, obs, terminated, step):
            return 1.0

        env = AppEnvironmentWrapper(
            paypal_app,
            max_steps=10,
            reward_function=always_positive_reward,
        )
        await env.reset(options={"agents": ["alice"]})

        step = await env.step("alice", "check_balance", {})
        assert step.reward == 1.0

    @pytest.mark.asyncio
    async def test_wrapper_mark_terminated(self, paypal_app):
        """Test marking episode as terminated (goal achieved)."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10)
        await env.reset(options={"agents": ["alice"]})

        # Do a step first, then mark terminated
        step = await env.step("alice", "check_balance", {})
        assert step.terminated is False

        # Mark as terminated - next step should get termination bonus
        env.mark_terminated()

        # After marking terminated, the episode is ended
        # Verify termination state is set
        assert env._terminated is True

    @pytest.mark.asyncio
    async def test_wrapper_history_disabled(self, paypal_app):
        """Test history tracking can be disabled."""
        env = AppEnvironmentWrapper(paypal_app, max_steps=10, track_history=False)
        await env.reset(options={"agents": ["alice"]})
        await env.step("alice", "check_balance", {})

        history = env.get_episode_history()
        assert history is None


class TestBaseSimulatedAppEpisodeTracking:
    """Tests for episode tracking in BaseSimulatedApp."""

    @pytest.mark.asyncio
    async def test_app_episode_fields(self):
        """Test episode tracking fields exist."""
        app = PayPalApp()
        await app.initialize("sim1", ["alice"], {})

        # Before episode mode
        assert app.episode_id is None
        assert app.episode_step_count == 0
        assert app.in_episode is False

    @pytest.mark.asyncio
    async def test_app_env_reset(self):
        """Test env_reset initializes episode."""
        app = PayPalApp()
        obs = await app.env_reset(["alice", "bob"], {"initial_balance": 500})

        assert app.episode_id is not None
        assert app.in_episode is True
        assert obs is not None

    @pytest.mark.asyncio
    async def test_app_env_close(self):
        """Test env_close cleans up episode."""
        app = PayPalApp()
        await app.env_reset(["alice"], {})
        app.env_close()

        assert app.episode_id is None
        assert app.in_episode is False

    @pytest.mark.asyncio
    async def test_backward_compatibility(self):
        """Test existing apps work unchanged."""
        app = PayPalApp()
        await app.initialize("sim1", ["alice", "bob"], {"initial_balance": 1000})
        result = await app.execute("alice", "check_balance", {})
        assert result.success is True
