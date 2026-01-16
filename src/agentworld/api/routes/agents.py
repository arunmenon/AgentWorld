"""Agent API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.api.schemas.agents import (
    AgentResponse,
    AgentListResponse,
    TraitVectorResponse,
    MemoryResponse,
    MemoryListResponse,
)


router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


def agent_to_response(agent: dict, repo: Repository) -> AgentResponse:
    """Convert agent dict to response."""
    traits = agent.get("traits", {})
    trait_response = None
    if traits:
        trait_response = TraitVectorResponse(
            openness=traits.get("openness", 0.5),
            conscientiousness=traits.get("conscientiousness", 0.5),
            extraversion=traits.get("extraversion", 0.5),
            agreeableness=traits.get("agreeableness", 0.5),
            neuroticism=traits.get("neuroticism", 0.3),
        )

    # Count memories
    memory_count = repo.count_memories(agent["id"])

    return AgentResponse(
        id=agent["id"],
        simulation_id=agent["simulation_id"],
        name=agent["name"],
        traits=trait_response,
        background=agent.get("background"),
        model=agent.get("model"),
        message_count=0,  # TODO: Count messages
        memory_count=memory_count,
        created_at=agent.get("created_at"),
    )


@router.get("/simulations/{simulation_id}/agents", response_model=AgentListResponse)
async def list_agents(simulation_id: str):
    """List all agents in a simulation."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    agents = repo.get_agents_for_simulation(simulation_id)
    responses = [agent_to_response(agent, repo) for agent in agents]

    return AgentListResponse(
        agents=responses,
        total=len(responses),
    )


@router.get("/simulations/{simulation_id}/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(simulation_id: str, agent_id: str):
    """Get an agent by ID."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    agent = repo.get_agent(agent_id)
    if not agent or agent.get("simulation_id") != simulation_id:
        raise HTTPException(status_code=404, detail={
            "code": "AGENT_NOT_FOUND",
            "message": f"Agent '{agent_id}' not found in simulation '{simulation_id}'",
        })

    return agent_to_response(agent, repo)


@router.get("/simulations/{simulation_id}/agents/{agent_id}/memories", response_model=MemoryListResponse)
async def get_agent_memories(
    simulation_id: str,
    agent_id: str,
    memory_type: Optional[str] = Query(None, description="Filter by type: observation or reflection"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get memories for an agent."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Check agent exists
    agent = repo.get_agent(agent_id)
    if not agent or agent.get("simulation_id") != simulation_id:
        raise HTTPException(status_code=404, detail={
            "code": "AGENT_NOT_FOUND",
            "message": f"Agent '{agent_id}' not found in simulation '{simulation_id}'",
        })

    memories = repo.get_memories_for_agent(agent_id, memory_type=memory_type, limit=limit)

    responses = [
        MemoryResponse(
            id=mem["id"],
            agent_id=mem["agent_id"],
            memory_type=mem["memory_type"],
            content=mem["content"],
            importance=mem.get("importance", 5.0),
            source=mem.get("source"),
            created_at=mem.get("created_at"),
        )
        for mem in memories
    ]

    return MemoryListResponse(
        memories=responses,
        total=len(responses),
    )
