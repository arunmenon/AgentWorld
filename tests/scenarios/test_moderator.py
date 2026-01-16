"""Tests for moderator agent creation."""

import pytest

from agentworld.scenarios.moderator import (
    ModeratorConfig,
    ModeratorRole,
    MODERATOR_TRAITS_BY_STYLE,
    MODERATOR_PROMPTS_BY_ROLE,
    STYLE_DESCRIPTIONS,
    create_moderator_agent,
    create_moderator_for_focus_group,
    create_moderator_for_interview,
    create_moderator_for_debate,
)
from agentworld.agents.agent import Agent


class TestModeratorRole:
    """Tests for ModeratorRole enum."""

    def test_roles_exist(self):
        """Test that all roles exist."""
        assert ModeratorRole.FACILITATOR.value == "facilitator"
        assert ModeratorRole.INTERVIEWER.value == "interviewer"
        assert ModeratorRole.OBSERVER.value == "observer"
        assert ModeratorRole.DEBATE_HOST.value == "debate_host"


class TestModeratorConfig:
    """Tests for ModeratorConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = ModeratorConfig()

        assert config.name == "Moderator"
        assert config.style == "friendly"
        assert config.role == ModeratorRole.FACILITATOR
        assert config.custom_instructions == ""

    def test_custom_values(self):
        """Test custom values."""
        config = ModeratorConfig(
            name="Sarah",
            style="formal",
            role=ModeratorRole.INTERVIEWER,
            custom_instructions="Focus on technical questions",
        )

        assert config.name == "Sarah"
        assert config.style == "formal"
        assert config.role == ModeratorRole.INTERVIEWER
        assert "technical" in config.custom_instructions

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ModeratorConfig(name="Test", style="probing")
        data = config.to_dict()

        assert data["name"] == "Test"
        assert data["style"] == "probing"
        assert data["role"] == "facilitator"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "Alex",
            "style": "formal",
            "role": "interviewer",
            "custom_instructions": "Be thorough",
        }
        config = ModeratorConfig.from_dict(data)

        assert config.name == "Alex"
        assert config.style == "formal"
        assert config.role == ModeratorRole.INTERVIEWER


class TestModeratorTraits:
    """Tests for moderator trait configurations."""

    def test_friendly_traits(self):
        """Test friendly style traits."""
        traits = MODERATOR_TRAITS_BY_STYLE["friendly"]

        assert traits.agreeableness >= 0.8  # Should be agreeable
        assert traits.neuroticism <= 0.3  # Should be calm

    def test_formal_traits(self):
        """Test formal style traits."""
        traits = MODERATOR_TRAITS_BY_STYLE["formal"]

        assert traits.conscientiousness >= 0.9  # Should be organized
        assert traits.extraversion <= 0.6  # More reserved

    def test_probing_traits(self):
        """Test probing style traits."""
        traits = MODERATOR_TRAITS_BY_STYLE["probing"]

        assert traits.openness >= 0.8  # Curious
        assert traits.extraversion >= 0.6  # Engaged


class TestModeratorPrompts:
    """Tests for moderator prompt templates."""

    def test_prompts_exist_for_all_roles(self):
        """Test that prompts exist for all roles."""
        for role in ModeratorRole:
            assert role in MODERATOR_PROMPTS_BY_ROLE
            prompt = MODERATOR_PROMPTS_BY_ROLE[role]
            assert "{name}" in prompt
            assert "{style_description}" in prompt

    def test_style_descriptions_exist(self):
        """Test that style descriptions exist."""
        assert "friendly" in STYLE_DESCRIPTIONS
        assert "formal" in STYLE_DESCRIPTIONS
        assert "probing" in STYLE_DESCRIPTIONS


class TestCreateModeratorAgent:
    """Tests for create_moderator_agent function."""

    def test_default_moderator(self):
        """Test creating moderator with defaults."""
        agent = create_moderator_agent()

        assert isinstance(agent, Agent)
        assert agent.name == "Moderator"

    def test_custom_moderator(self):
        """Test creating moderator with custom config."""
        config = ModeratorConfig(
            name="Sarah",
            style="friendly",
            role=ModeratorRole.FACILITATOR,
        )
        agent = create_moderator_agent(config)

        assert agent.name == "Sarah"
        assert "Sarah" in agent.system_prompt

    def test_moderator_traits_applied(self):
        """Test that traits are applied correctly."""
        config = ModeratorConfig(style="friendly")
        agent = create_moderator_agent(config)

        expected_traits = MODERATOR_TRAITS_BY_STYLE["friendly"]
        assert agent.traits.agreeableness == expected_traits.agreeableness

    def test_moderator_system_prompt(self):
        """Test that system prompt is generated."""
        config = ModeratorConfig(
            name="Test",
            role=ModeratorRole.FACILITATOR,
            custom_instructions="Focus on feedback",
        )
        agent = create_moderator_agent(config)

        assert "Test" in agent.system_prompt
        assert "Focus on feedback" in agent.system_prompt

    def test_simulation_id_passed(self):
        """Test that simulation ID is passed."""
        agent = create_moderator_agent(simulation_id="sim123")

        assert agent.simulation_id == "sim123"


class TestCreateModeratorForFocusGroup:
    """Tests for create_moderator_for_focus_group function."""

    def test_creates_facilitator(self):
        """Test that it creates a facilitator."""
        agent = create_moderator_for_focus_group()

        assert isinstance(agent, Agent)
        # Check system prompt contains focus group keywords
        assert any(word in agent.system_prompt.lower() for word in [
            "discussion", "participant", "question"
        ])

    def test_custom_name_and_style(self):
        """Test custom name and style."""
        agent = create_moderator_for_focus_group(
            name="Maria",
            style="probing",
        )

        assert agent.name == "Maria"
        expected_traits = MODERATOR_TRAITS_BY_STYLE["probing"]
        assert agent.traits.openness == expected_traits.openness


class TestCreateModeratorForInterview:
    """Tests for create_moderator_for_interview function."""

    def test_creates_interviewer(self):
        """Test that it creates an interviewer."""
        agent = create_moderator_for_interview()

        assert isinstance(agent, Agent)
        # Check system prompt contains interview keywords
        assert any(word in agent.system_prompt.lower() for word in [
            "interview", "question"
        ])

    def test_default_is_formal(self):
        """Test default style is formal."""
        agent = create_moderator_for_interview()

        expected_traits = MODERATOR_TRAITS_BY_STYLE["formal"]
        assert agent.traits.conscientiousness == expected_traits.conscientiousness


class TestCreateModeratorForDebate:
    """Tests for create_moderator_for_debate function."""

    def test_creates_debate_host(self):
        """Test that it creates a debate host."""
        agent = create_moderator_for_debate()

        assert isinstance(agent, Agent)
        # Check system prompt contains debate keywords
        assert any(word in agent.system_prompt.lower() for word in [
            "debate", "argument", "neutral"
        ])

    def test_custom_name(self):
        """Test custom name."""
        agent = create_moderator_for_debate(name="Anderson")

        assert agent.name == "Anderson"
