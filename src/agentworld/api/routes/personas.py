"""Persona API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.api.schemas.personas import (
    PersonaResponse,
    PersonaListResponse,
    CreatePersonaRequest,
    UpdatePersonaRequest,
    CollectionResponse,
    CollectionListResponse,
    CreateCollectionRequest,
    AddToCollectionRequest,
)


router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


def persona_to_response(persona: dict) -> PersonaResponse:
    """Convert persona dict to response."""
    return PersonaResponse(
        id=persona["id"],
        name=persona["name"],
        description=persona.get("description"),
        occupation=persona.get("occupation"),
        age=persona.get("age"),
        background=persona.get("background"),
        traits=persona.get("traits", {}),
        tags=persona.get("tags", []),
        usage_count=persona.get("usage_count", 0),
        created_at=persona.get("created_at"),
        updated_at=persona.get("updated_at"),
    )


def collection_to_response(collection: dict) -> CollectionResponse:
    """Convert collection dict to response."""
    return CollectionResponse(
        id=collection["id"],
        name=collection["name"],
        description=collection.get("description"),
        tags=collection.get("tags", []),
        member_count=collection.get("member_count", 0),
        created_at=collection.get("created_at"),
        updated_at=collection.get("updated_at"),
    )


# Persona endpoints

@router.get("/personas", response_model=PersonaListResponse)
async def list_personas(
    occupation: Optional[str] = Query(None, description="Filter by occupation"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """List personas in the library."""
    repo = get_repo()

    offset = (page - 1) * per_page
    personas = repo.list_personas(occupation=occupation, limit=per_page, offset=offset)

    responses = [persona_to_response(p) for p in personas]

    return PersonaListResponse(
        personas=responses,
        total=len(responses),
    )


@router.get("/personas/search", response_model=PersonaListResponse)
async def search_personas(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search personas by name, description, or occupation."""
    repo = get_repo()

    personas = repo.search_personas(q, limit=limit)
    responses = [persona_to_response(p) for p in personas]

    return PersonaListResponse(
        personas=responses,
        total=len(responses),
    )


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str):
    """Get a persona by ID."""
    repo = get_repo()

    persona = repo.get_persona(persona_id)
    if not persona:
        # Try by name
        persona = repo.get_persona_by_name(persona_id)

    if not persona:
        raise HTTPException(status_code=404, detail={
            "code": "PERSONA_NOT_FOUND",
            "message": f"Persona '{persona_id}' not found",
        })

    return persona_to_response(persona)


@router.post("/personas", response_model=PersonaResponse, status_code=201)
async def create_persona(request: CreatePersonaRequest):
    """Create a new persona."""
    repo = get_repo()

    # Check if name already exists
    existing = repo.get_persona_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail={
            "code": "PERSONA_EXISTS",
            "message": f"A persona named '{request.name}' already exists",
        })

    traits = {}
    if request.traits:
        traits = {
            "openness": request.traits.openness,
            "conscientiousness": request.traits.conscientiousness,
            "extraversion": request.traits.extraversion,
            "agreeableness": request.traits.agreeableness,
            "neuroticism": request.traits.neuroticism,
        }

    persona_data = {
        "id": str(uuid.uuid4()),
        "name": request.name,
        "description": request.description,
        "occupation": request.occupation,
        "age": request.age,
        "background": request.background,
        "traits": traits,
        "tags": request.tags,
    }

    repo.save_persona(persona_data)

    return persona_to_response(persona_data)


@router.patch("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(persona_id: str, request: UpdatePersonaRequest):
    """Update a persona."""
    repo = get_repo()

    persona = repo.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail={
            "code": "PERSONA_NOT_FOUND",
            "message": f"Persona '{persona_id}' not found",
        })

    # Build updated data
    updated_data = dict(persona)

    if request.name is not None:
        updated_data["name"] = request.name
    if request.description is not None:
        updated_data["description"] = request.description
    if request.occupation is not None:
        updated_data["occupation"] = request.occupation
    if request.age is not None:
        updated_data["age"] = request.age
    if request.background is not None:
        updated_data["background"] = request.background
    if request.tags is not None:
        updated_data["tags"] = request.tags
    if request.traits is not None:
        updated_data["traits"] = {
            "openness": request.traits.openness,
            "conscientiousness": request.traits.conscientiousness,
            "extraversion": request.traits.extraversion,
            "agreeableness": request.traits.agreeableness,
            "neuroticism": request.traits.neuroticism,
        }

    repo.save_persona(updated_data)

    return persona_to_response(updated_data)


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona."""
    repo = get_repo()

    if not repo.get_persona(persona_id):
        raise HTTPException(status_code=404, detail={
            "code": "PERSONA_NOT_FOUND",
            "message": f"Persona '{persona_id}' not found",
        })

    repo.delete_persona(persona_id)

    return {"success": True, "message": f"Persona '{persona_id}' deleted"}


# Collection endpoints

@router.get("/collections", response_model=CollectionListResponse)
async def list_collections(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """List persona collections."""
    repo = get_repo()

    offset = (page - 1) * per_page
    collections = repo.list_collections(limit=per_page, offset=offset)

    responses = [collection_to_response(c) for c in collections]

    return CollectionListResponse(
        collections=responses,
        total=len(responses),
    )


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: str):
    """Get a collection by ID."""
    repo = get_repo()

    collection = repo.get_collection(collection_id)
    if not collection:
        collection = repo.get_collection_by_name(collection_id)

    if not collection:
        raise HTTPException(status_code=404, detail={
            "code": "COLLECTION_NOT_FOUND",
            "message": f"Collection '{collection_id}' not found",
        })

    return collection_to_response(collection)


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection."""
    repo = get_repo()

    # Check if name already exists
    existing = repo.get_collection_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail={
            "code": "COLLECTION_EXISTS",
            "message": f"A collection named '{request.name}' already exists",
        })

    collection_data = {
        "id": str(uuid.uuid4()),
        "name": request.name,
        "description": request.description,
        "tags": request.tags,
    }

    repo.save_collection(collection_data)

    return collection_to_response(collection_data)


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str):
    """Delete a collection."""
    repo = get_repo()

    if not repo.get_collection(collection_id):
        raise HTTPException(status_code=404, detail={
            "code": "COLLECTION_NOT_FOUND",
            "message": f"Collection '{collection_id}' not found",
        })

    repo.delete_collection(collection_id)

    return {"success": True, "message": f"Collection '{collection_id}' deleted"}


@router.get("/collections/{collection_id}/personas", response_model=PersonaListResponse)
async def list_collection_personas(collection_id: str):
    """List personas in a collection."""
    repo = get_repo()

    collection = repo.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail={
            "code": "COLLECTION_NOT_FOUND",
            "message": f"Collection '{collection_id}' not found",
        })

    personas = repo.get_personas_in_collection(collection_id)
    responses = [persona_to_response(p) for p in personas]

    return PersonaListResponse(
        personas=responses,
        total=len(responses),
    )


@router.post("/collections/{collection_id}/personas")
async def add_persona_to_collection(collection_id: str, request: AddToCollectionRequest):
    """Add a persona to a collection."""
    repo = get_repo()

    collection = repo.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail={
            "code": "COLLECTION_NOT_FOUND",
            "message": f"Collection '{collection_id}' not found",
        })

    persona = repo.get_persona(request.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail={
            "code": "PERSONA_NOT_FOUND",
            "message": f"Persona '{request.persona_id}' not found",
        })

    repo.add_persona_to_collection(collection_id, request.persona_id)

    return {
        "success": True,
        "message": f"Persona '{persona['name']}' added to collection '{collection['name']}'",
    }


@router.delete("/collections/{collection_id}/personas/{persona_id}")
async def remove_persona_from_collection(collection_id: str, persona_id: str):
    """Remove a persona from a collection."""
    repo = get_repo()

    collection = repo.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail={
            "code": "COLLECTION_NOT_FOUND",
            "message": f"Collection '{collection_id}' not found",
        })

    if not repo.remove_persona_from_collection(collection_id, persona_id):
        raise HTTPException(status_code=404, detail={
            "code": "NOT_IN_COLLECTION",
            "message": f"Persona '{persona_id}' not in collection '{collection_id}'",
        })

    return {"success": True, "message": "Persona removed from collection"}
