"""API routes for dual-control tasks (ADR-020.1).

This module provides REST endpoints for:
- Dual-control task definitions (CRUD)
- Coordination event tracking
- Solo vs dual mode comparison
- Coordination metrics
"""

import json
import logging
import uuid
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from agentworld.api.dependencies import get_repository
from agentworld.api.schemas.dual_control import (
    CreateDualControlTaskRequest,
    UpdateDualControlTaskRequest,
    DualControlTaskResponse,
    DualControlTaskListResponse,
    CreateCoordinationEventRequest,
    CoordinationEventSchema,
    CoordinationEventListResponse,
    CoordinationMetricsSchema,
    SoloDualComparisonSchema,
    RunComparisonRequest,
    RunComparisonResponse,
    GenerateTaskRequest,
    GenerateTaskResponse,
)
from agentworld.persistence.models import (
    DualControlTaskModel,
    CoordinationEventModel,
    SoloDualComparisonModel,
)
from agentworld.persistence.repository import Repository


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dual-control-tasks", tags=["Dual Control Tasks"])


def _validate_apps_exist(
    app_ids: list[str],
    repo: "Repository",
    field_name: str = "apps",
) -> list[str]:
    """Validate that all app IDs reference existing apps.

    Args:
        app_ids: List of app IDs to validate
        repo: Repository instance for database access
        field_name: Name of the field (for error messages)

    Returns:
        List of missing app IDs (empty if all exist)
    """
    if not app_ids:
        return []

    missing = []
    for app_id in app_ids:
        app_def = repo.get_app_definition_by_app_id(app_id)
        if not app_def:
            missing.append(app_id)

    return missing


def _get_session(repo: Repository = Depends(get_repository)) -> Session:
    """Get SQLAlchemy session from repository."""
    return repo.session


# =============================================================================
# Dual-Control Task Definitions
# =============================================================================


@router.post("", response_model=DualControlTaskResponse, status_code=201)
async def create_dual_control_task(
    request: CreateDualControlTaskRequest,
    session: Session = Depends(_get_session),
    repo: Repository = Depends(get_repository),
) -> DualControlTaskResponse:
    """Create a new dual-control task definition.

    Dual-control tasks specify:
    - Agent configuration (service agent with backend access)
    - User configuration (customer with device access)
    - Required coordination handoffs
    - Goal states for both parties

    Validates that all referenced apps exist in the App Studio.
    """
    # Check for duplicate task_id
    existing = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == request.task_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Dual-control task with ID '{request.task_id}' already exists",
        )

    # Validate that all referenced apps exist
    all_apps = list(set(request.agent_apps + request.user_apps))
    missing_apps = _validate_apps_exist(all_apps, repo, "agent_apps/user_apps")
    if missing_apps:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "APPS_NOT_FOUND",
                "message": f"The following apps do not exist: {', '.join(missing_apps)}. Please create them in App Studio first.",
                "missing_apps": missing_apps,
            },
        )

    # Create task model
    task = DualControlTaskModel(
        id=str(uuid.uuid4()),
        task_id=request.task_id,
        name=request.name,
        description=request.description,
        domain=request.domain,
        difficulty=request.difficulty,
        simulation_config_json=json.dumps(request.simulation_config),
        agent_id=request.agent_id,
        agent_role=request.agent_role,
        agent_instruction=request.agent_instruction,
        agent_apps_json=json.dumps(request.agent_apps),
        agent_initial_state_json=json.dumps(request.agent_initial_state),
        agent_goal_state_json=json.dumps(request.agent_goal_state),
        user_id=request.user_id,
        user_role=request.user_role,
        user_instruction=request.user_instruction,
        user_apps_json=json.dumps(request.user_apps),
        user_initial_state_json=json.dumps(request.user_initial_state),
        user_goal_state_json=json.dumps(request.user_goal_state),
        required_handoffs_json=json.dumps([h.model_dump() for h in request.required_handoffs]),
        max_turns=request.max_turns,
        expected_coordination_count=request.expected_coordination_count,
        tags_json=json.dumps(request.tags),
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return DualControlTaskResponse(**task.to_dict())


@router.get("", response_model=DualControlTaskListResponse)
async def list_dual_control_tasks(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    session: Session = Depends(_get_session),
) -> DualControlTaskListResponse:
    """List dual-control task definitions with optional filtering."""
    query = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.is_active == 1
    )

    if domain:
        query = query.filter(DualControlTaskModel.domain == domain)
    if difficulty:
        query = query.filter(DualControlTaskModel.difficulty == difficulty)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (DualControlTaskModel.name.ilike(search_pattern)) |
            (DualControlTaskModel.description.ilike(search_pattern))
        )

    # Tag filtering (JSON contains)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.filter(DualControlTaskModel.tags_json.contains(f'"{tag}"'))

    total = query.count()
    offset = (page - 1) * per_page
    tasks = query.order_by(DualControlTaskModel.created_at.desc()).offset(offset).limit(per_page).all()

    return DualControlTaskListResponse(
        tasks=[DualControlTaskResponse(**t.to_dict()) for t in tasks],
        total=total,
    )


# =============================================================================
# Static Routes (must be before /{task_id} to avoid matching)
# =============================================================================


@router.post("/generate", response_model=GenerateTaskResponse)
async def generate_task(
    request: GenerateTaskRequest,
) -> GenerateTaskResponse:
    """Generate a task definition from natural language.

    Uses an LLM to interpret the natural language description and generate
    a complete dual-control task definition that can be reviewed and modified.
    """
    from agentworld.tasks.ai_generator import AITaskGenerator

    try:
        # Convert available apps to dict format for generator
        available_apps = None
        if request.available_apps:
            available_apps = [
                {
                    "app_id": app.app_id,
                    "name": app.name,
                    "actions": [{"name": a.name, "description": a.description} for a in app.actions],
                }
                for app in request.available_apps
            ]

        generator = AITaskGenerator()
        task_data = await generator.generate_task(
            description=request.description,
            domain_hint=request.domain_hint,
            available_apps=available_apps,
        )
        return GenerateTaskResponse(
            success=True,
            task=task_data,
        )
    except ValueError as e:
        logger.warning(f"Task generation failed: {e}")
        return GenerateTaskResponse(
            success=False,
            task={},
            error=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during task generation: {e}")
        return GenerateTaskResponse(
            success=False,
            task={},
            error="Failed to generate task. Please try again with a clearer description.",
        )


@router.get("/domains/list")
async def list_domains(
    session: Session = Depends(_get_session),
) -> dict:
    """List all unique domains for dual-control tasks."""
    from sqlalchemy import distinct
    domains = session.query(distinct(DualControlTaskModel.domain)).filter(
        DualControlTaskModel.is_active == 1
    ).all()

    return {
        "domains": [d[0] for d in domains if d[0]],
        "count": len(domains),
    }


@router.get("/stats")
async def get_dual_control_stats(
    session: Session = Depends(_get_session),
) -> dict:
    """Get statistics about dual-control tasks."""
    total_tasks = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.is_active == 1
    ).count()

    total_events = session.query(CoordinationEventModel).count()

    successful_events = session.query(CoordinationEventModel).filter(
        CoordinationEventModel.handoff_successful == 1
    ).count()

    total_comparisons = session.query(SoloDualComparisonModel).count()

    return {
        "total_tasks": total_tasks,
        "total_coordination_events": total_events,
        "successful_handoffs": successful_events,
        "handoff_success_rate": successful_events / total_events if total_events > 0 else 0.0,
        "total_comparisons": total_comparisons,
    }


# =============================================================================
# Task-specific Routes
# =============================================================================


@router.get("/{task_id}", response_model=DualControlTaskResponse)
async def get_dual_control_task(
    task_id: str,
    session: Session = Depends(_get_session),
) -> DualControlTaskResponse:
    """Get a dual-control task by task_id."""
    task = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Dual-control task '{task_id}' not found")

    return DualControlTaskResponse(**task.to_dict())


@router.patch("/{task_id}", response_model=DualControlTaskResponse)
async def update_dual_control_task(
    task_id: str,
    request: UpdateDualControlTaskRequest,
    session: Session = Depends(_get_session),
    repo: Repository = Depends(get_repository),
) -> DualControlTaskResponse:
    """Update a dual-control task definition.

    Validates that any updated app references exist in the App Studio.
    """
    task = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Dual-control task '{task_id}' not found")

    # Validate updated apps if provided
    apps_to_validate = []
    if request.agent_apps is not None:
        apps_to_validate.extend(request.agent_apps)
    if request.user_apps is not None:
        apps_to_validate.extend(request.user_apps)

    if apps_to_validate:
        missing_apps = _validate_apps_exist(list(set(apps_to_validate)), repo, "agent_apps/user_apps")
        if missing_apps:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "APPS_NOT_FOUND",
                    "message": f"The following apps do not exist: {', '.join(missing_apps)}. Please create them in App Studio first.",
                    "missing_apps": missing_apps,
                },
            )

    # Apply updates
    if request.name is not None:
        task.name = request.name
    if request.description is not None:
        task.description = request.description
    if request.difficulty is not None:
        task.difficulty = request.difficulty
    if request.agent_instruction is not None:
        task.agent_instruction = request.agent_instruction
    if request.user_instruction is not None:
        task.user_instruction = request.user_instruction
    if request.agent_apps is not None:
        task.agent_apps_json = json.dumps(request.agent_apps)
    if request.user_apps is not None:
        task.user_apps_json = json.dumps(request.user_apps)
    if request.agent_initial_state is not None:
        task.agent_initial_state_json = json.dumps(request.agent_initial_state)
    if request.user_initial_state is not None:
        task.user_initial_state_json = json.dumps(request.user_initial_state)
    if request.agent_goal_state is not None:
        task.agent_goal_state_json = json.dumps(request.agent_goal_state)
    if request.user_goal_state is not None:
        task.user_goal_state_json = json.dumps(request.user_goal_state)
    if request.required_handoffs is not None:
        task.required_handoffs_json = json.dumps([h.model_dump() for h in request.required_handoffs])
    if request.max_turns is not None:
        task.max_turns = request.max_turns
    if request.tags is not None:
        task.tags_json = json.dumps(request.tags)
    if request.is_active is not None:
        task.is_active = int(request.is_active)

    session.commit()
    session.refresh(task)

    return DualControlTaskResponse(**task.to_dict())


@router.delete("/{task_id}", status_code=204)
async def delete_dual_control_task(
    task_id: str,
    hard: bool = Query(False, description="Permanently delete"),
    session: Session = Depends(_get_session),
) -> None:
    """Delete a dual-control task (soft delete by default)."""
    task = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Dual-control task '{task_id}' not found")

    if hard:
        session.delete(task)
    else:
        task.is_active = 0

    session.commit()


# =============================================================================
# Coordination Events
# =============================================================================


@router.get("/{task_id}/events", response_model=CoordinationEventListResponse)
async def list_coordination_events(
    task_id: str,
    trial_id: Optional[str] = Query(None, description="Filter by trial ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(_get_session),
) -> CoordinationEventListResponse:
    """Get coordination events for a dual-control task."""
    query = session.query(CoordinationEventModel).filter(
        CoordinationEventModel.task_id == task_id
    )

    if trial_id:
        query = query.filter(CoordinationEventModel.trial_id == trial_id)

    total = query.count()
    events = query.order_by(CoordinationEventModel.timestamp.desc()).offset(offset).limit(limit).all()

    return CoordinationEventListResponse(
        events=[CoordinationEventSchema(**e.to_dict()) for e in events],
        total=total,
    )


@router.post("/{task_id}/events", response_model=CoordinationEventSchema, status_code=201)
async def create_coordination_event(
    task_id: str,
    event: CreateCoordinationEventRequest,
    session: Session = Depends(_get_session),
) -> CoordinationEventSchema:
    """Record a coordination event for a dual-control task."""
    # Verify task exists
    task = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Dual-control task '{task_id}' not found")

    event_model = CoordinationEventModel(
        id=str(uuid.uuid4()),
        event_id=event.event_id,
        trial_id=event.trial_id,
        task_id=task_id,
        instructor_id=event.instructor_id,
        instructor_role=event.instructor_role,
        instruction_text=event.instruction_text,
        actor_id=event.actor_id,
        actor_role=event.actor_role,
        action_taken=event.action_taken,
        action_params_json=json.dumps(event.action_params) if event.action_params else None,
        matched_handoff_id=event.matched_handoff_id,
        match_confidence=event.match_confidence,
        handoff_successful=int(event.handoff_successful),
        latency_turns=event.latency_turns,
    )

    session.add(event_model)
    session.commit()
    session.refresh(event_model)

    return CoordinationEventSchema(**event_model.to_dict())


# =============================================================================
# Coordination Metrics
# =============================================================================


@router.get("/{task_id}/metrics", response_model=CoordinationMetricsSchema)
async def get_coordination_metrics(
    task_id: str,
    trial_id: Optional[str] = Query(None, description="Specific trial (None for aggregate)"),
    session: Session = Depends(_get_session),
) -> CoordinationMetricsSchema:
    """Compute coordination metrics for a dual-control task."""
    # Verify task exists
    task = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Dual-control task '{task_id}' not found")

    # Build query
    query = session.query(CoordinationEventModel).filter(
        CoordinationEventModel.task_id == task_id
    )
    if trial_id:
        query = query.filter(CoordinationEventModel.trial_id == trial_id)

    events = query.all()

    # Compute metrics
    total_handoffs_required = task.expected_coordination_count or 0
    handoffs_completed = sum(1 for e in events if e.handoff_successful)
    success_rate = handoffs_completed / total_handoffs_required if total_handoffs_required > 0 else 0.0

    # Latency metrics
    latencies = [e.latency_turns for e in events if e.handoff_successful and e.latency_turns > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # Count events that might indicate confusion (low confidence matches)
    confusion_count = sum(1 for e in events if e.match_confidence < 0.5 and e.instruction_text)

    return CoordinationMetricsSchema(
        task_id=task_id,
        trial_id=trial_id,
        total_handoffs_required=total_handoffs_required,
        handoffs_completed=handoffs_completed,
        coordination_success_rate=success_rate,
        avg_instruction_to_action_turns=avg_latency,
        unnecessary_user_actions=0,  # Would need action analysis to compute
        instruction_clarity_score=None,  # Would need LLM analysis
        user_confusion_count=confusion_count,
        computed_at=datetime.now(UTC),
    )


# =============================================================================
# Solo vs Dual Comparison
# =============================================================================


@router.get("/{task_id}/comparison", response_model=SoloDualComparisonSchema)
async def get_solo_dual_comparison(
    task_id: str,
    session: Session = Depends(_get_session),
) -> SoloDualComparisonSchema:
    """Get the latest solo vs dual comparison for a task."""
    comparison = session.query(SoloDualComparisonModel).filter(
        SoloDualComparisonModel.task_id == task_id
    ).order_by(SoloDualComparisonModel.computed_at.desc()).first()

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail=f"No comparison found for task '{task_id}'. Run comparison first.",
        )

    return SoloDualComparisonSchema(**comparison.to_dict())


@router.post("/{task_id}/compare", response_model=RunComparisonResponse)
async def run_solo_dual_comparison(
    task_id: str,
    request: RunComparisonRequest,
    session: Session = Depends(_get_session),
) -> RunComparisonResponse:
    """Run comparison between solo and dual mode.

    This is a placeholder that records the comparison request.
    Actual trial execution would require integration with the simulation runner.
    """
    # Verify task exists
    task = session.query(DualControlTaskModel).filter(
        DualControlTaskModel.task_id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Dual-control task '{task_id}' not found")

    # For now, create a placeholder comparison
    # In a full implementation, this would run actual trials
    comparison = SoloDualComparisonModel(
        id=str(uuid.uuid4()),
        task_id=task_id,
        solo_trials=request.num_trials,
        solo_successes=0,  # Would be computed from actual runs
        solo_pass_1=0.0,
        solo_avg_steps=0.0,
        dual_trials=request.num_trials,
        dual_successes=0,
        dual_pass_1=0.0,
        dual_avg_steps=0.0,
        performance_drop=0.0,
        step_increase=0.0,
    )

    session.add(comparison)
    session.commit()
    session.refresh(comparison)

    return RunComparisonResponse(
        comparison=SoloDualComparisonSchema(**comparison.to_dict()),
        insight="Comparison initialized. Run trials to compute actual metrics.",
    )


