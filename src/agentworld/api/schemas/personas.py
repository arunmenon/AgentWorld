"""Persona API schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TraitsRequest(BaseModel):
    """Traits for persona creation."""

    openness: float = Field(default=0.5, ge=0.0, le=1.0)
    conscientiousness: float = Field(default=0.5, ge=0.0, le=1.0)
    extraversion: float = Field(default=0.5, ge=0.0, le=1.0)
    agreeableness: float = Field(default=0.5, ge=0.0, le=1.0)
    neuroticism: float = Field(default=0.3, ge=0.0, le=1.0)


class PersonaResponse(BaseModel):
    """Persona response schema."""

    id: str
    name: str
    description: Optional[str] = None
    occupation: Optional[str] = None
    age: Optional[int] = None
    background: Optional[str] = None
    traits: Optional[dict[str, float]] = None
    tags: list[str] = []
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PersonaListResponse(BaseModel):
    """List of personas."""

    personas: list[PersonaResponse]
    total: int


class CreatePersonaRequest(BaseModel):
    """Create persona request."""

    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    occupation: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    background: Optional[str] = None
    traits: Optional[TraitsRequest] = None
    tags: list[str] = []


class UpdatePersonaRequest(BaseModel):
    """Update persona request."""

    name: Optional[str] = None
    description: Optional[str] = None
    occupation: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    background: Optional[str] = None
    traits: Optional[TraitsRequest] = None
    tags: Optional[list[str]] = None


class CollectionResponse(BaseModel):
    """Collection response schema."""

    id: str
    name: str
    description: Optional[str] = None
    tags: list[str] = []
    member_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CollectionListResponse(BaseModel):
    """List of collections."""

    collections: list[CollectionResponse]
    total: int


class CreateCollectionRequest(BaseModel):
    """Create collection request."""

    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    tags: list[str] = []


class AddToCollectionRequest(BaseModel):
    """Add persona to collection request."""

    persona_id: str
