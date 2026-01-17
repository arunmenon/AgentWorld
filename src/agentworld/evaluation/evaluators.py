"""Evaluator protocol and built-in evaluators for message quality scoring.

Provides a Protocol-based evaluator system with provenance tracking
for training data quality filtering and agent benchmarking.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from agentworld.evaluation.client import JSONParseError, LLMClient
from agentworld.evaluation.config import ValidationConfig

if TYPE_CHECKING:
    from agentworld.agents.agent import Agent


@dataclass
class EvaluationResult:
    """Result of an evaluation with full provenance tracking."""

    score: float  # 0.0 - 1.0
    explanation: str | None  # User-facing rationale

    # Provenance metadata
    evaluator_name: str
    evaluator_version: str
    judge_model: str | None = None
    judge_prompt_hash: str | None = None
    input_hash: str = ""

    # Operational metadata
    cost_usd: float = 0.0
    latency_ms: int = 0

    # Optional details
    passed: bool = True  # score >= threshold
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(uuid.uuid4()),
            "score": self.score,
            "explanation": self.explanation,
            "evaluator_name": self.evaluator_name,
            "evaluator_version": self.evaluator_version,
            "judge_model": self.judge_model,
            "judge_prompt_hash": self.judge_prompt_hash,
            "input_hash": self.input_hash,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass
class EvaluationContext:
    """Context for message evaluation."""

    message_id: str
    message_content: str
    sender_id: str
    sender_name: str | None = None
    persona_context: str | None = None
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    agent: Agent | None = None

    def compute_input_hash(self) -> str:
        """Compute hash of evaluation input for provenance."""
        content = f"{self.message_id}:{self.message_content}:{self.persona_context}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@runtime_checkable
class EvaluatorProtocol(Protocol):
    """Protocol for message evaluators."""

    @property
    def name(self) -> str:
        """Unique evaluator name."""
        ...

    @property
    def version(self) -> str:
        """Evaluator version for provenance tracking."""
        ...

    async def evaluate(
        self,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """Evaluate a message and return result with provenance."""
        ...


class BaseEvaluator:
    """Base class for evaluators with common functionality."""

    _name: str = "base"
    _version: str = "1.0.0"

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    def _create_result(
        self,
        score: float,
        explanation: str | None,
        context: EvaluationContext,
        judge_model: str | None = None,
        judge_prompt_hash: str | None = None,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        threshold: float = 0.5,
        details: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        """Create evaluation result with provenance."""
        return EvaluationResult(
            score=score,
            explanation=explanation,
            evaluator_name=self.name,
            evaluator_version=self.version,
            judge_model=judge_model,
            judge_prompt_hash=judge_prompt_hash,
            input_hash=context.compute_input_hash(),
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            passed=score >= threshold,
            details=details or {},
        )


class LLMEvaluator(BaseEvaluator):
    """Base class for LLM-based evaluators."""

    def __init__(
        self,
        llm_client: LLMClient,
        config: ValidationConfig | None = None,
    ) -> None:
        self.llm = llm_client
        self.config = config or ValidationConfig()

    def _compute_prompt_hash(self, prompt: str) -> str:
        """Compute hash of evaluation prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    async def _evaluate_with_llm(
        self,
        prompt: str,
        context: EvaluationContext,
        threshold: float = 0.5,
    ) -> EvaluationResult:
        """Run LLM evaluation with timing and provenance."""
        start_time = time.time()
        prompt_hash = self._compute_prompt_hash(prompt)

        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}},
            )
            latency_ms = int((time.time() - start_time) * 1000)
            score = float(result["score"])

            # Estimate cost (rough approximation)
            prompt_tokens = len(prompt.split()) * 1.3
            response_tokens = len(str(result).split()) * 1.3
            cost_usd = (prompt_tokens * 0.001 + response_tokens * 0.002) / 1000

            return self._create_result(
                score=score,
                explanation=result.get("explanation"),
                context=context,
                judge_model=getattr(self.llm, "model", "unknown"),
                judge_prompt_hash=prompt_hash,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                threshold=threshold,
            )
        except (JSONParseError, KeyError) as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return self._create_result(
                score=0.0,
                explanation=f"Evaluation failed: {e}",
                context=context,
                judge_model=getattr(self.llm, "model", "unknown"),
                judge_prompt_hash=prompt_hash,
                latency_ms=latency_ms,
                threshold=threshold,
            )


class PersonaAdherenceEvaluator(LLMEvaluator):
    """Evaluates how well a message matches the agent's persona."""

    _name = "persona_adherence"
    _version = "1.0.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate persona adherence."""
        persona_context = context.persona_context or "No persona context available"

        prompt = f"""
Evaluate if this response matches the agent's personality profile.

Agent Persona:
{persona_context}

Agent's Response:
"{context.message_content[:1000]}"

Rate adherence from 0.0 (completely out of character) to 1.0 (perfectly in character).
Consider: tone, vocabulary, expressed opinions, and behavioral patterns.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        return await self._evaluate_with_llm(
            prompt,
            context,
            threshold=self.config.persona_adherence_threshold,
        )


class CoherenceEvaluator(LLMEvaluator):
    """Evaluates message coherence and quality."""

    _name = "coherence"
    _version = "1.0.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate message coherence."""
        prompt = f"""
Evaluate the coherence and quality of this response.

Response:
"{context.message_content[:1000]}"

Consider:
1. Grammatical correctness
2. Logical flow and structure
3. Completeness (not abruptly cut off)
4. Internal consistency

Rate coherence from 0.0 (incoherent/broken) to 1.0 (clear and well-formed).

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        return await self._evaluate_with_llm(
            prompt,
            context,
            threshold=self.config.coherence_threshold,
        )


class RelevanceEvaluator(LLMEvaluator):
    """Evaluates message relevance to conversation context."""

    _name = "relevance"
    _version = "1.0.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate message relevance."""
        # Build conversation context
        history_text = ""
        if context.conversation_history:
            recent = context.conversation_history[-5:]
            history_text = "\n".join(
                f'- {msg.get("sender", "Unknown")}: "{msg.get("content", "")[:200]}"'
                for msg in recent
            )
        else:
            history_text = "No previous conversation"

        prompt = f"""
Evaluate how relevant this response is to the conversation context.

Conversation History:
{history_text}

Current Response:
"{context.message_content[:1000]}"

Rate relevance from 0.0 (completely off-topic) to 1.0 (highly relevant and on-topic).
Consider: topic continuation, addressing previous points, contextual appropriateness.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        return await self._evaluate_with_llm(
            prompt,
            context,
            threshold=0.6,
        )


class ConsistencyEvaluator(LLMEvaluator):
    """Evaluates consistency with agent's previous statements."""

    _name = "consistency"
    _version = "1.0.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate consistency with previous statements."""
        if not context.conversation_history:
            return self._create_result(
                score=1.0,
                explanation="No previous statements to compare",
                context=context,
                threshold=self.config.consistency_threshold,
            )

        # Filter to agent's own previous statements
        agent_statements = [
            msg for msg in context.conversation_history
            if msg.get("sender_id") == context.sender_id
        ][-5:]

        if not agent_statements:
            return self._create_result(
                score=1.0,
                explanation="No previous statements from this agent",
                context=context,
                threshold=self.config.consistency_threshold,
            )

        history_text = "\n".join(
            f'- "{msg.get("content", "")[:200]}"'
            for msg in agent_statements
        )

        prompt = f"""
Check if this new response is consistent with the agent's previous statements.

Previous statements by this agent:
{history_text}

New response:
"{context.message_content[:500]}"

Rate consistency from 0.0 (contradicts previous statements) to 1.0 (fully consistent).
Consider: factual claims, opinions, personality, and knowledge.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        return await self._evaluate_with_llm(
            prompt,
            context,
            threshold=self.config.consistency_threshold,
        )


# Heuristic Evaluators (fast, no LLM cost)


class LengthCheckEvaluator(BaseEvaluator):
    """Fast heuristic evaluator for message length."""

    _name = "length_check"
    _version = "1.0.0"

    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 10000,
        optimal_range: tuple[int, int] = (50, 2000),
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.optimal_range = optimal_range

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate message length."""
        length = len(context.message_content)

        if length < self.min_length:
            score = 0.2
            explanation = f"Message too short ({length} chars, min {self.min_length})"
        elif length > self.max_length:
            score = 0.3
            explanation = f"Message too long ({length} chars, max {self.max_length})"
        elif self.optimal_range[0] <= length <= self.optimal_range[1]:
            score = 1.0
            explanation = f"Message length optimal ({length} chars)"
        else:
            # Partial score for out-of-optimal but acceptable length
            score = 0.7
            explanation = f"Message length acceptable ({length} chars)"

        return self._create_result(
            score=score,
            explanation=explanation,
            context=context,
            threshold=0.5,
            details={"length": length},
        )


class KeywordFilterEvaluator(BaseEvaluator):
    """Fast heuristic evaluator for prohibited/required keywords."""

    _name = "keyword_filter"
    _version = "1.0.0"

    def __init__(
        self,
        prohibited_keywords: list[str] | None = None,
        required_keywords: list[str] | None = None,
    ) -> None:
        self.prohibited = [k.lower() for k in (prohibited_keywords or [])]
        self.required = [k.lower() for k in (required_keywords or [])]

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate message for prohibited/required keywords."""
        content_lower = context.message_content.lower()

        found_prohibited = [k for k in self.prohibited if k in content_lower]
        found_required = [k for k in self.required if k in content_lower]
        missing_required = [k for k in self.required if k not in content_lower]

        if found_prohibited:
            score = 0.0
            explanation = f"Prohibited keywords found: {found_prohibited}"
        elif missing_required:
            score = 0.5 * (len(found_required) / len(self.required)) if self.required else 1.0
            explanation = f"Missing required keywords: {missing_required}"
        else:
            score = 1.0
            explanation = "Keyword check passed"

        return self._create_result(
            score=score,
            explanation=explanation,
            context=context,
            threshold=0.5,
            details={
                "found_prohibited": found_prohibited,
                "found_required": found_required,
                "missing_required": missing_required,
            },
        )


class EvaluatorRegistry:
    """Registry for managing and running evaluators."""

    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorProtocol] = {}

    def register(self, evaluator: EvaluatorProtocol) -> None:
        """Register an evaluator."""
        self._evaluators[evaluator.name] = evaluator

    def get(self, name: str) -> EvaluatorProtocol | None:
        """Get evaluator by name."""
        return self._evaluators.get(name)

    def list_evaluators(self) -> list[str]:
        """List registered evaluator names."""
        return list(self._evaluators.keys())

    async def evaluate_message(
        self,
        context: EvaluationContext,
        evaluator_names: list[str] | None = None,
    ) -> list[EvaluationResult]:
        """Run specified evaluators on a message.

        Args:
            context: Evaluation context
            evaluator_names: List of evaluator names to run (None = all)

        Returns:
            List of evaluation results
        """
        names = evaluator_names or list(self._evaluators.keys())
        results = []

        for name in names:
            evaluator = self._evaluators.get(name)
            if evaluator:
                result = await evaluator.evaluate(context)
                results.append(result)

        return results


def create_default_registry(
    llm_client: LLMClient | None = None,
    config: ValidationConfig | None = None,
) -> EvaluatorRegistry:
    """Create registry with default evaluators.

    Args:
        llm_client: LLM client for LLM-based evaluators (optional)
        config: Validation configuration

    Returns:
        Registry with registered evaluators
    """
    registry = EvaluatorRegistry()

    # Always register heuristic evaluators
    registry.register(LengthCheckEvaluator())
    registry.register(KeywordFilterEvaluator())

    # Register LLM evaluators if client provided
    if llm_client:
        registry.register(PersonaAdherenceEvaluator(llm_client, config))
        registry.register(CoherenceEvaluator(llm_client, config))
        registry.register(RelevanceEvaluator(llm_client, config))
        registry.register(ConsistencyEvaluator(llm_client, config))

    return registry
