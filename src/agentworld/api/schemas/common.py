"""Common API schemas."""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class MetaResponse(BaseModel):
    """Response metadata."""

    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "2026-01-16"


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int
    per_page: int
    total_pages: int
    total_count: int


class LinksResponse(BaseModel):
    """HATEOAS links."""

    self_link: Optional[str] = Field(None, alias="self")
    next_link: Optional[str] = Field(None, alias="next")
    prev_link: Optional[str] = Field(None, alias="prev")
    first_link: Optional[str] = Field(None, alias="first")
    last_link: Optional[str] = Field(None, alias="last")

    class Config:
        populate_by_name = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    data: list[T]
    meta: MetaResponse
    pagination: PaginationMeta
    links: Optional[LinksResponse] = None


class SingleResponse(BaseModel, Generic[T]):
    """Single item response wrapper."""

    data: T
    meta: MetaResponse
    links: Optional[LinksResponse] = None


class ErrorDetail(BaseModel):
    """Error detail."""

    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: ErrorDetail
    meta: MetaResponse


class SuccessResponse(BaseModel):
    """Simple success response."""

    success: bool = True
    message: Optional[str] = None
    meta: MetaResponse
