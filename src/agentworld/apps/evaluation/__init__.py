"""App evaluation framework for ADR-021.

This module provides tools for evaluating app definitions:
- Quality metrics: Score app definitions on completeness, documentation, etc.
- Scenario runner: Execute test scenarios against apps
- Benchmarks: Standard benchmark apps for comparison
- Agent evaluation: Evaluate agent interactions with apps
- Regression detection: Compare behavior between versions
- Coverage analysis: Measure test coverage of app logic
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
from agentworld.apps.evaluation.agent_eval import (
    EvaluationTask,
    ActionRecord,
    ErrorPattern,
    AgentEvaluation,
    classify_error,
    analyze_error_patterns,
    calculate_efficiency,
    evaluate_comprehension,
    evaluate_agent,
    create_evaluation_task,
    PAYMENT_EVALUATION_TASKS,
)
from agentworld.apps.evaluation.regression import (
    OutputDiff,
    TestDelta,
    PerformanceDelta,
    RegressionReport,
    detect_regressions,
    is_safe_to_deploy,
    format_regression_report,
)
from agentworld.apps.evaluation.coverage import (
    BranchInfo,
    ExecutionStep,
    ExecutionTrace,
    CoverageReport,
    ControlFlowGraph,
    build_control_flow_graph,
    count_branches,
    count_blocks,
    analyze_coverage,
    generate_coverage_recommendations,
    format_coverage_report,
    create_trace_from_scenario_result,
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
    # Agent Evaluation (REQ-21-03)
    "EvaluationTask",
    "ActionRecord",
    "ErrorPattern",
    "AgentEvaluation",
    "classify_error",
    "analyze_error_patterns",
    "calculate_efficiency",
    "evaluate_comprehension",
    "evaluate_agent",
    "create_evaluation_task",
    "PAYMENT_EVALUATION_TASKS",
    # Regression Detection (REQ-21-05)
    "OutputDiff",
    "TestDelta",
    "PerformanceDelta",
    "RegressionReport",
    "detect_regressions",
    "is_safe_to_deploy",
    "format_regression_report",
    # Coverage Analysis (REQ-21-06)
    "BranchInfo",
    "ExecutionStep",
    "ExecutionTrace",
    "CoverageReport",
    "ControlFlowGraph",
    "build_control_flow_graph",
    "count_branches",
    "count_blocks",
    "analyze_coverage",
    "generate_coverage_recommendations",
    "format_coverage_report",
    "create_trace_from_scenario_result",
]
