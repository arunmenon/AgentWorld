"""Task definition data classes for ADR-020.

This module defines the core types for task-based evaluation:
- TaskDefinition: Complete task specification with ground truth
- GoalState: Expected outcome verification
- FaultClassification: Structured failure analysis
- PolicyRule: Agent compliance rules
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import comb
from typing import Any


class FaultAssignment(str, Enum):
    """Who is responsible for the failure."""
    AGENT = "agent"              # Agent made an error
    ENVIRONMENT = "environment"  # System/API error
    TASK = "task"                # Task definition issue


class FaultCategory(str, Enum):
    """High-level error category for τ²-bench analysis.

    Per τ²-bench requirements, errors are grouped into three categories
    for fine-grained error analysis.
    """
    REASONING = "reasoning"        # Agent reasoning/planning errors
    COMMUNICATION = "communication"  # Agent-user communication failures
    EXECUTION = "execution"        # Environment/system errors


class FaultType(str, Enum):
    """What type of error occurred.

    Extended per τ²-bench (ADR-020.1) to include communication error
    subcategories for dual-control scenarios.
    """
    # Task completion
    GOAL_NOT_ACHIEVED = "goal_not_achieved"
    GOAL_PARTIAL = "goal_partial"

    # Action errors
    WRONG_ACTION = "wrong_action"
    WRONG_PARAMS = "wrong_params"
    MISSING_ACTION = "missing_action"
    EXTRA_ACTION = "extra_action"
    ACTION_ORDER = "action_order"

    # Policy violations
    POLICY_VIOLATION = "policy_violation"
    MISSING_CONFIRMATION = "missing_confirmation"

    # Reasoning errors
    MISUNDERSTOOD_TASK = "misunderstood_task"
    REASONING_ERROR = "reasoning_error"

    # Environment errors
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    SYSTEM_ERROR = "system_error"

    # NEW: Communication error subcategories (τ²-bench)
    # Agent gave vague or ambiguous instructions to user
    INSTRUCTION_UNCLEAR = "instruction_unclear"
    # Agent missed necessary steps in instructions
    INSTRUCTION_INCOMPLETE = "instruction_incomplete"
    # Agent gave incorrect instructions to user
    INSTRUCTION_WRONG = "instruction_wrong"
    # User interpreted agent's instructions incorrectly
    USER_MISUNDERSTOOD = "user_misunderstood"
    # User asked for clarification (indicates confusion)
    USER_CONFUSED = "user_confused"
    # User failed to perform the requested action
    USER_ACTION_FAILED = "user_action_failed"

    @property
    def category(self) -> FaultCategory:
        """Get the high-level category for this fault type.

        Returns:
            FaultCategory: reasoning, communication, or execution
        """
        communication_types = {
            FaultType.INSTRUCTION_UNCLEAR,
            FaultType.INSTRUCTION_INCOMPLETE,
            FaultType.INSTRUCTION_WRONG,
            FaultType.USER_MISUNDERSTOOD,
            FaultType.USER_CONFUSED,
            FaultType.USER_ACTION_FAILED,
        }

        execution_types = {
            FaultType.API_ERROR,
            FaultType.TIMEOUT,
            FaultType.SYSTEM_ERROR,
        }

        if self in communication_types:
            return FaultCategory.COMMUNICATION
        elif self in execution_types:
            return FaultCategory.EXECUTION
        else:
            return FaultCategory.REASONING

    @classmethod
    def get_communication_types(cls) -> list["FaultType"]:
        """Get all communication-related fault types."""
        return [
            cls.INSTRUCTION_UNCLEAR,
            cls.INSTRUCTION_INCOMPLETE,
            cls.INSTRUCTION_WRONG,
            cls.USER_MISUNDERSTOOD,
            cls.USER_CONFUSED,
            cls.USER_ACTION_FAILED,
        ]

    @classmethod
    def get_reasoning_types(cls) -> list["FaultType"]:
        """Get all reasoning-related fault types."""
        return [
            cls.GOAL_NOT_ACHIEVED,
            cls.GOAL_PARTIAL,
            cls.WRONG_ACTION,
            cls.WRONG_PARAMS,
            cls.MISSING_ACTION,
            cls.EXTRA_ACTION,
            cls.ACTION_ORDER,
            cls.POLICY_VIOLATION,
            cls.MISSING_CONFIRMATION,
            cls.MISUNDERSTOOD_TASK,
            cls.REASONING_ERROR,
        ]

    @classmethod
    def get_execution_types(cls) -> list["FaultType"]:
        """Get all execution/environment-related fault types."""
        return [cls.API_ERROR, cls.TIMEOUT, cls.SYSTEM_ERROR]


@dataclass
class ExpectedAction:
    """Expected app action in ground truth.

    Attributes:
        agent_id: ID of the agent that should perform this action
        app_id: ID of the app to interact with
        action_name: Name of the action to execute
        params: Expected parameters (partial match allowed)
        order: Execution order (None = any order OK)
        required: Whether this action is required for success
    """
    agent_id: str
    app_id: str
    action_name: str
    params: dict[str, Any] = field(default_factory=dict)
    order: int | None = None
    required: bool = True

    def matches(self, agent_id: str, app_id: str, action: str, params: dict) -> bool:
        """Check if an actual action matches this expectation.

        Performs partial matching on params - only checks keys that are specified
        in the expected params.
        """
        if self.agent_id != agent_id:
            return False
        if self.app_id != app_id:
            return False
        if self.action_name != action:
            return False

        # Partial param matching
        for key, expected_value in self.params.items():
            if key not in params:
                return False
            if params[key] != expected_value:
                return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "app_id": self.app_id,
            "action_name": self.action_name,
            "params": self.params,
            "order": self.order,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpectedAction":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            app_id=data["app_id"],
            action_name=data["action_name"],
            params=data.get("params", {}),
            order=data.get("order"),
            required=data.get("required", True),
        )


@dataclass
class GoalState:
    """Expected outcome for task verification.

    Attributes:
        task_id: Reference to the task
        expected_app_states: Expected final states per app per agent
        expected_actions: Required action sequence
        required_outputs: Required strings in agent responses
    """
    task_id: str
    expected_app_states: dict[str, dict[str, dict]] = field(default_factory=dict)
    expected_actions: list[ExpectedAction] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "expected_app_states": self.expected_app_states,
            "expected_actions": [a.to_dict() for a in self.expected_actions],
            "required_outputs": self.required_outputs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalState":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            expected_app_states=data.get("expected_app_states", {}),
            expected_actions=[
                ExpectedAction.from_dict(a)
                for a in data.get("expected_actions", [])
            ],
            required_outputs=data.get("required_outputs", []),
        )


@dataclass
class TaskDefinition:
    """Complete task definition with ground truth.

    A task defines:
    - What simulation to run (agents, apps, config)
    - What instruction to give the agent
    - What outcome is expected (states, actions, outputs)
    - What policies apply

    Attributes:
        task_id: Unique identifier for this task
        name: Human-readable name
        description: Detailed description
        domain: Task domain (payment, shopping, etc.)
        difficulty: Difficulty level (easy, medium, hard)
        simulation_config: Full simulation configuration
        initial_app_states: Optional initial app states
        agent_instruction: What the agent should accomplish
        expected_final_states: Expected app states after success
        expected_actions: Expected action sequence
        required_outputs: Required strings in responses
        policy_rules: Policy rule IDs to enforce
        estimated_steps: Estimated steps to complete
        tags: Searchable tags
    """
    task_id: str
    name: str
    domain: str
    difficulty: str
    simulation_config: dict[str, Any]
    agent_instruction: str
    expected_final_states: dict[str, dict[str, dict]]

    # Optional fields
    description: str = ""
    initial_app_states: dict[str, dict[str, dict]] = field(default_factory=dict)
    expected_actions: list[ExpectedAction] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)
    policy_rules: list[str] = field(default_factory=list)
    estimated_steps: int | None = None
    tags: list[str] = field(default_factory=list)

    # Metadata
    id: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_goal_state(self) -> GoalState:
        """Extract GoalState for verification."""
        return GoalState(
            task_id=self.task_id,
            expected_app_states=self.expected_final_states,
            expected_actions=self.expected_actions,
            required_outputs=self.required_outputs,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "simulation_config": self.simulation_config,
            "initial_app_states": self.initial_app_states,
            "agent_instruction": self.agent_instruction,
            "expected_final_states": self.expected_final_states,
            "expected_actions": [a.to_dict() for a in self.expected_actions],
            "required_outputs": self.required_outputs,
            "policy_rules": self.policy_rules,
            "estimated_steps": self.estimated_steps,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskDefinition":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id"),
            task_id=data["task_id"],
            name=data["name"],
            description=data.get("description", ""),
            domain=data["domain"],
            difficulty=data["difficulty"],
            simulation_config=data.get("simulation_config", {}),
            initial_app_states=data.get("initial_app_states", {}),
            agent_instruction=data["agent_instruction"],
            expected_final_states=data.get("expected_final_states", {}),
            expected_actions=[
                ExpectedAction.from_dict(a)
                for a in data.get("expected_actions", [])
            ],
            required_outputs=data.get("required_outputs", []),
            policy_rules=data.get("policy_rules", []),
            estimated_steps=data.get("estimated_steps"),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class TaskSet:
    """A collection of tasks for benchmark evaluation.

    Attributes:
        name: Unique name for this task set
        description: Description of the benchmark
        domain: Optional domain filter
        task_ids: List of task IDs in this set
    """
    name: str
    task_ids: list[str]
    description: str = ""
    domain: str | None = None

    # Metadata
    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "task_ids": self.task_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskSet":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            domain=data.get("domain"),
            task_ids=data.get("task_ids", []),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class TrialResult:
    """Result of a single task trial.

    Attributes:
        task_id: ID of the task that was run
        trial_number: Trial number (1-indexed)
        success: Overall success (state_match AND output_match)
        state_match: Final state matches expected
        output_match: Required outputs present
        final_state_hash: Hash of final app states
        expected_state_hash: Hash of expected states
        duration_seconds: Execution time
        token_count: Total tokens used
        step_count: Number of simulation steps
        simulation_id: Reference to simulation
        error_message: Error message if failed
        trajectory: List of actions taken
    """
    task_id: str
    trial_number: int
    success: bool

    # Detailed results
    state_match: bool | None = None
    output_match: bool | None = None
    final_state_hash: str | None = None
    expected_state_hash: str | None = None

    # Performance
    duration_seconds: float | None = None
    token_count: int | None = None
    step_count: int | None = None

    # References
    simulation_id: str | None = None
    error_message: str | None = None
    trajectory: list[dict] = field(default_factory=list)

    # Metadata
    id: str | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "trial_number": self.trial_number,
            "success": self.success,
            "state_match": self.state_match,
            "output_match": self.output_match,
            "final_state_hash": self.final_state_hash,
            "expected_state_hash": self.expected_state_hash,
            "duration_seconds": self.duration_seconds,
            "token_count": self.token_count,
            "step_count": self.step_count,
            "simulation_id": self.simulation_id,
            "error_message": self.error_message,
            "trajectory": self.trajectory,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrialResult":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=data.get("id"),
            task_id=data["task_id"],
            trial_number=data["trial_number"],
            success=data["success"],
            state_match=data.get("state_match"),
            output_match=data.get("output_match"),
            final_state_hash=data.get("final_state_hash"),
            expected_state_hash=data.get("expected_state_hash"),
            duration_seconds=data.get("duration_seconds"),
            token_count=data.get("token_count"),
            step_count=data.get("step_count"),
            simulation_id=data.get("simulation_id"),
            error_message=data.get("error_message"),
            trajectory=data.get("trajectory", []),
            created_at=created_at,
        )


@dataclass
class PassKMetrics:
    """Pass^k reliability metrics.

    The pass^k metric measures the probability that k consecutive
    trials all succeed. It's computed as:

        pass^k = C(c,k) / C(n,k)

    where n = total trials, c = successes, k = threshold.

    Attributes:
        task_id: ID of the task
        total_trials: Number of trials run (n)
        successful_trials: Number of successful trials (c)
        pass_k_scores: Dictionary mapping k to pass^k score
        mean_duration_seconds: Average trial duration
        mean_token_count: Average tokens per trial
    """
    task_id: str
    total_trials: int
    successful_trials: int
    pass_k_scores: dict[int, float] = field(default_factory=dict)
    mean_duration_seconds: float | None = None
    mean_token_count: float | None = None

    # Metadata
    id: str | None = None
    computed_at: datetime | None = None

    @staticmethod
    def compute_pass_k(n: int, c: int, k: int) -> float:
        """Compute pass^k = C(c,k) / C(n,k).

        Args:
            n: Total number of trials
            c: Number of successful trials
            k: Number of consecutive successes required

        Returns:
            Probability of k consecutive successes
        """
        if k > n or k > c or n == 0:
            return 0.0
        if k == 0:
            return 1.0
        return comb(c, k) / comb(n, k)

    @classmethod
    def from_trials(cls, task_id: str, trials: list[TrialResult]) -> "PassKMetrics":
        """Compute metrics from trial results.

        Args:
            task_id: ID of the task
            trials: List of trial results

        Returns:
            Computed PassKMetrics
        """
        n = len(trials)
        c = sum(1 for t in trials if t.success)

        # Compute pass^k for standard k values
        k_values = [1, 2, 4, 8]
        pass_k_scores = {k: cls.compute_pass_k(n, c, k) for k in k_values}

        # Compute averages
        durations = [t.duration_seconds for t in trials if t.duration_seconds is not None]
        tokens = [t.token_count for t in trials if t.token_count is not None]

        return cls(
            task_id=task_id,
            total_trials=n,
            successful_trials=c,
            pass_k_scores=pass_k_scores,
            mean_duration_seconds=sum(durations) / len(durations) if durations else None,
            mean_token_count=sum(tokens) / len(tokens) if tokens else None,
            computed_at=datetime.now(),
        )

    @property
    def pass_1(self) -> float:
        """Get pass^1 score (traditional success rate)."""
        return self.pass_k_scores.get(1, 0.0)

    @property
    def pass_2(self) -> float:
        """Get pass^2 score."""
        return self.pass_k_scores.get(2, 0.0)

    @property
    def pass_4(self) -> float:
        """Get pass^4 score."""
        return self.pass_k_scores.get(4, 0.0)

    @property
    def pass_8(self) -> float:
        """Get pass^8 score."""
        return self.pass_k_scores.get(8, 0.0)

    @property
    def reliability_gap(self) -> float:
        """Gap between pass^1 and pass^8, measuring fragility.

        A large gap indicates inconsistent performance.
        """
        return self.pass_1 - self.pass_8

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "total_trials": self.total_trials,
            "successful_trials": self.successful_trials,
            "pass_1": self.pass_1,
            "pass_2": self.pass_2,
            "pass_4": self.pass_4,
            "pass_8": self.pass_8,
            "reliability_gap": self.reliability_gap,
            "mean_duration_seconds": self.mean_duration_seconds,
            "mean_token_count": self.mean_token_count,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PassKMetrics":
        """Create from dictionary."""
        computed_at = data.get("computed_at")
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)

        pass_k_scores = {}
        for k in [1, 2, 4, 8]:
            key = f"pass_{k}"
            if key in data and data[key] is not None:
                pass_k_scores[k] = data[key]

        return cls(
            id=data.get("id"),
            task_id=data["task_id"],
            total_trials=data["total_trials"],
            successful_trials=data["successful_trials"],
            pass_k_scores=pass_k_scores,
            mean_duration_seconds=data.get("mean_duration_seconds"),
            mean_token_count=data.get("mean_token_count"),
            computed_at=computed_at,
        )


@dataclass
class FaultClassification:
    """Classification of a task failure.

    Attributes:
        trial_id: ID of the failed trial
        task_id: ID of the task
        fault_assignment: Who is responsible
        fault_type: What type of error
        description: Human-readable description
        evidence: Supporting evidence (log entries, etc.)
        violated_rules: Policy rules that were violated
        classifier: How this was classified (rule_based, llm_based)
        confidence: Confidence in classification (0-1)
    """
    trial_id: str
    task_id: str
    fault_assignment: FaultAssignment
    fault_type: FaultType
    description: str = ""
    evidence: list[str] = field(default_factory=list)
    violated_rules: list[str] = field(default_factory=list)
    classifier: str = "rule_based"
    confidence: float = 1.0

    # Metadata
    id: str | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "trial_id": self.trial_id,
            "task_id": self.task_id,
            "fault_assignment": self.fault_assignment.value,
            "fault_type": self.fault_type.value,
            "description": self.description,
            "evidence": self.evidence,
            "violated_rules": self.violated_rules,
            "classifier": self.classifier,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FaultClassification":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=data.get("id"),
            trial_id=data["trial_id"],
            task_id=data["task_id"],
            fault_assignment=FaultAssignment(data["fault_assignment"]),
            fault_type=FaultType(data["fault_type"]),
            description=data.get("description", ""),
            evidence=data.get("evidence", []),
            violated_rules=data.get("violated_rules", []),
            classifier=data.get("classifier", "rule_based"),
            confidence=data.get("confidence", 1.0),
            created_at=created_at,
        )


@dataclass
class PolicyRule:
    """A rule the agent must follow.

    Attributes:
        rule_id: Unique identifier
        name: Human-readable name
        description: Detailed description
        category: Rule category (confirmation, limit, eligibility, prohibition)
        domain: Optional domain restriction
        trigger_actions: Actions that trigger this rule
        conditions: Additional conditions for triggering
        requirements: What must happen when triggered
        severity: error or warning
    """
    rule_id: str
    name: str
    category: str
    requirements: list[str]

    description: str = ""
    domain: str | None = None
    trigger_actions: list[str] = field(default_factory=list)
    conditions: list[dict] = field(default_factory=list)
    severity: str = "error"

    # Metadata
    id: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def applies_to_action(self, action_name: str, params: dict, context: dict) -> bool:
        """Check if this rule applies to a given action.

        Args:
            action_name: Name of the action
            params: Action parameters
            context: Additional context (agent state, etc.)

        Returns:
            True if rule applies
        """
        # Check if action triggers this rule
        if self.trigger_actions and action_name not in self.trigger_actions:
            return False

        # Check additional conditions
        for condition in self.conditions:
            field = condition.get("field", "")
            operator = condition.get("operator", "eq")
            value = condition.get("value")

            # Resolve field path (e.g., "params.amount")
            actual_value = self._resolve_field(field, params, context)

            # Compare
            if not self._compare(actual_value, operator, value):
                return False

        return True

    def _resolve_field(self, field: str, params: dict, context: dict) -> Any:
        """Resolve a field path to its value."""
        parts = field.split(".")
        if not parts:
            return None

        # Determine root object
        root_name = parts[0]
        if root_name == "params":
            current = params
        elif root_name in context:
            current = context[root_name]
        else:
            return None

        # Navigate path
        for part in parts[1:]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values using operator."""
        if actual is None:
            return False

        if operator == "eq":
            return actual == expected
        elif operator == "ne":
            return actual != expected
        elif operator == "gt":
            return actual > expected
        elif operator == "gte":
            return actual >= expected
        elif operator == "lt":
            return actual < expected
        elif operator == "lte":
            return actual <= expected
        elif operator == "in":
            return actual in expected
        elif operator == "contains":
            return expected in actual

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "domain": self.domain,
            "trigger_actions": self.trigger_actions,
            "conditions": self.conditions,
            "requirements": self.requirements,
            "severity": self.severity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyRule":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id"),
            rule_id=data["rule_id"],
            name=data["name"],
            description=data.get("description", ""),
            category=data["category"],
            domain=data.get("domain"),
            trigger_actions=data.get("trigger_actions", []),
            conditions=data.get("conditions", []),
            requirements=data.get("requirements", []),
            severity=data.get("severity", "error"),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class PolicyViolation:
    """A single policy violation.

    Attributes:
        rule: The rule that was violated
        action_index: Index of the violating action in trajectory
        description: Human-readable description of violation
    """
    rule: PolicyRule
    action_index: int | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule.rule_id,
            "rule_name": self.rule.name,
            "severity": self.rule.severity,
            "action_index": self.action_index,
            "description": self.description,
        }


@dataclass
class PolicyComplianceResult:
    """Result of policy compliance check.

    Attributes:
        compliant: True if no error-level violations
        violations: Error-level violations
        warnings: Warning-level violations
        compliance_rate: Ratio of actions without violations
    """
    compliant: bool
    violations: list[PolicyViolation] = field(default_factory=list)
    warnings: list[PolicyViolation] = field(default_factory=list)
    compliance_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compliant": self.compliant,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "compliance_rate": self.compliance_rate,
            "total_violations": len(self.violations),
            "total_warnings": len(self.warnings),
        }
