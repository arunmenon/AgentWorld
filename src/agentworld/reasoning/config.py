"""Visibility configuration for reasoning traces per ADR-015."""

from dataclasses import dataclass, field
from enum import Enum


class VisibilityLevel(str, Enum):
    """Visibility levels for reasoning and prompts."""

    NONE = "none"  # No internal details exposed
    SUMMARY = "summary"  # High-level summaries only
    DETAILED = "detailed"  # Full reasoning, redacted prompts
    FULL = "full"  # Everything including raw prompts
    DEBUG = "debug"  # Full + internal scores, embeddings

    def __lt__(self, other: "VisibilityLevel") -> bool:
        """Compare visibility levels for ordering."""
        order = [
            VisibilityLevel.NONE,
            VisibilityLevel.SUMMARY,
            VisibilityLevel.DETAILED,
            VisibilityLevel.FULL,
            VisibilityLevel.DEBUG,
        ]
        return order.index(self) < order.index(other)

    def __le__(self, other: "VisibilityLevel") -> bool:
        return self == other or self < other


@dataclass
class VisibilityConfig:
    """Configuration for reasoning visibility."""

    # Live display (CLI/Web)
    live_visibility: VisibilityLevel = VisibilityLevel.SUMMARY

    # Logging
    log_visibility: VisibilityLevel = VisibilityLevel.DETAILED

    # Export/persistence
    export_visibility: VisibilityLevel = VisibilityLevel.SUMMARY

    # What to capture
    capture_system_prompts: bool = True
    capture_chain_of_thought: bool = True
    capture_tool_calls: bool = True
    capture_memory_retrieval: bool = True

    # Redaction
    redact_api_keys: bool = True
    redact_custom_patterns: list[str] = field(default_factory=list)

    # Display options
    show_thinking_indicator: bool = True
    show_tool_calls: bool = True
    max_content_preview: int = 100

    @classmethod
    def from_dict(cls, data: dict) -> "VisibilityConfig":
        """Create config from dictionary."""
        config = cls()

        if "live" in data:
            if "level" in data["live"]:
                config.live_visibility = VisibilityLevel(data["live"]["level"])
            if "show_thinking" in data["live"]:
                config.show_thinking_indicator = data["live"]["show_thinking"]
            if "show_tool_calls" in data["live"]:
                config.show_tool_calls = data["live"]["show_tool_calls"]

        if "logging" in data:
            if "level" in data["logging"]:
                config.log_visibility = VisibilityLevel(data["logging"]["level"])
            if "include_prompts" in data["logging"]:
                config.capture_system_prompts = data["logging"]["include_prompts"]

        if "export" in data:
            if "level" in data["export"]:
                config.export_visibility = VisibilityLevel(data["export"]["level"])

        if "capture" in data:
            capture = data["capture"]
            if "system_prompts" in capture:
                config.capture_system_prompts = capture["system_prompts"]
            if "chain_of_thought" in capture:
                config.capture_chain_of_thought = capture["chain_of_thought"]
            if "tool_calls" in capture:
                config.capture_tool_calls = capture["tool_calls"]
            if "memory_retrieval" in capture:
                config.capture_memory_retrieval = capture["memory_retrieval"]

        if "redaction" in data:
            redaction = data["redaction"]
            if "api_keys" in redaction:
                config.redact_api_keys = redaction["api_keys"]
            if "custom_patterns" in redaction:
                config.redact_custom_patterns = redaction["custom_patterns"]

        return config

    def to_dict(self) -> dict:
        """Export config to dictionary."""
        return {
            "live": {
                "level": self.live_visibility.value,
                "show_thinking": self.show_thinking_indicator,
                "show_tool_calls": self.show_tool_calls,
            },
            "logging": {
                "level": self.log_visibility.value,
                "include_prompts": self.capture_system_prompts,
            },
            "export": {
                "level": self.export_visibility.value,
            },
            "capture": {
                "system_prompts": self.capture_system_prompts,
                "chain_of_thought": self.capture_chain_of_thought,
                "tool_calls": self.capture_tool_calls,
                "memory_retrieval": self.capture_memory_retrieval,
            },
            "redaction": {
                "api_keys": self.redact_api_keys,
                "custom_patterns": self.redact_custom_patterns,
            },
        }
