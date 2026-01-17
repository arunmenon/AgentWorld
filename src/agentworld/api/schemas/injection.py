"""Agent injection API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InjectAgentRequest(BaseModel):
    """Request to inject an external agent."""

    agent_id: str = Field(description="ID of agent to replace")
    endpoint_url: str = Field(description="URL of external agent endpoint")
    api_key: str | None = Field(None, description="Optional API key")
    timeout_seconds: int = Field(30, ge=1, le=300, description="Request timeout")
    privacy_tier: str = Field(
        "basic",
        description="Privacy tier: minimal, basic, full"
    )
    fallback_to_simulated: bool = Field(
        True,
        description="Fall back to simulated agent on failure"
    )
    max_retries: int = Field(3, ge=0, le=10, description="Max retry attempts")


class CircuitBreakerConfigRequest(BaseModel):
    """Circuit breaker configuration."""

    failure_threshold: int = Field(5, ge=1, le=20)
    half_open_probe_interval_seconds: int = Field(30, ge=5, le=300)
    success_threshold: int = Field(2, ge=1, le=10)


class InjectedAgentResponse(BaseModel):
    """Response for an injected agent."""

    agent_id: str
    endpoint_url: str
    privacy_tier: str
    fallback_to_simulated: bool
    circuit_state: str
    is_healthy: bool | None = None
    injected_at: datetime | None = None


class InjectedAgentMetricsResponse(BaseModel):
    """Metrics for an injected agent."""

    agent_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    latency_p50_ms: int = 0
    latency_p99_ms: int = 0
    circuit_state: str = "CLOSED"


class InjectedAgentListResponse(BaseModel):
    """List of injected agents."""

    simulation_id: str
    injected_agents: list[InjectedAgentResponse]
    total: int


class InjectAgentResponse(BaseModel):
    """Response from inject agent operation."""

    simulation_id: str
    agent_id: str
    success: bool
    message: str
    is_healthy: bool | None = None


class HealthCheckResponse(BaseModel):
    """Response from endpoint health check."""

    agent_id: str
    endpoint_url: str
    is_healthy: bool
    latency_ms: int | None = None
    error: str | None = None
