"""Validation components for agent behavior quality per ADR-010."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agentworld.evaluation.client import JSONParseError, LLMClient
from agentworld.evaluation.config import ValidationConfig

if TYPE_CHECKING:
    from agentworld.agents.agent import Agent


@dataclass
class ValidationResult:
    """Result of a validation check."""

    check_type: str
    score: float  # 0-1
    passed: bool  # score >= threshold
    explanation: str
    agent_id: str | None = None
    response_excerpt: str = ""  # First 100 chars of validated response


class Validator:
    """
    Validate agent behavior quality using LLM scoring.

    Uses configurable thresholds and optional separate evaluation model
    to reduce scoring bias.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: ValidationConfig | None = None,
    ) -> None:
        self.llm = llm_client
        self.config = config or ValidationConfig()
        self._validation_count = 0

    def _should_validate(self) -> bool:
        """Check if we should run validation (budget/sampling)."""
        if self._validation_count >= self.config.max_validations_per_run:
            return False
        if self.config.sampling_rate < 1.0:
            return random.random() < self.config.sampling_rate
        return True

    async def check_persona_adherence(
        self,
        agent: "Agent",
        response: str,
    ) -> ValidationResult:
        """
        Score how well response matches agent's persona (ADR-004).
        Returns score 0-1 with explanation.
        """
        if not self._should_validate():
            return ValidationResult(
                check_type="persona_adherence",
                score=0.0,
                passed=False,
                explanation="Skipped due to budget/sampling",
                agent_id=agent.id,
            )

        self._validation_count += 1

        # Get persona context
        persona_context = ""
        if hasattr(agent, "persona") and agent.persona:
            if hasattr(agent.persona, "to_prompt_context"):
                persona_context = agent.persona.to_prompt_context()
            elif hasattr(agent.persona, "to_prompt_description"):
                persona_context = agent.persona.to_prompt_description()
            else:
                persona_context = str(agent.persona)

        prompt = f"""
Evaluate if this response matches the agent's personality profile.

Agent Persona:
{persona_context}

Agent's Response:
"{response[:1000]}"

Rate adherence from 0.0 (completely out of character) to 1.0 (perfectly in character).
Consider: tone, vocabulary, expressed opinions, and behavioral patterns.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}},
            )
            score = float(result["score"])
            return ValidationResult(
                check_type="persona_adherence",
                score=score,
                passed=score >= self.config.persona_adherence_threshold,
                explanation=result["explanation"],
                agent_id=agent.id,
                response_excerpt=response[:100],
            )
        except (JSONParseError, KeyError) as e:
            return ValidationResult(
                check_type="persona_adherence",
                score=0.0,
                passed=False,
                explanation=f"Validation failed: {e}",
                agent_id=agent.id,
            )

    async def check_consistency(
        self,
        agent: "Agent",
        response: str,
        previous_responses: list[str],
    ) -> ValidationResult:
        """Check if response is consistent with agent's previous statements."""
        if not self._should_validate():
            return ValidationResult(
                check_type="consistency",
                score=0.0,
                passed=False,
                explanation="Skipped due to budget/sampling",
                agent_id=agent.id,
            )

        if not previous_responses:
            return ValidationResult(
                check_type="consistency",
                score=1.0,
                passed=True,
                explanation="No previous responses to compare",
                agent_id=agent.id,
            )

        self._validation_count += 1

        # Use last 5 responses for context
        context_responses = previous_responses[-5:]
        prompt = f"""
Check if this new response is consistent with the agent's previous statements.

Previous statements:
{chr(10).join(f'- "{r[:200]}"' for r in context_responses)}

New response:
"{response[:500]}"

Rate consistency from 0.0 (contradicts previous statements) to 1.0 (fully consistent).
Consider: factual claims, opinions, personality, and knowledge.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}},
            )
            score = float(result["score"])
            return ValidationResult(
                check_type="consistency",
                score=score,
                passed=score >= self.config.consistency_threshold,
                explanation=result["explanation"],
                agent_id=agent.id,
                response_excerpt=response[:100],
            )
        except (JSONParseError, KeyError) as e:
            return ValidationResult(
                check_type="consistency",
                score=0.0,
                passed=False,
                explanation=f"Validation failed: {e}",
                agent_id=agent.id,
            )

    async def check_coherence(self, response: str) -> ValidationResult:
        """
        Check if response is coherent and well-formed.

        Evaluates:
        - Grammatical correctness
        - Logical flow
        - Completeness (not cut off)
        - Relevance to context
        """
        if not self._should_validate():
            return ValidationResult(
                check_type="coherence",
                score=0.0,
                passed=False,
                explanation="Skipped due to budget/sampling",
            )

        self._validation_count += 1

        prompt = f"""
Evaluate the coherence and quality of this response.

Response:
"{response[:1000]}"

Consider:
1. Grammatical correctness
2. Logical flow and structure
3. Completeness (not abruptly cut off)
4. Internal consistency

Rate coherence from 0.0 (incoherent/broken) to 1.0 (clear and well-formed).

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}},
            )
            score = float(result["score"])
            return ValidationResult(
                check_type="coherence",
                score=score,
                passed=score >= self.config.coherence_threshold,
                explanation=result["explanation"],
                response_excerpt=response[:100],
            )
        except (JSONParseError, KeyError) as e:
            return ValidationResult(
                check_type="coherence",
                score=0.0,
                passed=False,
                explanation=f"Validation failed: {e}",
            )

    async def validate_all(
        self,
        agent: "Agent",
        response: str,
        previous_responses: list[str] | None = None,
    ) -> list[ValidationResult]:
        """Run all validation checks on a response."""
        results = []
        results.append(await self.check_persona_adherence(agent, response))
        results.append(
            await self.check_consistency(agent, response, previous_responses or [])
        )
        results.append(await self.check_coherence(response))
        return results

    def reset_budget(self) -> None:
        """Reset validation count for new run."""
        self._validation_count = 0
