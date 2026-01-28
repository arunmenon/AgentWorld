"""Dual-control task definitions and coordination tracking.

This module implements τ²-bench style dual-control evaluation per ADR-020.1:
- DualControlTaskDefinition: Tasks requiring agent-user coordination
- CoordinationEvent: Tracks instruction → action handoffs
- CoordinationMetrics: Measures coordination success and efficiency
- InstructionTemplate: Structured instruction matching

Per ADR-020.1: https://arxiv.org/abs/2506.07982
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from agentworld.apps.definition import AgentRole


# ==============================================================================
# Instruction Templates (for handoff detection)
# ==============================================================================


@dataclass
class InstructionTemplate:
    """Structured instruction matching for coordination detection.

    More reliable than free-form NLU. Uses tiered matching:
    1. Keyword matching (fast, high precision)
    2. Semantic similarity (fallback for paraphrasing)

    Per ADR-020.1.
    """

    template_id: str
    keywords: list[str]        # Action keywords (e.g., ["toggle", "turn", "switch"])
    target_keywords: list[str] # Target object keywords (e.g., ["data", "mobile data"])
    semantic_embedding: list[float] | None = None  # Optional semantic fallback
    semantic_threshold: float = 0.85

    def matches(self, instruction_text: str) -> tuple[bool, float]:
        """Match instruction text against template.

        Returns:
            Tuple of (matched, confidence)
        """
        text_lower = instruction_text.lower()

        # Tier 1: Keyword matching (fast, high precision)
        action_keyword_found = any(kw in text_lower for kw in self.keywords)
        target_keyword_found = any(kw in text_lower for kw in self.target_keywords)

        if action_keyword_found and target_keyword_found:
            return True, 0.95  # High confidence keyword match

        # Tier 2: Semantic similarity would go here
        # (requires embedding model integration)
        if self.semantic_embedding:
            # Placeholder for semantic matching
            # In production, would compute cosine similarity
            pass

        return False, 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "keywords": self.keywords,
            "target_keywords": self.target_keywords,
            "semantic_threshold": self.semantic_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstructionTemplate":
        """Create from dictionary."""
        return cls(
            template_id=data["template_id"],
            keywords=data.get("keywords", []),
            target_keywords=data.get("target_keywords", []),
            semantic_embedding=data.get("semantic_embedding"),
            semantic_threshold=data.get("semantic_threshold", 0.85),
        )


# ==============================================================================
# Coordination Handoff
# ==============================================================================


@dataclass
class CoordinationHandoff:
    """A required coordination point in a dual-control task.

    Defines what instruction the agent should give and what action
    the user should take in response.

    Per ADR-020.1.
    """

    handoff_id: str
    from_role: AgentRole
    to_role: AgentRole
    expected_action: str  # Action the user should take
    description: str = ""

    # Matching options
    instruction_pattern: str | None = None  # Regex pattern (legacy)
    instruction_template: InstructionTemplate | None = None  # Structured matching

    def matches_instruction(self, instruction_text: str) -> tuple[bool, float]:
        """Check if instruction text matches this handoff.

        Returns:
            Tuple of (matched, confidence)
        """
        # Try structured template first
        if self.instruction_template:
            matched, confidence = self.instruction_template.matches(instruction_text)
            if matched:
                return True, confidence

        # Fall back to regex pattern
        if self.instruction_pattern:
            if re.search(self.instruction_pattern, instruction_text, re.IGNORECASE):
                return True, 0.90

        return False, 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "handoff_id": self.handoff_id,
            "from_role": self.from_role.value if isinstance(self.from_role, AgentRole) else self.from_role,
            "to_role": self.to_role.value if isinstance(self.to_role, AgentRole) else self.to_role,
            "expected_action": self.expected_action,
            "description": self.description,
        }
        if self.instruction_pattern:
            result["instruction_pattern"] = self.instruction_pattern
        if self.instruction_template:
            result["instruction_template"] = self.instruction_template.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoordinationHandoff":
        """Create from dictionary."""
        from_role = data.get("from_role", "service_agent")
        to_role = data.get("to_role", "customer")

        template_data = data.get("instruction_template")
        template = InstructionTemplate.from_dict(template_data) if template_data else None

        return cls(
            handoff_id=data["handoff_id"],
            from_role=AgentRole(from_role) if isinstance(from_role, str) else from_role,
            to_role=AgentRole(to_role) if isinstance(to_role, str) else to_role,
            expected_action=data["expected_action"],
            description=data.get("description", ""),
            instruction_pattern=data.get("instruction_pattern"),
            instruction_template=template,
        )


# ==============================================================================
# Dual Control Task Definition
# ==============================================================================


@dataclass
class DualControlTaskDefinition:
    """Task requiring agent-user coordination.

    Extends TaskDefinition for τ²-bench style dual-control evaluation.

    The key insight: Agent guides a user who has device access.
    Agent cannot directly execute device actions.

    Per ADR-020.1.
    """

    # Required fields (no defaults) must come first
    task_id: str
    name: str
    description: str
    domain: str
    difficulty: str

    # Simulation setup
    simulation_config: dict[str, Any]

    # Agent-side (e.g., service agent)
    agent_id: str
    agent_role: AgentRole
    agent_instruction: str
    agent_apps: list[str]  # Apps the agent can access

    # User-side (e.g., customer)
    user_id: str
    user_role: AgentRole
    user_instruction: str  # What user is trying to achieve
    user_apps: list[str]   # Apps the user can access

    # Fields with defaults must come after required fields
    agent_initial_state: dict[str, Any] = field(default_factory=dict)
    agent_goal_state: dict[str, Any] = field(default_factory=dict)
    user_initial_state: dict[str, Any] = field(default_factory=dict)
    user_goal_state: dict[str, Any] = field(default_factory=dict)

    # Coordination requirements
    required_handoffs: list[CoordinationHandoff] = field(default_factory=list)

    # Constraints
    max_turns: int = 20
    expected_coordination_count: int = 0

    # Metadata
    id: str | None = None
    is_active: bool = True
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "simulation_config": self.simulation_config,
            "agent_id": self.agent_id,
            "agent_role": self.agent_role.value if isinstance(self.agent_role, AgentRole) else self.agent_role,
            "agent_instruction": self.agent_instruction,
            "agent_apps": self.agent_apps,
            "agent_initial_state": self.agent_initial_state,
            "agent_goal_state": self.agent_goal_state,
            "user_id": self.user_id,
            "user_role": self.user_role.value if isinstance(self.user_role, AgentRole) else self.user_role,
            "user_instruction": self.user_instruction,
            "user_apps": self.user_apps,
            "user_initial_state": self.user_initial_state,
            "user_goal_state": self.user_goal_state,
            "required_handoffs": [h.to_dict() for h in self.required_handoffs],
            "max_turns": self.max_turns,
            "expected_coordination_count": self.expected_coordination_count,
            "is_active": self.is_active,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DualControlTaskDefinition":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        agent_role = data.get("agent_role", "service_agent")
        user_role = data.get("user_role", "customer")

        return cls(
            id=data.get("id"),
            task_id=data["task_id"],
            name=data["name"],
            description=data.get("description", ""),
            domain=data["domain"],
            difficulty=data["difficulty"],
            simulation_config=data.get("simulation_config", {}),
            agent_id=data["agent_id"],
            agent_role=AgentRole(agent_role) if isinstance(agent_role, str) else agent_role,
            agent_instruction=data["agent_instruction"],
            agent_apps=data.get("agent_apps", []),
            agent_initial_state=data.get("agent_initial_state", {}),
            agent_goal_state=data.get("agent_goal_state", {}),
            user_id=data["user_id"],
            user_role=AgentRole(user_role) if isinstance(user_role, str) else user_role,
            user_instruction=data["user_instruction"],
            user_apps=data.get("user_apps", []),
            user_initial_state=data.get("user_initial_state", {}),
            user_goal_state=data.get("user_goal_state", {}),
            required_handoffs=[
                CoordinationHandoff.from_dict(h)
                for h in data.get("required_handoffs", [])
            ],
            max_turns=data.get("max_turns", 20),
            expected_coordination_count=data.get("expected_coordination_count", 0),
            is_active=data.get("is_active", True),
            tags=data.get("tags", []),
            created_at=created_at,
            updated_at=updated_at,
        )


# ==============================================================================
# Coordination Events (runtime tracking)
# ==============================================================================


@dataclass
class CoordinationEvent:
    """Tracked coordination between agent and user.

    Records when an agent instructs a user and whether the user
    successfully completes the expected action.

    Per ADR-020.1.
    """

    event_id: str
    trial_id: str
    task_id: str

    # Who instructed
    instructor_id: str
    instructor_role: AgentRole
    instruction_text: str

    # Who acted (may be None if user didn't act)
    actor_id: str | None = None
    actor_role: AgentRole | None = None
    action_taken: str | None = None
    action_params: dict[str, Any] | None = None

    # Matching
    matched_handoff_id: str | None = None
    match_confidence: float = 0.0

    # Result
    handoff_successful: bool = False
    latency_turns: int = 0  # Turns between instruction and action

    # Metadata
    timestamp: datetime | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "trial_id": self.trial_id,
            "task_id": self.task_id,
            "instructor_id": self.instructor_id,
            "instructor_role": self.instructor_role.value if isinstance(self.instructor_role, AgentRole) else self.instructor_role,
            "instruction_text": self.instruction_text,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role.value if isinstance(self.actor_role, AgentRole) and self.actor_role else None,
            "action_taken": self.action_taken,
            "action_params": self.action_params,
            "matched_handoff_id": self.matched_handoff_id,
            "match_confidence": self.match_confidence,
            "handoff_successful": self.handoff_successful,
            "latency_turns": self.latency_turns,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoordinationEvent":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        instructor_role = data.get("instructor_role", "service_agent")
        actor_role = data.get("actor_role")

        return cls(
            id=data.get("id"),
            event_id=data["event_id"],
            trial_id=data["trial_id"],
            task_id=data["task_id"],
            instructor_id=data["instructor_id"],
            instructor_role=AgentRole(instructor_role) if isinstance(instructor_role, str) else instructor_role,
            instruction_text=data.get("instruction_text", ""),
            actor_id=data.get("actor_id"),
            actor_role=AgentRole(actor_role) if actor_role and isinstance(actor_role, str) else actor_role,
            action_taken=data.get("action_taken"),
            action_params=data.get("action_params"),
            matched_handoff_id=data.get("matched_handoff_id"),
            match_confidence=data.get("match_confidence", 0.0),
            handoff_successful=data.get("handoff_successful", False),
            latency_turns=data.get("latency_turns", 0),
            timestamp=timestamp,
        )


# ==============================================================================
# Coordination Metrics
# ==============================================================================


@dataclass
class CoordinationMetrics:
    """Metrics for dual-control evaluation.

    Aggregated metrics from coordination events.

    Per ADR-020.1.
    """

    task_id: str
    trial_id: str | None = None  # None for task-level aggregation

    # Coordination success
    total_handoffs_required: int = 0
    handoffs_completed: int = 0
    coordination_success_rate: float = 0.0

    # Efficiency
    avg_instruction_to_action_turns: float = 0.0
    unnecessary_user_actions: int = 0

    # Communication quality (LLM-judged, 0-1 scale)
    instruction_clarity_score: float | None = None
    user_confusion_count: int = 0

    # Events
    events: list[CoordinationEvent] = field(default_factory=list)

    # Metadata
    id: str | None = None
    computed_at: datetime | None = None

    @classmethod
    def from_events(
        cls,
        task_id: str,
        events: list[CoordinationEvent],
        required_handoffs: int,
        trial_id: str | None = None,
    ) -> "CoordinationMetrics":
        """Compute metrics from coordination events.

        Args:
            task_id: ID of the task
            events: List of coordination events
            required_handoffs: Number of required handoffs in task
            trial_id: Optional trial ID for trial-level metrics

        Returns:
            Computed CoordinationMetrics
        """
        successful = [e for e in events if e.handoff_successful]
        success_rate = len(successful) / required_handoffs if required_handoffs > 0 else 0.0

        # Calculate average latency
        latencies = [e.latency_turns for e in successful if e.latency_turns > 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return cls(
            task_id=task_id,
            trial_id=trial_id,
            total_handoffs_required=required_handoffs,
            handoffs_completed=len(successful),
            coordination_success_rate=success_rate,
            avg_instruction_to_action_turns=avg_latency,
            events=events,
            computed_at=datetime.now(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "trial_id": self.trial_id,
            "total_handoffs_required": self.total_handoffs_required,
            "handoffs_completed": self.handoffs_completed,
            "coordination_success_rate": self.coordination_success_rate,
            "avg_instruction_to_action_turns": self.avg_instruction_to_action_turns,
            "unnecessary_user_actions": self.unnecessary_user_actions,
            "instruction_clarity_score": self.instruction_clarity_score,
            "user_confusion_count": self.user_confusion_count,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }


# ==============================================================================
# Solo vs Dual Comparison
# ==============================================================================


@dataclass
class SoloDualComparison:
    """Compare same task in solo vs dual mode.

    The key finding from τ²-bench: ~25 point pass^1 drop when
    agents must guide users instead of acting directly.

    Per ADR-020.1.
    """

    task_id: str

    # Solo mode: Agent gets all info, acts directly
    solo_trials: int = 0
    solo_successes: int = 0
    solo_pass_1: float = 0.0
    solo_avg_steps: float = 0.0

    # Dual mode: Agent must guide user
    dual_trials: int = 0
    dual_successes: int = 0
    dual_pass_1: float = 0.0
    dual_avg_steps: float = 0.0

    # The gap (τ²-bench key finding)
    performance_drop: float = 0.0  # solo_pass_1 - dual_pass_1
    step_increase: float = 0.0     # dual_avg_steps - solo_avg_steps

    # Metadata
    id: str | None = None
    computed_at: datetime | None = None

    def compute_gaps(self) -> None:
        """Compute performance drop and step increase."""
        self.performance_drop = self.solo_pass_1 - self.dual_pass_1
        self.step_increase = self.dual_avg_steps - self.solo_avg_steps

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "solo_trials": self.solo_trials,
            "solo_successes": self.solo_successes,
            "solo_pass_1": self.solo_pass_1,
            "solo_avg_steps": self.solo_avg_steps,
            "dual_trials": self.dual_trials,
            "dual_successes": self.dual_successes,
            "dual_pass_1": self.dual_pass_1,
            "dual_avg_steps": self.dual_avg_steps,
            "performance_drop": self.performance_drop,
            "step_increase": self.step_increase,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SoloDualComparison":
        """Create from dictionary."""
        computed_at = data.get("computed_at")
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)

        return cls(
            id=data.get("id"),
            task_id=data["task_id"],
            solo_trials=data.get("solo_trials", 0),
            solo_successes=data.get("solo_successes", 0),
            solo_pass_1=data.get("solo_pass_1", 0.0),
            solo_avg_steps=data.get("solo_avg_steps", 0.0),
            dual_trials=data.get("dual_trials", 0),
            dual_successes=data.get("dual_successes", 0),
            dual_pass_1=data.get("dual_pass_1", 0.0),
            dual_avg_steps=data.get("dual_avg_steps", 0.0),
            performance_drop=data.get("performance_drop", 0.0),
            step_increase=data.get("step_increase", 0.0),
            computed_at=computed_at,
        )


# ==============================================================================
# Common Instruction Templates (ready-to-use)
# ==============================================================================

# Telecom domain templates
TOGGLE_DATA_TEMPLATE = InstructionTemplate(
    template_id="toggle_mobile_data",
    keywords=["toggle", "turn", "switch", "enable", "disable", "turn on", "turn off"],
    target_keywords=["data", "mobile data", "cellular", "internet", "connectivity"],
)

CHECK_STATUS_TEMPLATE = InstructionTemplate(
    template_id="check_status",
    keywords=["check", "look", "see", "view", "tell me", "what does", "read"],
    target_keywords=["status", "bar", "signal", "screen", "display", "icon"],
)

RESTART_DEVICE_TEMPLATE = InstructionTemplate(
    template_id="restart_device",
    keywords=["restart", "reboot", "turn off and on", "power cycle"],
    target_keywords=["device", "phone", "mobile", "handset"],
)

TOGGLE_AIRPLANE_TEMPLATE = InstructionTemplate(
    template_id="toggle_airplane_mode",
    keywords=["toggle", "turn", "switch", "enable", "disable"],
    target_keywords=["airplane", "flight mode", "aeroplane"],
)
