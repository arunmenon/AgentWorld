"""AI-assisted task generation from natural language descriptions.

Uses LLM to generate dual-control task definitions from natural language.
"""

import json
import logging
import re
from typing import Any

from agentworld.llm.provider import LLMProvider, get_provider

logger = logging.getLogger(__name__)

TASK_GENERATOR_SYSTEM_PROMPT = """You are a task definition generator for τ²-bench dual-control evaluation scenarios.

Given a natural language scenario description, generate a complete task definition as JSON.

## Output Schema

{
  "name": "Short task name (3-6 words)",
  "description": "Full scenario description - preserve the user's input details, do not summarize",
  "domain": "paypal|emirates|banking|shopping|general",
  "difficulty": "easy|medium|hard",

  "agent_role": "service_agent",
  "agent_instruction": "What the service agent should do to help the customer",

  "user_role": "customer",
  "user_instruction": "What the customer is trying to accomplish",
  "user_apps": ["app_id"],

  "initial_state": {
    "app_id": { "field": "value" }
  },

  "goal_state": {
    "app_id.field": "expected_value"
  },

  "required_handoffs": [
    {
      "from_role": "service_agent",
      "to_role": "customer",
      "app_id": "the_app_id_from_available_apps",
      "expected_action": "action_name_from_that_app",
      "description": "What this handoff accomplishes",
      "instruction_template": {
        "template_id": "unique_template_id",
        "keywords": ["action verbs the agent might use"],
        "target_keywords": ["nouns/objects the instruction refers to"]
      }
    }
  ],

  "goal_conditions": [
    {
      "goal_type": "state_equals|action_executed|handoff_completed|output_contains",
      "description": "What this goal verifies",
      "app_id": "for state/action goals",
      "field_path": "for state goals",
      "expected_value": "for state/action goals",
      "handoff_id": "for coordination goals",
      "required_phrase": "for output goals"
    }
  ],

  "scenario_prompt": "Natural conversation starter for the simulation",
  "max_turns": 10,
  "tags": ["tag1", "tag2"]
}

## Handoff Instruction Templates

CRITICAL: Each handoff MUST include an instruction_template. This helps the simulation engine detect when the agent gives an instruction to the user.

The instruction_template has:
- template_id: Unique identifier (e.g., "verify_identity_instruction")
- keywords: Action verbs the agent might use (e.g., ["verify", "confirm", "authenticate", "check"])
- target_keywords: Nouns the instruction refers to (e.g., ["identity", "ID", "yourself", "account"])

When agent says "Please verify your identity", the system matches:
- "verify" matches keywords ✓
- "identity" matches target_keywords ✓
→ Instruction detected for this handoff!

### Example Handoffs with Templates

PayPal - Verify Identity:
{
  "expected_action": "verify_identity",
  "instruction_template": {
    "template_id": "verify_identity",
    "keywords": ["verify", "confirm", "authenticate", "prove"],
    "target_keywords": ["identity", "ID", "yourself", "who you are", "account holder"]
  }
}

PayPal - Confirm Transfer:
{
  "expected_action": "confirm_transfer",
  "instruction_template": {
    "template_id": "confirm_transfer",
    "keywords": ["confirm", "approve", "accept", "authorize", "complete"],
    "target_keywords": ["transfer", "payment", "transaction", "send"]
  }
}

Emirates - Check Booking:
{
  "expected_action": "view_booking",
  "instruction_template": {
    "template_id": "check_booking",
    "keywords": ["check", "look", "view", "open", "see", "find"],
    "target_keywords": ["booking", "reservation", "trip", "flight", "itinerary", "app"]
  }
}

## Guidelines

1. **Realistic scenarios**: Create believable customer service interactions
2. **Clear handoffs**: Each handoff needs distinct instruction_template keywords
3. **Multiple keyword variations**: Include synonyms (verify/confirm/authenticate)
4. **Verifiable goals**: Goals should be objectively measurable
5. **Appropriate difficulty**:
   - Easy: 1-2 handoffs, simple state changes
   - Medium: 3-4 handoffs, multiple state changes
   - Hard: 5+ handoffs, complex multi-step coordination

## Common Apps and Actions

- paypal_test: balance, transactions, disputes
  Actions: transfer, check_balance, file_dispute, verify_identity, confirm_transfer, review_transaction
- emirates_test: bookings, flights, loyalty_points
  Actions: book_flight, check_booking, cancel_flight, modify_booking, view_boarding_pass, select_seat
- banking_test: accounts, transactions
  Actions: check_balance, transfer, view_history, set_alert, update_info
- shopping_test: orders, cart, inventory
  Actions: add_to_cart, checkout, track_order, return_item, apply_coupon, confirm_address

## Goal Types

- state_equals: Check if app state field equals expected value
- state_contains: Check if array/object contains value
- action_executed: Verify specific action was called
- handoff_completed: Check if specific handoff occurred
- all_handoffs_done: Check if all handoffs completed
- output_contains: Check if agent output contains phrase

Return ONLY valid JSON, no explanations or markdown code blocks."""


class AITaskGenerator:
    """Generate task definitions from natural language descriptions."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        """Initialize the generator.

        Args:
            llm_provider: Optional LLM provider instance. Uses default if not provided.
        """
        self.provider = llm_provider or get_provider()

    async def generate_task(
        self,
        description: str,
        domain_hint: str | None = None,
        available_apps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate a complete task definition from natural language.

        Args:
            description: Natural language scenario description
            domain_hint: Optional domain hint (paypal, emirates, etc.)
            available_apps: Optional list of available apps with their actions

        Returns:
            Dict matching DualControlTaskDefinition structure
        """
        prompt = self._build_prompt(description, domain_hint, available_apps)

        response = await self.provider.complete(
            prompt=prompt,
            model="openai/gpt-4o",  # Use GPT-4o for high-quality generation
            temperature=0.7,  # Some creativity
            max_tokens=2000,
            system_prompt=TASK_GENERATOR_SYSTEM_PROMPT,
        )

        # Parse and validate JSON response
        task_data = self._parse_response(response.content)

        # Post-process to ensure required fields
        task_data = self._ensure_required_fields(task_data, description)

        return task_data

    def _build_prompt(
        self,
        description: str,
        domain_hint: str | None,
        available_apps: list[dict[str, Any]] | None = None,
    ) -> str:
        """Build the prompt for task generation."""
        domain_context = f"\nDomain hint: {domain_hint}" if domain_hint else ""

        # Build available apps context
        apps_context = ""
        if available_apps:
            apps_lines = ["\n\n## Available Apps (USE THESE app_ids for handoffs):"]
            for app in available_apps:
                actions = app.get("actions", [])
                action_names = [a.get("name", "") for a in actions]
                apps_lines.append(f"- {app['app_id']} ({app['name']}): {', '.join(action_names)}")
            apps_context = "\n".join(apps_lines)
            apps_context += "\n\nIMPORTANT: For each handoff, set 'app_id' to one of the above app_ids and 'expected_action' to one of its available actions."

        return f"""Generate a complete dual-control evaluation task from this scenario:

{description}
{domain_context}{apps_context}

Return a JSON object with the task definition. Focus on:
1. Realistic handoff sequences between service agent and customer
2. Verifiable goal conditions
3. Appropriate difficulty level based on complexity
4. Use the available app_ids and actions provided above for handoffs"""

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
        raise ValueError("Failed to parse task definition from LLM response")

    def _ensure_required_fields(
        self, task_data: dict[str, Any], description: str
    ) -> dict[str, Any]:
        """Ensure all required fields are present with defaults."""
        defaults = {
            "name": "Generated Task",
            "description": description[:200],
            "domain": "general",
            "difficulty": "medium",
            "agent_role": "service_agent",
            "agent_instruction": "Help the customer accomplish their goal.",
            "user_role": "customer",
            "user_instruction": description[:500],
            "user_apps": [],
            "initial_state": {},
            "goal_state": {},
            "required_handoffs": [],
            "goal_conditions": [],
            "scenario_prompt": description[:300],
            "max_turns": 10,
            "tags": [],
        }

        for key, default_value in defaults.items():
            if key not in task_data:
                task_data[key] = default_value

        # Generate handoff IDs if missing
        for i, handoff in enumerate(task_data.get("required_handoffs", [])):
            if "handoff_id" not in handoff:
                handoff["handoff_id"] = f"handoff_{i + 1}"

        # Generate goal condition IDs if missing
        for i, condition in enumerate(task_data.get("goal_conditions", [])):
            if "id" not in condition:
                condition["id"] = f"goal_{i + 1}"

        return task_data
