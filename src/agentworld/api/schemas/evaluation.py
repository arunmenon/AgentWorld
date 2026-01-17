"""Evaluation API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Request to run evaluations on a simulation."""

    evaluator_names: list[str] | None = Field(
        None,
        description="List of evaluator names to run. None = all available"
    )
    message_ids: list[str] | None = Field(
        None,
        description="Specific message IDs to evaluate. None = all messages"
    )
    async_mode: bool = Field(
        False,
        description="Run evaluation asynchronously, returning job_id"
    )


class EvaluationResultResponse(BaseModel):
    """Single evaluation result."""

    id: str
    message_id: str
    evaluator_name: str
    score: float = Field(ge=0.0, le=1.0)
    explanation: str | None = None
    evaluator_version: str
    judge_model: str | None = None
    judge_prompt_hash: str | None = None
    input_hash: str
    cost_usd: float = 0.0
    latency_ms: int = 0
    passed: bool = True
    created_at: datetime | None = None


class EvaluationListResponse(BaseModel):
    """List of evaluation results."""

    evaluations: list[EvaluationResultResponse]
    total: int
    simulation_id: str


class EvaluationSummary(BaseModel):
    """Aggregated evaluation summary."""

    simulation_id: str
    evaluator_summaries: dict[str, "EvaluatorSummary"]
    total_evaluations: int
    average_score: float
    pass_rate: float
    total_cost_usd: float
    total_latency_ms: int


class EvaluatorSummary(BaseModel):
    """Summary for a single evaluator."""

    evaluator_name: str
    count: int
    average_score: float
    min_score: float
    max_score: float
    pass_rate: float
    total_cost_usd: float


class JobStatusResponse(BaseModel):
    """Status of an async job."""

    job_id: str
    status: str = Field(description="pending | running | completed | failed")
    progress: dict[str, Any] | None = Field(
        None,
        description="Progress info: {current: int, total: int}"
    )
    result: Any | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class RunEvaluationResponse(BaseModel):
    """Response from running evaluations."""

    simulation_id: str
    job_id: str | None = Field(None, description="Set if async_mode=true")
    status: str = "completed"
    evaluations_run: int = 0
    message: str = ""


# Allow forward references
EvaluationSummary.model_rebuild()
