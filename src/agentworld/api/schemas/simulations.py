"""Simulation API schemas."""

from datetime import datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class GoalConditionResponse(BaseModel):
    """Goal condition in response."""

    id: Optional[str] = None
    goal_type: str
    description: str
    app_id: Optional[str] = None
    field_path: Optional[str] = None
    operator: str = "equals"
    expected_value: Any = None
    # handoff_id can be int (from task data) or str
    handoff_id: Optional[Union[str, int]] = None
    required_phrase: Optional[str] = None


class GoalSpecResponse(BaseModel):
    """Goal specification in response."""

    conditions: list[GoalConditionResponse] = []
    success_mode: Literal["all", "any"] = "all"
    description: str = ""


class GoalProgressResponse(BaseModel):
    """Goal progress information."""

    goal_spec: Optional[GoalSpecResponse] = None
    goal_achieved: bool = False
    goal_achieved_step: Optional[int] = None
    termination_mode: str = "max_steps"


class SimulationResponse(BaseModel):
    """Simulation response schema."""

    id: str
    name: str
    status: str
    current_step: int
    total_steps: int
    total_tokens: int = 0
    total_cost: float = 0.0
    agent_count: int = 0
    message_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    progress_percent: Optional[float] = None
    # τ²-bench: Task reference for evaluation runs
    task_id: Optional[str] = None
    # Goal-based termination (ADR-020.1)
    goal: Optional[GoalProgressResponse] = None

    class Config:
        from_attributes = True


class SimulationListResponse(BaseModel):
    """List of simulations."""

    simulations: list[SimulationResponse]
    total: int


class AgentConfigRequest(BaseModel):
    """Agent configuration for creation."""

    name: str
    traits: Optional[dict[str, float]] = None
    background: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    # τ²-bench: Role for dual-control simulations
    role: Optional[str] = Field(
        default=None,
        description="Agent role: 'peer', 'service_agent', or 'customer'"
    )


class AppConfigRequest(BaseModel):
    """App configuration for simulation."""

    app_id: str
    config: Optional[dict[str, Any]] = None


class CreateSimulationRequest(BaseModel):
    """Create simulation request."""

    name: str
    initial_prompt: str = Field(..., min_length=1)
    steps: int = Field(default=10, ge=1, le=1000)
    model: str = Field(default="openai/gpt-4o-mini")
    agents: Optional[list[AgentConfigRequest]] = None
    topology_type: Optional[str] = Field(default="fully_connected")
    config_yaml: Optional[str] = None  # Full YAML configuration
    apps: Optional[list[AppConfigRequest]] = None  # Apps to add to simulation
    # τ²-bench: Optional task reference for evaluation
    task_id: Optional[str] = Field(
        default=None,
        description="Dual-control task ID for τ²-bench evaluation. When set, simulation runs as a task trial."
    )
    # Goal-based termination (ADR-020.1)
    termination_mode: Literal["max_steps", "goal", "hybrid"] = Field(
        default="max_steps",
        description="How simulation determines when to stop. 'goal' stops when goal conditions are met."
    )


class StepRequest(BaseModel):
    """Step execution request."""

    count: int = Field(default=1, ge=1, le=100)


class StepResponse(BaseModel):
    """Step execution response."""

    simulation_id: str
    steps_executed: int
    current_step: int
    total_steps: int
    messages_generated: int
    status: str


class InjectRequest(BaseModel):
    """Inject stimulus request."""

    content: str = Field(..., min_length=1)
    source: str = Field(default="moderator")
    target_agents: Optional[list[str]] = None  # None = all agents


class InjectResponse(BaseModel):
    """Inject stimulus response."""

    simulation_id: str
    injected: bool
    content: str
    affected_agents: int


class SimulationControlResponse(BaseModel):
    """Response for control operations (start/pause/resume/stop)."""

    simulation_id: str
    status: str
    message: str


# ==============================================================================
# AI Generation Schemas
# ==============================================================================


class GenerateSimulationRequest(BaseModel):
    """Request to generate a simulation from natural language."""

    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the simulation scenario"
    )
    num_agents: Optional[int] = Field(
        None,
        ge=2,
        le=10,
        description="Optional hint for number of agents"
    )


class GenerateSimulationResponse(BaseModel):
    """Response containing generated simulation configuration."""

    success: bool = Field(..., description="Whether generation succeeded")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Generated simulation configuration"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


# ==============================================================================
# Episode Schemas
# ==============================================================================


class EpisodeResponse(BaseModel):
    """Episode information response."""

    id: str
    simulation_id: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    action_count: int = 0   # App actions only
    turn_count: int = 0     # All agent messages
    total_reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    metadata: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class EpisodeStartResponse(BaseModel):
    """Response when starting a new episode."""

    simulation_id: str
    episode_id: str
    message: str = "Episode started"


class EpisodeEndRequest(BaseModel):
    """Request to end an episode."""

    terminated: bool = Field(
        default=False,
        description="True if goal was achieved"
    )
    truncated: bool = Field(
        default=True,
        description="True if ending due to max steps or manual stop"
    )


class EpisodeEndResponse(BaseModel):
    """Response when ending an episode."""

    simulation_id: str
    episode_id: str
    action_count: int   # App actions only
    turn_count: int     # All agent messages
    total_reward: float
    terminated: bool
    truncated: bool
    message: str = "Episode ended"


class EpisodeListResponse(BaseModel):
    """List of episodes for a simulation."""

    simulation_id: str
    episodes: list[EpisodeResponse]
    total: int
