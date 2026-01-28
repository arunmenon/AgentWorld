"""Fault classification for ADR-020.

This module provides structured error analysis for failed task trials,
categorizing failures by assignment (who) and type (what).

Example:
    >>> from agentworld.evaluation.fault_classifier import (
    ...     FaultClassifier,
    ...     classify_trial_failure,
    ... )
    >>>
    >>> classifier = FaultClassifier()
    >>> classification = classifier.classify(task, trial_result)
    >>> print(f"{classification.fault_assignment}: {classification.fault_type}")
    agent: wrong_action
"""

import re
from dataclasses import dataclass, field
from typing import Any

from agentworld.tasks.definitions import (
    ExpectedAction,
    FaultAssignment,
    FaultClassification,
    FaultType,
    TaskDefinition,
    TrialResult,
)


@dataclass
class ClassificationContext:
    """Context for fault classification.

    Attributes:
        task: Task definition
        result: Trial result
        trajectory: List of actions taken
        expected_actions: Expected action list
        state_diff: List of state differences
    """
    task: TaskDefinition
    result: TrialResult
    trajectory: list[dict] = field(default_factory=list)
    expected_actions: list[ExpectedAction] = field(default_factory=list)
    state_diff: list[dict] = field(default_factory=list)


class FaultClassifier:
    """Classifies task failures into categories.

    The classifier uses a rule-based approach to determine:
    1. Fault assignment: Who is responsible (agent, environment, task)
    2. Fault type: What type of error occurred

    Classification priority:
    1. Environment errors (timeout, API errors)
    2. Communication errors (τ²-bench dual-control scenarios)
    3. Agent action errors (wrong/missing/extra actions)
    4. Agent reasoning errors
    5. Task definition issues

    Extended per τ²-bench (ADR-020.1) to detect communication failures
    in dual-control scenarios.
    """

    def __init__(self):
        """Initialize the classifier."""
        # Patterns for environment error detection
        self._env_error_patterns = [
            (r"timeout", FaultType.TIMEOUT),
            (r"timed?\s*out", FaultType.TIMEOUT),
            (r"api\s*(error|fail)", FaultType.API_ERROR),
            (r"connection\s*(error|fail|refused)", FaultType.API_ERROR),
            (r"network\s*(error|fail)", FaultType.API_ERROR),
            (r"500\s*(internal)?server", FaultType.SYSTEM_ERROR),
            (r"503\s*service\s*unavailable", FaultType.SYSTEM_ERROR),
            (r"rate\s*limit", FaultType.API_ERROR),
        ]

        # Patterns for communication error detection (τ²-bench)
        self._communication_patterns = [
            # User confusion indicators
            (r"(i\s+)?don't\s+understand", FaultType.USER_CONFUSED),
            (r"what\s+do\s+you\s+mean", FaultType.USER_CONFUSED),
            (r"can\s+you\s+(please\s+)?clarify", FaultType.USER_CONFUSED),
            (r"i'm\s+(not\s+sure|confused)", FaultType.USER_CONFUSED),
            (r"which\s+(one|button|option)", FaultType.USER_CONFUSED),

            # User misunderstanding indicators
            (r"(i\s+)?thought\s+you\s+(said|meant)", FaultType.USER_MISUNDERSTOOD),
            (r"but\s+you\s+(said|told)", FaultType.USER_MISUNDERSTOOD),
            (r"did\s+you\s+mean", FaultType.USER_MISUNDERSTOOD),

            # Instruction clarity issues
            (r"unclear\s+instruction", FaultType.INSTRUCTION_UNCLEAR),
            (r"vague\s+(instruction|direction)", FaultType.INSTRUCTION_UNCLEAR),
            (r"ambiguous", FaultType.INSTRUCTION_UNCLEAR),

            # User action failure
            (r"(i\s+)?(can't|cannot|couldn't)\s+(find|see|do)", FaultType.USER_ACTION_FAILED),
            (r"(it\s+)?doesn't\s+(work|show)", FaultType.USER_ACTION_FAILED),
            (r"nothing\s+happen", FaultType.USER_ACTION_FAILED),
        ]

    def classify(
        self,
        task: TaskDefinition,
        result: TrialResult,
    ) -> FaultClassification | None:
        """Classify a trial failure.

        Args:
            task: Task definition
            result: Trial result to classify

        Returns:
            FaultClassification or None if trial succeeded
        """
        if result.success:
            return None

        ctx = ClassificationContext(
            task=task,
            result=result,
            trajectory=result.trajectory or [],
            expected_actions=task.expected_actions,
        )

        # Try classification in priority order
        classification = (
            self._check_environment_error(ctx)
            or self._check_communication_errors(ctx)  # NEW: τ²-bench communication errors
            or self._check_action_errors(ctx)
            or self._check_state_errors(ctx)
            or self._check_output_errors(ctx)
            or self._default_classification(ctx)
        )

        return classification

    def _check_environment_error(
        self,
        ctx: ClassificationContext,
    ) -> FaultClassification | None:
        """Check for environment-related errors.

        Args:
            ctx: Classification context

        Returns:
            FaultClassification or None
        """
        error_msg = ctx.result.error_message or ""
        error_lower = error_msg.lower()

        for pattern, fault_type in self._env_error_patterns:
            if re.search(pattern, error_lower):
                return FaultClassification(
                    trial_id=ctx.result.id or "",
                    task_id=ctx.task.task_id,
                    fault_assignment=FaultAssignment.ENVIRONMENT,
                    fault_type=fault_type,
                    description=f"Environment error: {error_msg[:200]}",
                    evidence=[error_msg],
                    classifier="rule_based",
                    confidence=0.9,
                )

        return None

    def _check_communication_errors(
        self,
        ctx: ClassificationContext,
    ) -> FaultClassification | None:
        """Check for communication-related errors (τ²-bench dual-control).

        Analyzes the conversation trajectory to detect communication failures
        between agent and user in dual-control scenarios.

        Args:
            ctx: Classification context

        Returns:
            FaultClassification or None
        """
        # Analyze trajectory for user messages indicating confusion
        user_messages = []
        agent_instructions = []

        for entry in ctx.trajectory:
            role = entry.get("role") or entry.get("agent_role")
            content = entry.get("content") or entry.get("message", "")

            if role in ("user", "customer"):
                user_messages.append(content.lower())
            elif role in ("agent", "service_agent", "assistant"):
                agent_instructions.append(content.lower())

        # Check user messages for communication error patterns
        for user_msg in user_messages:
            for pattern, fault_type in self._communication_patterns:
                if re.search(pattern, user_msg, re.IGNORECASE):
                    return FaultClassification(
                        trial_id=ctx.result.id or "",
                        task_id=ctx.task.task_id,
                        fault_assignment=FaultAssignment.AGENT,
                        fault_type=fault_type,
                        description=f"Communication error detected: {fault_type.value}",
                        evidence=[f"User message: {user_msg[:200]}..."],
                        classifier="rule_based",
                        confidence=0.75,
                    )

        # Check for instruction completeness issues
        # If task has coordination handoffs, verify agent provided all steps
        if hasattr(ctx.task, "coordination_handoffs"):
            handoffs = ctx.task.coordination_handoffs
            if handoffs and agent_instructions:
                # Check if agent mentioned all required actions
                for handoff in handoffs:
                    expected_keywords = getattr(handoff, "expected_keywords", [])
                    instruction = getattr(handoff, "instruction_pattern", "")

                    if expected_keywords:
                        # Check if agent instructions covered all keywords
                        agent_text = " ".join(agent_instructions)
                        missing_keywords = [
                            kw for kw in expected_keywords
                            if kw.lower() not in agent_text
                        ]

                        if len(missing_keywords) > len(expected_keywords) // 2:
                            return FaultClassification(
                                trial_id=ctx.result.id or "",
                                task_id=ctx.task.task_id,
                                fault_assignment=FaultAssignment.AGENT,
                                fault_type=FaultType.INSTRUCTION_INCOMPLETE,
                                description="Agent instructions missing key steps",
                                evidence=[
                                    f"Missing keywords: {missing_keywords}",
                                    f"Expected instruction: {instruction[:100]}",
                                ],
                                classifier="rule_based",
                                confidence=0.7,
                            )

        return None

    def _check_action_errors(
        self,
        ctx: ClassificationContext,
    ) -> FaultClassification | None:
        """Check for action-related errors.

        Args:
            ctx: Classification context

        Returns:
            FaultClassification or None
        """
        if not ctx.expected_actions:
            return None

        trajectory = ctx.trajectory
        expected = ctx.expected_actions

        # Extract actual actions from trajectory
        actual_actions = [
            (a.get("agent_id"), a.get("app_id"), a.get("action") or a.get("action_name"))
            for a in trajectory
        ]

        expected_tuples = [
            (a.agent_id, a.app_id, a.action_name)
            for a in expected
            if a.required
        ]

        actual_set = set(actual_actions)
        expected_set = set(expected_tuples)

        # Check for missing required actions
        missing = expected_set - actual_set
        if missing:
            missing_list = list(missing)
            return FaultClassification(
                trial_id=ctx.result.id or "",
                task_id=ctx.task.task_id,
                fault_assignment=FaultAssignment.AGENT,
                fault_type=FaultType.MISSING_ACTION,
                description=f"Missing required actions: {missing_list}",
                evidence=[f"Expected: {expected_set}", f"Actual: {actual_set}"],
                classifier="rule_based",
                confidence=0.95,
            )

        # Check for wrong parameters
        for expected_action in expected:
            if not expected_action.params:
                continue

            # Find matching action in trajectory
            for actual in trajectory:
                if (
                    actual.get("agent_id") == expected_action.agent_id
                    and actual.get("app_id") == expected_action.app_id
                    and (actual.get("action") or actual.get("action_name")) == expected_action.action_name
                ):
                    actual_params = actual.get("params", {})
                    for param_name, expected_value in expected_action.params.items():
                        if param_name in actual_params and actual_params[param_name] != expected_value:
                            return FaultClassification(
                                trial_id=ctx.result.id or "",
                                task_id=ctx.task.task_id,
                                fault_assignment=FaultAssignment.AGENT,
                                fault_type=FaultType.WRONG_PARAMS,
                                description=(
                                    f"Wrong parameter for {expected_action.action_name}: "
                                    f"{param_name}={actual_params[param_name]} "
                                    f"(expected {expected_value})"
                                ),
                                evidence=[
                                    f"Expected: {expected_action.params}",
                                    f"Actual: {actual_params}",
                                ],
                                classifier="rule_based",
                                confidence=0.9,
                            )

        # Check for extra actions that might have caused issues
        extra = actual_set - expected_set
        if extra and not ctx.result.state_match:
            return FaultClassification(
                trial_id=ctx.result.id or "",
                task_id=ctx.task.task_id,
                fault_assignment=FaultAssignment.AGENT,
                fault_type=FaultType.EXTRA_ACTION,
                description=f"Unexpected actions that may have affected state: {list(extra)}",
                evidence=[f"Extra actions: {extra}"],
                classifier="rule_based",
                confidence=0.7,
            )

        # Check action order if specified
        ordered_expected = [a for a in expected if a.order is not None]
        if ordered_expected:
            ordered_expected.sort(key=lambda a: a.order or 0)

            # Check if order matches
            expected_order = [(a.agent_id, a.app_id, a.action_name) for a in ordered_expected]
            actual_order = [
                (a.get("agent_id"), a.get("app_id"), a.get("action") or a.get("action_name"))
                for a in trajectory
            ]

            # Filter actual to only ordered expected
            filtered_actual = [a for a in actual_order if a in set(expected_order)]

            if filtered_actual != expected_order:
                return FaultClassification(
                    trial_id=ctx.result.id or "",
                    task_id=ctx.task.task_id,
                    fault_assignment=FaultAssignment.AGENT,
                    fault_type=FaultType.ACTION_ORDER,
                    description="Actions executed in wrong order",
                    evidence=[
                        f"Expected order: {expected_order}",
                        f"Actual order: {filtered_actual}",
                    ],
                    classifier="rule_based",
                    confidence=0.85,
                )

        return None

    def _check_state_errors(
        self,
        ctx: ClassificationContext,
    ) -> FaultClassification | None:
        """Check for state-related errors.

        Args:
            ctx: Classification context

        Returns:
            FaultClassification or None
        """
        if ctx.result.state_match is False:
            # State didn't match - generic goal not achieved
            evidence = []
            if ctx.result.final_state_hash != ctx.result.expected_state_hash:
                evidence.append(
                    f"State hash mismatch: {ctx.result.final_state_hash[:16]}... "
                    f"vs expected {ctx.result.expected_state_hash[:16]}..."
                )

            return FaultClassification(
                trial_id=ctx.result.id or "",
                task_id=ctx.task.task_id,
                fault_assignment=FaultAssignment.AGENT,
                fault_type=FaultType.GOAL_NOT_ACHIEVED,
                description="Final state does not match expected state",
                evidence=evidence,
                classifier="rule_based",
                confidence=0.8,
            )

        return None

    def _check_output_errors(
        self,
        ctx: ClassificationContext,
    ) -> FaultClassification | None:
        """Check for output-related errors.

        Args:
            ctx: Classification context

        Returns:
            FaultClassification or None
        """
        if ctx.result.output_match is False:
            return FaultClassification(
                trial_id=ctx.result.id or "",
                task_id=ctx.task.task_id,
                fault_assignment=FaultAssignment.AGENT,
                fault_type=FaultType.GOAL_PARTIAL,
                description="Required outputs not present in agent response",
                evidence=[f"Required outputs: {ctx.task.required_outputs}"],
                classifier="rule_based",
                confidence=0.85,
            )

        return None

    def _default_classification(
        self,
        ctx: ClassificationContext,
    ) -> FaultClassification:
        """Default classification when no specific cause found.

        Args:
            ctx: Classification context

        Returns:
            FaultClassification with reasoning error
        """
        evidence = []
        if ctx.result.error_message:
            evidence.append(f"Error: {ctx.result.error_message[:200]}")

        return FaultClassification(
            trial_id=ctx.result.id or "",
            task_id=ctx.task.task_id,
            fault_assignment=FaultAssignment.AGENT,
            fault_type=FaultType.REASONING_ERROR,
            description="Unknown failure - possible reasoning error",
            evidence=evidence,
            classifier="rule_based",
            confidence=0.5,
        )


def classify_trial_failure(
    task: TaskDefinition,
    result: TrialResult,
) -> FaultClassification | None:
    """Convenience function to classify a trial failure.

    Args:
        task: Task definition
        result: Trial result

    Returns:
        FaultClassification or None if successful
    """
    classifier = FaultClassifier()
    return classifier.classify(task, result)


@dataclass
class FaultSummary:
    """Summary of faults across multiple trials.

    Extended per τ²-bench (ADR-020.1) to include category-based analysis
    (reasoning vs communication vs execution errors).

    Attributes:
        total_failures: Number of failed trials
        by_assignment: Count by fault assignment
        by_type: Count by fault type
        by_category: Count by fault category (τ²-bench)
        common_patterns: Most common fault patterns
    """
    total_failures: int = 0
    by_assignment: dict[str, int] = field(default_factory=dict)
    by_type: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)  # NEW: τ²-bench
    common_patterns: list[dict] = field(default_factory=list)

    @classmethod
    def from_classifications(
        cls,
        classifications: list[FaultClassification],
    ) -> "FaultSummary":
        """Create summary from list of classifications.

        Args:
            classifications: List of fault classifications

        Returns:
            FaultSummary with aggregated data
        """
        by_assignment: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_category: dict[str, int] = {}  # NEW: τ²-bench category counts
        pattern_counts: dict[str, int] = {}

        for c in classifications:
            assignment = c.fault_assignment.value
            fault_type = c.fault_type.value

            by_assignment[assignment] = by_assignment.get(assignment, 0) + 1
            by_type[fault_type] = by_type.get(fault_type, 0) + 1

            # Track category (τ²-bench)
            category = c.fault_type.category.value
            by_category[category] = by_category.get(category, 0) + 1

            # Track patterns (assignment + type)
            pattern = f"{assignment}:{fault_type}"
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Get most common patterns
        sorted_patterns = sorted(
            pattern_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        common_patterns = [
            {"pattern": p, "count": c, "percentage": c / len(classifications) * 100}
            for p, c in sorted_patterns[:5]
        ]

        return cls(
            total_failures=len(classifications),
            by_assignment=by_assignment,
            by_type=by_type,
            by_category=by_category,
            common_patterns=common_patterns,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_failures": self.total_failures,
            "by_assignment": self.by_assignment,
            "by_type": self.by_type,
            "by_category": self.by_category,  # τ²-bench category breakdown
            "common_patterns": self.common_patterns,
        }

    def get_most_common_cause(self) -> str:
        """Get the most common fault cause.

        Returns:
            String describing most common cause
        """
        if not self.common_patterns:
            return "No failures recorded"

        top = self.common_patterns[0]
        assignment, fault_type = top["pattern"].split(":")
        return f"{assignment} - {fault_type} ({top['count']} occurrences, {top['percentage']:.1f}%)"
