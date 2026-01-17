"""Export API endpoints."""

import io
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from agentworld.api.schemas.export import (
    DPOExportRequest,
    ExportListResponse,
    ExportManifestResponse,
    ExportRequest,
    ExportResponse,
)
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.services.export import (
    DPOConfig,
    ExportFormat,
    ExportOptions,
    ExportService,
    RedactionProfile,
)

router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


def get_export_service(repo: Repository) -> ExportService:
    """Get export service instance."""
    return ExportService(repository=repo)


@router.get("/simulations/{simulation_id}/export/formats", response_model=ExportListResponse)
async def list_export_formats(simulation_id: str):
    """List available export formats for a simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    message_count = repo.count_messages(simulation_id)
    evaluations = repo.get_evaluations_for_simulation(simulation_id)

    formats = ["jsonl", "openai", "anthropic", "sharegpt", "alpaca"]
    if evaluations:
        formats.append("dpo")

    return ExportListResponse(
        simulation_id=simulation_id,
        available_formats=formats,
        message_count=message_count,
        has_evaluations=len(evaluations) > 0,
    )


@router.get("/simulations/{simulation_id}/export")
async def export_simulation(
    simulation_id: str,
    format: str = Query("jsonl", description="Export format"),
    redaction: str = Query("basic", description="Redaction profile"),
    anonymize: bool = Query(False, description="Anonymize agent names"),
    min_score: float | None = Query(None, ge=0.0, le=1.0, description="Min score filter"),
    inline: bool = Query(False, description="Return data inline instead of file download"),
):
    """Export simulation data in specified format.

    Returns JSONL file download by default, or inline JSON if inline=true.
    """
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Validate format
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_FORMAT",
            "message": f"Invalid format: {format}. Valid: jsonl, openai, anthropic, sharegpt, alpaca, dpo",
        })

    # Validate redaction profile
    try:
        redaction_profile = RedactionProfile(redaction)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_REDACTION_PROFILE",
            "message": f"Invalid redaction: {redaction}. Valid: none, basic, strict",
        })

    # Check if DPO format requires evaluations
    if export_format == ExportFormat.DPO:
        evaluations = repo.get_evaluations_for_simulation(simulation_id)
        if not evaluations:
            raise HTTPException(status_code=400, detail={
                "code": "EVALUATIONS_REQUIRED",
                "message": "DPO format requires evaluation data. Run evaluations first.",
            })

    # Create export options
    options = ExportOptions(
        redaction_profile=redaction_profile,
        anonymize=anonymize,
        min_score=min_score,
        include_manifest=True,
    )

    service = get_export_service(repo)

    # Get data based on format
    if export_format == ExportFormat.JSONL:
        data = service.export_jsonl(simulation_id, options)
    elif export_format == ExportFormat.OPENAI:
        data = service.export_openai_format(simulation_id, options)
    elif export_format == ExportFormat.ANTHROPIC:
        data = service.export_anthropic_format(simulation_id, options)
    elif export_format == ExportFormat.SHAREGPT:
        data = service.export_sharegpt_format(simulation_id, options)
    elif export_format == ExportFormat.ALPACA:
        data = service.export_alpaca_format(simulation_id, options)
    elif export_format == ExportFormat.DPO:
        evaluations = repo.get_evaluations_for_simulation(simulation_id)
        data = service.export_dpo_pairs(simulation_id, evaluations, options)
    else:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_FORMAT",
            "message": f"Unsupported format: {format}",
        })

    if inline:
        # Return as JSON response
        manifest = service._create_manifest(
            simulation_ids=[simulation_id],
            format_name=export_format.value,
            record_count=len(data),
            options=options
        )

        return ExportResponse(
            simulation_id=simulation_id,
            format=format,
            record_count=len(data),
            manifest=ExportManifestResponse(**manifest.to_dict()),
            data=data,
        )

    # Return as file download
    content = "\n".join(json.dumps(record, default=str) for record in data)
    buffer = io.BytesIO(content.encode("utf-8"))

    filename = f"{simulation_id}_{format}.jsonl"
    return StreamingResponse(
        buffer,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(len(data)),
        }
    )


@router.post("/simulations/{simulation_id}/export", response_model=ExportResponse)
async def export_simulation_post(simulation_id: str, request: ExportRequest):
    """Export simulation data with detailed options via POST.

    Useful for complex export configurations.
    """
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Validate format
    try:
        export_format = ExportFormat(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_FORMAT",
            "message": f"Invalid format: {request.format}",
        })

    # Validate redaction profile
    try:
        redaction_profile = RedactionProfile(request.redaction_profile)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_REDACTION_PROFILE",
            "message": f"Invalid redaction profile: {request.redaction_profile}",
        })

    # Handle DPO-specific config
    dpo_config = None
    if export_format == ExportFormat.DPO and isinstance(request, DPOExportRequest):
        dpo_config = DPOConfig(
            source=request.dpo_source,
            chosen_threshold=request.chosen_threshold,
            rejected_threshold=request.rejected_threshold,
            min_score_gap=request.min_score_gap,
        )

    # Create export options
    options = ExportOptions(
        redaction_profile=redaction_profile,
        anonymize=request.anonymize,
        min_score=request.min_score,
        excluded_agents=request.excluded_agents,
        include_manifest=request.include_manifest,
        dpo_config=dpo_config,
    )

    service = get_export_service(repo)

    # Get data based on format
    if export_format == ExportFormat.JSONL:
        data = service.export_jsonl(simulation_id, options)
    elif export_format == ExportFormat.OPENAI:
        data = service.export_openai_format(simulation_id, options)
    elif export_format == ExportFormat.ANTHROPIC:
        data = service.export_anthropic_format(simulation_id, options)
    elif export_format == ExportFormat.SHAREGPT:
        data = service.export_sharegpt_format(simulation_id, options)
    elif export_format == ExportFormat.ALPACA:
        data = service.export_alpaca_format(simulation_id, options)
    elif export_format == ExportFormat.DPO:
        evaluations = repo.get_evaluations_for_simulation(simulation_id)
        if not evaluations:
            raise HTTPException(status_code=400, detail={
                "code": "EVALUATIONS_REQUIRED",
                "message": "DPO format requires evaluation data",
            })
        data = service.export_dpo_pairs(simulation_id, evaluations, options)
    else:
        data = []

    # Create manifest
    manifest = None
    if request.include_manifest:
        manifest_obj = service._create_manifest(
            simulation_ids=[simulation_id],
            format_name=export_format.value,
            record_count=len(data),
            options=options
        )
        manifest = ExportManifestResponse(**manifest_obj.to_dict())

    return ExportResponse(
        simulation_id=simulation_id,
        format=request.format,
        record_count=len(data),
        manifest=manifest,
        data=data,
    )


@router.get("/simulations/{simulation_id}/export/manifest", response_model=ExportManifestResponse)
async def get_export_manifest(
    simulation_id: str,
    format: str = Query("jsonl", description="Export format"),
):
    """Get export manifest without downloading data.

    Useful for checking export metadata before downloading.
    """
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_FORMAT",
            "message": f"Invalid format: {format}",
        })

    service = get_export_service(repo)
    message_count = repo.count_messages(simulation_id)

    options = ExportOptions()
    manifest = service._create_manifest(
        simulation_ids=[simulation_id],
        format_name=export_format.value,
        record_count=message_count,
        options=options
    )

    return ExportManifestResponse(**manifest.to_dict())
