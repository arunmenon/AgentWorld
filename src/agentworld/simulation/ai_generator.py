"""AI-assisted simulation generation from natural language descriptions.

Uses LLM to generate simulation configurations from natural language.
"""

import json
import logging
import re
from typing import Any

from agentworld.llm.provider import LLMProvider, get_provider

logger = logging.getLogger(__name__)

SIMULATION_GENERATOR_SYSTEM_PROMPT = """You generate simulation configurations for multi-agent conversations.

Given a natural language description, generate a complete simulation configuration as JSON.

## Output Schema

{
  "name": "Short simulation name",
  "description": "Brief description",
  "initial_prompt": "What the agents should discuss/do",
  "steps": 10,

  "agents": [
    {
      "name": "Agent Name",
      "role": "peer|service_agent|customer",
      "background": "Agent's background and expertise",
      "traits": {
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.3
      }
    }
  ],

  "apps": []
}

## Big Five Personality Traits

Each trait is a value from 0.0 to 1.0:

- **openness**: Low (0.0) = practical, conventional; High (1.0) = creative, curious
- **conscientiousness**: Low (0.0) = flexible, spontaneous; High (1.0) = organized, disciplined
- **extraversion**: Low (0.0) = reserved, introspective; High (1.0) = outgoing, energetic
- **agreeableness**: Low (0.0) = challenging, skeptical; High (1.0) = cooperative, trusting
- **neuroticism**: Low (0.0) = calm, emotionally stable; High (1.0) = sensitive, reactive

## Agent Roles

- **peer**: Equal participant in conversation (default for most scenarios)
- **service_agent**: Service provider, support agent, or expert
- **customer**: Person seeking help or service

## Guidelines

1. Create distinct, realistic agent personalities
2. Use Big Five traits appropriately for the role/background
3. Background should inform how agent participates
4. initial_prompt should naturally start the conversation
5. Match number of agents to the scenario described
6. Typical scenarios: 2-5 agents
7. steps: Usually 10-20 for short discussions, 30+ for complex scenarios

## Examples

"Two friends discussing a movie" → 2 agents with peer roles, casual backgrounds
"Customer support call" → 2 agents (service_agent + customer)
"Board meeting with 4 executives" → 4 agents with professional backgrounds
"Panel discussion with moderator" → 3-5 agents, one with higher conscientiousness

Return ONLY valid JSON, no explanations or markdown code blocks."""


class AISimulationGenerator:
    """Generate simulation configs from natural language descriptions."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        """Initialize the generator.

        Args:
            llm_provider: Optional LLM provider instance. Uses default if not provided.
        """
        self.provider = llm_provider or get_provider()

    async def generate_simulation(
        self,
        description: str,
        num_agents_hint: int | None = None,
    ) -> dict[str, Any]:
        """Generate a simulation configuration from natural language.

        Args:
            description: Natural language description of the simulation
            num_agents_hint: Optional hint for number of agents

        Returns:
            Dict matching simulation configuration structure
        """
        prompt = self._build_prompt(description, num_agents_hint)

        response = await self.provider.complete(
            prompt=prompt,
            model="openai/gpt-4o",  # Use GPT-4o for high-quality generation
            temperature=0.7,  # Some creativity for personalities
            max_tokens=2000,
            system_prompt=SIMULATION_GENERATOR_SYSTEM_PROMPT,
        )

        # Parse and validate JSON response
        config = self._parse_response(response.content)

        # Post-process to ensure required fields
        config = self._ensure_required_fields(config, description)

        return config

    def _build_prompt(self, description: str, num_agents_hint: int | None) -> str:
        """Build the prompt for simulation generation."""
        agent_context = ""
        if num_agents_hint:
            agent_context = f"\nNumber of agents: {num_agents_hint}"

        return f"""Generate a simulation configuration for this scenario:

{description}
{agent_context}

Return a JSON object with:
1. A descriptive name
2. An initial_prompt that starts the conversation naturally
3. Agents with distinct personalities and appropriate roles
4. Realistic Big Five trait values for each agent"""

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response.

        Handles markdown code blocks and extracts valid JSON.
        """
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            # Remove opening fence (with optional language identifier)
            content = re.sub(r"^```(?:json)?\s*\n?", "", content)
            # Remove closing fence
            content = re.sub(r"\n?```\s*$", "", content)

        # Try to find JSON object in content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from content
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        logger.error(f"Failed to parse JSON from response: {content[:200]}...")
        raise ValueError("Failed to parse simulation config from LLM response")

    def _ensure_required_fields(
        self, config: dict[str, Any], description: str
    ) -> dict[str, Any]:
        """Ensure all required fields are present with defaults."""
        # Basic defaults
        if "name" not in config:
            # Generate name from first few words of description
            words = description.split()[:5]
            config["name"] = " ".join(words)

        if "description" not in config:
            config["description"] = description[:200]

        if "initial_prompt" not in config:
            config["initial_prompt"] = description[:300]

        if "steps" not in config:
            config["steps"] = 10

        if "apps" not in config:
            config["apps"] = []

        # Ensure agents exist
        if "agents" not in config or not config["agents"]:
            config["agents"] = [
                {
                    "name": "Agent 1",
                    "role": "peer",
                    "background": "",
                    "traits": self._default_traits(),
                },
                {
                    "name": "Agent 2",
                    "role": "peer",
                    "background": "",
                    "traits": self._default_traits(),
                },
            ]
        else:
            # Ensure each agent has required fields
            for agent in config["agents"]:
                if "role" not in agent:
                    agent["role"] = "peer"
                if "background" not in agent:
                    agent["background"] = ""
                if "traits" not in agent:
                    agent["traits"] = self._default_traits()
                else:
                    # Ensure all traits are present
                    default = self._default_traits()
                    for trait in default:
                        if trait not in agent["traits"]:
                            agent["traits"][trait] = default[trait]

        return config

    def _default_traits(self) -> dict[str, float]:
        """Return default Big Five trait values."""
        return {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.3,
        }
