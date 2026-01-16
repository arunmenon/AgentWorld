"""LLM provider abstraction using LiteLLM."""

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import litellm
from litellm import acompletion

from agentworld.core.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError
from agentworld.core.models import LLMResponse
from agentworld.llm.cache import LLMCache
from agentworld.llm.cost import estimate_cost
from agentworld.llm.tokens import count_tokens


# Configure litellm
litellm.drop_params = True  # Drop unsupported params silently

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_RETRY_MULTIPLIER = 2.0


@dataclass
class LLMCallRecord:
    """Audit record for every LLM call.

    Used for reproducibility and debugging per ADR-003.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Request
    provider: str = ""
    model: str = ""
    messages: list[dict] = field(default_factory=list)
    temperature: float = 0.7
    seed: int | None = None
    other_params: dict = field(default_factory=dict)

    # Response
    response_content: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0

    # Context
    agent_id: str | None = None
    simulation_id: str | None = None
    step: int | None = None

    # Status
    cached: bool = False
    error: str | None = None
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "seed": self.seed,
            "other_params": self.other_params,
            "response_content": self.response_content,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
            "agent_id": self.agent_id,
            "simulation_id": self.simulation_id,
            "step": self.step,
            "cached": self.cached,
            "error": self.error,
            "retries": self.retries,
        }


class LLMProvider:
    """Multi-provider LLM abstraction layer."""

    def __init__(
        self,
        default_model: str = "openai/gpt-4o-mini",
        cache: LLMCache | None = None,
        timeout: int = 60,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        retry_multiplier: float = DEFAULT_RETRY_MULTIPLIER,
        simulation_id: str | None = None,
    ):
        """Initialize the LLM provider.

        Args:
            default_model: Default model to use (format: provider/model)
            cache: Optional cache instance for response caching
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
            retry_delay: Initial delay between retries in seconds
            retry_multiplier: Multiplier for exponential backoff
            simulation_id: Simulation ID for call logging
        """
        self.default_model = default_model
        self.cache = cache or LLMCache()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_multiplier = retry_multiplier
        self.simulation_id = simulation_id
        self._total_tokens = 0
        self._total_cost = 0.0
        self._call_history: list[LLMCallRecord] = []

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: str | None = None,
        use_cache: bool = True,
        seed: int | None = None,
        agent_id: str | None = None,
        step: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt
            use_cache: Whether to use caching
            seed: Seed for reproducibility (provider support varies)
            agent_id: Agent ID for call attribution/logging
            step: Simulation step for call logging
            **kwargs: Additional parameters passed to the model

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMError: If the completion fails
            LLMRateLimitError: If rate limited
            LLMTimeoutError: If request times out
        """
        model = model or self.default_model
        provider = model.split("/")[0] if "/" in model else "unknown"

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Check cache
        cache_key = self._cache_key(messages, model, temperature, seed)
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                # Log cached call
                record = LLMCallRecord(
                    provider=provider,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    seed=seed,
                    response_content=cached["content"],
                    prompt_tokens=cached["prompt_tokens"],
                    completion_tokens=cached["completion_tokens"],
                    agent_id=agent_id,
                    simulation_id=self.simulation_id,
                    step=step,
                    cached=True,
                )
                self._call_history.append(record)

                return LLMResponse(
                    content=cached["content"],
                    tokens_used=cached["tokens_used"],
                    prompt_tokens=cached["prompt_tokens"],
                    completion_tokens=cached["completion_tokens"],
                    cost=cached["cost"],
                    model=model,
                    cached=True,
                )

        # Prepare call record
        record = LLMCallRecord(
            provider=provider,
            model=model,
            messages=messages,
            temperature=temperature,
            seed=seed,
            other_params=kwargs,
            agent_id=agent_id,
            simulation_id=self.simulation_id,
            step=step,
        )

        # Make API call with retry logic
        start_time = datetime.now(timezone.utc)
        last_error: Exception | None = None
        retries = 0

        for attempt in range(self.max_retries + 1):
            try:
                # Build API params
                api_params: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                }
                # Add seed if provided (not all providers support it)
                if seed is not None:
                    api_params["seed"] = seed

                response = await asyncio.wait_for(
                    acompletion(**api_params),
                    timeout=self.timeout,
                )
                break  # Success, exit retry loop

            except asyncio.TimeoutError:
                last_error = LLMTimeoutError(f"LLM request timed out after {self.timeout}s")
                retries = attempt
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (self.retry_multiplier ** attempt))
                    continue
                record.error = str(last_error)
                record.retries = retries
                self._call_history.append(record)
                raise last_error

            except litellm.RateLimitError as e:
                last_error = LLMRateLimitError(f"Rate limit exceeded: {e}")
                retries = attempt
                if attempt < self.max_retries:
                    # Longer delay for rate limits
                    await asyncio.sleep(self.retry_delay * (self.retry_multiplier ** (attempt + 1)))
                    continue
                record.error = str(last_error)
                record.retries = retries
                self._call_history.append(record)
                raise last_error

            except Exception as e:
                last_error = LLMError(f"LLM completion failed: {e}")
                retries = attempt
                # Don't retry on non-transient errors
                record.error = str(last_error)
                record.retries = retries
                self._call_history.append(record)
                raise last_error

        # Calculate latency
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Extract response data
        content = response.choices[0].message.content or ""
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else count_tokens(prompt, model)
        completion_tokens = usage.completion_tokens if usage else count_tokens(content, model)
        tokens_used = prompt_tokens + completion_tokens
        cost = estimate_cost(model, prompt_tokens, completion_tokens)

        # Update totals
        self._total_tokens += tokens_used
        self._total_cost += cost

        # Update and log call record
        record.response_content = content
        record.prompt_tokens = prompt_tokens
        record.completion_tokens = completion_tokens
        record.latency_ms = latency_ms
        record.retries = retries
        self._call_history.append(record)

        # Build response
        llm_response = LLMResponse(
            content=content,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            model=model,
            cached=False,
        )

        # Cache response
        if use_cache:
            self.cache.set(cache_key, llm_response.to_dict())

        return llm_response

    def _cache_key(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        seed: int | None = None,
    ) -> str:
        """Generate a cache key for the request.

        Includes seed in key per ADR-003 for reproducibility.
        """
        key_data = json.dumps(
            {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "seed": seed,
            },
            sort_keys=True,
        )
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all requests."""
        return self._total_tokens

    @property
    def total_cost(self) -> float:
        """Total cost across all requests."""
        return self._total_cost

    @property
    def call_history(self) -> list[LLMCallRecord]:
        """Get the call history for auditing."""
        return self._call_history.copy()

    def get_calls_for_agent(self, agent_id: str) -> list[LLMCallRecord]:
        """Get call history filtered by agent ID.

        Args:
            agent_id: Agent ID to filter by

        Returns:
            List of LLMCallRecord for the specified agent
        """
        return [r for r in self._call_history if r.agent_id == agent_id]

    def get_calls_for_step(self, step: int) -> list[LLMCallRecord]:
        """Get call history filtered by step.

        Args:
            step: Simulation step to filter by

        Returns:
            List of LLMCallRecord for the specified step
        """
        return [r for r in self._call_history if r.step == step]

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._total_tokens = 0
        self._total_cost = 0.0

    def clear_history(self) -> None:
        """Clear call history."""
        self._call_history.clear()


# Global provider instance
_default_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """Get or create the default LLM provider."""
    global _default_provider
    if _default_provider is None:
        _default_provider = LLMProvider()
    return _default_provider


async def complete(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    system_prompt: str | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """Convenience function to generate a completion.

    Uses the default provider instance.
    """
    provider = get_provider()
    return await provider.complete(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        **kwargs,
    )
