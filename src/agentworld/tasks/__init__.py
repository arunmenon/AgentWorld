"""Task-based evaluation framework per ADR-020.

This module provides τ-bench inspired evaluation capabilities including:
- TaskDefinition: Structured task definitions with ground truth
- TaskRunner: Execute tasks and capture results
- PassKMetrics: Reliability measurement across trials
- GoalState: Expected outcome verification
- FaultClassification: Structured error analysis

Example usage:
    from agentworld.tasks import (
        TaskDefinition,
        TaskRunner,
        compute_pass_k,
    )

    # Define a task
    task = TaskDefinition(
        task_id="payment_transfer",
        name="Simple Transfer",
        domain="payment",
        difficulty="easy",
        simulation_config={...},
        agent_instruction="Transfer $50 from Alice to Bob",
        expected_final_states={...},
    )

    # Run multiple trials
    runner = TaskRunner()
    results = await runner.run_trials(task, k=8)

    # Compute reliability metrics
    metrics = compute_pass_k(results)
    print(f"pass^1: {metrics.pass_1}, pass^4: {metrics.pass_4}")
"""

from agentworld.tasks.definitions import (
    # Core types
    TaskDefinition,
    TaskSet,
    ExpectedAction,
    GoalState,
    # Trial results
    TrialResult,
    PassKMetrics,
    # Fault analysis
    FaultAssignment,
    FaultType,
    FaultClassification,
    # Policy
    PolicyRule,
    PolicyViolation,
    PolicyComplianceResult,
)
from agentworld.tasks.runner import (
    TaskRunner,
    TaskExecutionConfig,
)
from agentworld.tasks.repository import (
    TaskRepository,
)

__all__ = [
    # Core types
    "TaskDefinition",
    "TaskSet",
    "ExpectedAction",
    "GoalState",
    # Trial results
    "TrialResult",
    "PassKMetrics",
    # Fault analysis
    "FaultAssignment",
    "FaultType",
    "FaultClassification",
    # Policy
    "PolicyRule",
    "PolicyViolation",
    "PolicyComplianceResult",
    # Runner
    "TaskRunner",
    "TaskExecutionConfig",
    # Repository
    "TaskRepository",
]
