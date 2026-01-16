"""Importance scoring for memories."""

from typing import List, Optional

from agentworld.llm.provider import LLMProvider


class ImportanceRater:
    """Rates the importance of observations and memories.

    Supports both LLM-based rating (accurate but costly) and heuristic-based
    rating (fast but less accurate) for different use cases.
    """

    # Keywords that signal important content
    IMPORTANT_KEYWORDS = [
        "important", "critical", "urgent", "decision", "agree", "disagree",
        "believe", "feel", "think", "want", "need", "must", "should",
        "concerned", "worried", "excited", "surprised", "unexpected",
        "plan", "goal", "strategy", "problem", "solution", "insight",
    ]

    IMPORTANCE_PROMPT = """Rate the importance of this observation on a scale of 1-10.
1 = mundane (routine activity, small talk)
5 = moderate (notable event, useful information)
10 = crucial (major event, critical insight)

Observation: "{content}"

Return only a number 1-10."""

    BATCH_IMPORTANCE_PROMPT = """Rate the importance of each observation (1-10 scale).
1 = mundane, 5 = moderate, 10 = crucial
Return one number per line, nothing else.

Observations:
{observations}"""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize importance rater.

        Args:
            llm_provider: LLM provider for full rating mode. If None, uses heuristics.
        """
        self.llm = llm_provider

    async def rate(self, content: str, use_llm: bool = True) -> float:
        """Rate the importance of an observation.

        Args:
            content: The observation text to rate
            use_llm: Whether to use LLM (if available) or heuristics

        Returns:
            Importance score from 1.0 to 10.0
        """
        if use_llm and self.llm is not None:
            return await self._rate_llm(content)
        return self._rate_heuristic(content)

    async def rate_batch(self, contents: List[str], use_llm: bool = True) -> List[float]:
        """Rate importance of multiple observations efficiently.

        Args:
            contents: List of observation texts
            use_llm: Whether to use LLM (if available) or heuristics

        Returns:
            List of importance scores
        """
        if not contents:
            return []

        if use_llm and self.llm is not None:
            return await self._rate_batch_llm(contents)
        return [self._rate_heuristic(c) for c in contents]

    async def _rate_llm(self, content: str) -> float:
        """Rate importance using LLM."""
        prompt = self.IMPORTANCE_PROMPT.format(content=content)

        try:
            response = await self.llm.complete(prompt)
            score = float(response.content.strip())
            return max(1.0, min(10.0, score))
        except (ValueError, AttributeError):
            # Fall back to heuristic if LLM fails
            return self._rate_heuristic(content)

    async def _rate_batch_llm(self, contents: List[str]) -> List[float]:
        """Rate multiple observations in a single LLM call."""
        observations = "\n".join(f"{i+1}. {obs}" for i, obs in enumerate(contents))
        prompt = self.BATCH_IMPORTANCE_PROMPT.format(observations=observations)

        try:
            response = await self.llm.complete(prompt)
            lines = response.content.strip().split("\n")
            scores = []
            for line in lines:
                try:
                    # Handle various formats: "1. 7" or just "7"
                    parts = line.strip().split()
                    score_str = parts[-1] if parts else "5"
                    score = float(score_str.rstrip("."))
                    scores.append(max(1.0, min(10.0, score)))
                except (ValueError, IndexError):
                    scores.append(5.0)

            # Pad with heuristic scores if LLM returned fewer
            while len(scores) < len(contents):
                scores.append(self._rate_heuristic(contents[len(scores)]))

            return scores[:len(contents)]
        except Exception:
            # Fall back to heuristics
            return [self._rate_heuristic(c) for c in contents]

    def _rate_heuristic(self, content: str) -> float:
        """Fast heuristic importance rating.

        Uses content length, keyword presence, and punctuation as signals.
        """
        score = 3.0  # Baseline

        # Length bonus (longer = more detail = potentially more important)
        if len(content) > 200:
            score += 1.0
        if len(content) > 500:
            score += 1.0

        # Keyword signals
        content_lower = content.lower()
        keyword_matches = sum(1 for kw in self.IMPORTANT_KEYWORDS if kw in content_lower)
        score += min(3.0, keyword_matches * 0.5)

        # Exclamation/question marks often signal importance
        if "!" in content:
            score += 0.5
        if "?" in content:
            score += 0.3

        # First-person statements often indicate beliefs/feelings
        if any(phrase in content_lower for phrase in ["i think", "i believe", "i feel", "my opinion"]):
            score += 1.0

        return max(1.0, min(10.0, score))
