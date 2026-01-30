"""Message API schemas."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


# Message types for distinguishing regular messages from system events
MessageType = Literal[
    "message",           # Regular agent message
    "episode_reset",     # Episode reset event
    "episode_step",      # Episode step event
    "episode_close",     # Episode close event
    "episode_action",    # App action within episode
    "episode_turn",      # Agent turn within episode
]


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
    # Message type for distinguishing episode events
    message_type: MessageType = "message"
    # Metadata for episode events (app_id, episode_id, action, reward, etc.)
    metadata: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """List of messages."""

    messages: list[MessageResponse]
    total: int
