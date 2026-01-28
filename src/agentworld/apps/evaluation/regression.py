"""Regression detection for ADR-021 (REQ-21-05).

This module compares behavior between app versions:
- Identify breaking changes (new test failures)
- Track fixed tests (tests that now pass)
- Detect output changes (different but valid outputs)
- Measure performance deltas
- Track quality score changes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time

from agentworld.apps.evaluation.scenarios import (
    TestScenario,
    ScenarioResult,
    ScenarioRunner,
)
from agentworld.apps.evaluation.quality import calculate_quality_score


@dataclass
class OutputDiff:
    """Difference in output between versions.

    Represents cases where both versions succeed but produce
    different (but both valid) outputs.

    Attributes:
        scenario_name: Name of the scenario
        step_name: Name of the step with different output
        step_index: Index of the step
        old_output: Output from old version
        new_output: Output from new version
        diff_type: Type of difference (value_change, field_added, field_removed)
        severity: How significant the change is (info, warning, breaking)
    """
    scenario_name: str
    step_name: str
    step_index: int
    old_output: dict[str, Any]
    new_output: dict[str, Any]
    diff_type: str = "value_change"
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "old_output": self.old_output,
            "new_output": self.new_output,
            "diff_type": self.diff_type,
            "severity": self.severity,
        }


@dataclass
class TestDelta:
    """Change in test status between versions.

    Attributes:
        scenario_name: Name of the scenario
        old_passed: Whether it passed in old version
        new_passed: Whether it passed in new version
        old_failures: Failure details from old version
        new_failures: Failure details from new version
    """
    scenario_name: str
    old_passed: bool
    new_passed: bool
    old_failures: list[str] = field(default_factory=list)
    new_failures: list[str] = field(default_factory=list)

    @property
    def is_regression(self) -> bool:
        """True if test newly fails."""
        return self.old_passed and not self.new_passed

    @property
    def is_fix(self) -> bool:
        """True if test newly passes."""
        return not self.old_passed and self.new_passed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "old_passed": self.old_passed,
            "new_passed": self.new_passed,
            "is_regression": self.is_regression,
            "is_fix": self.is_fix,
            "old_failures": self.old_failures,
            "new_failures": self.new_failures,
        }


@dataclass
class PerformanceDelta:
    """Performance change between versions.

    Attributes:
        scenario_name: Name of the scenario
        old_duration_ms: Execution time in old version
        new_duration_ms: Execution time in new version
        change_pct: Percentage change (positive = slower)
    """
    scenario_name: str
    old_duration_ms: float
    new_duration_ms: float

    @property
    def change_pct(self) -> float:
        """Calculate percentage change."""
        if self.old_duration_ms == 0:
            return 0.0
        return ((self.new_duration_ms - self.old_duration_ms) / self.old_duration_ms) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "old_duration_ms": self.old_duration_ms,
            "new_duration_ms": self.new_duration_ms,
            "change_pct": self.change_pct,
        }


@dataclass
class RegressionReport:
    """Comprehensive regression analysis report.

    Compares behavior between two app versions, identifying:
    - Breaking changes (tests that newly fail)
    - Fixed tests (tests that now pass)
    - Output changes (different but valid outputs)
    - Performance changes
    - Quality score changes

    Attributes:
        old_version: Version identifier for baseline
        new_version: Version identifier for comparison
        new_failures: Scenario names that newly fail
        fixed_tests: Scenario names that now pass
        output_changes: Steps with different outputs
        test_deltas: Detailed test status changes
        latency_change_pct: Overall latency change
        throughput_change_pct: Overall throughput change
        performance_deltas: Per-scenario performance changes
        quality_score_delta: Change in quality score
        dimension_changes: Changes in quality dimensions
        is_breaking: True if any regressions exist
        summary: Human-readable summary
        timestamp: When the report was generated
    """
    old_version: str | int
    new_version: str | int

    # Behavioral changes
    new_failures: list[str] = field(default_factory=list)
    fixed_tests: list[str] = field(default_factory=list)
    output_changes: list[OutputDiff] = field(default_factory=list)
    test_deltas: list[TestDelta] = field(default_factory=list)

    # Performance changes
    latency_change_pct: float = 0.0
    throughput_change_pct: float = 0.0
    performance_deltas: list[PerformanceDelta] = field(default_factory=list)

    # Quality changes
    quality_score_delta: float = 0.0
    dimension_changes: dict[str, float] = field(default_factory=dict)

    # Metadata
    is_breaking: bool = False
    summary: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Calculate derived fields."""
        # is_breaking if any new failures
        self.is_breaking = len(self.new_failures) > 0

        # Generate summary if not provided
        if not self.summary:
            self.summary = self._generate_summary()

    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        parts = []

        if self.is_breaking:
            parts.append(f"BREAKING: {len(self.new_failures)} test(s) now failing")

        if self.fixed_tests:
            parts.append(f"Fixed: {len(self.fixed_tests)} test(s)")

        if self.output_changes:
            parts.append(f"Output changes: {len(self.output_changes)}")

        if abs(self.latency_change_pct) > 10:
            direction = "slower" if self.latency_change_pct > 0 else "faster"
            parts.append(f"Performance: {abs(self.latency_change_pct):.1f}% {direction}")

        if abs(self.quality_score_delta) > 0.05:
            direction = "improved" if self.quality_score_delta > 0 else "degraded"
            parts.append(f"Quality: {direction} by {abs(self.quality_score_delta):.2f}")

        if not parts:
            return "No significant changes detected"

        return "; ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "new_failures": self.new_failures,
            "fixed_tests": self.fixed_tests,
            "output_changes": [o.to_dict() for o in self.output_changes],
            "test_deltas": [t.to_dict() for t in self.test_deltas],
            "latency_change_pct": self.latency_change_pct,
            "throughput_change_pct": self.throughput_change_pct,
            "performance_deltas": [p.to_dict() for p in self.performance_deltas],
            "quality_score_delta": self.quality_score_delta,
            "dimension_changes": self.dimension_changes,
            "is_breaking": self.is_breaking,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


def _compare_outputs(
    old_result: dict[str, Any],
    new_result: dict[str, Any],
) -> tuple[bool, str, str]:
    """Compare outputs from two versions.

    Args:
        old_result: Result from old version
        new_result: Result from new version

    Returns:
        Tuple of (is_different, diff_type, severity)
    """
    old_data = old_result.get("data", {})
    new_data = new_result.get("data", {})

    # Check for removed fields
    old_keys = set(old_data.keys()) if isinstance(old_data, dict) else set()
    new_keys = set(new_data.keys()) if isinstance(new_data, dict) else set()

    if old_keys - new_keys:
        return True, "field_removed", "warning"

    if new_keys - old_keys:
        return True, "field_added", "info"

    # Check for value changes
    if old_data != new_data:
        return True, "value_change", "info"

    return False, "", ""


def _find_output_differences(
    scenario_name: str,
    old_results: list[dict],
    new_results: list[dict],
) -> list[OutputDiff]:
    """Find output differences between scenario runs.

    Args:
        scenario_name: Name of the scenario
        old_results: Step results from old version
        new_results: Step results from new version

    Returns:
        List of OutputDiff for differing outputs
    """
    diffs = []

    # Compare step by step
    for i, (old_step, new_step) in enumerate(zip(old_results, new_results)):
        # Only compare if both succeeded
        old_success = old_step.get("action_result", {}).get("success", False)
        new_success = new_step.get("action_result", {}).get("success", False)

        if old_success and new_success:
            is_diff, diff_type, severity = _compare_outputs(
                old_step.get("action_result", {}),
                new_step.get("action_result", {}),
            )

            if is_diff:
                diffs.append(OutputDiff(
                    scenario_name=scenario_name,
                    step_name=old_step.get("step_name", f"Step {i}"),
                    step_index=i,
                    old_output=old_step.get("action_result", {}),
                    new_output=new_step.get("action_result", {}),
                    diff_type=diff_type,
                    severity=severity,
                ))

    return diffs


async def run_scenarios_for_version(
    app: Any,
    scenarios: list[TestScenario],
) -> tuple[list[ScenarioResult], float]:
    """Run scenarios and return results with total duration.

    Args:
        app: App instance to test
        scenarios: Scenarios to run

    Returns:
        Tuple of (results, total_duration_ms)
    """
    runner = ScenarioRunner(app)
    results = []
    total_duration = 0.0

    for scenario in scenarios:
        result = await runner.run_scenario(scenario)
        results.append(result)
        total_duration += result.duration_ms

    return results, total_duration


async def detect_regressions(
    app_old: Any,
    app_new: Any,
    scenarios: list[TestScenario],
    old_version: str | int = "old",
    new_version: str | int = "new",
) -> RegressionReport:
    """Compare behavior between two app versions.

    Runs the same scenarios against both versions and compares:
    - Which tests pass/fail
    - Output differences for passing tests
    - Performance differences
    - Quality score changes

    Args:
        app_old: Old version of the app
        app_new: New version of the app
        scenarios: Test scenarios to run
        old_version: Version identifier for old app
        new_version: Version identifier for new app

    Returns:
        RegressionReport with detailed comparison
    """
    # Run scenarios on both versions
    old_results, old_total_duration = await run_scenarios_for_version(app_old, scenarios)
    new_results, new_total_duration = await run_scenarios_for_version(app_new, scenarios)

    # Initialize report fields
    new_failures: list[str] = []
    fixed_tests: list[str] = []
    output_changes: list[OutputDiff] = []
    test_deltas: list[TestDelta] = []
    performance_deltas: list[PerformanceDelta] = []

    # Compare results
    for old_result, new_result in zip(old_results, new_results):
        scenario_name = old_result.scenario_name

        # Track test status changes
        old_passed = old_result.passed
        new_passed = new_result.passed

        delta = TestDelta(
            scenario_name=scenario_name,
            old_passed=old_passed,
            new_passed=new_passed,
            old_failures=[f.error for f in old_result.failures] if old_result.failures else [],
            new_failures=[f.error for f in new_result.failures] if new_result.failures else [],
        )
        test_deltas.append(delta)

        if delta.is_regression:
            new_failures.append(scenario_name)
        elif delta.is_fix:
            fixed_tests.append(scenario_name)

        # Find output differences for passing tests
        if old_passed and new_passed:
            old_step_dicts = [r.to_dict() for r in old_result.step_results]
            new_step_dicts = [r.to_dict() for r in new_result.step_results]
            diffs = _find_output_differences(scenario_name, old_step_dicts, new_step_dicts)
            output_changes.extend(diffs)

        # Track performance
        performance_deltas.append(PerformanceDelta(
            scenario_name=scenario_name,
            old_duration_ms=old_result.duration_ms,
            new_duration_ms=new_result.duration_ms,
        ))

    # Calculate overall performance changes
    latency_change_pct = 0.0
    if old_total_duration > 0:
        latency_change_pct = ((new_total_duration - old_total_duration) / old_total_duration) * 100

    # Throughput (scenarios per second) - inverse of latency
    throughput_change_pct = -latency_change_pct if latency_change_pct != 0 else 0.0

    # Calculate quality score changes if apps have definitions
    quality_score_delta = 0.0
    dimension_changes: dict[str, float] = {}

    try:
        if hasattr(app_old, "definition") and hasattr(app_new, "definition"):
            old_quality = await calculate_quality_score(app_old.definition)
            new_quality = await calculate_quality_score(app_new.definition)

            quality_score_delta = new_quality.overall_score - old_quality.overall_score

            # Track dimension changes
            for dimension, old_score in old_quality.dimension_scores.items():
                new_score = new_quality.dimension_scores.get(dimension, old_score)
                if old_score != new_score:
                    dimension_changes[dimension] = new_score - old_score
    except Exception:
        # Quality scoring might not be available
        pass

    return RegressionReport(
        old_version=old_version,
        new_version=new_version,
        new_failures=new_failures,
        fixed_tests=fixed_tests,
        output_changes=output_changes,
        test_deltas=test_deltas,
        latency_change_pct=latency_change_pct,
        throughput_change_pct=throughput_change_pct,
        performance_deltas=performance_deltas,
        quality_score_delta=quality_score_delta,
        dimension_changes=dimension_changes,
    )


def is_safe_to_deploy(report: RegressionReport, thresholds: dict[str, float] | None = None) -> tuple[bool, list[str]]:
    """Determine if changes are safe to deploy based on regression report.

    Args:
        report: Regression report to evaluate
        thresholds: Custom thresholds for evaluation:
            - max_latency_increase_pct: Max allowed latency increase (default 20)
            - min_quality_score: Min allowed quality score delta (default -0.1)
            - allow_output_changes: Whether output changes are allowed (default True)

    Returns:
        Tuple of (is_safe, list of reasons if not safe)
    """
    if thresholds is None:
        thresholds = {}

    max_latency_increase = thresholds.get("max_latency_increase_pct", 20.0)
    min_quality_delta = thresholds.get("min_quality_score", -0.1)
    allow_output_changes = thresholds.get("allow_output_changes", True)

    reasons = []

    # Check for breaking changes
    if report.is_breaking:
        reasons.append(f"Breaking changes: {len(report.new_failures)} test(s) now failing")

    # Check latency
    if report.latency_change_pct > max_latency_increase:
        reasons.append(f"Latency increased by {report.latency_change_pct:.1f}% (threshold: {max_latency_increase}%)")

    # Check quality
    if report.quality_score_delta < min_quality_delta:
        reasons.append(f"Quality degraded by {abs(report.quality_score_delta):.2f} (threshold: {abs(min_quality_delta)})")

    # Check output changes
    if not allow_output_changes and report.output_changes:
        reasons.append(f"Output changes detected: {len(report.output_changes)} step(s)")

    return len(reasons) == 0, reasons


def format_regression_report(report: RegressionReport) -> str:
    """Format regression report as human-readable text.

    Args:
        report: Report to format

    Returns:
        Formatted string
    """
    lines = [
        "=" * 60,
        "REGRESSION REPORT",
        "=" * 60,
        f"Comparing: {report.old_version} → {report.new_version}",
        f"Status: {'BREAKING' if report.is_breaking else 'OK'}",
        "",
        "SUMMARY",
        "-" * 40,
        report.summary,
        "",
    ]

    if report.new_failures:
        lines.extend([
            "NEW FAILURES (Regressions)",
            "-" * 40,
        ])
        for name in report.new_failures:
            lines.append(f"  ❌ {name}")
        lines.append("")

    if report.fixed_tests:
        lines.extend([
            "FIXED TESTS",
            "-" * 40,
        ])
        for name in report.fixed_tests:
            lines.append(f"  ✅ {name}")
        lines.append("")

    if report.output_changes:
        lines.extend([
            "OUTPUT CHANGES",
            "-" * 40,
        ])
        for diff in report.output_changes:
            lines.append(f"  [{diff.severity.upper()}] {diff.scenario_name}:{diff.step_name}")
            lines.append(f"    Type: {diff.diff_type}")
        lines.append("")

    lines.extend([
        "PERFORMANCE",
        "-" * 40,
        f"  Latency change: {report.latency_change_pct:+.1f}%",
        f"  Throughput change: {report.throughput_change_pct:+.1f}%",
        "",
    ])

    if report.quality_score_delta != 0 or report.dimension_changes:
        lines.extend([
            "QUALITY",
            "-" * 40,
            f"  Score change: {report.quality_score_delta:+.2f}",
        ])
        for dim, change in report.dimension_changes.items():
            lines.append(f"    {dim}: {change:+.2f}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
