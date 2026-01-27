"""State verification for ADR-020.

This module provides goal state verification functionality,
comparing actual final states to expected states.

Example:
    >>> from agentworld.evaluation.state_verification import (
    ...     verify_goal_state,
    ...     StateVerificationResult,
    ... )
    >>>
    >>> expected = {"paypal": {"alice": {"balance": 950}}}
    >>> actual = {"paypal": {"alice": {"balance": 950}}}
    >>> outputs = ["Transfer successful", "New balance: $950"]
    >>> required = ["transfer successful"]
    >>>
    >>> result = verify_goal_state(expected, actual, outputs, required)
    >>> print(result.success)
    True
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StateDiff:
    """A single difference between expected and actual state.

    Attributes:
        diff_type: Type of difference (missing_app, missing_agent, field_mismatch, etc.)
        path: Path to the difference (e.g., "paypal.alice.balance")
        expected: Expected value
        actual: Actual value
        severity: Severity of the difference (error, warning, info)
    """
    diff_type: str
    path: str
    expected: Any = None
    actual: Any = None
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.diff_type,
            "path": self.path,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity,
        }


@dataclass
class StateVerificationResult:
    """Result of goal state verification.

    Attributes:
        state_match: Whether final state matches expected (r_action)
        output_match: Whether required outputs present (r_output)
        success: Overall success (state_match AND output_match)
        state_diff: List of differences found
        missing_outputs: List of missing required outputs
        final_state_hash: SHA-256 hash of final state
        expected_state_hash: SHA-256 hash of expected state
        partial_match_score: Ratio of matching fields (0.0-1.0)
    """
    state_match: bool
    output_match: bool
    success: bool
    state_diff: list[StateDiff] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)
    final_state_hash: str = ""
    expected_state_hash: str = ""
    partial_match_score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state_match": self.state_match,
            "output_match": self.output_match,
            "success": self.success,
            "state_diff": [d.to_dict() for d in self.state_diff],
            "missing_outputs": self.missing_outputs,
            "final_state_hash": self.final_state_hash,
            "expected_state_hash": self.expected_state_hash,
            "partial_match_score": self.partial_match_score,
            "diff_count": len(self.state_diff),
        }


def compute_state_hash(state: dict) -> str:
    """Compute deterministic hash of state for comparison.

    Args:
        state: State dictionary to hash

    Returns:
        SHA-256 hex digest
    """
    # Sort keys for deterministic serialization
    serialized = json.dumps(state, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def compare_values(expected: Any, actual: Any, tolerance: float = 0.001) -> bool:
    """Compare two values with numeric tolerance.

    Args:
        expected: Expected value
        actual: Actual value
        tolerance: Tolerance for numeric comparison

    Returns:
        True if values match
    """
    # Handle None
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    # Handle numeric comparison with tolerance
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(expected - actual) <= tolerance

    # Handle lists
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False
        return all(
            compare_values(e, a, tolerance)
            for e, a in zip(expected, actual)
        )

    # Handle dicts
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected.keys()) != set(actual.keys()):
            return False
        return all(
            compare_values(expected[k], actual[k], tolerance)
            for k in expected.keys()
        )

    # Direct comparison
    return expected == actual


def compare_states(
    expected: dict[str, dict[str, dict]],
    actual: dict[str, dict[str, dict]],
    strict: bool = False,
) -> tuple[bool, list[StateDiff]]:
    """Compare expected and actual states.

    Args:
        expected: Expected app states {app_id: {agent_id: state}}
        actual: Actual app states
        strict: If True, actual must not have extra fields

    Returns:
        Tuple of (match, list of differences)
    """
    diffs: list[StateDiff] = []
    total_fields = 0
    matching_fields = 0

    for app_id, expected_agents in expected.items():
        if app_id not in actual:
            diffs.append(StateDiff(
                diff_type="missing_app",
                path=app_id,
                expected=expected_agents,
                actual=None,
            ))
            continue

        actual_agents = actual[app_id]

        for agent_id, expected_state in expected_agents.items():
            path_prefix = f"{app_id}.{agent_id}"

            if agent_id not in actual_agents:
                diffs.append(StateDiff(
                    diff_type="missing_agent",
                    path=path_prefix,
                    expected=expected_state,
                    actual=None,
                ))
                continue

            actual_state = actual_agents[agent_id]

            # Compare each expected field
            for field_name, expected_value in expected_state.items():
                field_path = f"{path_prefix}.{field_name}"
                total_fields += 1

                if field_name not in actual_state:
                    diffs.append(StateDiff(
                        diff_type="missing_field",
                        path=field_path,
                        expected=expected_value,
                        actual=None,
                    ))
                elif not compare_values(expected_value, actual_state[field_name]):
                    diffs.append(StateDiff(
                        diff_type="field_mismatch",
                        path=field_path,
                        expected=expected_value,
                        actual=actual_state[field_name],
                    ))
                else:
                    matching_fields += 1

            # In strict mode, check for extra fields
            if strict:
                extra_fields = set(actual_state.keys()) - set(expected_state.keys())
                for field_name in extra_fields:
                    diffs.append(StateDiff(
                        diff_type="extra_field",
                        path=f"{path_prefix}.{field_name}",
                        expected=None,
                        actual=actual_state[field_name],
                        severity="warning",
                    ))

    match = len([d for d in diffs if d.severity == "error"]) == 0
    return match, diffs


def check_required_outputs(
    outputs: list[str],
    required: list[str],
    case_sensitive: bool = False,
) -> tuple[bool, list[str]]:
    """Check if required strings are present in outputs.

    Args:
        outputs: List of agent outputs/responses
        required: List of required strings
        case_sensitive: Whether to do case-sensitive matching

    Returns:
        Tuple of (all_present, missing_outputs)
    """
    if not required:
        return True, []

    # Combine all outputs into one searchable string
    combined = " ".join(outputs)
    if not case_sensitive:
        combined = combined.lower()

    missing: list[str] = []
    for req in required:
        search_term = req if case_sensitive else req.lower()
        if search_term not in combined:
            missing.append(req)

    return len(missing) == 0, missing


def verify_goal_state(
    expected_states: dict[str, dict[str, dict]],
    actual_states: dict[str, dict[str, dict]],
    agent_outputs: list[str],
    required_outputs: list[str],
    strict_state: bool = False,
) -> StateVerificationResult:
    """Verify that actual results match expected goal state.

    This is the main verification function per ADR-020. It checks:
    1. State match (r_action): Final app state equals expected
    2. Output match (r_output): Required strings in responses
    3. Success: Both conditions met

    Args:
        expected_states: Expected final app states
        actual_states: Actual final app states
        agent_outputs: List of agent responses
        required_outputs: Required strings that must appear
        strict_state: If True, disallow extra fields in state

    Returns:
        StateVerificationResult with detailed analysis
    """
    # Compute hashes
    final_hash = compute_state_hash(actual_states)
    expected_hash = compute_state_hash(expected_states)

    # Compare states
    state_match, state_diff = compare_states(
        expected_states,
        actual_states,
        strict=strict_state,
    )

    # Check outputs
    output_match, missing_outputs = check_required_outputs(
        agent_outputs,
        required_outputs,
    )

    # Calculate partial match score
    error_diffs = [d for d in state_diff if d.severity == "error"]
    if expected_states:
        # Count total expected fields
        total_fields = sum(
            len(agent_state)
            for agents in expected_states.values()
            for agent_state in agents.values()
        )
        if total_fields > 0:
            partial_score = 1.0 - (len(error_diffs) / total_fields)
        else:
            partial_score = 1.0
    else:
        partial_score = 1.0

    return StateVerificationResult(
        state_match=state_match,
        output_match=output_match,
        success=state_match and output_match,
        state_diff=state_diff,
        missing_outputs=missing_outputs,
        final_state_hash=final_hash,
        expected_state_hash=expected_hash,
        partial_match_score=max(0.0, partial_score),
    )


def verify_action_sequence(
    expected_actions: list[dict],
    actual_actions: list[dict],
    ordered: bool = False,
) -> tuple[bool, list[dict]]:
    """Verify that expected actions were executed.

    Args:
        expected_actions: List of expected actions
        actual_actions: List of actual actions executed
        ordered: Whether order must match

    Returns:
        Tuple of (all_executed, missing_actions)
    """
    if not expected_actions:
        return True, []

    missing: list[dict] = []

    if ordered:
        # Check exact sequence match
        actual_idx = 0
        for expected in expected_actions:
            found = False
            while actual_idx < len(actual_actions):
                actual = actual_actions[actual_idx]
                actual_idx += 1
                if _action_matches(expected, actual):
                    found = True
                    break
            if not found:
                missing.append(expected)
    else:
        # Check all expected actions exist (any order)
        remaining = list(actual_actions)
        for expected in expected_actions:
            found = False
            for i, actual in enumerate(remaining):
                if _action_matches(expected, actual):
                    remaining.pop(i)
                    found = True
                    break
            if not found:
                missing.append(expected)

    return len(missing) == 0, missing


def _action_matches(expected: dict, actual: dict) -> bool:
    """Check if an actual action matches expected.

    Uses partial matching - only checks fields present in expected.

    Args:
        expected: Expected action specification
        actual: Actual action executed

    Returns:
        True if action matches
    """
    # Check required fields
    for key in ["agent_id", "app_id", "action_name"]:
        if key in expected:
            # Handle alternate key names
            actual_key = key if key in actual else key.replace("_name", "")
            if actual_key not in actual:
                return False
            if expected[key] != actual[actual_key]:
                return False

    # Check params if specified
    if "params" in expected and expected["params"]:
        actual_params = actual.get("params", {})
        for param_key, expected_value in expected["params"].items():
            if param_key not in actual_params:
                return False
            if not compare_values(expected_value, actual_params[param_key]):
                return False

    return True
