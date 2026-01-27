"""Evaluation and metrics system per ADR-010 and ADR-020.

This module provides comprehensive evaluation capabilities including:
- MetricsCollector: Collect behavioral, memory, network, and cost metrics
- Validator: LLM-based validation for persona adherence, consistency, coherence
- ResultsExtractor: Extract structured data (opinions, themes, quotes) from outputs
- ExperimentRunner: A/B testing support for comparative experiments

ADR-020 additions (τ-bench inspired evaluation):
- Reliability: Pass^k computation for measuring agent consistency
- StateVerification: Goal state verification for task completion
- FaultClassifier: Categorize failures by assignment and type
- PolicyEngine: Evaluate agent compliance with rules
"""

from agentworld.evaluation.client import (
    JSONParseError,
    LLMClient,
    LLMResponse,
    SchemaValidationError,
)
from agentworld.evaluation.config import EvaluationConfig, ValidationConfig
from agentworld.evaluation.experiment import (
    ABTestResult,
    ExperimentRunner,
    RunResult,
    StatisticalComparison,
    VariantResults,
    compute_cohens_d,
    interpret_effect_size,
)
from agentworld.evaluation.extractors import (
    Opinion,
    Quote,
    ResultsExtractor,
    Theme,
)
from agentworld.evaluation.metrics import (
    LLMCallEvent,
    MemoryEvent,
    MessageEvent,
    MetricsCollector,
    RetrievalEvent,
    SimulationMetrics,
)
from agentworld.evaluation.validators import (
    ValidationResult,
    Validator,
)
from agentworld.evaluation.evaluators import (
    EvaluationResult,
    EvaluationContext,
    EvaluatorProtocol,
    EvaluatorRegistry,
    BaseEvaluator,
    LLMEvaluator,
    PersonaAdherenceEvaluator,
    CoherenceEvaluator,
    RelevanceEvaluator,
    ConsistencyEvaluator,
    LengthCheckEvaluator,
    KeywordFilterEvaluator,
    create_default_registry,
)

# ADR-020: τ-bench inspired evaluation
from agentworld.evaluation.reliability import (
    compute_pass_k,
    compute_all_pass_k,
    interpret_reliability,
    compute_reliability_gap,
    BenchmarkMetrics,
    ReliabilityComparison,
)
from agentworld.evaluation.state_verification import (
    StateDiff,
    StateVerificationResult,
    compute_state_hash,
    compare_states,
    check_required_outputs,
    verify_goal_state,
    verify_action_sequence,
)
from agentworld.evaluation.fault_classifier import (
    ClassificationContext,
    FaultClassifier,
    FaultSummary,
    classify_trial_failure,
)
from agentworld.evaluation.policy_engine import (
    TrajectoryAction,
    PolicyEngine,
    check_trajectory_compliance,
    get_default_policies,
    PAYMENT_POLICIES,
    SHOPPING_POLICIES,
)

__all__ = [
    # Client
    "LLMClient",
    "LLMResponse",
    "JSONParseError",
    "SchemaValidationError",
    # Config
    "ValidationConfig",
    "EvaluationConfig",
    # Metrics
    "SimulationMetrics",
    "MetricsCollector",
    "MessageEvent",
    "MemoryEvent",
    "RetrievalEvent",
    "LLMCallEvent",
    # Validators
    "ValidationResult",
    "Validator",
    # Extractors
    "Opinion",
    "Theme",
    "Quote",
    "ResultsExtractor",
    # Experiment
    "RunResult",
    "VariantResults",
    "StatisticalComparison",
    "ABTestResult",
    "ExperimentRunner",
    "compute_cohens_d",
    "interpret_effect_size",
    # Evaluators
    "EvaluationResult",
    "EvaluationContext",
    "EvaluatorProtocol",
    "EvaluatorRegistry",
    "BaseEvaluator",
    "LLMEvaluator",
    "PersonaAdherenceEvaluator",
    "CoherenceEvaluator",
    "RelevanceEvaluator",
    "ConsistencyEvaluator",
    "LengthCheckEvaluator",
    "KeywordFilterEvaluator",
    "create_default_registry",
    # ADR-020: Reliability (pass^k)
    "compute_pass_k",
    "compute_all_pass_k",
    "interpret_reliability",
    "compute_reliability_gap",
    "BenchmarkMetrics",
    "ReliabilityComparison",
    # ADR-020: State Verification
    "StateDiff",
    "StateVerificationResult",
    "compute_state_hash",
    "compare_states",
    "check_required_outputs",
    "verify_goal_state",
    "verify_action_sequence",
    # ADR-020: Fault Classification
    "ClassificationContext",
    "FaultClassifier",
    "FaultSummary",
    "classify_trial_failure",
    # ADR-020: Policy Engine
    "TrajectoryAction",
    "PolicyEngine",
    "check_trajectory_compliance",
    "get_default_policies",
    "PAYMENT_POLICIES",
    "SHOPPING_POLICIES",
]
