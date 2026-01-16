"""Tests for persona serialization utilities."""

import json
import pytest
from agentworld.personas.serialization import (
    trait_vector_to_json,
    trait_vector_from_json,
    persona_to_dict,
    persona_from_dict,
)
from agentworld.personas.traits import TraitVector


class TestTraitVectorSerialization:
    """Tests for TraitVector JSON serialization."""

    def test_to_json_basic(self):
        """Test converting TraitVector to JSON."""
        traits = TraitVector(openness=0.8, conscientiousness=0.6)
        json_str = trait_vector_to_json(traits)

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["openness"] == 0.8
        assert data["conscientiousness"] == 0.6

    def test_from_json_basic(self):
        """Test creating TraitVector from JSON."""
        json_str = '{"openness": 0.9, "conscientiousness": 0.3, "extraversion": 0.7, "agreeableness": 0.5, "neuroticism": 0.4}'
        traits = trait_vector_from_json(json_str)

        assert traits.openness == 0.9
        assert traits.conscientiousness == 0.3
        assert traits.extraversion == 0.7

    def test_roundtrip(self):
        """Test JSON serialization roundtrip."""
        original = TraitVector(
            openness=0.8,
            conscientiousness=0.3,
            extraversion=0.9,
            agreeableness=0.4,
            neuroticism=0.2,
        )
        json_str = trait_vector_to_json(original)
        restored = trait_vector_from_json(json_str)

        assert restored.openness == original.openness
        assert restored.conscientiousness == original.conscientiousness
        assert restored.extraversion == original.extraversion
        assert restored.agreeableness == original.agreeableness
        assert restored.neuroticism == original.neuroticism

    def test_with_custom_traits(self):
        """Test serialization with custom traits.

        Note: to_dict() flattens custom traits into the main dict.
        """
        original = TraitVector(
            openness=0.7,
            custom_traits={"creativity": 0.9, "humor": 0.8}
        )
        json_str = trait_vector_to_json(original)
        data = json.loads(json_str)

        # Custom traits are flattened (not nested)
        assert data["creativity"] == 0.9
        assert data["humor"] == 0.8


class TestPersonaSerialization:
    """Tests for persona dict serialization."""

    def test_persona_to_dict_basic(self):
        """Test converting persona to dictionary."""
        traits = TraitVector(openness=0.8)
        result = persona_to_dict(
            name="Alice",
            traits=traits,
            background="A software engineer",
            tags=["tech", "introvert"]
        )

        assert result["name"] == "Alice"
        assert result["background"] == "A software engineer"
        assert result["tags"] == ["tech", "introvert"]
        assert result["traits"]["openness"] == 0.8

    def test_persona_to_dict_defaults(self):
        """Test persona_to_dict with default values."""
        traits = TraitVector()
        result = persona_to_dict(name="Bob", traits=traits)

        assert result["name"] == "Bob"
        assert result["background"] == ""
        assert result["tags"] == []

    def test_persona_from_dict_basic(self):
        """Test creating persona from dictionary."""
        data = {
            "name": "Charlie",
            "traits": {"openness": 0.9, "conscientiousness": 0.4},
            "background": "An artist",
            "tags": ["creative"],
        }
        name, traits, background, tags = persona_from_dict(data)

        assert name == "Charlie"
        assert traits.openness == 0.9
        assert background == "An artist"
        assert tags == ["creative"]

    def test_persona_from_dict_missing_fields(self):
        """Test persona_from_dict with missing optional fields."""
        data = {"name": "Dana"}
        name, traits, background, tags = persona_from_dict(data)

        assert name == "Dana"
        assert traits.openness == 0.5  # default
        assert background == ""
        assert tags == []

    def test_roundtrip_persona(self):
        """Test persona serialization roundtrip."""
        original_traits = TraitVector(openness=0.8, extraversion=0.3)
        original_data = persona_to_dict(
            name="Eve",
            traits=original_traits,
            background="A researcher",
            tags=["science", "curious"]
        )

        name, traits, background, tags = persona_from_dict(original_data)

        assert name == "Eve"
        assert traits.openness == 0.8
        assert traits.extraversion == 0.3
        assert background == "A researcher"
        assert tags == ["science", "curious"]
