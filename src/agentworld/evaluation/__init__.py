"""Evaluation and metrics system per ADR-010.

This module provides comprehensive evaluation capabilities including:
- MetricsCollector: Collect behavioral, memory, network, and cost metrics
- Validator: LLM-based validation for persona adherence, consistency, coherence
- ResultsExtractor: Extract structured data (opinions, themes, quotes) from outputs
- ExperimentRunner: A/B testing support for comparative experiments
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
]
