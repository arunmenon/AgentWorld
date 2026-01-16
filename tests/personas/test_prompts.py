"""Tests for persona prompt generation."""

import pytest
from agentworld.personas.prompts import (
    generate_system_prompt,
    generate_personality_prompt,
    generate_response_guidance,
)
from agentworld.personas.traits import TraitVector


class TestGenerateSystemPrompt:
    """Tests for generate_system_prompt function."""

    @pytest.fixture
    def basic_traits(self):
        """Create basic trait vector."""
        return TraitVector()

    @pytest.fixture
    def extreme_traits(self):
        """Create extreme trait vector."""
        return TraitVector(
            openness=0.95,
            conscientiousness=0.1,
            extraversion=0.9,
            agreeableness=0.3,
            neuroticism=0.8
        )

    def test_generates_string(self, basic_traits):
        """Test that function returns a string."""
        prompt = generate_system_prompt(basic_traits, name="Alice")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_includes_name(self, basic_traits):
        """Test that prompt includes agent name."""
        prompt = generate_system_prompt(basic_traits, name="TestAgent")
        assert "TestAgent" in prompt

    def test_includes_background(self, basic_traits):
        """Test that prompt includes background."""
        background = "A software engineer with 10 years of experience."
        prompt = generate_system_prompt(
            basic_traits,
            name="Bob",
            background=background
        )
        assert background in prompt or "software engineer" in prompt.lower()

    def test_different_traits_different_prompts(self, basic_traits, extreme_traits):
        """Test that different traits produce different prompts."""
        prompt1 = generate_system_prompt(basic_traits, name="Agent1")
        prompt2 = generate_system_prompt(extreme_traits, name="Agent1")

        # Prompts should differ based on traits
        assert prompt1 != prompt2

    def test_high_openness_mentioned(self):
        """Test that high openness is reflected in prompt."""
        high_openness = TraitVector(openness=0.95)
        prompt = generate_system_prompt(high_openness, name="Creative")

        # Should mention creativity, curiosity, or similar
        prompt_lower = prompt.lower()
        assert any(word in prompt_lower for word in [
            "creative", "curious", "imaginative", "open", "innovative", "unconventional"
        ])

    def test_low_openness_mentioned(self):
        """Test that low openness is reflected in prompt."""
        low_openness = TraitVector(openness=0.05)
        prompt = generate_system_prompt(low_openness, name="Traditional")

        prompt_lower = prompt.lower()
        assert any(word in prompt_lower for word in [
            "traditional", "practical", "conventional", "proven"
        ])


class TestGeneratePersonalityPrompt:
    """Tests for generate_personality_prompt function."""

    def test_includes_name(self):
        """Test that personality prompt includes name."""
        traits = TraitVector()
        prompt = generate_personality_prompt(traits, name="Alice")
        assert "Alice" in prompt

    def test_includes_trait_descriptions(self):
        """Test that prompt includes trait descriptions."""
        traits = TraitVector(extraversion=0.9)
        prompt = generate_personality_prompt(traits, name="Bob")

        # Should have some personality description
        assert len(prompt) > 20


class TestGenerateResponseGuidance:
    """Tests for generate_response_guidance function."""

    def test_high_extraversion_guidance(self):
        """Test guidance for high extraversion."""
        traits = TraitVector(extraversion=0.9)
        guidance = generate_response_guidance(traits)

        assert len(guidance) > 0
        guidance_lower = guidance.lower()
        assert any(word in guidance_lower for word in ["expressive", "engaging"])

    def test_low_extraversion_guidance(self):
        """Test guidance for low extraversion."""
        traits = TraitVector(extraversion=0.1)
        guidance = generate_response_guidance(traits)

        guidance_lower = guidance.lower()
        assert any(word in guidance_lower for word in ["concise", "listening"])

    def test_high_agreeableness_guidance(self):
        """Test guidance for high agreeableness."""
        traits = TraitVector(agreeableness=0.9)
        guidance = generate_response_guidance(traits)

        guidance_lower = guidance.lower()
        assert any(word in guidance_lower for word in ["warm", "supportive", "common ground"])

    def test_neutral_traits_guidance(self):
        """Test guidance for neutral traits."""
        traits = TraitVector()  # All 0.5
        guidance = generate_response_guidance(traits)

        # Should still return something
        assert len(guidance) > 0
