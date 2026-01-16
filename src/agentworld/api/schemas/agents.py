"""Agent API schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TraitVectorResponse(BaseModel):
    """Trait vector response."""

    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)


class AgentResponse(BaseModel):
    """Agent response schema."""

    id: str
    simulation_id: str
    name: str
    traits: Optional[TraitVectorResponse] = None
    background: Optional[str] = None
    model: Optional[str] = None
    message_count: int = 0
    memory_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """List of agents."""

    agents: list[AgentResponse]
    total: int


class MemoryResponse(BaseModel):
    """Memory (observation or reflection) response."""

    id: str
    agent_id: str
    memory_type: str  # "observation" or "reflection"
    content: str
    importance: float
    source: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    """List of memories."""

    memories: list[MemoryResponse]
    total: int
