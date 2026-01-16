"""Moderator agent for facilitated scenarios.

The moderator in focus group scenarios is a real agent with its own
persona, not a system role. This ensures consistent behavior and
enables moderator-participant interactions through the topology.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agentworld.personas.traits import TraitVector
from agentworld.agents.agent import Agent


class ModeratorRole(str, Enum):
    """Roles a moderator can play."""

    FACILITATOR = "facilitator"  # Guides discussion, asks questions
    INTERVIEWER = "interviewer"  # One-on-one interviews
    OBSERVER = "observer"  # Watches but doesn't participate
    DEBATE_HOST = "debate_host"  # Manages debates


@dataclass
class ModeratorConfig:
    """Configuration for moderator agent."""

    name: str = "Moderator"
    style: str = "friendly"  # friendly, formal, probing
    role: ModeratorRole = ModeratorRole.FACILITATOR
    custom_instructions: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "style": self.style,
            "role": self.role.value,
            "custom_instructions": self.custom_instructions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModeratorConfig":
        """Create from dictionary."""
        role = data.get("role")
        if isinstance(role, str):
            role = ModeratorRole(role)
        else:
            role = ModeratorRole.FACILITATOR

        return cls(
            name=data.get("name", "Moderator"),
            style=data.get("style", "friendly"),
            role=role,
            custom_instructions=data.get("custom_instructions", ""),
        )


# Style-specific trait configurations
MODERATOR_TRAITS_BY_STYLE = {
    "friendly": TraitVector(
        openness=0.7,
        conscientiousness=0.8,
        extraversion=0.6,
        agreeableness=0.85,
        neuroticism=0.2,
    ),
    "formal": TraitVector(
        openness=0.6,
        conscientiousness=0.95,
        extraversion=0.5,
        agreeableness=0.7,
        neuroticism=0.15,
    ),
    "probing": TraitVector(
        openness=0.85,
        conscientiousness=0.8,
        extraversion=0.7,
        agreeableness=0.6,
        neuroticism=0.2,
    ),
}

# Role-specific system prompt templates
MODERATOR_PROMPTS_BY_ROLE = {
    ModeratorRole.FACILITATOR: """You are {name}, a skilled focus group moderator.

Your responsibilities:
- Guide discussions in a structured way
- Ask probing follow-up questions to get deeper insights
- Ensure all participants have a chance to speak
- Keep the conversation on topic
- Remain neutral and avoid expressing your own opinions
- Summarize key points when transitioning between topics

Style: {style_description}

{custom_instructions}""",
    ModeratorRole.INTERVIEWER: """You are {name}, a professional interviewer.

Your responsibilities:
- Ask clear, open-ended questions
- Listen actively and ask follow-up questions
- Build rapport while maintaining professionalism
- Explore interesting responses in more depth
- Keep track of time and cover all planned topics
- Remain neutral and non-judgmental

Style: {style_description}

{custom_instructions}""",
    ModeratorRole.OBSERVER: """You are {name}, an observer in this discussion.

Your responsibilities:
- Watch and note interesting patterns
- Only speak when directly addressed
- Provide brief acknowledgments to keep discussion flowing
- Do not express opinions or guide the conversation

Style: {style_description}

{custom_instructions}""",
    ModeratorRole.DEBATE_HOST: """You are {name}, a debate moderator.

Your responsibilities:
- Introduce debate topics clearly
- Ensure fair time allocation between sides
- Ask clarifying questions
- Enforce debate rules and decorum
- Summarize arguments from both sides
- Remain strictly neutral

Style: {style_description}

{custom_instructions}""",
}

STYLE_DESCRIPTIONS = {
    "friendly": "Be warm, approachable, and encouraging. Use a conversational tone.",
    "formal": "Maintain professional distance. Use clear, precise language.",
    "probing": "Ask challenging follow-up questions. Push for specifics and examples.",
}


def create_moderator_agent(
    config: ModeratorConfig | None = None,
    simulation_id: str | None = None,
) -> Agent:
    """Create a moderator agent for scenarios.

    The moderator is a full Agent with:
    - Neutral persona optimized for facilitation
    - Access to questions/topics
    - Typically hub position in topology

    Args:
        config: Moderator configuration
        simulation_id: Optional simulation ID

    Returns:
        Configured Agent instance
    """
    config = config or ModeratorConfig()

    # Get traits for style
    traits = MODERATOR_TRAITS_BY_STYLE.get(
        config.style,
        MODERATOR_TRAITS_BY_STYLE["friendly"],
    )

    # Get system prompt template
    prompt_template = MODERATOR_PROMPTS_BY_ROLE.get(
        config.role,
        MODERATOR_PROMPTS_BY_ROLE[ModeratorRole.FACILITATOR],
    )

    # Format system prompt
    system_prompt = prompt_template.format(
        name=config.name,
        style_description=STYLE_DESCRIPTIONS.get(config.style, ""),
        custom_instructions=config.custom_instructions,
    )

    # Create agent
    agent = Agent(
        name=config.name,
        traits=traits,
        background=f"{config.role.value.replace('_', ' ').title()} ({config.style} style)",
        system_prompt=system_prompt,
        simulation_id=simulation_id,
    )

    return agent


def create_moderator_for_focus_group(
    name: str = "Sarah",
    style: str = "friendly",
    custom_instructions: str = "",
    simulation_id: str | None = None,
) -> Agent:
    """Create a moderator specifically for focus groups.

    Args:
        name: Moderator name
        style: Moderation style (friendly, formal, probing)
        custom_instructions: Additional instructions
        simulation_id: Optional simulation ID

    Returns:
        Configured moderator Agent
    """
    config = ModeratorConfig(
        name=name,
        style=style,
        role=ModeratorRole.FACILITATOR,
        custom_instructions=custom_instructions,
    )
    return create_moderator_agent(config, simulation_id)


def create_moderator_for_interview(
    name: str = "Dr. Chen",
    style: str = "formal",
    custom_instructions: str = "",
    simulation_id: str | None = None,
) -> Agent:
    """Create a moderator specifically for interviews.

    Args:
        name: Interviewer name
        style: Interview style (friendly, formal, probing)
        custom_instructions: Additional instructions
        simulation_id: Optional simulation ID

    Returns:
        Configured interviewer Agent
    """
    config = ModeratorConfig(
        name=name,
        style=style,
        role=ModeratorRole.INTERVIEWER,
        custom_instructions=custom_instructions,
    )
    return create_moderator_agent(config, simulation_id)


def create_moderator_for_debate(
    name: str = "Host",
    custom_instructions: str = "",
    simulation_id: str | None = None,
) -> Agent:
    """Create a moderator specifically for debates.

    Args:
        name: Host name
        custom_instructions: Additional instructions
        simulation_id: Optional simulation ID

    Returns:
        Configured debate host Agent
    """
    config = ModeratorConfig(
        name=name,
        style="formal",
        role=ModeratorRole.DEBATE_HOST,
        custom_instructions=custom_instructions,
    )
    return create_moderator_agent(config, simulation_id)
