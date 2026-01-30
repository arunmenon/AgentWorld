"""Message API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.api.schemas.messages import (
    MessageResponse,
    MessageListResponse,
)


router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


@router.get("/simulations/{simulation_id}/messages", response_model=MessageListResponse)
async def list_messages(
    simulation_id: str,
    step: Optional[int] = Query(None, description="Filter by step number"),
    sender_id: Optional[str] = Query(None, description="Filter by sender ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """List messages in a simulation."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Get messages
    messages = repo.get_messages_for_simulation(
        simulation_id,
        step=step,
        sender_id=sender_id,
        limit=per_page,
    )

    # Get agents for name lookup
    agents = repo.get_agents_for_simulation(simulation_id)
    agent_names = {a["id"]: a["name"] for a in agents}

    responses = []
    for msg in messages:
        sender_id = msg.get("sender_id")
        receiver_id = msg.get("receiver_id")
        message_type = msg.get("message_type", "message")

        # For episode events, use special sender name
        if message_type != "message":
            sender_name = "Environment"
        else:
            sender_name = agent_names.get(sender_id) if sender_id else None

        responses.append(MessageResponse(
            id=msg["id"],
            simulation_id=msg["simulation_id"],
            sender_id=sender_id or "",  # Empty string for episode events
            sender_name=sender_name,
            receiver_id=receiver_id,
            receiver_name=agent_names.get(receiver_id) if receiver_id else None,
            content=msg["content"],
            step=msg.get("step", 0),
            timestamp=msg.get("timestamp"),
            message_type=message_type,
            metadata=msg.get("metadata"),
        ))

    return MessageListResponse(
        messages=responses,
        total=len(responses),
    )


@router.get("/simulations/{simulation_id}/messages/{message_id}", response_model=MessageResponse)
async def get_message(simulation_id: str, message_id: str):
    """Get a message by ID."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    msg = repo.get_message(message_id)
    if not msg or msg.get("simulation_id") != simulation_id:
        raise HTTPException(status_code=404, detail={
            "code": "MESSAGE_NOT_FOUND",
            "message": f"Message '{message_id}' not found in simulation '{simulation_id}'",
        })

    # Get agents for name lookup
    agents = repo.get_agents_for_simulation(simulation_id)
    agent_names = {a["id"]: a["name"] for a in agents}

    sender_id = msg.get("sender_id")
    receiver_id = msg.get("receiver_id")
    message_type = msg.get("message_type", "message")

    # For episode events, use special sender name
    if message_type != "message":
        sender_name = "Environment"
    else:
        sender_name = agent_names.get(sender_id) if sender_id else None

    return MessageResponse(
        id=msg["id"],
        simulation_id=msg["simulation_id"],
        sender_id=sender_id or "",
        sender_name=sender_name,
        receiver_id=receiver_id,
        receiver_name=agent_names.get(receiver_id) if receiver_id else None,
        content=msg["content"],
        step=msg.get("step", 0),
        timestamp=msg.get("timestamp"),
        message_type=message_type,
        metadata=msg.get("metadata"),
    )
