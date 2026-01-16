"""A/B testing and experiment runner per ADR-010."""

from __future__ import annotations

import statistics
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Protocol

from agentworld.evaluation.metrics import MetricsCollector, SimulationMetrics
from agentworld.evaluation.validators import ValidationResult, Validator

if TYPE_CHECKING:
    from agentworld.scenarios.base import Scenario, ScenarioResult


class ScenarioFactory(Protocol):
    """Protocol for scenario factory."""

    def create(self, config: Any) -> "Scenario":
        """Create a scenario from config."""
        ...


@dataclass
class RunResult:
    """Result of a single scenario run."""

    scenario_result: Any  # ScenarioResult
    metrics: SimulationMetrics
    validations: list[ValidationResult]
    run_index: int


@dataclass
class VariantResults:
    """Aggregated results for a single variant."""

    variant_name: str
    runs: list[RunResult]
    avg_metrics: dict[str, float]
    validation_pass_rate: float


@dataclass
class StatisticalComparison:
    """Statistical comparison between variants."""

    metric_name: str
    variant_a: str
    variant_b: str
    mean_a: float
    mean_b: float
    difference: float
    percent_change: float
    significant: bool  # True if difference is statistically significant
    p_value: float | None = None
    effect_size: float | None = None  # Cohen's d


@dataclass
class ABTestResult:
    """Complete A/B test results."""

    variants: dict[str, VariantResults]
    comparisons: list[StatisticalComparison]
    winner: str | None = None  # Variant with best results
    recommendation: str = ""


class ExperimentRunner:
    """
    Run comparative experiments (inspired by TinyTroupe).

    Uses deep copies of config to prevent cross-variant
    contamination. Each run is fully isolated.
    """

    def __init__(
        self,
        scenario_factory: ScenarioFactory | Callable[[Any], "Scenario"],
        metrics_collector: MetricsCollector,
        validator: Validator,
    ) -> None:
        self.scenario_factory = scenario_factory
        self.metrics_collector = metrics_collector
        self.validator = validator

    async def run_ab_test(
        self,
        base_config: Any,
        variants: dict[str, dict[str, Any]],  # variant_name -> config changes
        runs_per_variant: int = 3,
    ) -> ABTestResult:
        """
        Run scenario with different configurations.

        Uses deep copies to prevent config mutation between variants.
        Each variant starts from a fresh copy of base_config.

        Args:
            base_config: Base scenario configuration
            variants: Dictionary mapping variant names to config overrides
            runs_per_variant: Number of runs per variant for statistical significance

        Returns:
            ABTestResult with aggregated results and comparisons
        """
        variant_results: dict[str, VariantResults] = {}

        for variant_name, config_overrides in variants.items():
            runs = []

            for run_idx in range(runs_per_variant):
                # Deep copy base config for each run
                run_config = deepcopy(base_config)

                # Apply variant overrides to the copy
                self._apply_overrides(run_config, config_overrides)

                # Reset metrics and validation budget
                self.metrics_collector.reset()
                self.validator.reset_budget()

                # Create fresh scenario instance
                if callable(self.scenario_factory):
                    scenario = self.scenario_factory(run_config)
                else:
                    scenario = self.scenario_factory.create(run_config)

                # Run scenario
                scenario_result = await scenario.run()
                metrics = self.metrics_collector.get_metrics()

                # Validate sample of responses
                validations = await self._validate_responses(scenario_result)

                runs.append(
                    RunResult(
                        scenario_result=scenario_result,
                        metrics=metrics,
                        validations=validations,
                        run_index=run_idx,
                    )
                )

            # Aggregate variant results
            variant_results[variant_name] = self._aggregate_variant(variant_name, runs)

        # Compute statistical comparisons
        comparisons = self._compute_comparisons(variant_results)

        # Determine winner
        winner, recommendation = self._determine_winner(variant_results, comparisons)

        return ABTestResult(
            variants=variant_results,
            comparisons=comparisons,
            winner=winner,
            recommendation=recommendation,
        )

    def _apply_overrides(self, config: Any, overrides: dict[str, Any]) -> None:
        """Apply config overrides using dot notation."""
        for key, value in overrides.items():
            parts = key.split(".")
            obj = config
            for part in parts[:-1]:
                if isinstance(obj, dict):
                    obj = obj[part]
                else:
                    obj = getattr(obj, part)
            if isinstance(obj, dict):
                obj[parts[-1]] = value
            else:
                setattr(obj, parts[-1], value)

    async def _validate_responses(
        self,
        result: Any,
    ) -> list[ValidationResult]:
        """Validate sample of responses from scenario."""
        validations = []

        # Get messages from result
        messages = getattr(result, "messages", [])
        if not messages:
            return validations

        # Sample messages for validation (avoid validating everything)
        sample_size = min(10, len(messages))
        sampled = messages[:sample_size]

        for msg in sampled:
            content = getattr(msg, "content", str(msg))
            v = await self.validator.check_coherence(content)
            validations.append(v)

        return validations

    def _aggregate_variant(
        self,
        variant_name: str,
        runs: list[RunResult],
    ) -> VariantResults:
        """Aggregate metrics across runs."""
        if not runs:
            return VariantResults(
                variant_name=variant_name,
                runs=[],
                avg_metrics={},
                validation_pass_rate=0.0,
            )

        # Average key metrics
        avg_metrics = {
            "total_messages": statistics.mean(r.metrics.total_messages for r in runs),
            "avg_response_length": statistics.mean(
                r.metrics.avg_response_length for r in runs
            ),
            "total_reflections": statistics.mean(
                r.metrics.total_reflections for r in runs
            ),
            "total_tokens": statistics.mean(r.metrics.total_tokens for r in runs),
            "api_calls": statistics.mean(r.metrics.api_calls for r in runs),
            "estimated_cost_usd": statistics.mean(
                r.metrics.estimated_cost_usd for r in runs
            ),
        }

        # Add standard deviations if multiple runs
        if len(runs) > 1:
            avg_metrics["total_messages_std"] = statistics.stdev(
                r.metrics.total_messages for r in runs
            )
            avg_metrics["estimated_cost_usd_std"] = statistics.stdev(
                r.metrics.estimated_cost_usd for r in runs
            )

        # Validation pass rate
        all_validations = [v for r in runs for v in r.validations]
        pass_rate = (
            sum(1 for v in all_validations if v.passed) / len(all_validations)
            if all_validations
            else 0.0
        )

        return VariantResults(
            variant_name=variant_name,
            runs=runs,
            avg_metrics=avg_metrics,
            validation_pass_rate=pass_rate,
        )

    def _compute_comparisons(
        self,
        variants: dict[str, VariantResults],
    ) -> list[StatisticalComparison]:
        """Compute statistical comparisons between variant pairs."""
        comparisons = []
        variant_names = list(variants.keys())

        metrics_to_compare = [
            "total_messages",
            "avg_response_length",
            "total_tokens",
            "estimated_cost_usd",
        ]

        for i, name_a in enumerate(variant_names):
            for name_b in variant_names[i + 1 :]:
                var_a = variants[name_a]
                var_b = variants[name_b]

                for metric in metrics_to_compare:
                    mean_a = var_a.avg_metrics.get(metric, 0)
                    mean_b = var_b.avg_metrics.get(metric, 0)
                    diff = mean_b - mean_a

                    # Calculate percent change
                    if mean_a != 0:
                        percent_change = (diff / abs(mean_a)) * 100
                    else:
                        percent_change = 100 if diff != 0 else 0

                    # Simple significance check (>10% difference)
                    threshold = max(abs(mean_a), abs(mean_b)) * 0.1
                    significant = abs(diff) > threshold

                    # Calculate effect size (Cohen's d) if we have variance
                    effect_size = None
                    std_a_key = f"{metric}_std"
                    std_b_key = f"{metric}_std"
                    if std_a_key in var_a.avg_metrics and std_b_key in var_b.avg_metrics:
                        std_a = var_a.avg_metrics[std_a_key]
                        std_b = var_b.avg_metrics[std_b_key]
                        pooled_std = ((std_a**2 + std_b**2) / 2) ** 0.5
                        if pooled_std > 0:
                            effect_size = diff / pooled_std

                    comparisons.append(
                        StatisticalComparison(
                            metric_name=metric,
                            variant_a=name_a,
                            variant_b=name_b,
                            mean_a=mean_a,
                            mean_b=mean_b,
                            difference=diff,
                            percent_change=percent_change,
                            significant=significant,
                            effect_size=effect_size,
                        )
                    )

        return comparisons

    def _determine_winner(
        self,
        variants: dict[str, VariantResults],
        comparisons: list[StatisticalComparison],
    ) -> tuple[str | None, str]:
        """Determine winning variant based on results."""
        if len(variants) < 2:
            return None, "Need at least 2 variants for comparison"

        # Score variants by validation pass rate (primary metric)
        scores = {name: var.validation_pass_rate for name, var in variants.items()}

        sorted_variants = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner = sorted_variants[0][0]
        runner_up = sorted_variants[1][0] if len(sorted_variants) > 1 else None

        if runner_up is None:
            return winner, f"{winner} is the only variant with results."

        diff = scores[winner] - scores[runner_up]

        if diff < 0.05:
            return None, f"No clear winner. {winner} and {runner_up} are similar."

        return winner, (
            f"{winner} outperforms {runner_up} with "
            f"{scores[winner]:.1%} vs {scores[runner_up]:.1%} validation pass rate."
        )


def compute_cohens_d(
    values_a: list[float],
    values_b: list[float],
) -> float | None:
    """
    Compute Cohen's d effect size between two groups.

    Returns:
        Cohen's d value, or None if cannot be computed
    """
    if len(values_a) < 2 or len(values_b) < 2:
        return None

    mean_a = statistics.mean(values_a)
    mean_b = statistics.mean(values_b)
    std_a = statistics.stdev(values_a)
    std_b = statistics.stdev(values_b)

    # Pooled standard deviation
    n_a = len(values_a)
    n_b = len(values_b)
    pooled_std = (
        ((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2)
    ) ** 0.5

    if pooled_std == 0:
        return None

    return (mean_b - mean_a) / pooled_std


def interpret_effect_size(d: float | None) -> str:
    """
    Interpret Cohen's d effect size.

    Returns:
        Human-readable interpretation
    """
    if d is None:
        return "Unable to compute"

    abs_d = abs(d)
    if abs_d < 0.2:
        magnitude = "negligible"
    elif abs_d < 0.5:
        magnitude = "small"
    elif abs_d < 0.8:
        magnitude = "medium"
    else:
        magnitude = "large"

    direction = "positive" if d > 0 else "negative"
    return f"{magnitude} {direction} effect (d={d:.2f})"
