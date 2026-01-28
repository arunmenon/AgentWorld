"""Task-based evaluation framework per ADR-020 and ADR-020.1.

This module provides τ-bench and τ²-bench inspired evaluation capabilities:

τ-bench (Single-Agent Evaluation):
- TaskDefinition: Structured task definitions with ground truth
- TaskRunner: Execute tasks and capture results
- PassKMetrics: Reliability measurement across trials
- GoalState: Expected outcome verification
- FaultClassification: Structured error analysis

τ²-bench (Dual-Control Evaluation) - ADR-020.1:
- DualControlTaskDefinition: Tasks requiring agent-user coordination
- CoordinationEvent: Tracks instruction → action handoffs
- CoordinationMetrics: Measures coordination success
- CoordinationTracker: Monitors simulations for handoffs
- SoloDualComparison: Compare solo vs dual mode performance

Example usage (single-agent):
    from agentworld.tasks import (
        TaskDefinition,
        TaskRunner,
    )

    task = TaskDefinition(
        task_id="payment_transfer",
        name="Simple Transfer",
        domain="payment",
        difficulty="easy",
        simulation_config={...},
        agent_instruction="Transfer $50 from Alice to Bob",
        expected_final_states={...},
    )

    runner = TaskRunner()
    results = await runner.run_trials(task, k=8)
    print(f"pass^1: {results.pass_1}")

Example usage (dual-control):
    from agentworld.tasks import (
        DualControlTaskDefinition,
        CoordinationTracker,
    )
    from agentworld.apps.definition import AgentRole

    task = DualControlTaskDefinition(
        task_id="telecom_fix_data",
        name="Fix Mobile Data",
        domain="telecom",
        difficulty="medium",
        simulation_config={...},
        agent_id="tech_support",
        agent_role=AgentRole.SERVICE_AGENT,
        agent_instruction="Help customer fix mobile data",
        agent_apps=["telecom_backend"],
        user_id="john",
        user_role=AgentRole.CUSTOMER,
        user_instruction="My mobile data isn't working",
        user_apps=["user_device"],
        user_goal_state={"mobile_data_enabled": True},
    )

    tracker = CoordinationTracker(task)
    # ... run simulation with tracker ...
    metrics = tracker.get_metrics()
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

# ADR-020.1: Dual-control evaluation
from agentworld.tasks.dual_control import (
    # Task definition
    DualControlTaskDefinition,
    InstructionTemplate,
    CoordinationHandoff,
    # Events and metrics
    CoordinationEvent,
    CoordinationMetrics,
    SoloDualComparison,
    # Common templates
    TOGGLE_DATA_TEMPLATE,
    CHECK_STATUS_TEMPLATE,
    RESTART_DEVICE_TEMPLATE,
    TOGGLE_AIRPLANE_TEMPLATE,
)
from agentworld.tasks.coordination import (
    CoordinationTracker,
    PendingInstruction,
    analyze_coordination,
)

__all__ = [
    # Core types (ADR-020)
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
    # Dual-control (ADR-020.1)
    "DualControlTaskDefinition",
    "InstructionTemplate",
    "CoordinationHandoff",
    "CoordinationEvent",
    "CoordinationMetrics",
    "SoloDualComparison",
    "CoordinationTracker",
    "PendingInstruction",
    "analyze_coordination",
    # Common templates
    "TOGGLE_DATA_TEMPLATE",
    "CHECK_STATUS_TEMPLATE",
    "RESTART_DEVICE_TEMPLATE",
    "TOGGLE_AIRPLANE_TEMPLATE",
]
