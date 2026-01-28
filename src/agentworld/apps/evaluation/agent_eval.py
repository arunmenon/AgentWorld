"""Agent evaluation framework for ADR-021 (REQ-21-03).

This module evaluates how well agents interact with apps:
- Success metrics: Track action success rates
- Efficiency metrics: Compare actual vs optimal steps
- Error patterns: Identify repeated errors and error types
- Comprehension: Measure appropriate action choices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections import Counter
import time

from agentworld.apps.definition import AppDefinition, AppState


@dataclass
class EvaluationTask:
    """A goal-oriented task for agent evaluation.

    Defines what the agent should accomplish and the optimal path.

    Attributes:
        name: Task identifier
        description: Human-readable task description
        app_id: Target app for this task
        initial_state: Starting state for the task
        goal_condition: Expression that must become true
        max_steps: Maximum allowed steps before timeout
        optimal_steps: Known optimal solution length
        required_actions: Actions that must be called
        forbidden_actions: Actions that should not be called
    """
    name: str
    description: str
    app_id: str
    initial_state: dict[str, Any]
    goal_condition: str
    max_steps: int = 20
    optimal_steps: int = 1
    required_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "app_id": self.app_id,
            "initial_state": self.initial_state,
            "goal_condition": self.goal_condition,
            "max_steps": self.max_steps,
            "optimal_steps": self.optimal_steps,
            "required_actions": self.required_actions,
            "forbidden_actions": self.forbidden_actions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationTask":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            app_id=data["app_id"],
            initial_state=data["initial_state"],
            goal_condition=data["goal_condition"],
            max_steps=data.get("max_steps", 20),
            optimal_steps=data.get("optimal_steps", 1),
            required_actions=data.get("required_actions", []),
            forbidden_actions=data.get("forbidden_actions", []),
        )


@dataclass
class ActionRecord:
    """Record of a single action execution during evaluation.

    Attributes:
        action_name: Name of the action called
        params: Parameters passed to the action
        success: Whether the action succeeded
        error_type: Type of error if failed (validation, logic, etc.)
        error_message: Error message if failed
        timestamp: When the action was executed
        duration_ms: How long the action took
    """
    action_name: str
    params: dict[str, Any]
    success: bool
    error_type: str | None = None
    error_message: str | None = None
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_name": self.action_name,
            "params": self.params,
            "success": self.success,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ErrorPattern:
    """Pattern of errors observed during evaluation.

    Attributes:
        error_type: Type of error (validation, logic, etc.)
        count: Number of occurrences
        action_names: Actions that triggered this error
        example_message: Sample error message
        is_repeated: Whether same error occurred multiple times
    """
    error_type: str
    count: int
    action_names: list[str]
    example_message: str
    is_repeated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "count": self.count,
            "action_names": self.action_names,
            "example_message": self.example_message,
            "is_repeated": self.is_repeated,
        }


@dataclass
class AgentEvaluation:
    """Results of agent evaluation with an app.

    Comprehensive evaluation of agent performance including success rates,
    efficiency metrics, error patterns, and comprehension measures.

    Attributes:
        agent_id: The agent being evaluated
        app_id: The app used for evaluation
        task_name: Name of the evaluation task
        goal_achieved: Whether the agent achieved the goal

        # Success metrics
        actions_attempted: Total action attempts
        actions_succeeded: Successful actions
        success_rate: Ratio of successful actions

        # Efficiency metrics
        actions_to_goal: Steps taken to reach goal (or max if not reached)
        optimal_actions: Minimum possible actions
        efficiency_ratio: optimal / actual (higher is better)

        # Error patterns
        validation_errors: Input validation failures
        logic_errors: Business logic errors
        repeated_errors: Same error multiple times
        error_patterns: Detailed error pattern analysis

        # Comprehension
        used_all_actions: Whether agent tried all available actions
        appropriate_action_choice: Ratio of correct action choices
        forbidden_action_calls: Number of calls to forbidden actions
        missing_required_actions: Required actions not called

        # Trace
        action_trace: Full trace of actions taken
        duration_ms: Total evaluation time
    """
    agent_id: str
    app_id: str
    task_name: str
    goal_achieved: bool = False

    # Success metrics
    actions_attempted: int = 0
    actions_succeeded: int = 0
    success_rate: float = 0.0

    # Efficiency metrics
    actions_to_goal: int = 0
    optimal_actions: int = 1
    efficiency_ratio: float = 0.0

    # Error patterns
    validation_errors: int = 0
    logic_errors: int = 0
    repeated_errors: int = 0
    error_patterns: list[ErrorPattern] = field(default_factory=list)

    # Comprehension
    used_all_actions: bool = False
    appropriate_action_choice: float = 0.0
    forbidden_action_calls: int = 0
    missing_required_actions: list[str] = field(default_factory=list)

    # Trace
    action_trace: list[ActionRecord] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "app_id": self.app_id,
            "task_name": self.task_name,
            "goal_achieved": self.goal_achieved,
            "actions_attempted": self.actions_attempted,
            "actions_succeeded": self.actions_succeeded,
            "success_rate": self.success_rate,
            "actions_to_goal": self.actions_to_goal,
            "optimal_actions": self.optimal_actions,
            "efficiency_ratio": self.efficiency_ratio,
            "validation_errors": self.validation_errors,
            "logic_errors": self.logic_errors,
            "repeated_errors": self.repeated_errors,
            "error_patterns": [p.to_dict() for p in self.error_patterns],
            "used_all_actions": self.used_all_actions,
            "appropriate_action_choice": self.appropriate_action_choice,
            "forbidden_action_calls": self.forbidden_action_calls,
            "missing_required_actions": self.missing_required_actions,
            "action_trace": [a.to_dict() for a in self.action_trace],
            "duration_ms": self.duration_ms,
        }


def classify_error(error_message: str | None) -> str:
    """Classify an error message into an error type.

    Args:
        error_message: The error message to classify

    Returns:
        Error type: 'validation', 'logic', 'permission', 'not_found', 'unknown'
    """
    if not error_message:
        return "unknown"

    msg_lower = error_message.lower()

    # Validation errors
    validation_patterns = [
        "invalid", "must be", "required", "cannot be", "should be",
        "expected", "missing", "empty", "null", "undefined",
        "type error", "format", "pattern", "constraint"
    ]
    if any(p in msg_lower for p in validation_patterns):
        return "validation"

    # Permission/authorization errors
    permission_patterns = [
        "permission", "denied", "unauthorized", "forbidden",
        "not allowed", "access", "insufficient"
    ]
    if any(p in msg_lower for p in permission_patterns):
        return "permission"

    # Not found errors
    not_found_patterns = [
        "not found", "does not exist", "unknown", "no such",
        "missing", "unavailable"
    ]
    if any(p in msg_lower for p in not_found_patterns):
        return "not_found"

    # Logic/business rule errors
    logic_patterns = [
        "insufficient", "exceeded", "limit", "balance",
        "already", "duplicate", "conflict", "failed"
    ]
    if any(p in msg_lower for p in logic_patterns):
        return "logic"

    return "unknown"


def analyze_error_patterns(action_trace: list[ActionRecord]) -> list[ErrorPattern]:
    """Analyze action trace for error patterns.

    Args:
        action_trace: List of action records

    Returns:
        List of identified error patterns
    """
    # Group errors by type and message
    error_groups: dict[str, list[ActionRecord]] = {}

    for record in action_trace:
        if not record.success and record.error_message:
            key = f"{record.error_type}:{record.error_message[:50]}"
            if key not in error_groups:
                error_groups[key] = []
            error_groups[key].append(record)

    patterns = []
    for key, records in error_groups.items():
        error_type = records[0].error_type or "unknown"
        action_names = list(set(r.action_name for r in records))

        patterns.append(ErrorPattern(
            error_type=error_type,
            count=len(records),
            action_names=action_names,
            example_message=records[0].error_message or "",
            is_repeated=len(records) > 1,
        ))

    # Sort by count descending
    patterns.sort(key=lambda p: p.count, reverse=True)
    return patterns


def calculate_efficiency(
    actions_taken: int,
    optimal_actions: int,
    goal_achieved: bool
) -> float:
    """Calculate efficiency ratio.

    Args:
        actions_taken: Actual number of actions taken
        optimal_actions: Minimum possible actions
        goal_achieved: Whether the goal was achieved

    Returns:
        Efficiency ratio (0.0 to 1.0, higher is better)
    """
    if not goal_achieved:
        return 0.0
    if actions_taken == 0:
        return 0.0
    if optimal_actions <= 0:
        optimal_actions = 1

    # Efficiency = optimal / actual, capped at 1.0
    return min(1.0, optimal_actions / actions_taken)


def evaluate_comprehension(
    action_trace: list[ActionRecord],
    available_actions: list[str],
    required_actions: list[str],
    forbidden_actions: list[str],
) -> tuple[bool, float, int, list[str]]:
    """Evaluate agent's comprehension of the app.

    Args:
        action_trace: Actions taken by the agent
        available_actions: All available actions in the app
        required_actions: Actions that must be called
        forbidden_actions: Actions that should not be called

    Returns:
        Tuple of (used_all_actions, appropriate_choice_rate, forbidden_calls, missing_required)
    """
    actions_called = set(r.action_name for r in action_trace)

    # Check if all actions were used
    used_all = actions_called == set(available_actions)

    # Count forbidden action calls
    forbidden_calls = sum(
        1 for r in action_trace
        if r.action_name in forbidden_actions
    )

    # Find missing required actions
    missing_required = [
        a for a in required_actions
        if a not in actions_called
    ]

    # Calculate appropriate action choice rate
    # An action is "appropriate" if it's not forbidden and either required or succeeded
    total_actions = len(action_trace)
    if total_actions == 0:
        appropriate_rate = 0.0
    else:
        appropriate_count = sum(
            1 for r in action_trace
            if r.action_name not in forbidden_actions and (
                r.action_name in required_actions or r.success
            )
        )
        appropriate_rate = appropriate_count / total_actions

    return used_all, appropriate_rate, forbidden_calls, missing_required


async def evaluate_agent(
    agent_id: str,
    app: Any,  # DynamicApp
    task: EvaluationTask,
    action_callback: Any = None,  # Callable to get agent's next action
) -> AgentEvaluation:
    """Evaluate an agent's performance on a task.

    This is the main entry point for agent evaluation. It runs the agent
    through the task and collects comprehensive metrics.

    Args:
        agent_id: ID of the agent being evaluated
        app: The DynamicApp instance to evaluate against
        task: The evaluation task to run
        action_callback: Optional callback to get agent's next action
                        If None, uses simulated actions for testing

    Returns:
        AgentEvaluation with complete metrics
    """
    start_time = time.time()

    # Initialize state
    state = AppState.from_dict(task.initial_state) if isinstance(task.initial_state, dict) else task.initial_state

    # Track actions
    action_trace: list[ActionRecord] = []
    validation_errors = 0
    logic_errors = 0

    # Get available actions from app
    available_actions = [a.name for a in app.definition.actions]

    # Note: In a real implementation, this would interact with an actual agent
    # For now, we provide the framework that can be integrated with agent runners

    # Analyze error patterns
    error_patterns = analyze_error_patterns(action_trace)

    # Count repeated errors
    repeated_errors = sum(1 for p in error_patterns if p.is_repeated)

    # Evaluate comprehension
    used_all, appropriate_rate, forbidden_calls, missing_required = evaluate_comprehension(
        action_trace,
        available_actions,
        task.required_actions,
        task.forbidden_actions,
    )

    # Calculate metrics
    actions_attempted = len(action_trace)
    actions_succeeded = sum(1 for r in action_trace if r.success)
    success_rate = actions_succeeded / actions_attempted if actions_attempted > 0 else 0.0

    # Check if goal was achieved (placeholder - would need goal evaluation)
    goal_achieved = False  # Would be determined by evaluating goal_condition

    # Calculate efficiency
    efficiency_ratio = calculate_efficiency(
        actions_attempted,
        task.optimal_steps,
        goal_achieved,
    )

    duration_ms = (time.time() - start_time) * 1000

    return AgentEvaluation(
        agent_id=agent_id,
        app_id=task.app_id,
        task_name=task.name,
        goal_achieved=goal_achieved,
        actions_attempted=actions_attempted,
        actions_succeeded=actions_succeeded,
        success_rate=success_rate,
        actions_to_goal=actions_attempted,
        optimal_actions=task.optimal_steps,
        efficiency_ratio=efficiency_ratio,
        validation_errors=validation_errors,
        logic_errors=logic_errors,
        repeated_errors=repeated_errors,
        error_patterns=error_patterns,
        used_all_actions=used_all,
        appropriate_action_choice=appropriate_rate,
        forbidden_action_calls=forbidden_calls,
        missing_required_actions=missing_required,
        action_trace=action_trace,
        duration_ms=duration_ms,
    )


def create_evaluation_task(
    name: str,
    description: str,
    app_id: str,
    initial_balance: float = 1000.0,
    target_balance: float = 900.0,
    optimal_steps: int = 1,
) -> EvaluationTask:
    """Helper to create common evaluation tasks.

    Args:
        name: Task name
        description: Task description
        app_id: Target app ID
        initial_balance: Starting balance for payment apps
        target_balance: Target balance to achieve
        optimal_steps: Minimum steps needed

    Returns:
        Configured EvaluationTask
    """
    return EvaluationTask(
        name=name,
        description=description,
        app_id=app_id,
        initial_state={
            "per_agent": {
                "test_agent": {"balance": initial_balance}
            },
            "shared": {},
        },
        goal_condition=f"agent.balance == {target_balance}",
        max_steps=20,
        optimal_steps=optimal_steps,
    )


# Pre-defined evaluation tasks for common scenarios
PAYMENT_EVALUATION_TASKS = [
    EvaluationTask(
        name="simple_transfer",
        description="Transfer $100 to another user",
        app_id="paypal",
        initial_state={
            "per_agent": {
                "alice": {"balance": 1000},
                "bob": {"balance": 500},
            },
            "shared": {},
        },
        goal_condition="alice.balance == 900 and bob.balance == 600",
        max_steps=5,
        optimal_steps=1,
        required_actions=["transfer"],
        forbidden_actions=[],
    ),
    EvaluationTask(
        name="check_then_transfer",
        description="Check balance then transfer if sufficient",
        app_id="paypal",
        initial_state={
            "per_agent": {
                "alice": {"balance": 1000},
                "bob": {"balance": 500},
            },
            "shared": {},
        },
        goal_condition="alice.balance == 900",
        max_steps=10,
        optimal_steps=2,
        required_actions=["check_balance", "transfer"],
        forbidden_actions=[],
    ),
]
