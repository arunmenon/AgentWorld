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
