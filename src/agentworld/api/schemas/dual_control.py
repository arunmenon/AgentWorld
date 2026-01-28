"""API schemas for dual-control tasks per ADR-020.1."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ==============================================================================
# Type Literals
# ==============================================================================

AgentRoleLiteral = Literal["peer", "service_agent", "customer"]


# ==============================================================================
# Instruction Template Schemas
# ==============================================================================


class InstructionTemplateSchema(BaseModel):
    """Schema for instruction template (handoff detection)."""

    template_id: str = Field(..., description="Unique template identifier")
    keywords: list[str] = Field(
        default_factory=list,
        description="Action keywords (e.g., ['toggle', 'turn'])"
    )
    target_keywords: list[str] = Field(
        default_factory=list,
        description="Target object keywords (e.g., ['data', 'mobile data'])"
    )
    semantic_threshold: float = Field(
        0.85,
        description="Threshold for semantic matching fallback"
    )


# ==============================================================================
# Coordination Handoff Schemas
# ==============================================================================


class CoordinationHandoffSchema(BaseModel):
    """Schema for a coordination handoff requirement."""

    handoff_id: str = Field(..., description="Unique handoff identifier")
    from_role: AgentRoleLiteral = Field(
        ..., description="Role of the agent giving instructions"
    )
    to_role: AgentRoleLiteral = Field(
        ..., description="Role of the agent who should act"
    )
    expected_action: str = Field(
        ..., description="Action the user should execute"
    )
    description: str = Field("", description="Human-readable description")
    instruction_pattern: str | None = Field(
        None, description="Regex pattern for instruction matching (legacy)"
    )
    instruction_template: InstructionTemplateSchema | None = Field(
        None, description="Structured instruction template"
    )


# ==============================================================================
# Dual Control Task Schemas
# ==============================================================================


class DualControlTaskBase(BaseModel):
    """Base schema for dual-control task."""

    name: str = Field(..., min_length=1, max_length=200, description="Task name")
    description: str = Field("", max_length=1000, description="Task description")
    domain: str = Field(..., description="Task domain (e.g., telecom)")
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ..., description="Difficulty level"
    )

    # Simulation setup
    simulation_config: dict[str, Any] = Field(
        default_factory=dict, description="Simulation configuration"
    )

    # Agent-side
    agent_id: str = Field(..., description="Service agent ID")
    agent_role: AgentRoleLiteral = Field(
        "service_agent", description="Agent's role"
    )
    agent_instruction: str = Field(..., description="Instructions for the agent")
    agent_apps: list[str] = Field(
        default_factory=list, description="Apps the agent can access"
    )
    agent_initial_state: dict[str, Any] = Field(
        default_factory=dict, description="Initial app state for agent apps"
    )
    agent_goal_state: dict[str, Any] = Field(
        default_factory=dict, description="Expected final state for agent apps"
    )

    # User-side
    user_id: str = Field(..., description="Customer/user ID")
    user_role: AgentRoleLiteral = Field("customer", description="User's role")
    user_instruction: str = Field(
        ..., description="What the user is trying to achieve"
    )
    user_apps: list[str] = Field(
        default_factory=list, description="Apps the user can access"
    )
    user_initial_state: dict[str, Any] = Field(
        default_factory=dict, description="Initial app state for user apps"
    )
    user_goal_state: dict[str, Any] = Field(
        default_factory=dict, description="Expected final state for user apps"
    )

    # Coordination
    required_handoffs: list[CoordinationHandoffSchema] = Field(
        default_factory=list, description="Required coordination points"
    )
    max_turns: int = Field(20, description="Maximum simulation turns")
    expected_coordination_count: int = Field(
        0, description="Expected number of coordinations"
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Searchable tags")


class CreateDualControlTaskRequest(DualControlTaskBase):
    """Request schema for creating a dual-control task."""

    task_id: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique task identifier"
    )


class UpdateDualControlTaskRequest(BaseModel):
    """Request schema for updating a dual-control task."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    difficulty: Literal["easy", "medium", "hard"] | None = None
    agent_instruction: str | None = None
    user_instruction: str | None = None
    agent_apps: list[str] | None = None
    user_apps: list[str] | None = None
    agent_initial_state: dict[str, Any] | None = None
    user_initial_state: dict[str, Any] | None = None
    agent_goal_state: dict[str, Any] | None = None
    user_goal_state: dict[str, Any] | None = None
    required_handoffs: list[CoordinationHandoffSchema] | None = None
    max_turns: int | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class DualControlTaskResponse(DualControlTaskBase):
    """Response schema for a dual-control task."""

    id: str = Field(..., description="Database ID")
    task_id: str = Field(..., description="Unique task identifier")
    is_active: bool = Field(True, description="Whether task is active")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class DualControlTaskListResponse(BaseModel):
    """Response schema for listing dual-control tasks."""

    tasks: list[DualControlTaskResponse] = Field(
        default_factory=list, description="List of tasks"
    )
    total: int = Field(0, description="Total count")


# ==============================================================================
# Coordination Event Schemas
# ==============================================================================


class CreateCoordinationEventRequest(BaseModel):
    """Request schema for creating a coordination event."""

    event_id: str = Field(..., description="Unique event identifier")
    trial_id: str = Field(..., description="Trial this event belongs to")
    # Note: task_id comes from the URL path, not the body

    # Instructor
    instructor_id: str = Field(..., description="Agent who gave instruction")
    instructor_role: AgentRoleLiteral = Field(..., description="Instructor's role")
    instruction_text: str = Field(..., description="The instruction text")

    # Actor (may be None if user didn't act)
    actor_id: str | None = Field(None, description="Agent who acted")
    actor_role: AgentRoleLiteral | None = Field(None, description="Actor's role")
    action_taken: str | None = Field(None, description="Action executed")
    action_params: dict[str, Any] | None = Field(None, description="Action parameters")

    # Matching
    matched_handoff_id: str | None = Field(
        None, description="ID of matched handoff requirement"
    )
    match_confidence: float = Field(0.0, description="Confidence of instruction match")

    # Result
    handoff_successful: bool = Field(False, description="Whether handoff completed")
    latency_turns: int = Field(0, description="Turns between instruction and action")


class CoordinationEventSchema(BaseModel):
    """Schema for a coordination event."""

    event_id: str = Field(..., description="Unique event identifier")
    trial_id: str = Field(..., description="Trial this event belongs to")
    task_id: str = Field(..., description="Task this event belongs to")

    # Instructor
    instructor_id: str = Field(..., description="Agent who gave instruction")
    instructor_role: AgentRoleLiteral = Field(..., description="Instructor's role")
    instruction_text: str = Field(..., description="The instruction text")

    # Actor (may be None if user didn't act)
    actor_id: str | None = Field(None, description="Agent who acted")
    actor_role: AgentRoleLiteral | None = Field(None, description="Actor's role")
    action_taken: str | None = Field(None, description="Action executed")
    action_params: dict[str, Any] | None = Field(None, description="Action parameters")

    # Matching
    matched_handoff_id: str | None = Field(
        None, description="ID of matched handoff requirement"
    )
    match_confidence: float = Field(0.0, description="Confidence of instruction match")

    # Result
    handoff_successful: bool = Field(False, description="Whether handoff completed")
    latency_turns: int = Field(0, description="Turns between instruction and action")

    # Metadata
    timestamp: datetime | None = Field(None, description="Event timestamp")


class CoordinationEventListResponse(BaseModel):
    """Response schema for listing coordination events."""

    events: list[CoordinationEventSchema] = Field(
        default_factory=list, description="List of events"
    )
    total: int = Field(0, description="Total count")


# ==============================================================================
# Coordination Metrics Schemas
# ==============================================================================


class CoordinationMetricsSchema(BaseModel):
    """Schema for coordination metrics."""

    task_id: str = Field(..., description="Task ID")
    trial_id: str | None = Field(None, description="Trial ID (None for aggregated)")

    # Success metrics
    total_handoffs_required: int = Field(0, description="Required handoffs")
    handoffs_completed: int = Field(0, description="Completed handoffs")
    coordination_success_rate: float = Field(0.0, description="Success rate (0-1)")

    # Efficiency metrics
    avg_instruction_to_action_turns: float = Field(
        0.0, description="Average turns between instruction and action"
    )
    unnecessary_user_actions: int = Field(0, description="Extra actions not needed")

    # Communication quality
    instruction_clarity_score: float | None = Field(
        None, description="LLM-judged clarity (0-1)"
    )
    user_confusion_count: int = Field(0, description="Times user expressed confusion")

    # Metadata
    computed_at: datetime | None = Field(None, description="Computation timestamp")


# ==============================================================================
# Solo vs Dual Comparison Schemas
# ==============================================================================


class SoloDualComparisonSchema(BaseModel):
    """Schema for solo vs dual mode comparison."""

    task_id: str = Field(..., description="Task ID")

    # Solo mode results
    solo_trials: int = Field(0, description="Number of solo trials")
    solo_successes: int = Field(0, description="Successful solo trials")
    solo_pass_1: float = Field(0.0, description="Solo pass^1 rate")
    solo_avg_steps: float = Field(0.0, description="Average steps in solo mode")

    # Dual mode results
    dual_trials: int = Field(0, description="Number of dual trials")
    dual_successes: int = Field(0, description="Successful dual trials")
    dual_pass_1: float = Field(0.0, description="Dual pass^1 rate")
    dual_avg_steps: float = Field(0.0, description="Average steps in dual mode")

    # Key metrics
    performance_drop: float = Field(
        0.0, description="Pass rate drop: solo_pass_1 - dual_pass_1"
    )
    step_increase: float = Field(
        0.0, description="Step increase: dual_avg_steps - solo_avg_steps"
    )

    # Metadata
    computed_at: datetime | None = Field(None, description="Computation timestamp")


class RunComparisonRequest(BaseModel):
    """Request schema for running solo/dual comparison."""

    num_trials: int = Field(8, ge=1, le=100, description="Trials per mode")


class RunComparisonResponse(BaseModel):
    """Response schema for solo/dual comparison."""

    comparison: SoloDualComparisonSchema = Field(
        ..., description="Comparison results"
    )
    insight: str = Field(
        "", description="Key insight about the performance difference"
    )
