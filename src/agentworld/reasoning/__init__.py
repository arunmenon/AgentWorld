"""Reasoning and prompt visibility per ADR-015.

This module provides configurable visibility for agent reasoning including:
- VisibilityLevel: Control what's exposed (NONE, SUMMARY, DETAILED, FULL, DEBUG)
- VisibilityConfig: Configure capture and redaction settings
- ReasoningTrace: Structured trace of agent reasoning steps
- ReasoningCapture: Context manager for capturing reasoning during execution
- PrivacyManager: Redact sensitive information
- CLIReasoningDisplay: Display reasoning in CLI
- ReasoningStorage: Store and export reasoning traces
"""

from agentworld.reasoning.capture import ReasoningCapture
from agentworld.reasoning.config import VisibilityConfig, VisibilityLevel
from agentworld.reasoning.display import (
    CLIReasoningDisplay,
    ReasoningEventType,
    create_reasoning_event,
    thinking_end_event,
    thinking_start_event,
    thinking_step_event,
)
from agentworld.reasoning.privacy import PrivacyManager
from agentworld.reasoning.storage import ReasoningStorage
from agentworld.reasoning.trace import ReasoningStep, ReasoningTrace

__all__ = [
    # Config
    "VisibilityLevel",
    "VisibilityConfig",
    # Trace
    "ReasoningStep",
    "ReasoningTrace",
    # Capture
    "ReasoningCapture",
    # Privacy
    "PrivacyManager",
    # Display
    "CLIReasoningDisplay",
    "ReasoningEventType",
    "create_reasoning_event",
    "thinking_start_event",
    "thinking_step_event",
    "thinking_end_event",
    # Storage
    "ReasoningStorage",
]
