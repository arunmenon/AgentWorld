"""Simulation API schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


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
