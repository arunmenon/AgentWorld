"""Reliability evaluation for ADR-020.

This module provides pass^k reliability metrics and related computations.
Pass^k measures the probability that k consecutive trials all succeed.

Mathematical definition:
    pass^k = C(c,k) / C(n,k)

where:
    n = total number of trials
    c = number of successful trials
    k = number of consecutive successes required

Example:
    >>> from agentworld.evaluation.reliability import compute_pass_k, compute_all_pass_k
    >>>
    >>> # Single computation
    >>> pass_4 = compute_pass_k(n=8, c=6, k=4)
    >>> print(f"pass^4 = {pass_4:.3f}")
    pass^4 = 0.214
    >>>
    >>> # Compute standard k values
    >>> metrics = compute_all_pass_k(n=8, c=6)
    >>> print(metrics)
    {'pass_1': 0.75, 'pass_2': 0.536, 'pass_4': 0.214, 'pass_8': 0.0}
"""

from dataclasses import dataclass, field
from math import comb
from typing import Any


def compute_pass_k(n: int, c: int, k: int) -> float:
    """Compute pass^k = C(c,k) / C(n,k).

    The pass^k metric measures the probability of achieving k consecutive
    successes given n total trials with c successes.

    Args:
        n: Total number of trials
        c: Number of successful trials
        k: Number of consecutive successes required

    Returns:
        Probability of k consecutive successes (0.0 to 1.0)

    Examples:
        >>> compute_pass_k(8, 8, 8)  # All trials succeeded
        1.0
        >>> compute_pass_k(8, 0, 1)  # No trials succeeded
        0.0
        >>> compute_pass_k(8, 6, 4)  # 6/8 succeeded, need 4 consecutive
        0.21428571428571427
    """
    if n == 0 or k == 0:
        return 1.0 if k == 0 else 0.0

    if k > n or k > c:
        return 0.0

    return comb(c, k) / comb(n, k)


def compute_all_pass_k(
    n: int,
    c: int,
    k_values: list[int] | None = None,
) -> dict[str, float]:
    """Compute pass^k for multiple k values.

    Args:
        n: Total number of trials
        c: Number of successful trials
        k_values: List of k values to compute. Default: [1, 2, 4, 8]

    Returns:
        Dictionary mapping 'pass_k' to computed value

    Examples:
        >>> compute_all_pass_k(8, 6)
        {'pass_1': 0.75, 'pass_2': 0.5357142857142857, 'pass_4': 0.21428571428571427, 'pass_8': 0.0}
    """
    if k_values is None:
        k_values = [1, 2, 4, 8]

    return {f"pass_{k}": compute_pass_k(n, c, k) for k in k_values}


def interpret_reliability(pass_1: float, pass_8: float) -> str:
    """Interpret reliability based on pass^k scores.

    Args:
        pass_1: Traditional success rate (pass^1)
        pass_8: Reliability metric (pass^8)

    Returns:
        Human-readable interpretation
    """
    if pass_1 == 0:
        return "Critical: No successes observed"

    if pass_8 >= 0.9:
        return "Excellent: Highly reliable across repeated trials"

    if pass_8 >= 0.7:
        return "Good: Generally reliable with occasional failures"

    if pass_8 >= 0.5:
        return "Moderate: Some inconsistency in repeated trials"

    gap = pass_1 - pass_8

    if gap > 0.5:
        return f"Fragile: High success rate ({pass_1:.0%}) but low reliability ({pass_8:.0%})"

    if pass_1 >= 0.7:
        return "Inconsistent: Good single-trial performance but unreliable over time"

    return "Poor: Low success rate and reliability"


def compute_reliability_gap(pass_1: float, pass_8: float) -> float:
    """Compute the reliability gap between pass^1 and pass^8.

    A large gap indicates inconsistent performance - the agent might
    succeed often but can't do so reliably.

    Args:
        pass_1: Traditional success rate
        pass_8: Reliability metric

    Returns:
        Gap value (0.0 = perfectly reliable, higher = more fragile)
    """
    return pass_1 - pass_8


@dataclass
class BenchmarkMetrics:
    """Aggregated metrics for a benchmark (set of tasks).

    Attributes:
        task_metrics: Individual task metrics
        mean_pass_1: Average pass^1 across tasks
        mean_pass_8: Average pass^8 across tasks
        mean_reliability_gap: Average reliability gap
        total_trials: Total trials across all tasks
        total_successes: Total successes across all tasks
    """
    task_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    mean_pass_1: float = 0.0
    mean_pass_8: float = 0.0
    mean_reliability_gap: float = 0.0
    total_trials: int = 0
    total_successes: int = 0

    @classmethod
    def from_task_results(
        cls,
        results: dict[str, tuple[int, int]],  # task_id -> (total, successes)
    ) -> "BenchmarkMetrics":
        """Compute benchmark metrics from task results.

        Args:
            results: Dict mapping task_id to (total_trials, successful_trials)

        Returns:
            BenchmarkMetrics with aggregated values
        """
        task_metrics: dict[str, dict[str, float]] = {}
        pass_1_values: list[float] = []
        pass_8_values: list[float] = []
        total_trials = 0
        total_successes = 0

        for task_id, (n, c) in results.items():
            metrics = compute_all_pass_k(n, c)
            task_metrics[task_id] = metrics

            pass_1_values.append(metrics["pass_1"])
            pass_8_values.append(metrics["pass_8"])
            total_trials += n
            total_successes += c

        mean_pass_1 = sum(pass_1_values) / len(pass_1_values) if pass_1_values else 0.0
        mean_pass_8 = sum(pass_8_values) / len(pass_8_values) if pass_8_values else 0.0

        return cls(
            task_metrics=task_metrics,
            mean_pass_1=mean_pass_1,
            mean_pass_8=mean_pass_8,
            mean_reliability_gap=mean_pass_1 - mean_pass_8,
            total_trials=total_trials,
            total_successes=total_successes,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_metrics": self.task_metrics,
            "mean_pass_1": self.mean_pass_1,
            "mean_pass_8": self.mean_pass_8,
            "mean_reliability_gap": self.mean_reliability_gap,
            "total_trials": self.total_trials,
            "total_successes": self.total_successes,
            "interpretation": interpret_reliability(self.mean_pass_1, self.mean_pass_8),
        }


@dataclass
class ReliabilityComparison:
    """Comparison of reliability between two systems/variants.

    Useful for A/B testing and model comparison.

    Attributes:
        baseline_metrics: Metrics for baseline system
        variant_metrics: Metrics for variant being tested
        pass_1_delta: Change in pass^1 (positive = improvement)
        pass_8_delta: Change in pass^8 (positive = improvement)
        reliability_gap_delta: Change in reliability gap
    """
    baseline_metrics: dict[str, float]
    variant_metrics: dict[str, float]
    pass_1_delta: float = 0.0
    pass_8_delta: float = 0.0
    reliability_gap_delta: float = 0.0

    @classmethod
    def compare(
        cls,
        baseline: tuple[int, int],  # (total, successes)
        variant: tuple[int, int],
    ) -> "ReliabilityComparison":
        """Compare reliability between baseline and variant.

        Args:
            baseline: (total_trials, successful_trials) for baseline
            variant: (total_trials, successful_trials) for variant

        Returns:
            ReliabilityComparison with delta analysis
        """
        baseline_metrics = compute_all_pass_k(baseline[0], baseline[1])
        variant_metrics = compute_all_pass_k(variant[0], variant[1])

        return cls(
            baseline_metrics=baseline_metrics,
            variant_metrics=variant_metrics,
            pass_1_delta=variant_metrics["pass_1"] - baseline_metrics["pass_1"],
            pass_8_delta=variant_metrics["pass_8"] - baseline_metrics["pass_8"],
            reliability_gap_delta=(
                compute_reliability_gap(variant_metrics["pass_1"], variant_metrics["pass_8"])
                - compute_reliability_gap(baseline_metrics["pass_1"], baseline_metrics["pass_8"])
            ),
        )

    def is_improvement(self, min_delta: float = 0.0) -> bool:
        """Check if variant is an improvement over baseline.

        An improvement requires better pass^8 (reliability) with
        no regression in pass^1 (success rate).

        Args:
            min_delta: Minimum improvement threshold

        Returns:
            True if variant is better
        """
        return (
            self.pass_8_delta >= min_delta
            and self.pass_1_delta >= -0.05  # Allow small regression
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "baseline": self.baseline_metrics,
            "variant": self.variant_metrics,
            "delta": {
                "pass_1": self.pass_1_delta,
                "pass_8": self.pass_8_delta,
                "reliability_gap": self.reliability_gap_delta,
            },
            "is_improvement": self.is_improvement(),
            "summary": self._summarize(),
        }

    def _summarize(self) -> str:
        """Generate human-readable summary."""
        if self.is_improvement(min_delta=0.1):
            return f"Significant improvement: pass^8 +{self.pass_8_delta:.1%}"
        elif self.is_improvement():
            return f"Minor improvement: pass^8 +{self.pass_8_delta:.1%}"
        elif self.pass_8_delta < -0.1:
            return f"Regression: pass^8 {self.pass_8_delta:.1%}"
        else:
            return "No significant change"
