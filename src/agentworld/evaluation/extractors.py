"""Results extraction for structured data from simulation outputs per ADR-010."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from agentworld.evaluation.client import JSONParseError, LLMClient

if TYPE_CHECKING:
    from agentworld.core.message import Message


@dataclass
class Opinion:
    """Extracted opinion about a topic."""

    agent_id: str
    stance: str  # positive, negative, neutral, mixed
    summary: str
    key_points: list[str]
    confidence: float


@dataclass
class Theme:
    """Recurring theme across messages."""

    name: str
    frequency: int
    representative_quotes: list[str]
    sentiment: str


@dataclass
class Quote:
    """Notable quote from simulation."""

    agent_id: str
    content: str
    relevance_score: float
    context: str


class ResultsExtractor:
    """
    Extract structured data from simulation outputs.

    Uses LLM for semantic extraction with error handling
    and schema validation.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    def _format_messages(self, messages: list[Any]) -> str:
        """Format messages for LLM prompt."""
        formatted = []
        for msg in messages[:50]:  # Limit to prevent context overflow
            sender = getattr(msg, "sender", getattr(msg, "sender_id", "Unknown"))
            content = getattr(msg, "content", str(msg))
            formatted.append(f"[{sender}]: {content[:200]}")
        return "\n".join(formatted)

    async def extract_opinions(
        self,
        messages: list[Any],
        topic: str,
    ) -> dict[str, Opinion]:
        """Extract each agent's opinion on a topic."""
        prompt = f"""
Analyze these messages and extract each speaker's opinion on "{topic}".

Messages:
{self._format_messages(messages)}

For each speaker who expressed a view, provide their opinion.

Respond with JSON:
{{
  "opinions": [
    {{
      "agent_id": "<speaker id>",
      "stance": "<positive|negative|neutral|mixed>",
      "summary": "<one sentence summary>",
      "key_points": ["<point 1>", "<point 2>"],
      "confidence": <0.0-1.0>
    }}
  ]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            opinions = {}
            for op in result.get("opinions", []):
                opinions[op["agent_id"]] = Opinion(
                    agent_id=op["agent_id"],
                    stance=op.get("stance", "neutral"),
                    summary=op.get("summary", ""),
                    key_points=op.get("key_points", []),
                    confidence=float(op.get("confidence", 0.5)),
                )
            return opinions
        except (JSONParseError, KeyError, TypeError):
            # Return empty dict on extraction failure
            return {}

    async def extract_themes(
        self,
        messages: list[Any],
    ) -> list[Theme]:
        """Identify recurring themes across all messages."""
        prompt = f"""
Identify the main recurring themes in this conversation.

Messages:
{self._format_messages(messages)}

Find themes that appear multiple times across different speakers.

Respond with JSON:
{{
  "themes": [
    {{
      "name": "<theme name>",
      "frequency": <number of mentions>,
      "representative_quotes": ["<quote 1>", "<quote 2>"],
      "sentiment": "<positive|negative|neutral|mixed>"
    }}
  ]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            return [
                Theme(
                    name=t["name"],
                    frequency=t.get("frequency", 1),
                    representative_quotes=t.get("representative_quotes", []),
                    sentiment=t.get("sentiment", "neutral"),
                )
                for t in result.get("themes", [])
            ]
        except (JSONParseError, KeyError, TypeError):
            return []

    async def extract_quotes(
        self,
        messages: list[Any],
        criteria: str,
    ) -> list[Quote]:
        """Extract notable quotes matching criteria."""
        prompt = f"""
Extract notable quotes from this conversation that match: "{criteria}"

Messages:
{self._format_messages(messages)}

Find the most relevant and impactful quotes.

Respond with JSON:
{{
  "quotes": [
    {{
      "agent_id": "<speaker>",
      "content": "<exact quote>",
      "relevance_score": <0.0-1.0>,
      "context": "<brief context>"
    }}
  ]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            return [
                Quote(
                    agent_id=q["agent_id"],
                    content=q["content"],
                    relevance_score=float(q.get("relevance_score", 0.5)),
                    context=q.get("context", ""),
                )
                for q in result.get("quotes", [])
            ]
        except (JSONParseError, KeyError, TypeError):
            return []

    def extract_sentiment_scores(
        self,
        messages: list[Any],
    ) -> dict[str, float]:
        """
        Compute sentiment per agent using local heuristics.

        Uses simple keyword-based sentiment (no LLM call).
        For more accurate sentiment, use extract_opinions().
        """
        positive_words = {
            "good",
            "great",
            "love",
            "excellent",
            "amazing",
            "helpful",
            "useful",
            "agree",
            "yes",
            "definitely",
            "wonderful",
            "fantastic",
            "perfect",
            "awesome",
            "best",
        }
        negative_words = {
            "bad",
            "terrible",
            "hate",
            "awful",
            "useless",
            "disagree",
            "no",
            "never",
            "problem",
            "issue",
            "worst",
            "horrible",
            "poor",
            "wrong",
            "fail",
        }

        agent_scores: dict[str, list[float]] = {}

        for msg in messages:
            sender = getattr(msg, "sender", getattr(msg, "sender_id", "Unknown"))
            content = getattr(msg, "content", str(msg))
            words = set(content.lower().split())
            pos_count = len(words & positive_words)
            neg_count = len(words & negative_words)
            total = pos_count + neg_count

            if total > 0:
                score = (pos_count - neg_count) / total  # -1 to 1
                normalized = (score + 1) / 2  # 0 to 1
            else:
                normalized = 0.5  # Neutral

            if sender not in agent_scores:
                agent_scores[sender] = []
            agent_scores[sender].append(normalized)

        # Average scores per agent
        return {
            agent: sum(scores) / len(scores)
            for agent, scores in agent_scores.items()
            if scores
        }

    async def extract_summary(
        self,
        messages: list[Any],
        max_length: int = 200,
    ) -> str:
        """Generate a brief summary of the conversation."""
        prompt = f"""
Summarize this conversation in {max_length} characters or less.

Messages:
{self._format_messages(messages)}

Provide a concise summary focusing on the main points discussed and any conclusions reached.
"""
        try:
            response = await self.llm.complete(
                [{"role": "user", "content": prompt}]
            )
            return response.content[:max_length]
        except Exception:
            return "Summary unavailable"

    async def extract_key_insights(
        self,
        messages: list[Any],
        num_insights: int = 5,
    ) -> list[str]:
        """Extract key insights from the conversation."""
        prompt = f"""
Extract the {num_insights} most important insights from this conversation.

Messages:
{self._format_messages(messages)}

Respond with JSON:
{{
  "insights": ["<insight 1>", "<insight 2>", ...]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            return result.get("insights", [])[:num_insights]
        except (JSONParseError, KeyError, TypeError):
            return []
