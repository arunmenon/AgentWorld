"""Goal system for dual-control simulations.

Provides a structured goal taxonomy for defining and evaluating
simulation success criteria per ADR-020.1 (τ²-bench).
"""

from agentworld.goals.types import (
    GoalType,
    GoalOperator,
    GoalCondition,
    GoalSpec,
    GoalEvaluationResult,
)
from agentworld.goals.evaluator import GoalEvaluator

__all__ = [
    "GoalType",
    "GoalOperator",
    "GoalCondition",
    "GoalSpec",
    "GoalEvaluationResult",
    "GoalEvaluator",
]
