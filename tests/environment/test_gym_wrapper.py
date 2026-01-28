"""Tests for Gymnasium-compatible environment wrappers.

Tests the τ²-bench dual-control Gymnasium environments per ADR-020.1.
"""

import pytest
from unittest.mock import MagicMock, patch


# Skip all tests if gymnasium not installed
pytest.importorskip("gymnasium")


class TestDualControlAgentEnv:
    """Tests for the agent-side Gymnasium environment."""

    @pytest.fixture
    def mock_task(self):
        """Create a mock DualControlTaskDefinition."""
        from agentworld.tasks.dual_control import (
            DualControlTaskDefinition,
            CoordinationHandoff,
        )
        from agentworld.apps.definition import AgentRole

        # Create minimal task definition
        task = MagicMock(spec=DualControlTaskDefinition)
        task.task_id = "test_task_001"
        task.name = "Test Task"
        task.domain = "test"
        task.difficulty = "easy"
        task.initial_state = {
            "test_app": {"per_agent": {}, "shared": {"status": "initial"}}
        }
        task.goal_state = {
            "test_app": {"per_agent": {}, "shared": {"status": "completed"}}
        }

        # Mock agent and user configs
        task.agent_config = MagicMock()
        task.agent_config.apps = [{"id": "agent_app"}]
        task.agent_config.initial_message = None

        task.user_config = MagicMock()
        task.user_config.apps = [{"id": "user_app"}]
        task.user_config.initial_message = "I need help"

        task.coordination_handoffs = []

        return task

    def test_env_creation(self, mock_task):
        """Test environment can be created."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task, max_steps=10)
        assert env is not None
        assert env.max_steps == 10

    def test_env_reset(self, mock_task):
        """Test environment reset returns valid observation."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task)
        obs, info = env.reset()

        assert isinstance(obs, dict)
        assert "conversation" in obs
        assert "backend_state" in obs
        assert "step" in obs
        assert info["task_id"] == "test_task_001"

    def test_env_step(self, mock_task):
        """Test environment step executes correctly."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task)
        env.reset()

        # Take a step with agent action
        obs, reward, terminated, truncated, info = env.step(
            "Please check your settings"
        )

        assert isinstance(obs, dict)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_env_truncation(self, mock_task):
        """Test environment truncates after max_steps."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task, max_steps=3)
        env.reset()

        # Take steps until truncation
        for i in range(4):
            obs, reward, terminated, truncated, info = env.step(f"Action {i}")
            if truncated:
                break

        assert truncated is True
        assert env._state.step_count == 3

    def test_env_confusion_detection(self, mock_task):
        """Test user confusion detection affects reward."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task)
        env.reset()

        # Simulate confusion detection
        assert env._detect_user_confusion("I don't understand") is True
        assert env._detect_user_confusion("OK, done") is False

    def test_env_render(self, mock_task):
        """Test environment rendering."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task, render_mode="ansi")
        env.reset()
        env.step("Hello")

        output = env.render()
        assert output is not None
        assert "Step:" in output

    def test_env_close(self, mock_task):
        """Test environment cleanup."""
        from agentworld.environment.gym_wrapper import DualControlAgentEnv

        env = DualControlAgentEnv(task=mock_task)
        env.reset()
        env.close()

        assert env._state is None


class TestDualControlUserEnv:
    """Tests for the user-side Gymnasium environment."""

    @pytest.fixture
    def mock_task(self):
        """Create a mock task for user env."""
        task = MagicMock()
        task.task_id = "test_task_002"
        task.initial_state = {"app": {"status": "start"}}
        task.goal_state = {"app": {"status": "done"}}

        task.agent_config = MagicMock()
        task.agent_config.initial_message = "Please follow my instructions"

        task.user_config = MagicMock()
        task.user_config.apps = [{"id": "user_app"}]

        return task

    def test_user_env_creation(self, mock_task):
        """Test user environment creation."""
        from agentworld.environment.gym_wrapper import DualControlUserEnv

        env = DualControlUserEnv(task=mock_task, state_constrained=True)
        assert env is not None
        assert env.state_constrained is True

    def test_user_env_reset(self, mock_task):
        """Test user environment reset."""
        from agentworld.environment.gym_wrapper import DualControlUserEnv

        env = DualControlUserEnv(task=mock_task)
        obs, info = env.reset()

        assert "conversation" in obs
        assert "device_state" in obs


class TestEnvironmentRegistration:
    """Tests for Gymnasium environment registration."""

    def test_register_environments(self):
        """Test environments can be registered with gymnasium."""
        from agentworld.environment.gym_wrapper import register_environments

        # Should not raise
        register_environments()

    def test_environments_registered(self):
        """Test registered environments can be looked up."""
        import gymnasium as gym
        from agentworld.environment.gym_wrapper import register_environments

        register_environments()

        # Check environments are in registry
        # Note: This may fail if already registered, which is OK
        spec = gym.spec("AgentWorld/DualControl-Agent-v0")
        assert spec is not None
