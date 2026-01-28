"""Trait-aware prompt generation."""

from agentworld.personas.traits import TraitVector, TRAIT_DESCRIPTORS


def generate_personality_prompt(traits: TraitVector, name: str = "Agent") -> str:
    """Generate a personality description for use in system prompts.

    Args:
        traits: TraitVector defining the personality
        name: Name of the agent

    Returns:
        Formatted personality prompt section
    """
    lines = [f"You are {name}. Your personality is characterized by:"]

    for trait_name, value in traits.big_five.items():
        info = TRAIT_DESCRIPTORS[trait_name]
        level = traits.get_trait_level(trait_name)

        if level == "high":
            lines.append(f"- {info['name']}: You are {info['high']}")
        elif level == "low":
            lines.append(f"- {info['name']}: You are {info['low']}")
        else:
            lines.append(f"- {info['name']}: You have a balanced approach")

    # Add custom traits
    for trait_name, value in traits.custom_traits.items():
        formatted_name = trait_name.replace("_", " ").title()
        level = traits.get_trait_level(trait_name)
        if level == "high":
            lines.append(f"- {formatted_name}: Very high")
        elif level == "low":
            lines.append(f"- {formatted_name}: Low")

    return "\n".join(lines)


def generate_response_guidance(traits: TraitVector) -> str:
    """Generate response style guidance based on traits.

    Args:
        traits: TraitVector defining the personality

    Returns:
        Guidance for how the agent should respond
    """
    guidance = []

    # Extraversion affects verbosity
    if traits.extraversion > 0.7:
        guidance.append("Be expressive and engaging in your responses.")
    elif traits.extraversion < 0.3:
        guidance.append("Be concise and thoughtful. You prefer listening over talking.")

    # Agreeableness affects tone
    if traits.agreeableness > 0.7:
        guidance.append("Be warm, supportive, and look for common ground.")
    elif traits.agreeableness < 0.3:
        guidance.append("Don't hesitate to disagree or challenge ideas directly.")

    # Openness affects creativity
    if traits.openness > 0.7:
        guidance.append("Feel free to explore creative or unconventional ideas.")
    elif traits.openness < 0.3:
        guidance.append("Focus on practical, proven approaches.")

    # Conscientiousness affects structure
    if traits.conscientiousness > 0.7:
        guidance.append("Be thorough and well-organized in your responses.")
    elif traits.conscientiousness < 0.3:
        guidance.append("Don't worry too much about perfect structure. Be natural.")

    # Neuroticism affects emotional expression
    if traits.neuroticism > 0.7:
        guidance.append("You may express concern or caution about potential issues.")
    elif traits.neuroticism < 0.3:
        guidance.append("Stay calm and confident, even when discussing challenges.")

    if not guidance:
        return "Respond naturally and authentically."

    return " ".join(guidance)


def generate_system_prompt(
    traits: TraitVector,
    name: str,
    background: str = "",
    additional_instructions: str = "",
    observable_state: dict[str, any] | None = None,
    state_constrained_mode: bool = False,
) -> str:
    """Generate a complete system prompt for an agent.

    Args:
        traits: TraitVector defining the personality
        name: Name of the agent
        background: Optional background/context for the agent
        additional_instructions: Optional additional instructions
        observable_state: Optional dictionary of state fields the agent can observe.
            Used for τ²-bench state-constrained user simulation where user agents
            can only report what they actually "see" on their device.
        state_constrained_mode: If True, adds strict constraints about only
            reporting observable state. Per τ²-bench requirements.

    Returns:
        Complete system prompt
    """
    sections = []

    # Personality section
    sections.append(generate_personality_prompt(traits, name))

    # Background if provided
    if background:
        sections.append(f"\nBackground:\n{background}")

    # Response guidance
    sections.append(f"\nResponse Style:\n{generate_response_guidance(traits)}")

    # Observable state section (τ²-bench state-constrained mode)
    if observable_state is not None:
        state_lines = ["\nYour Observable Device State:"]
        state_lines.append("(This is what you can currently see on your device/screen)")
        state_lines.append("---")
        for key, value in observable_state.items():
            # Format the value appropriately
            if isinstance(value, bool):
                display_value = "Yes" if value else "No"
            elif value is None:
                display_value = "(not shown)"
            else:
                display_value = str(value)
            state_lines.append(f"  • {key}: {display_value}")
        state_lines.append("---")

        if state_constrained_mode:
            state_lines.append("")
            state_lines.append("IMPORTANT STATE CONSTRAINTS:")
            state_lines.append("- You can ONLY report information shown in your observable state above.")
            state_lines.append("- You CANNOT know or guess information not displayed on your device.")
            state_lines.append("- If asked about something not in your observable state, say you cannot see it.")
            state_lines.append("- Do NOT hallucinate or invent device information.")

        sections.append("\n".join(state_lines))

    # Additional instructions
    if additional_instructions:
        sections.append(f"\nAdditional Instructions:\n{additional_instructions}")

    # General guidelines
    sections.append(
        "\nGeneral Guidelines:\n"
        "- Stay in character throughout the conversation\n"
        "- Be authentic to your personality traits\n"
        "- Engage naturally with other participants\n"
        "- Express your genuine opinions and perspectives"
    )

    return "\n".join(sections)
