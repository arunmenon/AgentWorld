"""External agent provider for agent injection.

Enables testing external AI agents against simulated personas
by routing agent responses through HTTP endpoints.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from agentworld.agents.agent import Agent


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class PrivacyTier(str, Enum):
    """Privacy tiers for external context."""
    MINIMAL = "minimal"  # Only persona_ref (ID + hash)
    BASIC = "basic"      # + name, traits (no background)
    FULL = "full"        # + background, system prompt


@dataclass
class ExternalAgentConfig:
    """Configuration for an external agent endpoint."""

    endpoint_url: str
    api_key: str | None = None
    timeout_seconds: int = 30
    privacy_tier: PrivacyTier = PrivacyTier.BASIC
    fallback_to_simulated: bool = True
    max_retries: int = 3
    retry_backoff_base: float = 1.0

    # Concurrency limits
    max_inflight_requests: int = 10
    qps_cap: int = 100


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Consecutive failures to open
    half_open_probe_interval_seconds: int = 30
    success_threshold: int = 2  # Successes to close from half-open


@dataclass
class CircuitBreaker:
    """Circuit breaker for external endpoint protection."""

    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_state_change: float = field(default_factory=time.time)

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        elif self.failure_count >= self.config.failure_threshold:
            self._transition_to(CircuitState.OPEN)

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should probe
            elapsed = time.time() - self.last_state_change
            if elapsed >= self.config.half_open_probe_interval_seconds:
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False
        else:  # HALF_OPEN
            return True

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        self.state = new_state
        self.last_state_change = time.time()
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0


@dataclass
class ExternalAgentRequest:
    """Request payload for external agent."""

    schema_version: str = "1.0"
    request_id: str = ""
    run_id: str = ""
    turn_id: str = ""
    message_id: str = ""

    simulation_config_hash: str = ""
    persona_hash: str = ""

    agent_id: str = ""
    persona_ref: dict[str, Any] = field(default_factory=dict)
    persona_snapshot: dict[str, Any] | None = None

    conversation_context: dict[str, Any] = field(default_factory=dict)
    current_stimulus: str = ""

    topology_edge_context: dict[str, Any] | None = None

    timeout_ms: int = 30000
    response_format: dict[str, str] = field(default_factory=lambda: {"type": "text"})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "run_id": self.run_id,
            "turn_id": self.turn_id,
            "message_id": self.message_id,
            "simulation_config_hash": self.simulation_config_hash,
            "persona_hash": self.persona_hash,
            "agent_id": self.agent_id,
            "persona_ref": self.persona_ref,
            "conversation_context": self.conversation_context,
            "current_stimulus": self.current_stimulus,
            "timeout_ms": self.timeout_ms,
            "response_format": self.response_format,
        }
        if self.persona_snapshot:
            result["persona_snapshot"] = self.persona_snapshot
        if self.topology_edge_context:
            result["topology_edge_context"] = self.topology_edge_context
        return result


@dataclass
class ExternalAgentResponse:
    """Response from external agent."""

    response_text: str = ""
    explanation: str | None = None
    debug: dict[str, Any] | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    error: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExternalAgentResponse:
        """Create from dictionary."""
        return cls(
            response_text=data.get("response_text", ""),
            explanation=data.get("explanation"),
            debug=data.get("debug"),
            confidence=data.get("confidence"),
            latency_ms=data.get("latency_ms"),
            error=data.get("error"),
        )


@dataclass
class ExternalAgentMetrics:
    """Metrics for external agent performance."""

    # Response Quality
    persona_consistency: float = 0.0
    conversation_coherence: float = 0.0
    instruction_following: float = 0.0

    # Operational
    latency_p50_ms: int = 0
    latency_p99_ms: int = 0
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    circuit_state: str = "CLOSED"

    # Comparative (A/B)
    preference_score: float = 0.0
    elo_rating: float = 1000.0

    # Tracking
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    latencies: list[int] = field(default_factory=list)

    def record_call(self, latency_ms: int, success: bool) -> None:
        """Record a call result."""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
            self.latencies.append(latency_ms)
            # Keep only last 1000 latencies
            if len(self.latencies) > 1000:
                self.latencies = self.latencies[-1000:]
            self._update_percentiles()
        else:
            self.failed_calls += 1

        self.error_rate = self.failed_calls / self.total_calls if self.total_calls > 0 else 0.0

    def _update_percentiles(self) -> None:
        """Update latency percentiles."""
        if not self.latencies:
            return
        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        self.latency_p50_ms = sorted_lat[int(n * 0.5)]
        self.latency_p99_ms = sorted_lat[int(n * 0.99)] if n >= 100 else sorted_lat[-1]


class ExternalAgentProvider:
    """Provider for external agent HTTP endpoints.

    Handles:
    - HTTP communication with external endpoints
    - Privacy-tiered context building
    - Circuit breaker for reliability
    - Concurrency limiting
    - Retry with exponential backoff
    - Metrics collection
    """

    def __init__(
        self,
        config: ExternalAgentConfig,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ) -> None:
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            config=circuit_breaker_config or CircuitBreakerConfig()
        )
        self.metrics = ExternalAgentMetrics()
        self._semaphore = asyncio.Semaphore(config.max_inflight_requests)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            headers["Content-Type"] = "application/json"

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _compute_hash(self, data: Any) -> str:
        """Compute SHA256 hash of data."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return f"sha256:{hashlib.sha256(json_str.encode()).hexdigest()[:16]}"

    def _build_persona_context(
        self,
        agent: Agent,
        privacy_tier: PrivacyTier,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Build persona context based on privacy tier.

        Returns:
            Tuple of (persona_ref, persona_snapshot or None)
        """
        # Always include persona reference
        persona_ref = {
            "persona_id": agent.id,
            "persona_version": "1.0",
            "persona_hash": self._compute_hash({
                "name": agent.name,
                "traits": getattr(agent, "traits", {}),
            }),
        }

        if privacy_tier == PrivacyTier.MINIMAL:
            return persona_ref, None

        # Build persona snapshot based on tier
        snapshot: dict[str, Any] = {"name": agent.name}

        if hasattr(agent, "traits") and agent.traits:
            traits = agent.traits
            if hasattr(traits, "to_dict"):
                snapshot["traits"] = traits.to_dict()
            elif isinstance(traits, dict):
                snapshot["traits"] = traits
            else:
                snapshot["traits"] = {}

        if privacy_tier == PrivacyTier.FULL:
            if hasattr(agent, "background"):
                snapshot["background"] = agent.background or ""
            if hasattr(agent, "system_prompt"):
                snapshot["system_prompt"] = agent.system_prompt or ""

        return persona_ref, snapshot

    def _build_conversation_context(
        self,
        conversation_history: list[dict[str, Any]],
        token_budget: int = 4000,
        max_chars: int = 16000,
    ) -> dict[str, Any]:
        """Build bounded conversation context."""
        # Take last k turns that fit within budget
        last_k_turns = []
        total_chars = 0

        for turn in reversed(conversation_history):
            content = turn.get("content", "")
            if total_chars + len(content) > max_chars:
                break
            last_k_turns.insert(0, {
                "sender": turn.get("sender", ""),
                "content": content,
                "timestamp": turn.get("timestamp", ""),
            })
            total_chars += len(content)

        return {
            "last_k_turns": last_k_turns,
            "conversation_summary": "",  # TODO: Generate summary
            "token_budget": token_budget,
            "max_context_chars": max_chars,
        }

    def build_request(
        self,
        agent: Agent,
        stimulus: str,
        conversation_history: list[dict[str, Any]],
        run_id: str = "",
        turn_id: str = "",
        simulation_config: dict[str, Any] | None = None,
        topology_neighbors: list[str] | None = None,
    ) -> ExternalAgentRequest:
        """Build external agent request.

        Args:
            agent: The agent being replaced
            stimulus: Current message/stimulus
            conversation_history: Previous conversation turns
            run_id: Simulation run ID
            turn_id: Current turn ID
            simulation_config: Simulation configuration for hashing
            topology_neighbors: Agents this agent can message

        Returns:
            ExternalAgentRequest ready to send
        """
        persona_ref, persona_snapshot = self._build_persona_context(
            agent, self.config.privacy_tier
        )

        request = ExternalAgentRequest(
            request_id=str(uuid.uuid4()),
            run_id=run_id or str(uuid.uuid4()),
            turn_id=turn_id or str(uuid.uuid4()),
            message_id=str(uuid.uuid4()),
            simulation_config_hash=self._compute_hash(simulation_config or {}),
            persona_hash=persona_ref["persona_hash"],
            agent_id=agent.id,
            persona_ref=persona_ref,
            persona_snapshot=persona_snapshot,
            conversation_context=self._build_conversation_context(conversation_history),
            current_stimulus=stimulus,
            timeout_ms=self.config.timeout_seconds * 1000,
        )

        if topology_neighbors:
            request.topology_edge_context = {"can_message": topology_neighbors}

        return request

    async def generate_response(
        self,
        agent: Agent,
        stimulus: str,
        conversation_history: list[dict[str, Any]] | None = None,
        run_id: str = "",
        turn_id: str = "",
        simulation_config: dict[str, Any] | None = None,
    ) -> tuple[str, ExternalAgentMetrics]:
        """Generate a response from the external agent.

        Args:
            agent: The agent being replaced
            stimulus: Current message/stimulus
            conversation_history: Previous conversation turns
            run_id: Simulation run ID
            turn_id: Current turn ID
            simulation_config: Simulation configuration

        Returns:
            Tuple of (response_text, metrics)

        Raises:
            ExternalAgentError: If request fails and fallback is disabled
        """
        self.metrics.circuit_state = self.circuit_breaker.state.value

        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            if self.config.fallback_to_simulated:
                return "", self.metrics
            raise ExternalAgentError(
                "Circuit breaker OPEN",
                code="CIRCUIT_OPEN",
            )

        # Build request
        request = self.build_request(
            agent=agent,
            stimulus=stimulus,
            conversation_history=conversation_history or [],
            run_id=run_id,
            turn_id=turn_id,
            simulation_config=simulation_config,
        )

        # Execute with retry
        response_text = ""
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                response_text = await self._execute_request(request)
                self.circuit_breaker.record_success()
                return response_text, self.metrics
            except ExternalAgentError as e:
                last_error = e
                if e.code == "RATE_LIMITED":
                    # Exponential backoff
                    backoff = self.config.retry_backoff_base * (2 ** attempt)
                    await asyncio.sleep(backoff)
                else:
                    break  # Don't retry non-rate-limit errors

        # All retries failed
        self.circuit_breaker.record_failure()

        if self.config.fallback_to_simulated:
            return "", self.metrics

        raise last_error or ExternalAgentError("Request failed", code="UNKNOWN")

    async def _execute_request(self, request: ExternalAgentRequest) -> str:
        """Execute a single request to the external endpoint."""
        async with self._semaphore:
            client = await self._get_client()
            start_time = time.time()

            try:
                response = await client.post(
                    self.config.endpoint_url,
                    json=request.to_dict(),
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 429:
                    self.metrics.record_call(latency_ms, False)
                    raise ExternalAgentError(
                        "Rate limited",
                        code="RATE_LIMITED",
                    )

                if response.status_code >= 400:
                    self.metrics.record_call(latency_ms, False)
                    raise ExternalAgentError(
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        code="HTTP_ERROR",
                    )

                data = response.json()
                agent_response = ExternalAgentResponse.from_dict(data)

                if agent_response.error:
                    self.metrics.record_call(latency_ms, False)
                    raise ExternalAgentError(
                        agent_response.error.get("message", "Unknown error"),
                        code=agent_response.error.get("code", "EXTERNAL_ERROR"),
                    )

                self.metrics.record_call(latency_ms, True)
                return agent_response.response_text

            except httpx.TimeoutException:
                latency_ms = int((time.time() - start_time) * 1000)
                self.metrics.record_call(latency_ms, False)
                self.metrics.timeout_rate = (
                    sum(1 for lat in self.metrics.latencies if lat >= self.config.timeout_seconds * 1000)
                    / len(self.metrics.latencies)
                    if self.metrics.latencies else 0.0
                )
                raise ExternalAgentError("Request timed out", code="TIMEOUT")

            except httpx.RequestError as e:
                latency_ms = int((time.time() - start_time) * 1000)
                self.metrics.record_call(latency_ms, False)
                raise ExternalAgentError(str(e), code="CONNECTION_ERROR")

    async def health_check(self) -> bool:
        """Check if the external endpoint is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            client = await self._get_client()
            # Try to reach the endpoint with a minimal request
            response = await client.get(
                self.config.endpoint_url.replace("/respond", "/health"),
                timeout=5.0,
            )
            return response.status_code < 400
        except Exception:
            return False


class ExternalAgentError(Exception):
    """Error from external agent endpoint."""

    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class InjectedAgentManager:
    """Manages injected external agents for a simulation."""

    def __init__(self) -> None:
        self._providers: dict[str, ExternalAgentProvider] = {}

    def inject(
        self,
        agent_id: str,
        config: ExternalAgentConfig,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ) -> ExternalAgentProvider:
        """Inject an external agent.

        Args:
            agent_id: ID of agent to replace
            config: External agent configuration
            circuit_breaker_config: Optional circuit breaker config

        Returns:
            The provider instance
        """
        provider = ExternalAgentProvider(config, circuit_breaker_config)
        self._providers[agent_id] = provider
        return provider

    def remove(self, agent_id: str) -> bool:
        """Remove an injected agent.

        Args:
            agent_id: ID of agent to remove

        Returns:
            True if removed, False if not found
        """
        if agent_id in self._providers:
            del self._providers[agent_id]
            return True
        return False

    def get(self, agent_id: str) -> ExternalAgentProvider | None:
        """Get provider for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Provider or None if not injected
        """
        return self._providers.get(agent_id)

    def is_injected(self, agent_id: str) -> bool:
        """Check if an agent is injected.

        Args:
            agent_id: Agent ID

        Returns:
            True if injected
        """
        return agent_id in self._providers

    def list_injected(self) -> list[str]:
        """List all injected agent IDs."""
        return list(self._providers.keys())

    def get_all_metrics(self) -> dict[str, ExternalAgentMetrics]:
        """Get metrics for all injected agents."""
        return {
            agent_id: provider.metrics
            for agent_id, provider in self._providers.items()
        }

    async def close_all(self) -> None:
        """Close all provider connections."""
        for provider in self._providers.values():
            await provider.close()
