"""LLM client wrapper for evaluation components per ADR-010."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentworld.llm.provider import LLMProvider


class JSONParseError(Exception):
    """Raised when JSON parsing fails after retries."""

    pass


class SchemaValidationError(Exception):
    """Raised when JSON doesn't match expected schema."""

    pass


@dataclass
class LLMResponse:
    """Standardized response from LLM calls."""

    content: str
    tokens_used: int
    model: str
    latency_ms: float


class LLMClient:
    """
    Unified LLM interface for evaluation components.

    Wraps LiteLLM (ADR-003) with:
    - Consistent async interface
    - Structured output parsing
    - Error handling with retries
    - Cost tracking
    """

    def __init__(self, provider: "LLMProvider"):
        self._provider = provider

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """
        Send completion request with standardized response.

        Uses temperature=0 for deterministic evaluation by default.
        """
        import time

        start = time.time()
        record = await self._provider.acomplete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = (time.time() - start) * 1000

        return LLMResponse(
            content=record.response_content,
            tokens_used=record.prompt_tokens + record.completion_tokens,
            model=record.model,
            latency_ms=latency,
        )

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any] | None = None,
        retries: int = 2,
    ) -> dict[str, Any]:
        """
        Request JSON-formatted response with validation.

        Args:
            messages: Conversation messages
            schema: Optional JSON schema for validation
            retries: Number of retries on parse failure

        Returns:
            Parsed JSON dict

        Raises:
            JSONParseError: After all retries exhausted
        """
        current_messages = list(messages)
        response = None

        for attempt in range(retries + 1):
            try:
                response = await self.complete(current_messages)
                # Extract JSON from response (may be wrapped in markdown)
                json_str = self._extract_json(response.content)
                parsed = json.loads(json_str)

                if schema:
                    self._validate_schema(parsed, schema)

                return parsed
            except (json.JSONDecodeError, SchemaValidationError) as e:
                if attempt == retries:
                    raise JSONParseError(
                        f"Failed to parse JSON after {retries + 1} attempts: {e}"
                    ) from e
                # Retry with clarified prompt
                if response:
                    current_messages = current_messages + [
                        {"role": "assistant", "content": response.content},
                        {"role": "user", "content": "Please respond with valid JSON only."},
                    ]

        # Should not reach here
        raise JSONParseError("Unexpected error in JSON parsing")

    def _extract_json(self, content: str) -> str:
        """Extract JSON from response, handling markdown code blocks."""
        # Try to find JSON in code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # Try to find JSON object or array
        json_match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Assume entire content is JSON
        return content.strip()

    def _validate_schema(self, data: dict, schema: dict) -> None:
        """Basic schema validation (required fields, types)."""
        required = schema.get("required", {})
        if isinstance(required, dict):
            for field, field_type in required.items():
                if field not in data:
                    raise SchemaValidationError(f"Missing required field: {field}")
                if not isinstance(data[field], field_type):
                    raise SchemaValidationError(
                        f"Field {field} should be {field_type}, got {type(data[field])}"
                    )
        elif isinstance(required, list):
            for field in required:
                if field not in data:
                    raise SchemaValidationError(f"Missing required field: {field}")
