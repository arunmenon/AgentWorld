"""App evaluation framework for ADR-021.

This module provides tools for evaluating app definitions:
- Quality metrics: Score app definitions on completeness, documentation, etc.
- Scenario runner: Execute test scenarios against apps
- Benchmarks: Standard benchmark apps for comparison
- Regression detection: Compare behavior between versions
"""

from agentworld.apps.evaluation.quality import (
    QualityReport,
    QualitySuggestion,
    calculate_quality_score,
    score_completeness,
    score_documentation,
    score_validation,
    score_error_handling,
    score_state_safety,
    score_consistency,
    get_quality_level,
)
from agentworld.apps.evaluation.scenarios import (
    TestScenario,
    TestStep,
    StepExpectation,
    ScenarioResult,
    StepResult,
    StepFailure,
    ScenarioRunner,
    parse_scenario_yaml,
)
from agentworld.apps.evaluation.benchmarks import (
    BenchmarkResult,
    BenchmarkSuite,
    get_benchmark_apps,
    run_benchmark,
)

__all__ = [
    # Quality
    "QualityReport",
    "QualitySuggestion",
    "calculate_quality_score",
    "score_completeness",
    "score_documentation",
    "score_validation",
    "score_error_handling",
    "score_state_safety",
    "score_consistency",
    "get_quality_level",
    # Scenarios
    "TestScenario",
    "TestStep",
    "StepExpectation",
    "ScenarioResult",
    "StepResult",
    "StepFailure",
    "ScenarioRunner",
    "parse_scenario_yaml",
    # Benchmarks
    "BenchmarkResult",
    "BenchmarkSuite",
    "get_benchmark_apps",
    "run_benchmark",
]
