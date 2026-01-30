"""Simulation API endpoints."""

import time
import uuid
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.core.models import SimulationStatus, SimulationConfig, AgentConfig, TerminationMode

if TYPE_CHECKING:
    from agentworld.agents.external import InjectedAgentManager
    from agentworld.simulation.runner import Simulation
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.goals.types import GoalSpec
from agentworld.persistence.models import DualControlTaskModel
from agentworld.api.schemas.simulations import (
    SimulationResponse,
    SimulationListResponse,
    CreateSimulationRequest,
    StepRequest,
    StepResponse,
    InjectRequest,
    InjectResponse,
    SimulationControlResponse,
    GoalProgressResponse,
    GoalSpecResponse,
    GoalConditionResponse,
    GenerateSimulationRequest,
    GenerateSimulationResponse,
    EpisodeResponse,
    EpisodeStartResponse,
    EpisodeEndRequest,
    EpisodeEndResponse,
    EpisodeListResponse,
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
from agentworld.api.schemas.dual_control import CoordinationMetricsSchema


router = APIRouter()

# In-memory storage for injected agents per simulation
# In production, this should be persisted
_injected_agents: dict[str, "InjectedAgentManager"] = {}

# In-memory storage for active simulation runners (for episode management)
# In production, this should be persisted or use a more robust mechanism
_active_runners: dict[str, "Simulation"] = {}


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


def _reconstruct_simulation(simulation_id: str, repo: Repository | None = None) -> "Simulation":
    """Reconstruct a Simulation instance from database state.

    Args:
        simulation_id: ID of the simulation to reconstruct
        repo: Optional repository instance (creates new if not provided)

    Returns:
        Simulation instance with state restored from DB

    Raises:
        HTTPException: If simulation not found
    """
    from agentworld.simulation.runner import Simulation
    from agentworld.core.models import SimulationConfig, AgentConfig

    if repo is None:
        repo = get_repo()

    sim_data = repo.get_simulation(simulation_id)
    if not sim_data:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Reconstruct agent configs from stored data
    agents_data = repo.get_agents_for_simulation(simulation_id)
    agent_configs = [
        AgentConfig(
            name=agent_data.get("name", "Agent"),
            traits=agent_data.get("traits", {}),
            background=agent_data.get("background", ""),
            system_prompt=agent_data.get("system_prompt"),
            model=agent_data.get("model"),
        )
        for agent_data in agents_data
    ]

    config_data = sim_data.get("config") or {}
    apps_config = config_data.get("apps")

    config = SimulationConfig(
        name=sim_data.get("name", "Simulation"),
        agents=agent_configs,
        steps=sim_data.get("total_steps", 10),
        initial_prompt=config_data.get("initial_prompt", ""),
        model=config_data.get("model", "openai/gpt-4o-mini"),
        apps=apps_config,
    )

    sim = Simulation.from_config(config)
    sim.id = simulation_id
    sim.current_step = sim_data.get("current_step", 0)
    sim.status = SimulationStatus(sim_data.get("status", "pending"))

    # Match agent IDs with stored agents
    for i, agent in enumerate(sim.agents):
        if i < len(agents_data):
            agent.id = agents_data[i].get("id", agent.id)

    return sim


def simulation_to_response(sim: dict, repo: Repository) -> SimulationResponse:
    """Convert simulation dict to response."""
    agents = repo.get_agents_for_simulation(sim["id"])
    message_count = repo.count_messages(sim["id"])

    progress = None
    if sim.get("total_steps") and sim.get("total_steps") > 0:
        progress = (sim.get("current_step", 0) / sim["total_steps"]) * 100

    # Parse goal info from config if present
    goal_response = None
    config_data = sim.get("config") or {}
    goal_spec_data = config_data.get("goal_spec")
    if goal_spec_data:
        conditions = [
            GoalConditionResponse(**c) if isinstance(c, dict) else c
            for c in goal_spec_data.get("conditions", [])
        ]
        goal_response = GoalProgressResponse(
            goal_spec=GoalSpecResponse(
                conditions=conditions,
                success_mode=goal_spec_data.get("success_mode", "all"),
                description=goal_spec_data.get("description", ""),
            ),
            goal_achieved=config_data.get("goal_achieved", False),
            goal_achieved_step=config_data.get("goal_achieved_step"),
            termination_mode=config_data.get("termination_mode", "max_steps"),
        )

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
        task_id=config_data.get("task_id"),
        goal=goal_response,
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


@router.post("/simulations/generate", response_model=GenerateSimulationResponse)
async def generate_simulation(
    request: GenerateSimulationRequest,
) -> GenerateSimulationResponse:
    """Generate a simulation configuration from natural language.

    Uses an LLM to interpret the natural language description and generate
    a complete simulation configuration with agents, personality traits, and
    initial prompt that can be reviewed and modified.
    """
    import logging
    from agentworld.simulation.ai_generator import AISimulationGenerator

    logger = logging.getLogger(__name__)

    try:
        generator = AISimulationGenerator()
        config = await generator.generate_simulation(
            description=request.description,
            num_agents_hint=request.num_agents,
        )
        return GenerateSimulationResponse(
            success=True,
            config=config,
        )
    except ValueError as e:
        logger.warning(f"Simulation generation failed: {e}")
        return GenerateSimulationResponse(
            success=False,
            config={},
            error=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during simulation generation: {e}")
        return GenerateSimulationResponse(
            success=False,
            config={},
            error="Failed to generate simulation. Please try again with a clearer description.",
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
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    logger.info("=== CREATE SIMULATION REQUEST ===")
    logger.info(f"Name: {request.name}")
    logger.info(f"Apps: {request.apps}")

    repo = get_repo()

    # Build agent configs
    if request.agents:
        agent_configs = [
            AgentConfig(
                name=a.name,
                traits=a.traits or {},
                background=a.background or "",
                system_prompt=a.system_prompt,
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

    # Build apps config from request
    apps_config = None
    if request.apps:
        apps_config = [
            {"id": app.app_id, "config": app.config or {}}
            for app in request.apps
        ]

    # Parse termination mode
    termination_mode = TerminationMode(request.termination_mode)

    # If task_id provided, load task for goal_spec and potentially auto-configure apps
    goal_spec = None
    task_id = request.task_id
    task = None  # Store task for reuse

    if task_id:
        # Try to load task
        try:
            session = repo.session
            task_model = session.query(DualControlTaskModel).filter(
                DualControlTaskModel.task_id == task_id
            ).first()
            task = task_model.to_dict() if task_model else None
        except Exception as e:
            logger.warning(f"Failed to load task {task_id}: {e}")

    # Auto-configure apps from task if no apps provided in request
    if task and not apps_config:
        task_agent_apps = task.get("agent_apps", [])
        task_user_apps = task.get("user_apps", [])
        all_task_apps = list(set(task_agent_apps + task_user_apps))

        if all_task_apps:
            apps_config = [{"id": app_id, "config": {}} for app_id in all_task_apps]
            logger.info(f"Auto-configured apps from task {task_id}: {all_task_apps}")

    # If task_id provided and goal/hybrid mode, inherit goal_spec from task
    if task and termination_mode in (TerminationMode.GOAL, TerminationMode.HYBRID):
        try:
            # Check for new goal_conditions format in simulation_config first
            sim_config = task.get("simulation_config", {})
            goal_conditions = sim_config.get("goal_conditions", [])

            if goal_conditions:
                # Use new structured goal conditions format
                goal_spec = GoalSpec.from_dict({
                    "conditions": goal_conditions,
                    "success_mode": sim_config.get("success_mode", "all"),
                    "description": task.get("description", ""),
                })
                logger.info(f"Loaded goal_spec from task {task_id} (new format): {len(goal_spec.conditions)} conditions")
            else:
                # Fall back to legacy goal_state format
                user_goal = task.get("user_goal_state", {})
                agent_goal = task.get("agent_goal_state", {})
                combined_goals = {**user_goal, **agent_goal}
                if combined_goals:
                    # Parse legacy format - handle both "app_id.field" and nested dict formats
                    parsed_goals: dict[str, dict] = {}
                    for key, value in combined_goals.items():
                        if "." in key:
                            app_id, field = key.split(".", 1)
                            if app_id not in parsed_goals:
                                parsed_goals[app_id] = {}
                            parsed_goals[app_id][field] = value
                        elif isinstance(value, dict):
                            parsed_goals[key] = value

                    if parsed_goals:
                        goal_spec = GoalSpec.from_legacy_goal_state(
                            parsed_goals,
                            description=task.get("description", ""),
                        )
                        logger.info(f"Loaded goal_spec from task {task_id} (legacy format): {len(goal_spec.conditions)} conditions")
        except Exception as e:
            logger.warning(f"Failed to load goal_spec from task {task_id}: {e}")

    config = SimulationConfig(
        name=request.name,
        agents=agent_configs,
        steps=request.steps,
        initial_prompt=request.initial_prompt,
        model=request.model,
        apps=apps_config,
        termination_mode=termination_mode,
        goal_spec=goal_spec,
        task_id=task_id,
    )

    # Create simulation using runner
    try:
        from agentworld.simulation.runner import Simulation

        sim = Simulation.from_config(config)
        sim._save_state()

        return simulation_to_response(repo.get_simulation(sim.id), repo)
    except Exception as e:
        logger.error(f"Error creating simulation: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={
            "code": "SIMULATION_CREATION_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        })


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
    repo = get_repo()
    sim = _reconstruct_simulation(simulation_id, repo)

    # Get apps config to determine if initialization needed
    sim_data = repo.get_simulation(simulation_id)
    config_data = sim_data.get("config") or {}
    apps_config = config_data.get("apps")

    # Initialize apps if configured
    if apps_config:
        await sim.initialize_apps()

    # Start episode automatically if apps configured and no episode running
    if sim.app_manager is not None and sim.episode_id is None:
        sim.start_episode()

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


# =============================================================================
# Coordination Metrics Endpoints (ADR-020.1)
# =============================================================================


@router.get(
    "/simulations/{simulation_id}/coordination-metrics",
    response_model=CoordinationMetricsSchema
)
async def get_simulation_coordination_metrics(simulation_id: str):
    """Get coordination metrics for a simulation.

    Returns metrics computed from coordination events tracked during
    the simulation run. Uses the simulation ID as the trial_id for
    querying events.
    """
    from datetime import datetime, UTC
    from sqlalchemy.orm import Session as SQLSession

    from agentworld.persistence.database import get_session
    from agentworld.persistence.models import CoordinationEventModel, DualControlTaskModel

    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Get task_id from simulation config
    config_data = sim.get("config") or {}
    task_id = config_data.get("task_id")

    if not task_id:
        # No task associated - return empty metrics
        return CoordinationMetricsSchema(
            task_id="unknown",
            trial_id=simulation_id,
            total_handoffs_required=0,
            handoffs_completed=0,
            coordination_success_rate=0.0,
            avg_instruction_to_action_turns=0.0,
            unnecessary_user_actions=0,
            instruction_clarity_score=None,
            user_confusion_count=0,
            computed_at=datetime.now(UTC),
        )

    with get_session() as session:
        # Get task to know expected handoff count
        task = session.query(DualControlTaskModel).filter(
            DualControlTaskModel.task_id == task_id
        ).first()

        total_handoffs_required = task.expected_coordination_count if task else 0

        # Query coordination events for this simulation (trial)
        events = session.query(CoordinationEventModel).filter(
            CoordinationEventModel.trial_id == simulation_id
        ).all()

        # Compute metrics
        handoffs_completed = sum(1 for e in events if e.handoff_successful)
        success_rate = (
            handoffs_completed / total_handoffs_required
            if total_handoffs_required > 0 else 0.0
        )

        # Latency metrics
        latencies = [
            e.latency_turns for e in events
            if e.handoff_successful and e.latency_turns and e.latency_turns > 0
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        # Confusion count (low confidence matches)
        confusion_count = sum(
            1 for e in events
            if e.match_confidence and e.match_confidence < 0.5 and e.instruction_text
        )

        return CoordinationMetricsSchema(
            task_id=task_id,
            trial_id=simulation_id,
            total_handoffs_required=total_handoffs_required,
            handoffs_completed=handoffs_completed,
            coordination_success_rate=success_rate,
            avg_instruction_to_action_turns=avg_latency,
            unnecessary_user_actions=0,  # Would need more analysis
            instruction_clarity_score=None,  # Would need LLM analysis
            user_confusion_count=confusion_count,
            computed_at=datetime.now(UTC),
        )


# =============================================================================
# Episode Endpoints
# =============================================================================


def _get_or_create_runner(simulation_id: str) -> "Simulation":
    """Get or create a simulation runner for episode management.

    Uses the _active_runners cache for efficiency. Returns cached runner
    if available, otherwise reconstructs from DB state.
    """
    if simulation_id in _active_runners:
        return _active_runners[simulation_id]

    sim = _reconstruct_simulation(simulation_id)
    _active_runners[simulation_id] = sim
    return sim


@router.post(
    "/simulations/{simulation_id}/episode/start",
    response_model=EpisodeStartResponse
)
async def start_simulation_episode(simulation_id: str):
    """Start a new episode for a simulation.

    An episode tracks a sequence of app actions with reward accumulation.
    Use this to track distinct interaction periods within a simulation.
    """
    runner = _get_or_create_runner(simulation_id)

    # Check if there's already an active episode
    if runner.episode_id is not None and not runner._episode_terminated and not runner._episode_truncated:
        raise HTTPException(status_code=409, detail={
            "code": "EPISODE_ALREADY_ACTIVE",
            "message": f"Episode '{runner.episode_id}' is already active. End it first.",
        })

    episode_id = runner.start_episode()

    return EpisodeStartResponse(
        simulation_id=simulation_id,
        episode_id=episode_id,
        message="Episode started",
    )


@router.post(
    "/simulations/{simulation_id}/episode/end",
    response_model=EpisodeEndResponse
)
async def end_simulation_episode(
    simulation_id: str,
    request: EpisodeEndRequest = EpisodeEndRequest(),
):
    """End the current episode for a simulation.

    Args:
        terminated: True if goal was achieved (success)
        truncated: True if ending due to max steps or manual stop
    """
    runner = _get_or_create_runner(simulation_id)

    if runner.episode_id is None:
        raise HTTPException(status_code=404, detail={
            "code": "NO_ACTIVE_EPISODE",
            "message": "No active episode to end",
        })

    episode_id = runner.episode_id
    result = runner.end_episode(
        terminated=request.terminated,
        truncated=request.truncated,
    )

    return EpisodeEndResponse(
        simulation_id=simulation_id,
        episode_id=episode_id,
        action_count=result["action_count"],
        turn_count=result["turn_count"],
        total_reward=result["total_reward"],
        terminated=result["terminated"],
        truncated=result["truncated"],
        message="Episode ended",
    )


@router.get(
    "/simulations/{simulation_id}/episodes",
    response_model=EpisodeListResponse
)
async def list_simulation_episodes(
    simulation_id: str,
    limit: int = Query(50, ge=1, le=100),
):
    """List all episodes for a simulation.

    Returns episodes in reverse chronological order (newest first).
    """
    repo = get_repo()

    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    episodes = repo.get_episodes_for_simulation(simulation_id, limit=limit)

    return EpisodeListResponse(
        simulation_id=simulation_id,
        episodes=[EpisodeResponse(**ep) for ep in episodes],
        total=len(episodes),
    )


@router.get(
    "/simulations/{simulation_id}/episode/current",
    response_model=EpisodeResponse
)
async def get_current_episode(simulation_id: str):
    """Get the current active episode for a simulation.

    Returns 404 if no episode is active.
    """
    repo = get_repo()

    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    episode = repo.get_active_episode(simulation_id)
    if not episode:
        raise HTTPException(status_code=404, detail={
            "code": "NO_ACTIVE_EPISODE",
            "message": "No active episode for this simulation",
        })

    return EpisodeResponse(**episode)


@router.get(
    "/simulations/{simulation_id}/episodes/{episode_id}",
    response_model=EpisodeResponse
)
async def get_episode(simulation_id: str, episode_id: str):
    """Get a specific episode by ID."""
    repo = get_repo()

    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    episode = repo.get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail={
            "code": "EPISODE_NOT_FOUND",
            "message": f"Episode '{episode_id}' not found",
        })

    if episode["simulation_id"] != simulation_id:
        raise HTTPException(status_code=404, detail={
            "code": "EPISODE_NOT_FOUND",
            "message": f"Episode '{episode_id}' not found in simulation '{simulation_id}'",
        })

    return EpisodeResponse(**episode)
