"""Coordination tracking for dual-control evaluation.

This module monitors simulations to detect and track coordination events
between agents and users in dual-control scenarios.

Per ADR-020.1.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agentworld.apps.definition import AgentRole
from agentworld.tasks.dual_control import (
    CoordinationEvent,
    CoordinationHandoff,
    CoordinationMetrics,
    DualControlTaskDefinition,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Pending Instruction
# ==============================================================================


@dataclass
class PendingInstruction:
    """An instruction waiting for user action.

    Tracks when an agent gives an instruction and what action
    is expected from the user.
    """

    instruction_id: str
    instructor_id: str
    instructor_role: AgentRole
    instruction_text: str
    expected_action: str
    matched_handoff_id: str | None
    match_confidence: float
    turn_number: int
    timestamp: datetime


# ==============================================================================
# Coordination Tracker
# ==============================================================================


class CoordinationTracker:
    """Tracks coordination events in a dual-control simulation.

    Monitors agent messages for instructions and user app actions
    to detect successful handoffs.

    Per ADR-020.1.

    Usage:
        tracker = CoordinationTracker(task_definition)

        # On each agent message
        tracker.on_agent_message(agent_id, message_text, turn_number)

        # On each app action
        tracker.on_app_action(agent_id, app_id, action_name, params, turn_number)

        # Get metrics
        metrics = tracker.get_metrics()
    """

    def __init__(
        self,
        task: DualControlTaskDefinition,
        trial_id: str | None = None,
    ):
        """Initialize tracker for a dual-control task.

        Args:
            task: The dual-control task definition
            trial_id: Optional trial ID for tracking
        """
        self._task = task
        self._trial_id = trial_id or str(uuid.uuid4())

        # Track agent roles
        self._agent_roles: dict[str, AgentRole] = {
            task.agent_id: task.agent_role,
            task.user_id: task.user_role,
        }

        # Pending instructions waiting for user action
        self._pending_instructions: list[PendingInstruction] = []

        # Recorded coordination events
        self._events: list[CoordinationEvent] = []

        # Track which handoffs have been completed
        self._completed_handoffs: set[str] = set()

    @property
    def task_id(self) -> str:
        """Get task ID."""
        return self._task.task_id

    @property
    def trial_id(self) -> str:
        """Get trial ID."""
        return self._trial_id

    @property
    def events(self) -> list[CoordinationEvent]:
        """Get recorded coordination events."""
        return list(self._events)

    def set_agent_role(self, agent_id: str, role: AgentRole | str) -> None:
        """Set an agent's role.

        Args:
            agent_id: Agent ID
            role: Agent's role
        """
        if isinstance(role, str):
            role = AgentRole(role)
        self._agent_roles[agent_id] = role

    def get_agent_role(self, agent_id: str) -> AgentRole | None:
        """Get an agent's role."""
        return self._agent_roles.get(agent_id)

    def on_agent_message(
        self,
        agent_id: str,
        message_text: str,
        turn_number: int,
    ) -> list[PendingInstruction]:
        """Process an agent message for potential instructions.

        Detects if the message contains instructions that match
        required handoffs in the task definition.

        Args:
            agent_id: ID of the agent sending the message
            message_text: The message content
            turn_number: Current simulation turn

        Returns:
            List of detected pending instructions
        """
        role = self._agent_roles.get(agent_id)
        if not role:
            return []

        detected = []

        # Check each required handoff
        for handoff in self._task.required_handoffs:
            # Only match if this agent has the instructor role
            if handoff.from_role != role:
                continue

            # Check if instruction matches
            matched, confidence = handoff.matches_instruction(message_text)
            if matched:
                instruction = PendingInstruction(
                    instruction_id=str(uuid.uuid4()),
                    instructor_id=agent_id,
                    instructor_role=role,
                    instruction_text=message_text,
                    expected_action=handoff.expected_action,
                    matched_handoff_id=handoff.handoff_id,
                    match_confidence=confidence,
                    turn_number=turn_number,
                    timestamp=datetime.now(),
                )
                self._pending_instructions.append(instruction)
                detected.append(instruction)

                logger.debug(
                    f"Detected instruction from {agent_id} for handoff "
                    f"'{handoff.handoff_id}' (confidence: {confidence:.2f})"
                )

        return detected

    def on_app_action(
        self,
        agent_id: str,
        app_id: str,
        action_name: str,
        params: dict[str, Any],
        turn_number: int,
    ) -> CoordinationEvent | None:
        """Process an app action for potential handoff completion.

        Checks if this action completes a pending instruction.

        Args:
            agent_id: ID of the agent performing the action
            app_id: ID of the app
            action_name: Name of the action
            params: Action parameters
            turn_number: Current simulation turn

        Returns:
            CoordinationEvent if handoff was completed, None otherwise
        """
        role = self._agent_roles.get(agent_id)
        if not role:
            return None

        # Find matching pending instruction
        for instruction in self._pending_instructions:
            # Check if this action matches the expected action
            if instruction.expected_action != action_name:
                continue

            # Check if this agent has the expected actor role
            handoff = self._get_handoff(instruction.matched_handoff_id)
            if handoff and handoff.to_role != role:
                continue

            # Match found - create coordination event
            latency = turn_number - instruction.turn_number

            event = CoordinationEvent(
                event_id=str(uuid.uuid4()),
                trial_id=self._trial_id,
                task_id=self._task.task_id,
                instructor_id=instruction.instructor_id,
                instructor_role=instruction.instructor_role,
                instruction_text=instruction.instruction_text,
                actor_id=agent_id,
                actor_role=role,
                action_taken=action_name,
                action_params=params,
                matched_handoff_id=instruction.matched_handoff_id,
                match_confidence=instruction.match_confidence,
                handoff_successful=True,
                latency_turns=latency,
                timestamp=datetime.now(),
            )

            self._events.append(event)

            # Mark handoff as completed
            if instruction.matched_handoff_id:
                self._completed_handoffs.add(instruction.matched_handoff_id)

            # Remove from pending
            self._pending_instructions.remove(instruction)

            logger.info(
                f"Coordination completed: {instruction.instructor_id} -> {agent_id}, "
                f"action: {action_name}, latency: {latency} turns"
            )

            return event

        return None

    def _get_handoff(self, handoff_id: str | None) -> CoordinationHandoff | None:
        """Get a handoff definition by ID."""
        if not handoff_id:
            return None
        for handoff in self._task.required_handoffs:
            if handoff.handoff_id == handoff_id:
                return handoff
        return None

    def get_pending_instructions(self) -> list[PendingInstruction]:
        """Get currently pending instructions."""
        return list(self._pending_instructions)

    def get_completed_handoffs(self) -> set[str]:
        """Get IDs of completed handoffs."""
        return set(self._completed_handoffs)

    def get_missing_handoffs(self) -> list[str]:
        """Get IDs of required handoffs not yet completed."""
        required = {h.handoff_id for h in self._task.required_handoffs}
        return list(required - self._completed_handoffs)

    def get_metrics(self) -> CoordinationMetrics:
        """Compute coordination metrics from tracked events.

        Returns:
            CoordinationMetrics with aggregated statistics
        """
        required_count = len(self._task.required_handoffs)

        return CoordinationMetrics.from_events(
            task_id=self._task.task_id,
            events=self._events,
            required_handoffs=required_count,
            trial_id=self._trial_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize tracker state to dictionary."""
        return {
            "task_id": self._task.task_id,
            "trial_id": self._trial_id,
            "agent_roles": {k: v.value for k, v in self._agent_roles.items()},
            "events": [e.to_dict() for e in self._events],
            "completed_handoffs": list(self._completed_handoffs),
            "pending_instructions": [
                {
                    "instruction_id": p.instruction_id,
                    "instructor_id": p.instructor_id,
                    "instruction_text": p.instruction_text,
                    "expected_action": p.expected_action,
                    "turn_number": p.turn_number,
                }
                for p in self._pending_instructions
            ],
        }


# ==============================================================================
# Coordination Analysis
# ==============================================================================


def analyze_coordination(
    events: list[CoordinationEvent],
    task: DualControlTaskDefinition,
) -> dict[str, Any]:
    """Analyze coordination patterns in events.

    Args:
        events: List of coordination events
        task: The dual-control task definition

    Returns:
        Analysis results including success patterns, timing, etc.
    """
    if not events:
        return {
            "total_events": 0,
            "success_rate": 0.0,
            "patterns": [],
        }

    successful = [e for e in events if e.handoff_successful]
    failed = [e for e in events if not e.handoff_successful]

    # Calculate timing statistics
    latencies = [e.latency_turns for e in successful]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    # Group by handoff type
    by_handoff: dict[str, list[CoordinationEvent]] = {}
    for event in events:
        key = event.matched_handoff_id or "unknown"
        if key not in by_handoff:
            by_handoff[key] = []
        by_handoff[key].append(event)

    handoff_analysis = []
    for handoff_id, handoff_events in by_handoff.items():
        success_count = sum(1 for e in handoff_events if e.handoff_successful)
        handoff_analysis.append({
            "handoff_id": handoff_id,
            "total": len(handoff_events),
            "successful": success_count,
            "success_rate": success_count / len(handoff_events) if handoff_events else 0,
        })

    return {
        "total_events": len(events),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(events) if events else 0,
        "avg_latency_turns": avg_latency,
        "by_handoff": handoff_analysis,
        "required_handoffs": len(task.required_handoffs),
        "completed_unique": len({e.matched_handoff_id for e in successful if e.matched_handoff_id}),
    }
