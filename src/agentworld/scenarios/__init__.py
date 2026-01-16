"""Scenario implementations for AgentWorld.

This module provides structured scenarios for common use cases:
- Focus groups for product testing
- Interviews for user research
- Surveys for data collection
- Data generation for training
- Debates for perspective generation
"""

from agentworld.scenarios.base import (
    Scenario,
    ScenarioConfig,
    ScenarioResult,
    ScenarioStatus,
    AgentResponse,
    SystemEvent,
)
from agentworld.scenarios.moderator import (
    ModeratorConfig,
    ModeratorRole,
    create_moderator_agent,
)
from agentworld.scenarios.stimulus import (
    Stimulus,
    StimulusType,
    StimulusInjector,
)
from agentworld.scenarios.focus_group import (
    FocusGroupConfig,
    FocusGroupScenario,
    QuestionResult,
    FocusGroupResult,
)
from agentworld.scenarios.data_generation import (
    DataGenerationConfig,
    DataGenerationScenario,
    DataGenerationResult,
    GeneratedConversation,
    ConversationTurn,
    create_data_generation,
    DataSafetyFilter,
    DataExporter,
    QAPair,
    DebateResult,
    generate_qa_pairs,
    generate_debate,
)

__all__ = [
    # Base
    "Scenario",
    "ScenarioConfig",
    "ScenarioResult",
    "ScenarioStatus",
    "AgentResponse",
    "SystemEvent",
    # Moderator
    "ModeratorConfig",
    "ModeratorRole",
    "create_moderator_agent",
    # Stimulus
    "Stimulus",
    "StimulusType",
    "StimulusInjector",
    # Focus Group
    "FocusGroupConfig",
    "FocusGroupScenario",
    "QuestionResult",
    "FocusGroupResult",
    # Data Generation
    "DataGenerationConfig",
    "DataGenerationScenario",
    "DataGenerationResult",
    "GeneratedConversation",
    "ConversationTurn",
    "create_data_generation",
    "DataSafetyFilter",
    "DataExporter",
    "QAPair",
    "DebateResult",
    "generate_qa_pairs",
    "generate_debate",
]
