"""Task execution runner for ADR-020.

This module provides the TaskRunner class for executing tasks
and capturing results for reliability evaluation.
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from agentworld.tasks.definitions import (
    FaultAssignment,
    FaultClassification,
    FaultType,
    GoalState,
    PassKMetrics,
    TaskDefinition,
    TrialResult,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskExecutionConfig:
    """Configuration for task execution.

    Attributes:
        timeout_seconds: Maximum execution time per trial
        retry_on_error: Whether to retry on system errors
        max_retries: Maximum retry attempts
        capture_trajectory: Whether to capture action trajectory
        parallel_trials: Number of trials to run in parallel
    """
    timeout_seconds: float = 300.0  # 5 minutes
    retry_on_error: bool = True
    max_retries: int = 2
    capture_trajectory: bool = True
    parallel_trials: int = 1


@dataclass
class StateVerificationResult:
    """Result of goal state verification.

    Attributes:
        state_match: Whether final state matches expected
        output_match: Whether required outputs are present
        success: Overall success (both matches)
        state_diff: Detailed differences in state
        missing_outputs: Which outputs were missing
        final_state_hash: Hash of final state
        expected_state_hash: Hash of expected state
    """
    state_match: bool
    output_match: bool
    success: bool
    state_diff: list[dict] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)
    final_state_hash: str = ""
    expected_state_hash: str = ""


class TaskRunner:
    """Executes tasks and captures results for evaluation.

    The TaskRunner:
    1. Creates a simulation from task configuration
    2. Runs the simulation with the agent instruction
    3. Captures the final state and trajectory
    4. Verifies against expected outcomes
    5. Classifies any failures

    Example:
        runner = TaskRunner()
        results = await runner.run_trials(task, k=8)
        metrics = PassKMetrics.from_trials(task.task_id, results)
    """

    def __init__(
        self,
        simulation_factory: Callable | None = None,
        config: TaskExecutionConfig | None = None,
    ):
        """Initialize TaskRunner.

        Args:
            simulation_factory: Factory function to create simulations.
                If None, uses default simulation runner.
            config: Execution configuration
        """
        self._simulation_factory = simulation_factory
        self._config = config or TaskExecutionConfig()

    async def run_trial(
        self,
        task: TaskDefinition,
        trial_number: int,
    ) -> TrialResult:
        """Run a single trial of a task.

        Args:
            task: Task definition to execute
            trial_number: Trial number (1-indexed)

        Returns:
            TrialResult with success/failure and details
        """
        trial_id = str(uuid.uuid4())
        start_time = time.time()
        trajectory: list[dict] = []
        simulation_id: str | None = None
        error_message: str | None = None

        try:
            # Create and run simulation
            logger.info(f"Starting trial {trial_number} for task {task.task_id}")

            # Run the simulation
            sim_result = await self._execute_simulation(
                task,
                trajectory_callback=trajectory.append if self._config.capture_trajectory else None,
            )

            simulation_id = sim_result.get("simulation_id")
            final_state = sim_result.get("final_state", {})
            agent_outputs = sim_result.get("agent_outputs", [])
            token_count = sim_result.get("token_count", 0)
            step_count = sim_result.get("step_count", 0)

            # Verify against goal state
            verification = self._verify_goal_state(
                task.get_goal_state(),
                final_state,
                agent_outputs,
            )

            duration = time.time() - start_time

            return TrialResult(
                id=trial_id,
                task_id=task.task_id,
                trial_number=trial_number,
                success=verification.success,
                state_match=verification.state_match,
                output_match=verification.output_match,
                final_state_hash=verification.final_state_hash,
                expected_state_hash=verification.expected_state_hash,
                duration_seconds=duration,
                token_count=token_count,
                step_count=step_count,
                simulation_id=simulation_id,
                trajectory=trajectory,
                created_at=datetime.now(),
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            error_message = f"Task execution timed out after {self._config.timeout_seconds}s"
            logger.warning(f"Trial {trial_number} timed out: {error_message}")

            return TrialResult(
                id=trial_id,
                task_id=task.task_id,
                trial_number=trial_number,
                success=False,
                error_message=error_message,
                duration_seconds=duration,
                simulation_id=simulation_id,
                trajectory=trajectory,
                created_at=datetime.now(),
            )

        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            logger.exception(f"Trial {trial_number} failed with error: {e}")

            return TrialResult(
                id=trial_id,
                task_id=task.task_id,
                trial_number=trial_number,
                success=False,
                error_message=error_message,
                duration_seconds=duration,
                simulation_id=simulation_id,
                trajectory=trajectory,
                created_at=datetime.now(),
            )

    async def run_trials(
        self,
        task: TaskDefinition,
        k: int = 8,
    ) -> list[TrialResult]:
        """Run k trials of a task.

        Args:
            task: Task definition to execute
            k: Number of trials to run

        Returns:
            List of TrialResults
        """
        logger.info(f"Running {k} trials for task {task.task_id}")

        results: list[TrialResult] = []

        if self._config.parallel_trials > 1:
            # Run trials in parallel batches
            for batch_start in range(0, k, self._config.parallel_trials):
                batch_end = min(batch_start + self._config.parallel_trials, k)
                tasks = [
                    self.run_trial(task, i + 1)
                    for i in range(batch_start, batch_end)
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        # Convert exception to failed result
                        results.append(TrialResult(
                            id=str(uuid.uuid4()),
                            task_id=task.task_id,
                            trial_number=batch_start + i + 1,
                            success=False,
                            error_message=str(result),
                            created_at=datetime.now(),
                        ))
                    else:
                        results.append(result)
        else:
            # Run trials sequentially
            for i in range(k):
                result = await self.run_trial(task, i + 1)
                results.append(result)

        logger.info(
            f"Completed {k} trials for task {task.task_id}: "
            f"{sum(1 for r in results if r.success)}/{k} successful"
        )

        return results

    async def evaluate_task(
        self,
        task: TaskDefinition,
        k: int = 8,
    ) -> tuple[list[TrialResult], PassKMetrics]:
        """Run trials and compute pass^k metrics.

        Args:
            task: Task definition to execute
            k: Number of trials to run

        Returns:
            Tuple of (trial results, pass^k metrics)
        """
        results = await self.run_trials(task, k)
        metrics = PassKMetrics.from_trials(task.task_id, results)
        return results, metrics

    async def _execute_simulation(
        self,
        task: TaskDefinition,
        trajectory_callback: Callable[[dict], None] | None = None,
    ) -> dict[str, Any]:
        """Execute the simulation for a task.

        This is a placeholder implementation. In production, this would:
        1. Create a simulation from task.simulation_config
        2. Set up initial app states from task.initial_app_states
        3. Inject agent_instruction into the agent's context
        4. Run the simulation
        5. Return final state and outputs

        Args:
            task: Task to execute
            trajectory_callback: Optional callback for each action

        Returns:
            Dict with simulation_id, final_state, agent_outputs, etc.
        """
        # Check for custom simulation factory
        if self._simulation_factory:
            return await self._simulation_factory(task, trajectory_callback)

        # Default implementation: simulate success/failure for testing
        # In production, this would integrate with the actual simulation runner
        logger.warning(
            "Using placeholder simulation execution. "
            "Provide a simulation_factory for actual execution."
        )

        # For testing, return a basic result
        return {
            "simulation_id": f"sim_{uuid.uuid4().hex[:8]}",
            "final_state": task.expected_final_states,  # Assume success for testing
            "agent_outputs": task.required_outputs,
            "token_count": 1000,
            "step_count": task.estimated_steps or 5,
        }

    def _verify_goal_state(
        self,
        goal: GoalState,
        final_state: dict[str, dict[str, dict]],
        agent_outputs: list[str],
    ) -> StateVerificationResult:
        """Verify final state against expected goal state.

        Args:
            goal: Expected goal state
            final_state: Actual final state
            agent_outputs: Agent responses/outputs

        Returns:
            StateVerificationResult with match details
        """
        state_diff: list[dict] = []
        missing_outputs: list[str] = []

        # Compute state hashes
        final_hash = self._compute_state_hash(final_state)
        expected_hash = self._compute_state_hash(goal.expected_app_states)

        # Compare states
        state_match = self._compare_states(
            goal.expected_app_states,
            final_state,
            state_diff,
        )

        # Check required outputs
        output_text = " ".join(agent_outputs).lower()
        for required in goal.required_outputs:
            if required.lower() not in output_text:
                missing_outputs.append(required)

        output_match = len(missing_outputs) == 0

        return StateVerificationResult(
            state_match=state_match,
            output_match=output_match,
            success=state_match and output_match,
            state_diff=state_diff,
            missing_outputs=missing_outputs,
            final_state_hash=final_hash,
            expected_state_hash=expected_hash,
        )

    def _compare_states(
        self,
        expected: dict[str, dict[str, dict]],
        actual: dict[str, dict[str, dict]],
        diff: list[dict],
    ) -> bool:
        """Compare expected and actual states, recording differences.

        Args:
            expected: Expected app states
            actual: Actual app states
            diff: List to append differences to

        Returns:
            True if states match
        """
        match = True

        for app_id, expected_agents in expected.items():
            if app_id not in actual:
                diff.append({
                    "type": "missing_app",
                    "app_id": app_id,
                })
                match = False
                continue

            actual_agents = actual[app_id]

            for agent_id, expected_state in expected_agents.items():
                if agent_id not in actual_agents:
                    diff.append({
                        "type": "missing_agent",
                        "app_id": app_id,
                        "agent_id": agent_id,
                    })
                    match = False
                    continue

                actual_state = actual_agents[agent_id]

                # Compare each field in expected state
                for field, expected_value in expected_state.items():
                    actual_value = actual_state.get(field)

                    if actual_value != expected_value:
                        diff.append({
                            "type": "field_mismatch",
                            "app_id": app_id,
                            "agent_id": agent_id,
                            "field": field,
                            "expected": expected_value,
                            "actual": actual_value,
                        })
                        match = False

        return match

    def _compute_state_hash(self, state: dict) -> str:
        """Compute a hash of the state for quick comparison.

        Args:
            state: State dictionary

        Returns:
            SHA-256 hash of serialized state
        """
        # Sort keys for deterministic serialization
        serialized = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def classify_failure(
        self,
        task: TaskDefinition,
        result: TrialResult,
    ) -> FaultClassification | None:
        """Classify a failed trial.

        Args:
            task: Task definition
            result: Failed trial result

        Returns:
            FaultClassification or None if trial succeeded
        """
        if result.success:
            return None

        trial_id = result.id or str(uuid.uuid4())
        evidence: list[str] = []

        # Check for environment errors
        if result.error_message:
            if "timeout" in result.error_message.lower():
                return FaultClassification(
                    trial_id=trial_id,
                    task_id=task.task_id,
                    fault_assignment=FaultAssignment.ENVIRONMENT,
                    fault_type=FaultType.TIMEOUT,
                    description="Task execution timed out",
                    evidence=[result.error_message],
                )

            if any(err in result.error_message.lower() for err in ["api", "connection", "network"]):
                return FaultClassification(
                    trial_id=trial_id,
                    task_id=task.task_id,
                    fault_assignment=FaultAssignment.ENVIRONMENT,
                    fault_type=FaultType.API_ERROR,
                    description="API or network error occurred",
                    evidence=[result.error_message],
                )

        # Check state mismatch
        if result.state_match is False:
            evidence.append("Final state does not match expected state")

            # Analyze trajectory to determine specific fault
            if result.trajectory:
                # Check for wrong actions
                expected_actions = {
                    (a.agent_id, a.app_id, a.action_name)
                    for a in task.expected_actions
                }
                actual_actions = {
                    (a.get("agent_id"), a.get("app_id"), a.get("action"))
                    for a in result.trajectory
                }

                missing = expected_actions - actual_actions
                extra = actual_actions - expected_actions

                if missing:
                    return FaultClassification(
                        trial_id=trial_id,
                        task_id=task.task_id,
                        fault_assignment=FaultAssignment.AGENT,
                        fault_type=FaultType.MISSING_ACTION,
                        description=f"Missing required actions: {missing}",
                        evidence=evidence,
                    )

                if extra:
                    return FaultClassification(
                        trial_id=trial_id,
                        task_id=task.task_id,
                        fault_assignment=FaultAssignment.AGENT,
                        fault_type=FaultType.EXTRA_ACTION,
                        description=f"Unexpected actions: {extra}",
                        evidence=evidence,
                    )

            return FaultClassification(
                trial_id=trial_id,
                task_id=task.task_id,
                fault_assignment=FaultAssignment.AGENT,
                fault_type=FaultType.GOAL_NOT_ACHIEVED,
                description="Goal state not achieved",
                evidence=evidence,
            )

        # Check output mismatch
        if result.output_match is False:
            return FaultClassification(
                trial_id=trial_id,
                task_id=task.task_id,
                fault_assignment=FaultAssignment.AGENT,
                fault_type=FaultType.GOAL_PARTIAL,
                description="Required outputs not present in response",
                evidence=evidence,
            )

        # Default: unknown agent error
        return FaultClassification(
            trial_id=trial_id,
            task_id=task.task_id,
            fault_assignment=FaultAssignment.AGENT,
            fault_type=FaultType.REASONING_ERROR,
            description="Unknown failure reason",
            evidence=evidence,
        )
