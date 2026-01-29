"""API endpoints for simulated apps per ADR-017.

Includes environment semantics endpoints for Gymnasium-style episode
management and reward tracking.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.apps import get_app_registry
from agentworld.api.schemas.apps import (
    AppActionSchema,
    AppInfoResponse,
    AppInstanceResponse,
    AppListResponse,
    AgentAppStateResponse,
    AppActionLogEntryResponse,
    AppActionLogResponse,
    AvailableAppsResponse,
    # Environment semantics schemas
    EnvResetRequest,
    EnvResetResponse,
    EnvStepRequest,
    EnvStepResponse,
    StateSnapshotResponse,
    EpisodeHistoryResponse,
    EpisodeListResponse,
    TrajectoryItem,
    TrajectoryResponse,
)


router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


@router.get("/apps/available", response_model=AvailableAppsResponse)
async def list_available_apps():
    """List all available app types that can be used in simulations."""
    registry = get_app_registry()
    apps = []

    for app_info in registry.list_apps():
        app = registry.get(app_info["id"])
        if app:
            actions = [
                AppActionSchema(
                    name=action.name,
                    description=action.description,
                    parameters={k: v.to_dict() for k, v in action.parameters.items()},
                    returns=action.returns,
                )
                for action in app.get_actions()
            ]
            apps.append(AppInfoResponse(
                app_id=app.app_id,
                name=app.name,
                description=app.description,
                actions=actions,
            ))

    return AvailableAppsResponse(apps=apps)


@router.get("/simulations/{simulation_id}/apps", response_model=AppListResponse)
async def list_simulation_apps(simulation_id: str):
    """List all apps active in a simulation.

    Returns app instances if simulation has been run, otherwise returns
    apps from config (before instances are created).
    """
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # First try to get instantiated apps (simulation has run)
    instances = repo.get_app_instances_for_simulation(simulation_id)

    if instances:
        # Return actual app instances with state
        apps = [
            AppInstanceResponse(
                id=inst["id"],
                simulation_id=inst["simulation_id"],
                app_id=inst["app_id"],
                config=inst.get("config", {}),
                state=inst.get("state", {}),
                created_at=inst.get("created_at"),
                updated_at=inst.get("updated_at"),
            )
            for inst in instances
        ]
    else:
        # Simulation hasn't run yet - return apps from config
        config = sim.get("config") or {}
        config_apps = config.get("apps", [])

        apps = [
            AppInstanceResponse(
                id=f"pending-{app_config.get('id', 'unknown')}",
                simulation_id=simulation_id,
                app_id=app_config.get("id", "unknown"),
                config=app_config.get("config", {}),
                state={},  # No state yet
                created_at=None,
                updated_at=None,
            )
            for app_config in config_apps
        ]

    return AppListResponse(apps=apps, total=len(apps))


@router.get("/simulations/{simulation_id}/apps/{app_id}", response_model=AppInstanceResponse)
async def get_app_instance(simulation_id: str, app_id: str):
    """Get details of a specific app instance in a simulation."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    instance = repo.get_app_instance_by_app_id(simulation_id, app_id)
    if not instance:
        raise HTTPException(status_code=404, detail={
            "code": "APP_NOT_FOUND",
            "message": f"App '{app_id}' not found in simulation '{simulation_id}'",
        })

    return AppInstanceResponse(
        id=instance["id"],
        simulation_id=instance["simulation_id"],
        app_id=instance["app_id"],
        config=instance.get("config", {}),
        state=instance.get("state", {}),
        created_at=instance.get("created_at"),
        updated_at=instance.get("updated_at"),
    )


@router.get(
    "/simulations/{simulation_id}/apps/{app_id}/agents/{agent_id}",
    response_model=AgentAppStateResponse,
)
async def get_agent_app_state(simulation_id: str, app_id: str, agent_id: str):
    """Get an agent's state for a specific app."""
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

    # Get app instance
    instance = repo.get_app_instance_by_app_id(simulation_id, app_id)
    if not instance:
        raise HTTPException(status_code=404, detail={
            "code": "APP_NOT_FOUND",
            "message": f"App '{app_id}' not found in simulation '{simulation_id}'",
        })

    # Extract agent state from app state
    app_state = instance.get("state", {})
    agent_state = {}

    # Try to get agent-specific state from the app state structure
    state_data = app_state.get("state", {})
    if "accounts" in state_data and agent_id in state_data["accounts"]:
        # PayPal-style account state
        agent_state = state_data["accounts"][agent_id]
    else:
        # Generic: return whole state
        agent_state = state_data

    return AgentAppStateResponse(
        agent_id=agent_id,
        app_id=app_id,
        state=agent_state,
    )


@router.get(
    "/simulations/{simulation_id}/apps/{app_id}/actions",
    response_model=AppActionLogResponse,
)
async def get_app_action_log(
    simulation_id: str,
    app_id: str,
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    step: Optional[int] = Query(None, description="Filter by step"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return"),
):
    """Get the action audit log for an app."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Get app instance
    instance = repo.get_app_instance_by_app_id(simulation_id, app_id)
    if not instance:
        raise HTTPException(status_code=404, detail={
            "code": "APP_NOT_FOUND",
            "message": f"App '{app_id}' not found in simulation '{simulation_id}'",
        })

    # Get action log
    log_entries = repo.get_app_action_log(
        app_instance_id=instance["id"],
        agent_id=agent_id,
        step=step,
        limit=limit,
    )

    actions = [
        AppActionLogEntryResponse(
            id=entry["id"],
            app_instance_id=entry["app_instance_id"],
            agent_id=entry["agent_id"],
            step=entry["step"],
            action_name=entry["action_name"],
            params=entry.get("params", {}),
            success=entry.get("success", False),
            result=entry.get("result"),
            error=entry.get("error"),
            executed_at=entry.get("executed_at"),
        )
        for entry in log_entries
    ]

    return AppActionLogResponse(actions=actions, total=len(actions))


@router.get(
    "/simulations/{simulation_id}/actions",
    response_model=AppActionLogResponse,
)
async def get_simulation_action_log(
    simulation_id: str,
    app_id: Optional[str] = Query(None, description="Filter by app ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return"),
):
    """Get all action logs for a simulation across all apps."""
    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    log_entries = repo.get_app_action_log_for_simulation(
        simulation_id=simulation_id,
        app_id=app_id,
        agent_id=agent_id,
        limit=limit,
    )

    actions = [
        AppActionLogEntryResponse(
            id=entry["id"],
            app_instance_id=entry["app_instance_id"],
            agent_id=entry["agent_id"],
            step=entry["step"],
            action_name=entry["action_name"],
            params=entry.get("params", {}),
            success=entry.get("success", False),
            result=entry.get("result"),
            error=entry.get("error"),
            executed_at=entry.get("executed_at"),
        )
        for entry in log_entries
    ]

    return AppActionLogResponse(actions=actions, total=len(actions))


# ==============================================================================
# Environment Semantics Endpoints
# ==============================================================================

# In-memory storage for environment wrappers (keyed by simulation_id:app_id)
_env_wrappers: dict = {}


def _get_env_key(simulation_id: str, app_id: str) -> str:
    """Generate key for environment wrapper storage."""
    return f"{simulation_id}:{app_id}"


@router.post(
    "/simulations/{simulation_id}/apps/{app_id}/env/reset",
    response_model=EnvResetResponse,
)
async def reset_app_environment(
    simulation_id: str,
    app_id: str,
    request: EnvResetRequest,
):
    """Reset an app to initial state for a new episode.

    Creates or resets an environment wrapper for the specified app,
    starting a new episode with the provided configuration.

    Returns the initial observation and episode metadata.
    """
    from agentworld.apps.environment import AppEnvironmentWrapper

    repo = get_repo()

    # Check simulation exists
    sim = repo.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Get or create app instance
    registry = get_app_registry()
    app = registry.get(app_id)
    if app is None:
        raise HTTPException(status_code=404, detail={
            "code": "APP_NOT_FOUND",
            "message": f"App '{app_id}' not found in registry",
        })

    # Get or create environment wrapper
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        env = AppEnvironmentWrapper(
            app=app,
            max_steps=request.max_steps,
            track_history=True,
        )
        _env_wrappers[env_key] = env
    else:
        # Update max_steps if different
        env._max_steps = request.max_steps

    # Reset the environment
    try:
        result = await env.reset(
            seed=request.seed,
            options={
                "agents": request.agents,
                "config": request.config,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "RESET_FAILED",
            "message": f"Failed to reset environment: {str(e)}",
        })

    return EnvResetResponse(
        episode_id=result.info.get("episode_id", ""),
        observation=result.observation,
        info=result.info,
    )


@router.post(
    "/simulations/{simulation_id}/apps/{app_id}/env/step",
    response_model=EnvStepResponse,
)
async def step_app_environment(
    simulation_id: str,
    app_id: str,
    request: EnvStepRequest,
):
    """Execute an action and return Gymnasium-style step result.

    The environment must be reset before stepping. Returns the new
    observation, reward, and episode termination status.
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        raise HTTPException(status_code=400, detail={
            "code": "NO_ACTIVE_EPISODE",
            "message": "No active episode. Call /env/reset first.",
        })

    if not env.is_active:
        raise HTTPException(status_code=400, detail={
            "code": "EPISODE_ENDED",
            "message": "Episode has ended. Call /env/reset to start a new one.",
        })

    try:
        result = await env.step(
            agent_id=request.agent_id,
            action=request.action,
            params=request.params,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "STEP_FAILED",
            "message": f"Failed to execute step: {str(e)}",
        })

    return EnvStepResponse(
        observation=result.observation,
        reward=result.reward,
        terminated=result.terminated,
        truncated=result.truncated,
        info=result.info,
    )


@router.post("/simulations/{simulation_id}/apps/{app_id}/env/close")
async def close_app_environment(simulation_id: str, app_id: str):
    """Close the environment and finalize episode history.

    This should be called when done with the current episode to
    ensure the history is properly saved.
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        raise HTTPException(status_code=404, detail={
            "code": "ENV_NOT_FOUND",
            "message": "No environment wrapper found for this app.",
        })

    env.close()

    return {"status": "closed", "episode_count": env.get_episode_count()}


@router.get(
    "/simulations/{simulation_id}/apps/{app_id}/env/status",
)
async def get_env_status(simulation_id: str, app_id: str):
    """Get current environment status.

    Returns episode state including current step, cumulative reward,
    and termination status.
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        return {
            "active": False,
            "episode_id": None,
            "step_count": 0,
            "cumulative_reward": 0.0,
            "terminated": False,
            "truncated": False,
            "completed_episodes": 0,
        }

    return {
        "active": env.is_active,
        "episode_id": env.episode_id,
        "step_count": env.step_count,
        "max_steps": env.max_steps,
        "cumulative_reward": env.cumulative_reward,
        "terminated": env.terminated,
        "truncated": env.truncated,
        "completed_episodes": env.get_episode_count(),
    }


@router.get(
    "/simulations/{simulation_id}/apps/{app_id}/episodes",
    response_model=EpisodeListResponse,
)
async def list_app_episodes(
    simulation_id: str,
    app_id: str,
    include_current: bool = Query(True, description="Include current episode if active"),
):
    """List all episodes for an app environment.

    Returns completed episodes and optionally the current active episode.
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        return EpisodeListResponse(episodes=[], total=0)

    episodes = []

    # Add completed episodes
    for ep in env.get_all_episodes():
        episodes.append(EpisodeHistoryResponse(
            episode_id=ep.episode_id,
            started_at=ep.started_at,
            ended_at=ep.ended_at,
            snapshots=[
                StateSnapshotResponse(
                    step=s.step,
                    timestamp=s.timestamp,
                    state=s.state,
                    action=s.action,
                    params=s.params,
                    reward=s.reward,
                )
                for s in ep.snapshots
            ],
            terminated=ep.terminated,
            truncated=ep.truncated,
            total_reward=ep.total_reward,
            step_count=ep.step_count,
        ))

    # Include current episode if requested and active
    if include_current and env.is_active:
        current = env.get_episode_history()
        if current:
            episodes.append(EpisodeHistoryResponse(
                episode_id=current.episode_id,
                started_at=current.started_at,
                ended_at=current.ended_at,
                snapshots=[
                    StateSnapshotResponse(
                        step=s.step,
                        timestamp=s.timestamp,
                        state=s.state,
                        action=s.action,
                        params=s.params,
                        reward=s.reward,
                    )
                    for s in current.snapshots
                ],
                terminated=current.terminated,
                truncated=current.truncated,
                total_reward=current.total_reward,
                step_count=current.step_count,
            ))

    return EpisodeListResponse(episodes=episodes, total=len(episodes))


@router.get(
    "/simulations/{simulation_id}/apps/{app_id}/episodes/{episode_id}",
    response_model=EpisodeHistoryResponse,
)
async def get_episode_history(
    simulation_id: str,
    app_id: str,
    episode_id: str,
):
    """Get detailed history for a specific episode.

    Returns all state snapshots, actions, and rewards for the episode.
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        raise HTTPException(status_code=404, detail={
            "code": "ENV_NOT_FOUND",
            "message": "No environment wrapper found for this app.",
        })

    history = env.get_episode_history(episode_id)
    if history is None:
        raise HTTPException(status_code=404, detail={
            "code": "EPISODE_NOT_FOUND",
            "message": f"Episode '{episode_id}' not found.",
        })

    return EpisodeHistoryResponse(
        episode_id=history.episode_id,
        started_at=history.started_at,
        ended_at=history.ended_at,
        snapshots=[
            StateSnapshotResponse(
                step=s.step,
                timestamp=s.timestamp,
                state=s.state,
                action=s.action,
                params=s.params,
                reward=s.reward,
            )
            for s in history.snapshots
        ],
        terminated=history.terminated,
        truncated=history.truncated,
        total_reward=history.total_reward,
        step_count=history.step_count,
    )


@router.get(
    "/simulations/{simulation_id}/apps/{app_id}/episodes/{episode_id}/trajectory",
    response_model=TrajectoryResponse,
)
async def get_episode_trajectory(
    simulation_id: str,
    app_id: str,
    episode_id: str,
):
    """Get (state, action, reward) trajectory for RL training.

    Returns the trajectory in a format suitable for reinforcement
    learning algorithms.
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        raise HTTPException(status_code=404, detail={
            "code": "ENV_NOT_FOUND",
            "message": "No environment wrapper found for this app.",
        })

    history = env.get_episode_history(episode_id)
    if history is None:
        raise HTTPException(status_code=404, detail={
            "code": "EPISODE_NOT_FOUND",
            "message": f"Episode '{episode_id}' not found.",
        })

    trajectory = [
        TrajectoryItem(state=state, action=action, reward=reward)
        for state, action, reward in history.get_trajectory()
    ]

    return TrajectoryResponse(
        episode_id=history.episode_id,
        trajectory=trajectory,
        total_reward=history.total_reward,
    )


@router.post("/simulations/{simulation_id}/apps/{app_id}/env/mark-terminated")
async def mark_episode_terminated(
    simulation_id: str,
    app_id: str,
    terminated: bool = True,
):
    """Manually mark the current episode as terminated.

    Use this when external logic determines that the goal has been achieved
    (e.g., task completion verification).
    """
    env_key = _get_env_key(simulation_id, app_id)
    env = _env_wrappers.get(env_key)

    if env is None:
        raise HTTPException(status_code=404, detail={
            "code": "ENV_NOT_FOUND",
            "message": "No environment wrapper found for this app.",
        })

    if not env.is_active and not env.terminated:
        raise HTTPException(status_code=400, detail={
            "code": "NO_ACTIVE_EPISODE",
            "message": "No active episode to mark as terminated.",
        })

    env.mark_terminated(terminated)

    return {
        "status": "success",
        "episode_id": env.episode_id,
        "terminated": env.terminated,
    }
