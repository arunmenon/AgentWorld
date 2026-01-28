"""Evaluation benchmarks for AgentWorld simulations.

This module provides pass^k targets and policy rules for domains.
"""

from agentworld.evaluation.benchmarks.emirates_benchmark import (
    EMIRATES_PASS_K_TARGETS,
    EMIRATES_POLICY_RULES,
    get_emirates_pass_k_targets,
    get_emirates_policy_rules,
)

__all__ = [
    "EMIRATES_PASS_K_TARGETS",
    "EMIRATES_POLICY_RULES",
    "get_emirates_pass_k_targets",
    "get_emirates_policy_rules",
]
