"""Tests for trait vector system."""

import pytest
from agentworld.personas.traits import TraitVector


class TestTraitVector:
    """Tests for TraitVector class."""

    def test_creation_defaults(self):
        """Test creation with default values."""
        traits = TraitVector()
        assert traits.openness == 0.5
        assert traits.conscientiousness == 0.5
        assert traits.extraversion == 0.5
        assert traits.agreeableness == 0.5
        assert traits.neuroticism == 0.5

    def test_creation_with_values(self):
        """Test creation with custom values."""
        traits = TraitVector(
            openness=0.9,
            conscientiousness=0.3,
            extraversion=0.7,
            agreeableness=0.6,
            neuroticism=0.2
        )
        assert traits.openness == 0.9
        assert traits.conscientiousness == 0.3
        assert traits.extraversion == 0.7
        assert traits.agreeableness == 0.6
        assert traits.neuroticism == 0.2

    def test_validation_rejects_high_values(self):
        """Test that values above 1.0 raise ValidationError."""
        from agentworld.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            TraitVector(openness=1.5)

    def test_validation_rejects_low_values(self):
        """Test that values below 0.0 raise ValidationError."""
        from agentworld.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            TraitVector(openness=-0.5)

    def test_custom_traits(self):
        """Test adding custom traits."""
        traits = TraitVector(custom_traits={"creativity": 0.8, "empathy": 0.9})
        assert traits.custom_traits["creativity"] == 0.8
        assert traits.custom_traits["empathy"] == 0.9

    def test_to_dict(self):
        """Test serialization to dictionary."""
        traits = TraitVector(openness=0.7, conscientiousness=0.6)
        data = traits.to_dict()

        assert isinstance(data, dict)
        assert data["openness"] == 0.7
        assert data["conscientiousness"] == 0.6
        assert "extraversion" in data
        assert "agreeableness" in data
        assert "neuroticism" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "openness": 0.8,
            "conscientiousness": 0.4,
            "extraversion": 0.6,
            "agreeableness": 0.5,
            "neuroticism": 0.3,
        }
        traits = TraitVector.from_dict(data)

        assert traits.openness == 0.8
        assert traits.conscientiousness == 0.4
        assert traits.extraversion == 0.6

    def test_from_dict_with_custom_traits(self):
        """Test deserialization with custom traits.

        Note: from_dict treats all non-Big-Five keys as custom traits.
        """
        data = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
            "humor": 0.9  # Non-Big-Five key becomes custom trait
        }
        traits = TraitVector.from_dict(data)

        assert traits.custom_traits.get("humor") == 0.9

    def test_roundtrip_serialization(self):
        """Test to_dict -> from_dict roundtrip."""
        original = TraitVector(
            openness=0.8,
            conscientiousness=0.3,
            extraversion=0.9,
            agreeableness=0.4,
            neuroticism=0.1,
            custom_traits={"leadership": 0.7}
        )
        data = original.to_dict()
        restored = TraitVector.from_dict(data)

        assert restored.openness == original.openness
        assert restored.conscientiousness == original.conscientiousness
        assert restored.extraversion == original.extraversion
        assert restored.agreeableness == original.agreeableness
        assert restored.neuroticism == original.neuroticism

    def test_get_trait_level(self):
        """Test getting trait level descriptions."""
        high_openness = TraitVector(openness=0.9)
        low_openness = TraitVector(openness=0.1)

        high_level = high_openness.get_trait_level("openness")
        low_level = low_openness.get_trait_level("openness")

        # Should return different levels for high vs low
        assert high_level == "high"
        assert low_level == "low"

    def test_to_prompt_description(self):
        """Test generating personality description."""
        traits = TraitVector(
            openness=0.9,
            conscientiousness=0.2,
            extraversion=0.8,
            agreeableness=0.5,
            neuroticism=0.3
        )
        description = traits.to_prompt_description()

        assert isinstance(description, str)
        assert len(description) > 0
