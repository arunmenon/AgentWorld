"""Test scenario runner for ADR-021.

This module provides YAML-based test scenarios for apps:
- Define test steps with expected outcomes
- Chain state between steps
- Assert final state conditions
- Generate detailed failure reports
"""

from dataclasses import dataclass, field
from typing import Any
import time
import yaml


@dataclass
class StepExpectation:
    """Expected outcome for a test step.

    Attributes:
        success: Whether action should succeed
        data: Expected fields in result data
        error_contains: Expected substring in error message
        state: Expected state values after step
    """
    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    error_contains: str | None = None
    state: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "StepExpectation":
        """Create from dictionary."""
        return cls(
            success=d.get("success", True),
            data=d.get("data", {}),
            error_contains=d.get("error_contains"),
            state=d.get("state", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error_contains": self.error_contains,
            "state": self.state,
        }


@dataclass
class TestStep:
    """A single test step in a scenario.

    Attributes:
        name: Human-readable step name
        agent: Agent performing the action
        action: Action name to execute
        params: Action parameters
        expect: Expected outcome
    """
    name: str
    agent: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    expect: StepExpectation = field(default_factory=StepExpectation)

    @classmethod
    def from_dict(cls, d: dict) -> "TestStep":
        """Create from dictionary."""
        expect_data = d.get("expect", {})
        return cls(
            name=d.get("name", "Unnamed step"),
            agent=d.get("agent", ""),
            action=d.get("action", ""),
            params=d.get("params", {}),
            expect=StepExpectation.from_dict(expect_data),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "agent": self.agent,
            "action": self.action,
            "params": self.params,
            "expect": self.expect.to_dict(),
        }


@dataclass
class TestScenario:
    """A complete test scenario.

    Attributes:
        name: Scenario name
        description: Scenario description
        app_id: App to test
        setup: Initial setup configuration
        steps: List of test steps
        assertions: Final state assertions
        stop_on_failure: Whether to stop on first failure
    """
    name: str
    description: str
    app_id: str
    setup: dict[str, Any] = field(default_factory=dict)
    steps: list[TestStep] = field(default_factory=list)
    assertions: list[str] = field(default_factory=list)
    stop_on_failure: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> "TestScenario":
        """Create from dictionary."""
        steps = [TestStep.from_dict(s) for s in d.get("steps", [])]
        return cls(
            name=d.get("name", "Unnamed scenario"),
            description=d.get("description", ""),
            app_id=d.get("app_id", ""),
            setup=d.get("setup", {}),
            steps=steps,
            assertions=d.get("assertions", []),
            stop_on_failure=d.get("stop_on_failure", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "app_id": self.app_id,
            "setup": self.setup,
            "steps": [s.to_dict() for s in self.steps],
            "assertions": self.assertions,
            "stop_on_failure": self.stop_on_failure,
        }


@dataclass
class StepFailure:
    """Details of a failed step.

    Attributes:
        step_name: Name of the failed step
        step_index: Index in the step list
        failure_type: Type of failure
        expected: What was expected
        actual: What actually happened
        error: Error message if any
    """
    step_name: str
    step_index: int
    failure_type: str  # 'success_mismatch', 'data_mismatch', 'state_mismatch', 'error_mismatch'
    expected: Any
    actual: Any
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_name": self.step_name,
            "step_index": self.step_index,
            "failure_type": self.failure_type,
            "expected": self.expected,
            "actual": self.actual,
            "error": self.error,
        }


@dataclass
class StepResult:
    """Result of executing a single step.

    Attributes:
        step_name: Name of the step
        step_index: Index in the step list
        passed: Whether step passed
        action_result: Raw result from app
        state_after: State after execution
        failure: Failure details if failed
        duration_ms: Execution time in milliseconds
    """
    step_name: str
    step_index: int
    passed: bool
    action_result: dict[str, Any] = field(default_factory=dict)
    state_after: dict[str, Any] = field(default_factory=dict)
    failure: StepFailure | None = None
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_name": self.step_name,
            "step_index": self.step_index,
            "passed": self.passed,
            "action_result": self.action_result,
            "state_after": self.state_after,
            "failure": self.failure.to_dict() if self.failure else None,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ScenarioResult:
    """Result of running a test scenario.

    Attributes:
        scenario_name: Name of the scenario
        passed: Whether all steps passed
        steps_passed: Number of passed steps
        steps_total: Total number of steps
        step_results: Results for each step
        failures: List of failures
        assertion_failures: Failed final assertions
        duration_ms: Total execution time
    """
    scenario_name: str
    passed: bool
    steps_passed: int
    steps_total: int
    step_results: list[StepResult] = field(default_factory=list)
    failures: list[StepFailure] = field(default_factory=list)
    assertion_failures: list[str] = field(default_factory=list)
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "passed": self.passed,
            "steps_passed": self.steps_passed,
            "steps_total": self.steps_total,
            "step_results": [r.to_dict() for r in self.step_results],
            "failures": [f.to_dict() for f in self.failures],
            "assertion_failures": self.assertion_failures,
            "duration_ms": self.duration_ms,
        }


def parse_scenario_yaml(yaml_content: str) -> TestScenario:
    """Parse a YAML scenario definition.

    Args:
        yaml_content: YAML string content

    Returns:
        Parsed TestScenario

    Raises:
        ValueError: If YAML is invalid
    """
    try:
        data = yaml.safe_load(yaml_content)
        return TestScenario.from_dict(data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")


def _get_nested_value(obj: dict, path: str) -> Any:
    """Get value from nested dict using dot notation.

    Args:
        obj: Dictionary to traverse
        path: Dot-separated path (e.g., 'alice.balance')

    Returns:
        Value at path or None if not found
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _check_state_expectations(
    expected_state: dict[str, Any],
    actual_state: dict[str, Any],
) -> list[tuple[str, Any, Any]]:
    """Check if actual state matches expected values.

    Args:
        expected_state: Expected state values (dot notation paths)
        actual_state: Actual state dict

    Returns:
        List of (path, expected, actual) for mismatches
    """
    mismatches = []

    for path, expected_value in expected_state.items():
        actual_value = _get_nested_value(actual_state, path)
        if actual_value != expected_value:
            mismatches.append((path, expected_value, actual_value))

    return mismatches


def _evaluate_assertion(assertion: str, state: dict[str, Any]) -> tuple[bool, str]:
    """Evaluate a final assertion.

    Supports simple assertions like:
    - "Final alice.balance == 900"
    - "len(alice.transactions) == 1"

    Args:
        assertion: Assertion string
        state: Current state

    Returns:
        Tuple of (passed, error_message)
    """
    # Extract "Final X.Y == Z" pattern
    assertion = assertion.strip()
    if assertion.startswith("Final "):
        assertion = assertion[6:]

    # Parse comparison
    for op in ["==", "!=", ">=", "<=", ">", "<"]:
        if op in assertion:
            parts = assertion.split(op)
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()

                # Get left value
                if left.startswith("len(") and left.endswith(")"):
                    path = left[4:-1]
                    left_val = _get_nested_value(state, path)
                    left_val = len(left_val) if left_val else 0
                else:
                    left_val = _get_nested_value(state, left)

                # Parse right value
                try:
                    right_val = eval(right)  # Safe for simple literals
                except Exception:
                    right_val = right

                # Compare
                result = False
                if op == "==":
                    result = left_val == right_val
                elif op == "!=":
                    result = left_val != right_val
                elif op == ">=":
                    result = left_val >= right_val
                elif op == "<=":
                    result = left_val <= right_val
                elif op == ">":
                    result = left_val > right_val
                elif op == "<":
                    result = left_val < right_val

                if not result:
                    return False, f"Assertion failed: {left} {op} {right} (got {left_val})"
                return True, ""

    return False, f"Could not parse assertion: {assertion}"


class ScenarioRunner:
    """Executes test scenarios against apps.

    Example:
        from agentworld.apps.dynamic import DynamicApp

        app = DynamicApp(definition)
        runner = ScenarioRunner(app)
        result = await runner.run_scenario(scenario)
        print(f"Passed: {result.passed}")
    """

    def __init__(self, app: Any):
        """Initialize runner with an app.

        Args:
            app: App instance (DynamicApp or SimulatedAppPlugin)
        """
        self.app = app

    async def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        """Run a complete test scenario.

        Args:
            scenario: Scenario to execute

        Returns:
            ScenarioResult with pass/fail and details
        """
        start_time = time.time()

        # Initialize state from setup
        state = self._initialize_state(scenario.setup)

        step_results: list[StepResult] = []
        failures: list[StepFailure] = []
        steps_passed = 0

        for i, step in enumerate(scenario.steps):
            step_start = time.time()

            # Execute the step
            step_result = await self._execute_step(step, i, state)
            step_results.append(step_result)

            if step_result.passed:
                steps_passed += 1
                # Update state for next step
                state = step_result.state_after
            else:
                if step_result.failure:
                    failures.append(step_result.failure)

                if scenario.stop_on_failure:
                    break

        # Run final assertions
        assertion_failures = []
        for assertion in scenario.assertions:
            passed, error = _evaluate_assertion(assertion, state)
            if not passed:
                assertion_failures.append(error)

        total_time = (time.time() - start_time) * 1000

        return ScenarioResult(
            scenario_name=scenario.name,
            passed=len(failures) == 0 and len(assertion_failures) == 0,
            steps_passed=steps_passed,
            steps_total=len(scenario.steps),
            step_results=step_results,
            failures=failures,
            assertion_failures=assertion_failures,
            duration_ms=total_time,
        )

    def _initialize_state(self, setup: dict[str, Any]) -> dict[str, Any]:
        """Initialize app state from setup configuration.

        Args:
            setup: Setup configuration with initial_state

        Returns:
            Initialized state dict
        """
        initial_state = setup.get("initial_state", {})

        # Build state structure
        state = {
            "per_agent": initial_state.get("per_agent", {}),
            "shared": initial_state.get("shared", {}),
        }

        # Initialize app if it has initialize method
        if hasattr(self.app, "_state"):
            self.app._state = state.get("per_agent", {})
        if hasattr(self.app, "_shared_state"):
            self.app._shared_state = state.get("shared", {})

        return state

    async def _execute_step(
        self,
        step: TestStep,
        index: int,
        state: dict[str, Any],
    ) -> StepResult:
        """Execute a single test step.

        Args:
            step: Step to execute
            index: Step index
            state: Current state

        Returns:
            StepResult with outcome
        """
        start_time = time.time()

        try:
            # Execute the action
            if hasattr(self.app, "execute_stateless"):
                # Use stateless execution for testing
                result = await self.app.execute_stateless(
                    agent_id=step.agent,
                    action=step.action,
                    params=step.params,
                    state=state.get("per_agent", {}),
                )
            else:
                # Use regular execute
                result = await self.app.execute(
                    agent_id=step.agent,
                    action=step.action,
                    params=step.params,
                )

            duration = (time.time() - start_time) * 1000

            # Convert result to dict
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()
            elif hasattr(result, "__dict__"):
                result_dict = {
                    "success": getattr(result, "success", False),
                    "data": getattr(result, "data", {}),
                    "error": getattr(result, "error", None),
                }
            else:
                result_dict = {"success": False, "error": "Unknown result type"}

            # Get state after execution
            if hasattr(result, "state_after"):
                state_after = result.state_after
            elif hasattr(self.app, "get_state_snapshot"):
                state_after = self.app.get_state_snapshot()
            else:
                state_after = state

            # Check expectations
            failure = self._check_expectations(step, index, result_dict, state_after)

            return StepResult(
                step_name=step.name,
                step_index=index,
                passed=failure is None,
                action_result=result_dict,
                state_after=state_after,
                failure=failure,
                duration_ms=duration,
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000

            # Check if exception was expected
            if not step.expect.success and step.expect.error_contains:
                if step.expect.error_contains in str(e):
                    return StepResult(
                        step_name=step.name,
                        step_index=index,
                        passed=True,
                        action_result={"success": False, "error": str(e)},
                        state_after=state,
                        duration_ms=duration,
                    )

            return StepResult(
                step_name=step.name,
                step_index=index,
                passed=False,
                action_result={"success": False, "error": str(e)},
                state_after=state,
                failure=StepFailure(
                    step_name=step.name,
                    step_index=index,
                    failure_type="exception",
                    expected="success" if step.expect.success else "expected error",
                    actual=str(e),
                    error=str(e),
                ),
                duration_ms=duration,
            )

    def _check_expectations(
        self,
        step: TestStep,
        index: int,
        result: dict[str, Any],
        state_after: dict[str, Any],
    ) -> StepFailure | None:
        """Check if step result matches expectations.

        Args:
            step: The test step
            index: Step index
            result: Action result
            state_after: State after execution

        Returns:
            StepFailure if expectations not met, None otherwise
        """
        expect = step.expect

        # Check success/failure
        actual_success = result.get("success", False)
        if actual_success != expect.success:
            return StepFailure(
                step_name=step.name,
                step_index=index,
                failure_type="success_mismatch",
                expected=f"success={expect.success}",
                actual=f"success={actual_success}",
                error=result.get("error", ""),
            )

        # Check error message
        if not expect.success and expect.error_contains:
            error_msg = result.get("error", "")
            if expect.error_contains not in str(error_msg):
                return StepFailure(
                    step_name=step.name,
                    step_index=index,
                    failure_type="error_mismatch",
                    expected=f"error contains '{expect.error_contains}'",
                    actual=f"error: {error_msg}",
                )

        # Check result data
        if expect.data:
            result_data = result.get("data", {})
            for key, expected_value in expect.data.items():
                actual_value = result_data.get(key)
                if actual_value != expected_value:
                    return StepFailure(
                        step_name=step.name,
                        step_index=index,
                        failure_type="data_mismatch",
                        expected={key: expected_value},
                        actual={key: actual_value},
                    )

        # Check state
        if expect.state:
            # Flatten state for checking
            flat_state = {}
            per_agent = state_after.get("per_agent", state_after)
            for agent_id, agent_state in per_agent.items():
                if isinstance(agent_state, dict):
                    for key, value in agent_state.items():
                        flat_state[f"{agent_id}.{key}"] = value

            mismatches = _check_state_expectations(expect.state, flat_state)
            if mismatches:
                path, expected, actual = mismatches[0]
                return StepFailure(
                    step_name=step.name,
                    step_index=index,
                    failure_type="state_mismatch",
                    expected={path: expected},
                    actual={path: actual},
                )

        return None


async def run_scenarios(
    app: Any,
    scenarios: list[TestScenario],
) -> list[ScenarioResult]:
    """Run multiple scenarios against an app.

    Args:
        app: App instance
        scenarios: List of scenarios to run

    Returns:
        List of ScenarioResults
    """
    runner = ScenarioRunner(app)
    results = []

    for scenario in scenarios:
        result = await runner.run_scenario(scenario)
        results.append(result)

    return results
