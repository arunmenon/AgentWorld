"""Privacy management for reasoning visibility per ADR-015."""

from __future__ import annotations

import re
from typing import Pattern

from agentworld.reasoning.config import VisibilityConfig
from agentworld.reasoning.trace import ReasoningStep, ReasoningTrace


class PrivacyManager:
    """Manage privacy aspects of reasoning visibility."""

    # Default patterns for common sensitive data
    DEFAULT_PATTERNS = {
        "api_keys": [
            r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style API keys
            r"Bearer\s+[a-zA-Z0-9\-_.]+",  # Bearer tokens
            r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9\-_.]+",  # Generic API keys
        ],
        "emails": [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ],
        "phone_numbers": [
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # US phone numbers
        ],
        "credit_cards": [
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        ],
        "ssn": [
            r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",  # US SSN
        ],
    }

    def __init__(self, config: VisibilityConfig | None = None) -> None:
        """
        Initialize privacy manager.

        Args:
            config: Visibility configuration with redaction settings
        """
        self.config = config or VisibilityConfig()
        self._redaction_patterns: list[Pattern] = self._compile_patterns()

    def _compile_patterns(self) -> list[Pattern]:
        """Compile redaction patterns from config."""
        patterns: list[Pattern] = []

        # Add API key patterns if enabled
        if self.config.redact_api_keys:
            for pattern in self.DEFAULT_PATTERNS["api_keys"]:
                patterns.append(re.compile(pattern, re.IGNORECASE))

        # Add custom patterns from config
        for custom in self.config.redact_custom_patterns:
            try:
                patterns.append(re.compile(custom))
            except re.error:
                # Skip invalid patterns
                pass

        return patterns

    def redact(self, text: str) -> str:
        """
        Redact sensitive information from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        for pattern in self._redaction_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text

    def redact_with_type(self, text: str) -> str:
        """
        Redact sensitive information with type indicators.

        Args:
            text: Text to redact

        Returns:
            Redacted text with type indicators
        """
        # Redact API keys
        if self.config.redact_api_keys:
            text = re.sub(r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]", text)
            text = re.sub(
                r"Bearer\s+[a-zA-Z0-9\-_.]+", "[REDACTED_BEARER]", text, flags=re.I
            )

        # Redact emails
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[REDACTED_EMAIL]",
            text,
        )

        # Apply custom patterns
        for pattern in self.config.redact_custom_patterns:
            try:
                text = re.sub(pattern, "[REDACTED]", text)
            except re.error:
                pass

        return text

    def should_capture(self, content_type: str) -> bool:
        """
        Check if content type should be captured.

        Args:
            content_type: Type of content to check

        Returns:
            True if content should be captured
        """
        mapping = {
            "system_prompt": self.config.capture_system_prompts,
            "chain_of_thought": self.config.capture_chain_of_thought,
            "tool_call": self.config.capture_tool_calls,
            "memory_retrieval": self.config.capture_memory_retrieval,
        }
        return mapping.get(content_type, True)

    def filter_step(self, step: ReasoningStep) -> ReasoningStep:
        """
        Filter a reasoning step for privacy.

        Args:
            step: Step to filter

        Returns:
            Filtered step with redacted content
        """
        return ReasoningStep(
            step_type=step.step_type,
            timestamp=step.timestamp,
            content=self.redact(step.content),
            metadata={
                k: v
                for k, v in step.metadata.items()
                if k not in ("raw_prompt", "api_key", "password", "secret")
            },
        )

    def filter_trace(self, trace: ReasoningTrace) -> ReasoningTrace:
        """
        Filter trace for export based on privacy settings.

        Args:
            trace: Trace to filter

        Returns:
            Filtered trace with redacted content
        """
        filtered_steps = [self.filter_step(step) for step in trace.steps]

        return ReasoningTrace(
            agent_id=trace.agent_id,
            simulation_step=trace.simulation_step,
            action_id=trace.action_id,
            started_at=trace.started_at,
            completed_at=trace.completed_at,
            steps=filtered_steps,
            summary=self.redact(trace.summary) if trace.summary else None,
            final_action=self.redact(trace.final_action) if trace.final_action else None,
            tokens_used=trace.tokens_used,
            latency_ms=trace.latency_ms,
        )

    def add_pattern(self, pattern: str) -> bool:
        """
        Add a custom redaction pattern.

        Args:
            pattern: Regex pattern to add

        Returns:
            True if pattern was added successfully
        """
        try:
            compiled = re.compile(pattern)
            self._redaction_patterns.append(compiled)
            self.config.redact_custom_patterns.append(pattern)
            return True
        except re.error:
            return False

    def remove_pattern(self, pattern: str) -> bool:
        """
        Remove a custom redaction pattern.

        Args:
            pattern: Pattern to remove

        Returns:
            True if pattern was removed
        """
        if pattern in self.config.redact_custom_patterns:
            self.config.redact_custom_patterns.remove(pattern)
            self._redaction_patterns = self._compile_patterns()
            return True
        return False
