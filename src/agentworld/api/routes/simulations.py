"""Simulation API endpoints."""

import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.core.models import SimulationStatus, SimulationConfig, AgentConfig
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.api.schemas.simulations import (
    SimulationResponse,
    SimulationListResponse,
    CreateSimulationRequest,
    StepRequest,
    StepResponse,
    InjectRequest,
    InjectResponse,
    SimulationControlResponse,
)
from agentworld.api.schemas.injection import (
    InjectAgentRequest,
    InjectedAgentResponse,
    InjectedAgentListResponse,
    InjectedAgentMetricsResponse,
    InjectAgentResponse,
    HealthCheckResponse,
)
from agentworld.api.schemas.common import MetaResponse


router = APIRouter()

# In-memory storage for injected agents per simulation
# In production, this should be persisted
_injected_agents: dict[str, "InjectedAgentManager"] = {}


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


def simulation_to_response(sim: dict, repo: Repository) -> SimulationResponse:
    """Convert simulation dict to response."""
    agents = repo.get_agents_for_simulation(sim["id"])
    message_count = repo.count_messages(sim["id"])

    progress = None
    if sim.get("total_steps") and sim.get("total_steps") > 0:
        progress = (sim.get("current_step", 0) / sim["total_steps"]) * 100

    return SimulationResponse(
        id=sim["id"],
        name=sim["name"],
        status=sim.get("status", "pending"),
        current_step=sim.get("current_step", 0),
        total_steps=sim.get("total_steps", 10),
        total_tokens=sim.get("total_tokens", 0),
        total_cost=sim.get("total_cost", 0.0),
        agent_count=len(agents),
        message_count=message_count,
        created_at=sim.get("created_at"),
        updated_at=sim.get("updated_at"),
        progress_percent=progress,
    )


@router.get("/simulations", response_model=SimulationListResponse)
async def list_simulations(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
):
    """List all simulations."""
    repo = get_repo()

    status_filter = None
    if status:
        try:
            status_filter = SimulationStatus(status)
        except ValueError:
            pass

    offset = (page - 1) * per_page
    simulations = repo.list_simulations(status=status_filter, limit=per_page, offset=offset)

    responses = [simulation_to_response(sim, repo) for sim in simulations]

    return SimulationListResponse(
        simulations=responses,
        total=len(responses),
    )


@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    """Get a simulation by ID."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    return simulation_to_response(sim, repo)


@router.post("/simulations", response_model=SimulationResponse, status_code=201)
async def create_simulation(request: CreateSimulationRequest):
    """Create a new simulation."""
    repo = get_repo()

    # Build agent configs
    if request.agents:
        agent_configs = [
            AgentConfig(
                name=a.name,
                traits=a.traits or {},
                background=a.background or "",
                model=a.model,
            )
            for a in request.agents
        ]
    else:
        # Default agents
        agent_configs = [
            AgentConfig(
                name="Agent_1",
                traits={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                        "agreeableness": 0.5, "neuroticism": 0.3},
                background="",
            ),
            AgentConfig(
                name="Agent_2",
                traits={"openness": 0.6, "conscientiousness": 0.5, "extraversion": 0.5,
                        "agreeableness": 0.5, "neuroticism": 0.3},
                background="",
            ),
        ]

    config = SimulationConfig(
        name=request.name,
        agents=agent_configs,
        steps=request.steps,
        initial_prompt=request.initial_prompt,
        model=request.model,
    )

    # Create simulation using runner
    from agentworld.simulation.runner import Simulation

    sim = Simulation.from_config(config)
    sim._save_state()

    return simulation_to_response(repo.get_simulation(sim.id), repo)


@router.delete("/simulations/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """Delete a simulation."""
    repo = get_repo()

    if not repo.get_simulation(simulation_id):
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    repo.delete_simulation(simulation_id)

    return {
        "success": True,
        "message": f"Simulation '{simulation_id}' deleted",
        "meta": MetaResponse(request_id=str(uuid.uuid4())),
    }


@router.post("/simulations/{simulation_id}/start", response_model=SimulationControlResponse)
async def start_simulation(simulation_id: str):
    """Start a simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    current_status = sim.get("status", "pending")
    if current_status == "running":
        raise HTTPException(status_code=409, detail={
            "code": "SIMULATION_ALREADY_RUNNING",
            "message": "Simulation is already running",
        })

    repo.update_simulation(simulation_id, {"status": SimulationStatus.RUNNING})

    return SimulationControlResponse(
        simulation_id=simulation_id,
        status="running",
        message="Simulation started",
    )


@router.post("/simulations/{simulation_id}/pause", response_model=SimulationControlResponse)
async def pause_simulation(simulation_id: str):
    """Pause a simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    repo.update_simulation(simulation_id, {"status": SimulationStatus.PAUSED})

    return SimulationControlResponse(
        simulation_id=simulation_id,
        status="paused",
        message="Simulation paused",
    )


@router.post("/simulations/{simulation_id}/resume", response_model=SimulationControlResponse)
async def resume_simulation(simulation_id: str):
    """Resume a paused simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    repo.update_simulation(simulation_id, {"status": SimulationStatus.RUNNING})

    return SimulationControlResponse(
        simulation_id=simulation_id,
        status="running",
        message="Simulation resumed",
    )


@router.post("/simulations/{simulation_id}/step", response_model=StepResponse)
async def execute_step(simulation_id: str, request: StepRequest):
    """Execute simulation step(s)."""
    from agentworld.simulation.runner import Simulation
    from agentworld.core.models import SimulationConfig, AgentConfig

    repo = get_repo()
    sim_data = repo.get_simulation(simulation_id)

    if not sim_data:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Reconstruct the simulation from stored data
    agents_data = repo.get_agents_for_simulation(simulation_id)
    agent_configs = []
    for agent_data in agents_data:
        agent_configs.append(AgentConfig(
            name=agent_data.get("name", "Agent"),
            traits=agent_data.get("traits", {}),
            background=agent_data.get("background", ""),
            model=agent_data.get("model"),
        ))

    # Get config from stored simulation
    config_data = sim_data.get("config") or {}
    config = SimulationConfig(
        name=sim_data.get("name", "Simulation"),
        agents=agent_configs,
        steps=sim_data.get("total_steps", 10),
        initial_prompt=config_data.get("initial_prompt", ""),
        model=config_data.get("model", "openai/gpt-4o-mini"),
    )

    # Create simulation instance
    sim = Simulation.from_config(config)
    sim.id = simulation_id
    sim.current_step = sim_data.get("current_step", 0)
    sim.status = SimulationStatus(sim_data.get("status", "pending"))

    # Match agent IDs with stored agents
    for i, agent in enumerate(sim.agents):
        if i < len(agents_data):
            agent.id = agents_data[i].get("id", agent.id)

    # Connect injection manager for external agents
    sim.injection_manager = _get_injection_manager(simulation_id)

    # Execute the requested number of steps
    total_messages = 0
    steps_executed = 0

    for _ in range(request.count):
        if sim.current_step >= sim.total_steps:
            break
        if sim.status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED):
            break

        messages = await sim.step()
        total_messages += len(messages)
        steps_executed += 1

    # Refresh simulation data from DB
    updated_sim = repo.get_simulation(simulation_id)

    return StepResponse(
        simulation_id=simulation_id,
        steps_executed=steps_executed,
        current_step=updated_sim.get("current_step", 0),
        total_steps=updated_sim.get("total_steps", 10),
        messages_generated=total_messages,
        status=updated_sim.get("status", "pending"),
    )


@router.post("/simulations/{simulation_id}/inject", response_model=InjectResponse)
async def inject_stimulus(simulation_id: str, request: InjectRequest):
    """Inject a stimulus into a running simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    agents = repo.get_agents_for_simulation(simulation_id)
    affected = len(agents)

    if request.target_agents:
        affected = len([a for a in agents if a["id"] in request.target_agents])

    # TODO: Actually inject the stimulus into the simulation

    return InjectResponse(
        simulation_id=simulation_id,
        injected=True,
        content=request.content,
        affected_agents=affected,
    )


# Agent Injection Endpoints (per ADR-016)


def _get_injection_manager(simulation_id: str) -> "InjectedAgentManager":
    """Get or create injection manager for a simulation."""
    from agentworld.agents.external import InjectedAgentManager

    if simulation_id not in _injected_agents:
        _injected_agents[simulation_id] = InjectedAgentManager()
    return _injected_agents[simulation_id]


@router.post(
    "/simulations/{simulation_id}/inject-agent",
    response_model=InjectAgentResponse
)
async def inject_agent(simulation_id: str, request: InjectAgentRequest):
    """Register an external agent for a simulation.

    Replaces the specified agent with an external HTTP endpoint.
    """
    from agentworld.agents.external import (
        ExternalAgentConfig,
        PrivacyTier,
    )

    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Verify agent exists
    agents = repo.get_agents_for_simulation(simulation_id)
    agent_ids = [a["id"] for a in agents]
    if request.agent_id not in agent_ids:
        raise HTTPException(status_code=404, detail={
            "code": "AGENT_NOT_FOUND",
            "message": f"Agent '{request.agent_id}' not found in simulation",
        })

    # Validate privacy tier
    try:
        privacy_tier = PrivacyTier(request.privacy_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_PRIVACY_TIER",
            "message": f"Invalid privacy tier: {request.privacy_tier}",
        })

    # Create config and inject
    config = ExternalAgentConfig(
        endpoint_url=request.endpoint_url,
        api_key=request.api_key,
        timeout_seconds=request.timeout_seconds,
        privacy_tier=privacy_tier,
        fallback_to_simulated=request.fallback_to_simulated,
        max_retries=request.max_retries,
    )

    manager = _get_injection_manager(simulation_id)
    provider = manager.inject(request.agent_id, config)

    # Run health check
    is_healthy = await provider.health_check()

    return InjectAgentResponse(
        simulation_id=simulation_id,
        agent_id=request.agent_id,
        success=True,
        message="Agent injected successfully",
        is_healthy=is_healthy,
    )


@router.delete("/simulations/{simulation_id}/inject-agent/{agent_id}")
async def remove_injected_agent(simulation_id: str, agent_id: str):
    """Remove an injected external agent."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    manager = _get_injection_manager(simulation_id)
    removed = manager.remove(agent_id)

    if not removed:
        raise HTTPException(status_code=404, detail={
            "code": "AGENT_NOT_INJECTED",
            "message": f"Agent '{agent_id}' is not injected",
        })

    return {
        "success": True,
        "message": f"Agent '{agent_id}' removed from injection",
        "meta": MetaResponse(request_id=str(uuid.uuid4())),
    }


@router.get(
    "/simulations/{simulation_id}/injected-agents",
    response_model=InjectedAgentListResponse
)
async def list_injected_agents(simulation_id: str):
    """List all injected agents for a simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    manager = _get_injection_manager(simulation_id)
    agent_ids = manager.list_injected()

    responses = []
    for agent_id in agent_ids:
        provider = manager.get(agent_id)
        if provider:
            responses.append(InjectedAgentResponse(
                agent_id=agent_id,
                endpoint_url=provider.config.endpoint_url,
                privacy_tier=provider.config.privacy_tier.value,
                fallback_to_simulated=provider.config.fallback_to_simulated,
                circuit_state=provider.circuit_breaker.state.value,
            ))

    return InjectedAgentListResponse(
        simulation_id=simulation_id,
        injected_agents=responses,
        total=len(responses),
    )


@router.get(
    "/simulations/{simulation_id}/inject-agent/{agent_id}/metrics",
    response_model=InjectedAgentMetricsResponse
)
async def get_injection_metrics(simulation_id: str, agent_id: str):
    """Get metrics for an injected agent."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    manager = _get_injection_manager(simulation_id)
    provider = manager.get(agent_id)

    if not provider:
        raise HTTPException(status_code=404, detail={
            "code": "AGENT_NOT_INJECTED",
            "message": f"Agent '{agent_id}' is not injected",
        })

    metrics = provider.metrics
    return InjectedAgentMetricsResponse(
        agent_id=agent_id,
        total_calls=metrics.total_calls,
        successful_calls=metrics.successful_calls,
        failed_calls=metrics.failed_calls,
        error_rate=metrics.error_rate,
        timeout_rate=metrics.timeout_rate,
        latency_p50_ms=metrics.latency_p50_ms,
        latency_p99_ms=metrics.latency_p99_ms,
        circuit_state=metrics.circuit_state,
    )


@router.post(
    "/simulations/{simulation_id}/inject-agent/{agent_id}/health-check",
    response_model=HealthCheckResponse
)
async def check_injection_health(simulation_id: str, agent_id: str):
    """Run health check on an injected agent endpoint."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    manager = _get_injection_manager(simulation_id)
    provider = manager.get(agent_id)

    if not provider:
        raise HTTPException(status_code=404, detail={
            "code": "AGENT_NOT_INJECTED",
            "message": f"Agent '{agent_id}' is not injected",
        })

    start_time = time.time()
    is_healthy = await provider.health_check()
    latency_ms = int((time.time() - start_time) * 1000)

    return HealthCheckResponse(
        agent_id=agent_id,
        endpoint_url=provider.config.endpoint_url,
        is_healthy=is_healthy,
        latency_ms=latency_ms if is_healthy else None,
        error=None if is_healthy else "Health check failed",
    )
