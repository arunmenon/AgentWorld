"""Serialization utilities for personas."""

import json
from typing import Any

from agentworld.personas.traits import TraitVector


def trait_vector_to_json(traits: TraitVector) -> str:
    """Serialize a TraitVector to JSON string.

    Args:
        traits: TraitVector to serialize

    Returns:
        JSON string
    """
    return json.dumps(traits.to_dict())


def trait_vector_from_json(json_str: str) -> TraitVector:
    """Deserialize a TraitVector from JSON string.

    Args:
        json_str: JSON string

    Returns:
        TraitVector instance
    """
    data = json.loads(json_str)
    return TraitVector.from_dict(data)


def persona_to_dict(
    name: str,
    traits: TraitVector,
    background: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Convert persona data to a dictionary.

    Args:
        name: Persona name
        traits: TraitVector
        background: Optional background text
        tags: Optional tags

    Returns:
        Dictionary representation
    """
    return {
        "name": name,
        "traits": traits.to_dict(),
        "background": background,
        "tags": tags or [],
    }


def persona_from_dict(data: dict[str, Any]) -> tuple[str, TraitVector, str, list[str]]:
    """Parse persona data from a dictionary.

    Args:
        data: Dictionary with persona data

    Returns:
        Tuple of (name, traits, background, tags)
    """
    name = data["name"]
    traits = TraitVector.from_dict(data.get("traits", {}))
    background = data.get("background", "")
    tags = data.get("tags", [])
    return name, traits, background, tags
