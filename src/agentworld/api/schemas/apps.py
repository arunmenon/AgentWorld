"""API schemas for simulated apps per ADR-017."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AppActionSchema(BaseModel):
    """Schema for an app action definition."""

    name: str = Field(..., description="Action name")
    description: str = Field(..., description="Action description")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameter specifications")
    returns: dict[str, Any] = Field(default_factory=dict, description="Return value specification")


class AppInfoResponse(BaseModel):
    """Response for app info."""

    app_id: str = Field(..., description="Unique app identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="App description")
    actions: list[AppActionSchema] = Field(default_factory=list, description="Available actions")


class AppInstanceResponse(BaseModel):
    """Response for an app instance."""

    id: str = Field(..., description="Instance ID")
    simulation_id: str = Field(..., description="Simulation ID")
    app_id: str = Field(..., description="App ID")
    config: dict[str, Any] = Field(default_factory=dict, description="App configuration")
    state: dict[str, Any] = Field(default_factory=dict, description="App state")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class AppListResponse(BaseModel):
    """Response for listing apps in a simulation."""

    apps: list[AppInstanceResponse] = Field(default_factory=list, description="List of app instances")
    total: int = Field(0, description="Total number of apps")


class AgentAppStateResponse(BaseModel):
    """Response for an agent's app state."""

    agent_id: str = Field(..., description="Agent ID")
    app_id: str = Field(..., description="App ID")
    state: dict[str, Any] = Field(default_factory=dict, description="Agent's app state")


class AppActionLogEntryResponse(BaseModel):
    """Response for an action log entry."""

    id: str = Field(..., description="Log entry ID")
    app_instance_id: str = Field(..., description="App instance ID")
    agent_id: str = Field(..., description="Agent ID")
    step: int = Field(..., description="Simulation step")
    action_name: str = Field(..., description="Action name")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    success: bool = Field(..., description="Whether action succeeded")
    result: dict[str, Any] | None = Field(None, description="Action result data")
    error: str | None = Field(None, description="Error message if failed")
    executed_at: datetime | None = Field(None, description="Execution timestamp")


class AppActionLogResponse(BaseModel):
    """Response for listing action log entries."""

    actions: list[AppActionLogEntryResponse] = Field(
        default_factory=list, description="List of action log entries"
    )
    total: int = Field(0, description="Total number of entries")


class AvailableAppsResponse(BaseModel):
    """Response for listing available app types."""

    apps: list[AppInfoResponse] = Field(default_factory=list, description="Available app types")


# ==============================================================================
# Environment Semantics Schemas
# ==============================================================================


class EnvResetRequest(BaseModel):
    """Request to reset an app environment for a new episode."""

    agents: list[str] = Field(..., description="List of agent IDs for the episode")
    config: dict[str, Any] = Field(default_factory=dict, description="App configuration")
    seed: int | None = Field(None, description="Optional random seed for reproducibility")
    max_steps: int = Field(100, ge=1, le=10000, description="Maximum steps per episode")


class EnvResetResponse(BaseModel):
    """Response from resetting an app environment."""

    episode_id: str = Field(..., description="Unique episode identifier")
    observation: dict[str, Any] = Field(..., description="Initial state observation")
    info: dict[str, Any] = Field(default_factory=dict, description="Episode metadata")


class EnvStepRequest(BaseModel):
    """Request to execute a step in the environment."""

    agent_id: str = Field(..., description="ID of the agent performing the action")
    action: str = Field(..., description="Action name")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class EnvStepResponse(BaseModel):
    """Response from executing a step in the environment."""

    observation: dict[str, Any] = Field(..., description="State observation after action")
    reward: float = Field(..., description="Reward for this step")
    terminated: bool = Field(..., description="Whether episode ended due to goal completion")
    truncated: bool = Field(..., description="Whether episode ended due to max steps")
    info: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StateSnapshotResponse(BaseModel):
    """Response for a state snapshot at a point in time."""

    step: int = Field(..., description="Step number within the episode")
    timestamp: datetime = Field(..., description="When this snapshot was taken")
    state: dict[str, Any] = Field(..., description="Full state at this step")
    action: str | None = Field(None, description="Action taken (None for initial state)")
    params: dict[str, Any] | None = Field(None, description="Action parameters")
    reward: float = Field(0.0, description="Reward received for this step")


class EpisodeHistoryResponse(BaseModel):
    """Response for episode history."""

    episode_id: str = Field(..., description="Unique episode identifier")
    started_at: datetime = Field(..., description="When the episode started")
    ended_at: datetime | None = Field(None, description="When the episode ended")
    snapshots: list[StateSnapshotResponse] = Field(
        default_factory=list, description="State snapshots in order"
    )
    terminated: bool = Field(..., description="Whether episode ended due to goal")
    truncated: bool = Field(..., description="Whether episode was truncated")
    total_reward: float = Field(..., description="Cumulative reward")
    step_count: int = Field(0, description="Number of steps taken")


class EpisodeListResponse(BaseModel):
    """Response for listing episodes."""

    episodes: list[EpisodeHistoryResponse] = Field(
        default_factory=list, description="List of episodes"
    )
    total: int = Field(0, description="Total number of episodes")


class TrajectoryItem(BaseModel):
    """A single item in a trajectory (state, action, reward tuple)."""

    state: dict[str, Any] = Field(..., description="State at this step")
    action: str | None = Field(None, description="Action taken")
    reward: float = Field(..., description="Reward received")


class TrajectoryResponse(BaseModel):
    """Response for episode trajectory."""

    episode_id: str = Field(..., description="Episode identifier")
    trajectory: list[TrajectoryItem] = Field(
        default_factory=list, description="(state, action, reward) tuples"
    )
    total_reward: float = Field(..., description="Total episode reward")
