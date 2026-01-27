"""Built-in task scenarios for evaluation.

This module provides pre-defined task definitions for common domains:
- Payment: Money transfers, balance checks, refunds
- Shopping: Cart management, checkout, orders

These scenarios can be used as-is or as templates for custom tasks.

Example:
    from agentworld.tasks.scenarios import (
        get_all_scenarios,
        get_payment_scenarios,
        get_shopping_scenarios,
        PAYMENT_BENCHMARK,
    )

    # Get all built-in scenarios
    all_tasks = get_all_scenarios()

    # Get payment-specific scenarios
    payment_tasks = get_payment_scenarios()

    # Use the payment benchmark task set
    benchmark = PAYMENT_BENCHMARK
"""

from agentworld.tasks.scenarios.payment import (
    PAYMENT_SCENARIOS,
    PAYMENT_BENCHMARK,
    get_payment_scenarios,
)
from agentworld.tasks.scenarios.shopping import (
    SHOPPING_SCENARIOS,
    SHOPPING_BENCHMARK,
    get_shopping_scenarios,
)
from agentworld.tasks.definitions import TaskDefinition, TaskSet


def get_all_scenarios() -> list[TaskDefinition]:
    """Get all built-in task scenarios.

    Returns:
        List of all predefined TaskDefinitions
    """
    return get_payment_scenarios() + get_shopping_scenarios()


def get_all_benchmarks() -> list[TaskSet]:
    """Get all built-in benchmark task sets.

    Returns:
        List of all predefined TaskSets
    """
    return [PAYMENT_BENCHMARK, SHOPPING_BENCHMARK]


__all__ = [
    # Functions
    "get_all_scenarios",
    "get_all_benchmarks",
    "get_payment_scenarios",
    "get_shopping_scenarios",
    # Payment
    "PAYMENT_SCENARIOS",
    "PAYMENT_BENCHMARK",
    # Shopping
    "SHOPPING_SCENARIOS",
    "SHOPPING_BENCHMARK",
]
