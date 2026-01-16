"""Tests for simulation control mechanisms."""

import asyncio
import pytest

from agentworld.simulation.control import (
    ErrorStrategy,
    ControlSignal,
    StepConfig,
    SimulationController,
    with_timeout,
    retry_with_backoff,
    TimeoutResult,
)


class TestErrorStrategy:
    """Tests for ErrorStrategy enum."""

    def test_strategies_exist(self):
        """Test that all strategies exist."""
        assert ErrorStrategy.FAIL_FAST.value == "fail_fast"
        assert ErrorStrategy.LOG_AND_CONTINUE.value == "log_and_continue"
        assert ErrorStrategy.RETRY.value == "retry"
        assert ErrorStrategy.SUSPEND_AGENT.value == "suspend_agent"


class TestControlSignal:
    """Tests for ControlSignal enum."""

    def test_signals_exist(self):
        """Test that all signals exist."""
        assert ControlSignal.PAUSE.value == "pause"
        assert ControlSignal.RESUME.value == "resume"
        assert ControlSignal.CANCEL.value == "cancel"
        assert ControlSignal.STEP.value == "step"


class TestStepConfig:
    """Tests for StepConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = StepConfig()

        assert config.max_concurrent_agents == 5
        assert config.max_concurrent_llm_calls == 10
        assert config.step_timeout_seconds == 60.0
        assert config.agent_timeout_seconds == 30.0
        assert config.on_agent_error == ErrorStrategy.LOG_AND_CONTINUE
        assert config.max_consecutive_failures == 3
        assert config.checkpoint_every_n_steps == 0
        assert config.auto_checkpoint_on_pause is True

    def test_custom_values(self):
        """Test custom values."""
        config = StepConfig(
            max_concurrent_agents=10,
            max_concurrent_llm_calls=20,
            step_timeout_seconds=120.0,
            on_agent_error=ErrorStrategy.FAIL_FAST,
        )

        assert config.max_concurrent_agents == 10
        assert config.max_concurrent_llm_calls == 20
        assert config.step_timeout_seconds == 120.0
        assert config.on_agent_error == ErrorStrategy.FAIL_FAST

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = StepConfig()
        data = config.to_dict()

        assert data["max_concurrent_agents"] == 5
        assert data["on_agent_error"] == "log_and_continue"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "max_concurrent_agents": 8,
            "on_agent_error": "fail_fast",
            "step_timeout_seconds": 90.0,
        }
        config = StepConfig.from_dict(data)

        assert config.max_concurrent_agents == 8
        assert config.on_agent_error == ErrorStrategy.FAIL_FAST
        assert config.step_timeout_seconds == 90.0


class TestSimulationController:
    """Tests for SimulationController."""

    @pytest.fixture
    def controller(self):
        """Create controller instance."""
        return SimulationController()

    def test_initial_state(self, controller):
        """Test initial controller state."""
        assert not controller.is_paused
        assert not controller.is_cancelled
        assert len(controller.suspended_agents) == 0

    def test_pause_resume(self, controller):
        """Test pause and resume."""
        controller.pause()
        assert controller.is_paused

        controller.resume()
        assert not controller.is_paused

    def test_cancel(self, controller):
        """Test cancellation."""
        controller.cancel()
        assert controller.is_cancelled
        assert controller.should_terminate()

    def test_record_agent_success(self, controller):
        """Test recording agent success."""
        controller._agent_failures["agent1"] = 2
        controller.record_agent_success("agent1")

        assert controller.get_failure_count("agent1") == 0

    def test_record_agent_failure(self, controller):
        """Test recording agent failure."""
        controller.record_agent_failure("agent1")
        controller.record_agent_failure("agent1")

        assert controller.get_failure_count("agent1") == 2

    def test_agent_suspension(self, controller):
        """Test agent suspension after max failures."""
        controller.config = StepConfig(
            on_agent_error=ErrorStrategy.SUSPEND_AGENT,
            max_consecutive_failures=3,
        )

        # Fail 3 times
        controller.record_agent_failure("agent1")
        controller.record_agent_failure("agent1")
        suspended = controller.record_agent_failure("agent1")

        assert suspended
        assert controller.is_agent_suspended("agent1")
        assert "agent1" in controller.suspended_agents

    def test_unsuspend_agent(self, controller):
        """Test unsuspending an agent."""
        controller._suspended_agents.add("agent1")
        controller._agent_failures["agent1"] = 3

        controller.unsuspend_agent("agent1")

        assert not controller.is_agent_suspended("agent1")
        assert controller.get_failure_count("agent1") == 0

    def test_unsuspend_all(self, controller):
        """Test unsuspending all agents."""
        controller._suspended_agents.add("agent1")
        controller._suspended_agents.add("agent2")
        controller._agent_failures["agent1"] = 3
        controller._agent_failures["agent2"] = 3

        controller.unsuspend_all()

        assert len(controller.suspended_agents) == 0
        assert controller.get_failure_count("agent1") == 0
        assert controller.get_failure_count("agent2") == 0

    def test_reset(self, controller):
        """Test controller reset."""
        controller.pause()
        controller._suspended_agents.add("agent1")
        controller._agent_failures["agent1"] = 3

        controller.reset()

        assert not controller.is_paused
        assert not controller.is_cancelled
        assert len(controller.suspended_agents) == 0


class TestWithTimeout:
    """Tests for with_timeout function."""

    @pytest.mark.asyncio
    async def test_completes_in_time(self):
        """Test coroutine that completes within timeout."""

        async def quick_task():
            await asyncio.sleep(0.01)
            return "done"

        result, timeout_result = await with_timeout(quick_task(), timeout_seconds=1.0)

        assert result == "done"
        assert timeout_result.completed
        assert not timeout_result.timed_out
        assert timeout_result.duration_seconds < 1.0

    @pytest.mark.asyncio
    async def test_times_out(self):
        """Test coroutine that times out."""

        async def slow_task():
            await asyncio.sleep(10.0)
            return "done"

        result, timeout_result = await with_timeout(slow_task(), timeout_seconds=0.1)

        assert result is None
        assert not timeout_result.completed
        assert timeout_result.timed_out
        assert timeout_result.duration_seconds >= 0.1

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test coroutine that raises an error."""

        async def error_task():
            raise ValueError("Test error")

        result, timeout_result = await with_timeout(error_task(), timeout_seconds=1.0)

        assert result is None
        assert not timeout_result.completed
        assert not timeout_result.timed_out
        assert "Test error" in timeout_result.error


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        """Test success on first try."""
        call_count = 0

        async def success_task():
            nonlocal call_count
            call_count += 1
            return "done"

        result, retries = await retry_with_backoff(
            coro_factory=success_task,
            max_retries=3,
            base_delay=0.01,
        )

        assert result == "done"
        assert retries == 0
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_succeeds_after_retries(self):
        """Test success after some retries."""
        call_count = 0

        async def eventual_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "done"

        result, retries = await retry_with_backoff(
            coro_factory=eventual_success,
            max_retries=3,
            base_delay=0.01,
        )

        assert result == "done"
        assert retries == 2
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self):
        """Test failure after max retries."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_with_backoff(
                coro_factory=always_fails,
                max_retries=2,
                base_delay=0.01,
            )

        assert call_count == 3  # Initial + 2 retries
