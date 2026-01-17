"""Export API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Request to export simulation data."""

    format: str = Field(
        "jsonl",
        description="Export format: jsonl, openai, anthropic, sharegpt, alpaca, dpo"
    )
    redaction_profile: str = Field(
        "basic",
        description="Redaction profile: none, basic, strict"
    )
    anonymize: bool = Field(
        False,
        description="Anonymize agent names"
    )
    min_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum evaluation score filter"
    )
    excluded_agents: list[str] = Field(
        default_factory=list,
        description="Agent IDs to exclude from export"
    )
    include_manifest: bool = Field(
        True,
        description="Include manifest file with export"
    )


class DPOExportRequest(ExportRequest):
    """Request for DPO format export."""

    format: str = "dpo"
    dpo_source: str = Field(
        "score_ranking",
        description="DPO pair source: score_ranking, ab_preference, multi_response"
    )
    chosen_threshold: float = Field(0.75, ge=0.0, le=1.0)
    rejected_threshold: float = Field(0.25, ge=0.0, le=1.0)
    min_score_gap: float = Field(0.2, ge=0.0, le=1.0)


class ExportManifestResponse(BaseModel):
    """Export manifest."""

    manifest_version: str = "1.0"
    simulation_ids: list[str]
    run_ids: list[str] = Field(default_factory=list)
    config_hash: str
    persona_panel_hash: str
    seed: int | None = None
    exporter_version: str = "1.0.0"
    format_version: str
    filters_applied: dict[str, Any]
    record_count: int
    created_at: str


class ExportResponse(BaseModel):
    """Response from export operation."""

    simulation_id: str
    format: str
    record_count: int
    manifest: ExportManifestResponse | None = None
    download_url: str | None = Field(
        None,
        description="URL to download exported file (if persisted)"
    )
    data: list[dict[str, Any]] | None = Field(
        None,
        description="Inline data (for small exports)"
    )


class ExportListResponse(BaseModel):
    """List of available export formats."""

    simulation_id: str
    available_formats: list[str]
    message_count: int
    has_evaluations: bool
