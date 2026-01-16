"""Message API schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Message response schema."""

    id: str
    simulation_id: str
    sender_id: str
    sender_name: Optional[str] = None
    receiver_id: Optional[str] = None
    receiver_name: Optional[str] = None
    content: str
    step: int
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """List of messages."""

    messages: list[MessageResponse]
    total: int
