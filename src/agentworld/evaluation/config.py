"""Evaluation system configuration per ADR-010."""

from dataclasses import dataclass


@dataclass
class ValidationConfig:
    """Configuration for validation thresholds."""

    persona_adherence_threshold: float = 0.7
    consistency_threshold: float = 0.6
    coherence_threshold: float = 0.5
    use_separate_model: bool = False  # Use different model to reduce bias
    evaluation_model: str = "openai/gpt-4o-mini"  # Cheaper model for evaluation
    max_validations_per_run: int = 100  # Budget control
    sampling_rate: float = 1.0  # Sample rate for validation (1.0 = all)


@dataclass
class EvaluationConfig:
    """Configuration for the evaluation system."""

    # Model selection
    use_separate_evaluation_model: bool = True
    evaluation_model: str = "openai/gpt-4o-mini"  # Cheaper, reduces bias

    # Budget controls
    max_validation_calls: int = 100
    max_extraction_calls: int = 50
    validation_sampling_rate: float = 0.3  # Sample 30% of responses

    # Thresholds
    persona_adherence_threshold: float = 0.7
    consistency_threshold: float = 0.6
    coherence_threshold: float = 0.5

    # A/B testing
    default_runs_per_variant: int = 3
    significance_threshold: float = 0.1  # 10% difference for significance
