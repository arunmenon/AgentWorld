"""App definition API endpoints per ADR-018.

CRUD endpoints for managing app definitions stored in the database.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.apps.definition import AppDefinition, AppState
from agentworld.apps.dynamic import DynamicApp
from agentworld.api.schemas.app_definitions import (
    CreateAppDefinitionRequest,
    UpdateAppDefinitionRequest,
    AppDefinitionResponse,
    AppDefinitionListResponse,
    AppDefinitionVersionResponse,
    AppDefinitionVersionListResponse,
    TestActionRequest,
    TestActionResponse,
    DuplicateAppRequest,
)


router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


def definition_to_response(definition: dict) -> AppDefinitionResponse:
    """Convert definition dict to response."""
    # Merge stored fields with definition JSON
    full_def = definition.get("definition", {})

    return AppDefinitionResponse(
        id=definition["id"],
        app_id=definition["app_id"],
        name=definition["name"],
        description=definition.get("description") or "",
        category=definition["category"],
        icon=definition.get("icon") or "",
        version=definition.get("version", 1),
        is_builtin=bool(definition.get("is_builtin", 0)),
        is_active=bool(definition.get("is_active", 1)),
        created_by=definition.get("created_by"),
        created_at=definition.get("created_at"),
        updated_at=definition.get("updated_at"),
        actions=full_def.get("actions", []),
        state_schema=full_def.get("state_schema", []),
        initial_config=full_def.get("initial_config", {}),
        config_schema=full_def.get("config_schema", []),
    )


# ==============================================================================
# CRUD Endpoints
# ==============================================================================


@router.get("/app-definitions", response_model=AppDefinitionListResponse)
async def list_app_definitions(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    is_builtin: Optional[bool] = Query(None, description="Filter by builtin status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List all app definitions.

    Supports filtering by category and searching by name/description.
    """
    repo = get_repo()

    offset = (page - 1) * per_page
    definitions = repo.list_app_definitions(
        category=category,
        search=search,
        is_builtin=is_builtin,
        limit=per_page,
        offset=offset,
    )

    responses = [definition_to_response(d) for d in definitions]
    total = repo.count_app_definitions(category=category, is_builtin=is_builtin)

    return AppDefinitionListResponse(definitions=responses, total=total)


@router.post("/app-definitions", response_model=AppDefinitionResponse, status_code=201)
async def create_app_definition(request: CreateAppDefinitionRequest):
    """Create a new app definition.

    The app_id must be unique and follow snake_case format.
    """
    repo = get_repo()

    # Check for duplicate app_id
    existing = repo.get_app_definition_by_app_id(request.app_id)
    if existing:
        raise HTTPException(status_code=409, detail={
            "code": "APP_ID_EXISTS",
            "message": f"An app with ID '{request.app_id}' already exists",
        })

    # Validate the definition by parsing it
    try:
        definition_dict = {
            "app_id": request.app_id,
            "name": request.name,
            "description": request.description,
            "category": request.category,
            "icon": request.icon,
            "actions": [a.model_dump() for a in request.actions],
            "state_schema": [s.model_dump() for s in request.state_schema],
            "initial_config": request.initial_config,
            "config_schema": [c.model_dump() for c in request.config_schema],
        }
        # This validates the structure
        AppDefinition.from_dict(definition_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_DEFINITION",
            "message": f"Invalid app definition: {str(e)}",
        })

    # Create the record
    definition_id = str(uuid.uuid4())
    definition_data = {
        "id": definition_id,
        "app_id": request.app_id,
        "name": request.name,
        "description": request.description,
        "category": request.category,
        "icon": request.icon,
        "version": 1,
        "definition": definition_dict,
        "is_builtin": False,
        "is_active": True,
    }

    repo.save_app_definition(definition_data)

    # Save initial version
    repo.save_app_definition_version(definition_id, 1, definition_dict)

    # Retrieve and return
    saved = repo.get_app_definition(definition_id)
    return definition_to_response(saved)


@router.get("/app-definitions/{definition_id}", response_model=AppDefinitionResponse)
async def get_app_definition(definition_id: str):
    """Get an app definition by ID or app_id."""
    repo = get_repo()

    # Try by ID first
    definition = repo.get_app_definition(definition_id)

    # Try by app_id if not found
    if not definition:
        definition = repo.get_app_definition_by_app_id(definition_id)

    if not definition:
        raise HTTPException(status_code=404, detail={
            "code": "DEFINITION_NOT_FOUND",
            "message": f"App definition '{definition_id}' not found",
        })

    return definition_to_response(definition)


@router.patch("/app-definitions/{definition_id}", response_model=AppDefinitionResponse)
async def update_app_definition(definition_id: str, request: UpdateAppDefinitionRequest):
    """Update an app definition.

    Note: app_id cannot be changed after creation.
    """
    repo = get_repo()

    # Get existing definition
    definition = repo.get_app_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail={
            "code": "DEFINITION_NOT_FOUND",
            "message": f"App definition '{definition_id}' not found",
        })

    # Check if it's a built-in app
    if definition.get("is_builtin"):
        raise HTTPException(status_code=403, detail={
            "code": "BUILTIN_READONLY",
            "message": "Built-in app definitions cannot be modified",
        })

    # Build updates
    updates = {}
    full_def = dict(definition.get("definition", {}))

    if request.name is not None:
        updates["name"] = request.name
        full_def["name"] = request.name

    if request.description is not None:
        updates["description"] = request.description
        full_def["description"] = request.description

    if request.category is not None:
        updates["category"] = request.category
        full_def["category"] = request.category

    if request.icon is not None:
        updates["icon"] = request.icon
        full_def["icon"] = request.icon

    if request.actions is not None:
        full_def["actions"] = [a.model_dump() for a in request.actions]

    if request.state_schema is not None:
        full_def["state_schema"] = [s.model_dump() for s in request.state_schema]

    if request.initial_config is not None:
        full_def["initial_config"] = request.initial_config

    if request.config_schema is not None:
        full_def["config_schema"] = [c.model_dump() for c in request.config_schema]

    # Validate updated definition
    try:
        AppDefinition.from_dict(full_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_DEFINITION",
            "message": f"Invalid app definition: {str(e)}",
        })

    # Increment version
    new_version = definition.get("version", 1) + 1
    updates["version"] = new_version
    updates["definition"] = full_def

    repo.update_app_definition(definition_id, updates)

    # Save version snapshot
    repo.save_app_definition_version(definition_id, new_version, full_def)

    # Return updated definition
    updated = repo.get_app_definition(definition_id)
    return definition_to_response(updated)


@router.delete("/app-definitions/{definition_id}")
async def delete_app_definition(definition_id: str):
    """Delete (soft-delete) an app definition.

    Built-in apps cannot be deleted.
    """
    repo = get_repo()

    definition = repo.get_app_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail={
            "code": "DEFINITION_NOT_FOUND",
            "message": f"App definition '{definition_id}' not found",
        })

    if definition.get("is_builtin"):
        raise HTTPException(status_code=403, detail={
            "code": "BUILTIN_READONLY",
            "message": "Built-in app definitions cannot be deleted",
        })

    repo.delete_app_definition(definition_id, hard_delete=False)

    return {"success": True, "message": f"App definition '{definition_id}' deleted"}


# ==============================================================================
# Version History
# ==============================================================================


@router.get(
    "/app-definitions/{definition_id}/versions",
    response_model=AppDefinitionVersionListResponse,
)
async def get_app_definition_versions(definition_id: str):
    """Get version history for an app definition."""
    repo = get_repo()

    definition = repo.get_app_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail={
            "code": "DEFINITION_NOT_FOUND",
            "message": f"App definition '{definition_id}' not found",
        })

    versions = repo.get_app_definition_versions(definition_id)

    responses = [
        AppDefinitionVersionResponse(
            id=v["id"],
            app_definition_id=v["app_definition_id"],
            version=v["version"],
            definition=v.get("definition", {}),
            created_at=v.get("created_at"),
        )
        for v in versions
    ]

    return AppDefinitionVersionListResponse(versions=responses, total=len(responses))


# ==============================================================================
# Duplicate
# ==============================================================================


@router.post(
    "/app-definitions/{definition_id}/duplicate",
    response_model=AppDefinitionResponse,
    status_code=201,
)
async def duplicate_app_definition(definition_id: str, request: DuplicateAppRequest):
    """Duplicate an app definition with a new ID and name."""
    repo = get_repo()

    # Get source definition
    source = repo.get_app_definition(definition_id)
    if not source:
        raise HTTPException(status_code=404, detail={
            "code": "DEFINITION_NOT_FOUND",
            "message": f"App definition '{definition_id}' not found",
        })

    # Check for duplicate app_id
    existing = repo.get_app_definition_by_app_id(request.new_app_id)
    if existing:
        raise HTTPException(status_code=409, detail={
            "code": "APP_ID_EXISTS",
            "message": f"An app with ID '{request.new_app_id}' already exists",
        })

    # Create new definition from source
    source_def = source.get("definition", {})
    new_def = dict(source_def)
    new_def["app_id"] = request.new_app_id
    new_def["name"] = request.new_name

    # Create the record
    new_id = str(uuid.uuid4())
    definition_data = {
        "id": new_id,
        "app_id": request.new_app_id,
        "name": request.new_name,
        "description": source.get("description"),
        "category": source["category"],
        "icon": source.get("icon"),
        "version": 1,
        "definition": new_def,
        "is_builtin": False,
        "is_active": True,
    }

    repo.save_app_definition(definition_data)

    # Save initial version
    repo.save_app_definition_version(new_id, 1, new_def)

    # Return new definition
    saved = repo.get_app_definition(new_id)
    return definition_to_response(saved)


# ==============================================================================
# Test Endpoint
# ==============================================================================


@router.post("/app-definitions/{definition_id}/test", response_model=TestActionResponse)
async def test_app_action(definition_id: str, request: TestActionRequest):
    """Test an action in an isolated sandbox.

    Executes the action with the given parameters without persisting any state.
    Returns the result along with state before/after for debugging.
    """
    repo = get_repo()

    # Get definition
    definition = repo.get_app_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail={
            "code": "DEFINITION_NOT_FOUND",
            "message": f"App definition '{definition_id}' not found",
        })

    # Parse definition and create dynamic app
    try:
        full_def = definition.get("definition", {})
        app_def = AppDefinition.from_dict(full_def)
        app = DynamicApp(app_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_DEFINITION",
            "message": f"Failed to load app definition: {str(e)}",
        })

    # Prepare initial state
    if request.state:
        state = AppState.from_dict(request.state)
    else:
        # Create default state with test agent
        state = AppState()
        # Initialize with default per-agent state from schema
        defaults = {}
        for field_def in app_def.state_schema:
            if field_def.per_agent:
                defaults[field_def.name] = field_def.default
        state.ensure_agent(request.agent_id, defaults)

    state_before = state.to_dict()

    # Execute action
    config = request.config or app_def.initial_config
    result, state_after, observations = await app.execute_stateless(
        agent_id=request.agent_id,
        action=request.action,
        params=request.params,
        state=state,
        config=config,
    )

    return TestActionResponse(
        success=result.success,
        data=result.data if result.success else None,
        error=result.error if not result.success else None,
        state_before=state_before,
        state_after=state_after.to_dict(),
        observations=[
            {
                "agent_id": obs.agent_id,
                "message": obs.message,
                "data": obs.data,
                "priority": obs.priority,
            }
            for obs in observations
        ],
    )
