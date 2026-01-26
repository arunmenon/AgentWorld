"""API endpoints for simulated apps per ADR-017."""

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
