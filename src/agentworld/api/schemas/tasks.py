"""API schemas for task-based evaluation (ADR-020)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Task Definition Schemas
# =============================================================================


class ExpectedActionSchema(BaseModel):
    """Expected action in ground truth."""

    agent_id: str
    app_id: str
    action_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    order: Optional[int] = None
    required: bool = True


class CreateTaskDefinitionRequest(BaseModel):
    """Request to create a task definition."""

    task_id: str = Field(..., pattern=r"^[a-z][a-z0-9_]{1,99}$", description="Unique task identifier")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    domain: str = Field(..., description="Task domain (payment, shopping, etc.)")
    difficulty: str = Field(..., description="easy, medium, hard")

    simulation_config: dict[str, Any] = Field(..., description="Simulation configuration")
    initial_app_states: Optional[dict[str, Any]] = Field(None, description="Initial app states")
    agent_instruction: str = Field(..., min_length=1, description="Instruction for the agent")
    expected_final_states: dict[str, Any] = Field(..., description="Expected final states")
    expected_actions: list[ExpectedActionSchema] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)
    policy_rules: list[str] = Field(default_factory=list, description="Policy rule IDs to enforce")

    estimated_steps: Optional[int] = Field(None, ge=1)
    tags: list[str] = Field(default_factory=list)


class UpdateTaskDefinitionRequest(BaseModel):
    """Request to update a task definition."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    difficulty: Optional[str] = None

    simulation_config: Optional[dict[str, Any]] = None
    initial_app_states: Optional[dict[str, Any]] = None
    agent_instruction: Optional[str] = None
    expected_final_states: Optional[dict[str, Any]] = None
    expected_actions: Optional[list[ExpectedActionSchema]] = None
    required_outputs: Optional[list[str]] = None
    policy_rules: Optional[list[str]] = None

    estimated_steps: Optional[int] = Field(None, ge=1)
    tags: Optional[list[str]] = None


class TaskDefinitionResponse(BaseModel):
    """Response with task definition."""

    id: str
    task_id: str
    name: str
    description: Optional[str]
    domain: str
    difficulty: str

    simulation_config: dict[str, Any]
    initial_app_states: dict[str, Any]
    agent_instruction: str
    expected_final_states: dict[str, Any]
    expected_actions: list[dict[str, Any]]
    required_outputs: list[str]
    policy_rules: list[str]

    estimated_steps: Optional[int]
    tags: list[str]
    is_active: bool

    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class TaskDefinitionSummaryResponse(BaseModel):
    """Summary response for task listing."""

    id: str
    task_id: str
    name: str
    description: Optional[str]
    domain: str
    difficulty: str
    estimated_steps: Optional[int]
    tags: list[str]
    is_active: bool
    created_at: Optional[datetime]


class TaskDefinitionListResponse(BaseModel):
    """Paginated list of task definitions."""

    items: list[TaskDefinitionSummaryResponse]
    total: int
    page: int
    per_page: int


# =============================================================================
# Task Set Schemas
# =============================================================================


class CreateTaskSetRequest(BaseModel):
    """Request to create a task set (benchmark)."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    domain: Optional[str] = None
    task_ids: list[str] = Field(..., min_length=1)


class UpdateTaskSetRequest(BaseModel):
    """Request to update a task set."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    task_ids: Optional[list[str]] = None


class TaskSetResponse(BaseModel):
    """Response with task set."""

    id: str
    name: str
    description: Optional[str]
    domain: Optional[str]
    task_ids: list[str]
    task_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class TaskSetListResponse(BaseModel):
    """Paginated list of task sets."""

    items: list[TaskSetResponse]
    total: int


# =============================================================================
# Trial Result Schemas
# =============================================================================


class RunTrialRequest(BaseModel):
    """Request to run a single trial."""

    timeout_seconds: float = Field(default=300.0, ge=10.0, le=3600.0)
    capture_trajectory: bool = True


class RunTrialsRequest(BaseModel):
    """Request to run multiple trials."""

    k: int = Field(default=8, ge=1, le=100, description="Number of trials to run")
    timeout_seconds: float = Field(default=300.0, ge=10.0, le=3600.0)
    capture_trajectory: bool = True
    parallel_trials: int = Field(default=1, ge=1, le=10)


class TrialResultResponse(BaseModel):
    """Response with trial result."""

    id: str
    task_id: str
    trial_number: int
    success: bool

    state_match: Optional[bool]
    output_match: Optional[bool]
    final_state_hash: Optional[str]
    expected_state_hash: Optional[str]

    duration_seconds: Optional[float]
    token_count: Optional[int]
    step_count: Optional[int]
    simulation_id: Optional[str]

    error_message: Optional[str]
    trajectory: list[dict[str, Any]]

    created_at: Optional[datetime]


class TrialResultListResponse(BaseModel):
    """List of trial results."""

    items: list[TrialResultResponse]
    total: int


# =============================================================================
# Pass^k Metrics Schemas
# =============================================================================


class PassKMetricsResponse(BaseModel):
    """Response with pass^k metrics."""

    id: Optional[str]
    task_id: str
    total_trials: int
    successful_trials: int

    pass_1: float
    pass_2: float
    pass_4: float
    pass_8: float
    reliability_gap: float

    mean_duration_seconds: Optional[float]
    mean_token_count: Optional[float]

    computed_at: Optional[datetime]
    interpretation: Optional[str]


class EvaluateTaskResponse(BaseModel):
    """Response from task evaluation."""

    task_id: str
    trials: list[TrialResultResponse]
    metrics: PassKMetricsResponse


# =============================================================================
# Fault Classification Schemas
# =============================================================================


class FaultClassificationResponse(BaseModel):
    """Response with fault classification."""

    id: str
    trial_id: str
    task_id: str

    fault_assignment: str
    fault_type: str
    description: str

    evidence: list[str]
    violated_rules: list[str]

    classifier: str
    confidence: float

    created_at: Optional[datetime]


class FaultSummaryResponse(BaseModel):
    """Summary of faults for a task."""

    total_failures: int
    by_assignment: dict[str, int]
    by_type: dict[str, int]
    common_patterns: list[dict[str, Any]]
    most_common_cause: str


class FaultClassificationListResponse(BaseModel):
    """List of fault classifications."""

    items: list[FaultClassificationResponse]
    total: int


# =============================================================================
# Policy Rule Schemas
# =============================================================================


class PolicyConditionSchema(BaseModel):
    """Condition for policy rule triggering."""

    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, contains
    value: Any


class CreatePolicyRuleRequest(BaseModel):
    """Request to create a policy rule."""

    rule_id: str = Field(..., pattern=r"^[a-z][a-z0-9_]{1,99}$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field(..., description="confirmation, limit, eligibility, prohibition")
    domain: Optional[str] = None

    trigger_actions: list[str] = Field(default_factory=list)
    conditions: list[PolicyConditionSchema] = Field(default_factory=list)
    requirements: list[str] = Field(..., min_length=1)

    severity: str = Field(default="error", description="error or warning")


class UpdatePolicyRuleRequest(BaseModel):
    """Request to update a policy rule."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None

    trigger_actions: Optional[list[str]] = None
    conditions: Optional[list[PolicyConditionSchema]] = None
    requirements: Optional[list[str]] = None

    severity: Optional[str] = None
    is_active: Optional[bool] = None


class PolicyRuleResponse(BaseModel):
    """Response with policy rule."""

    id: str
    rule_id: str
    name: str
    description: Optional[str]
    category: str
    domain: Optional[str]

    trigger_actions: list[str]
    conditions: list[dict[str, Any]]
    requirements: list[str]

    severity: str
    is_active: bool

    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class PolicyRuleListResponse(BaseModel):
    """List of policy rules."""

    items: list[PolicyRuleResponse]
    total: int


# =============================================================================
# Policy Compliance Schemas
# =============================================================================


class PolicyViolationResponse(BaseModel):
    """Response with policy violation."""

    rule_id: str
    rule_name: str
    severity: str
    action_index: Optional[int]
    description: str


class PolicyComplianceResponse(BaseModel):
    """Response with policy compliance check result."""

    compliant: bool
    violations: list[PolicyViolationResponse]
    warnings: list[PolicyViolationResponse]
    compliance_rate: float
    total_violations: int
    total_warnings: int


class CheckComplianceRequest(BaseModel):
    """Request to check policy compliance."""

    trajectory: list[dict[str, Any]]
    domain: Optional[str] = None


# =============================================================================
# Benchmark Report Schemas
# =============================================================================


class BenchmarkTaskMetrics(BaseModel):
    """Metrics for a single task in benchmark."""

    task_id: str
    task_name: str
    total_trials: int
    successful_trials: int
    pass_1: float
    pass_8: float
    mean_duration_seconds: Optional[float]


class BenchmarkReportResponse(BaseModel):
    """Response with benchmark report."""

    task_set_name: str
    task_set_description: Optional[str]
    total_tasks: int
    completed_tasks: int

    task_metrics: list[BenchmarkTaskMetrics]

    mean_pass_1: float
    mean_pass_8: float
    mean_reliability_gap: float

    total_trials: int
    total_successes: int

    interpretation: str
    computed_at: datetime
