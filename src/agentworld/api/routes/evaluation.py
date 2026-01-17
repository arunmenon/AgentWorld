"""Evaluation API endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from agentworld.api.schemas.evaluation import (
    EvaluationListResponse,
    EvaluationRequest,
    EvaluationResultResponse,
    EvaluationSummary,
    EvaluatorSummary,
    JobStatusResponse,
    RunEvaluationResponse,
)
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository

router = APIRouter()


def get_repo() -> Repository:
    """Get a repository instance."""
    init_db()
    return Repository()


@router.post(
    "/simulations/{simulation_id}/evaluate",
    response_model=RunEvaluationResponse
)
async def run_evaluation(simulation_id: str, request: EvaluationRequest):
    """Run evaluators on simulation messages.

    If async_mode=true, returns immediately with a job_id.
    Otherwise, runs evaluation synchronously and returns results.
    """
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    # Get messages to evaluate
    messages = repo.get_messages_for_simulation(simulation_id)
    if request.message_ids:
        messages = [m for m in messages if m["id"] in request.message_ids]

    if not messages:
        return RunEvaluationResponse(
            simulation_id=simulation_id,
            status="completed",
            evaluations_run=0,
            message="No messages to evaluate",
        )

    if request.async_mode:
        # TODO: Implement async job queue
        job_id = str(uuid.uuid4())
        return RunEvaluationResponse(
            simulation_id=simulation_id,
            job_id=job_id,
            status="pending",
            message="Evaluation job queued",
        )

    # Synchronous evaluation
    from agentworld.evaluation import (
        EvaluationContext,
        create_default_registry,
    )
    from agentworld.evaluation.client import LLMClient
    from agentworld.llm.provider import get_provider

    # Check if any LLM-based evaluators are requested
    llm_evaluators = {"persona_adherence", "coherence", "relevance", "consistency"}
    requested_evaluators = set(request.evaluator_names or ["length_check", "keyword_filter"])
    needs_llm = bool(requested_evaluators & llm_evaluators)

    # Create evaluator registry
    llm_client = None
    if needs_llm:
        provider = get_provider()
        llm_client = LLMClient(provider)

    registry = create_default_registry(llm_client=llm_client)

    # Get agents for context
    agents = repo.get_agents_for_simulation(simulation_id)
    agent_map = {a["id"]: a for a in agents}

    evaluations_saved = 0

    for msg in messages:
        agent = agent_map.get(msg.get("sender_id", ""))
        persona_context = None
        if agent:
            traits = agent.get("traits", {})
            persona_context = f"Name: {agent.get('name')}\nTraits: {traits}"

        context = EvaluationContext(
            message_id=msg["id"],
            message_content=msg.get("content", ""),
            sender_id=msg.get("sender_id", ""),
            sender_name=agent.get("name") if agent else None,
            persona_context=persona_context,
        )

        # Run heuristic evaluators
        evaluator_names = request.evaluator_names or ["length_check", "keyword_filter"]
        results = await registry.evaluate_message(context, evaluator_names)

        for result in results:
            eval_data = result.to_dict()
            eval_data["message_id"] = msg["id"]
            try:
                repo.save_evaluation(eval_data)
                evaluations_saved += 1
            except RuntimeError:
                # Model not available yet, skip saving
                pass

    return RunEvaluationResponse(
        simulation_id=simulation_id,
        status="completed",
        evaluations_run=evaluations_saved,
        message=f"Evaluated {len(messages)} messages",
    )


@router.get(
    "/simulations/{simulation_id}/evaluations",
    response_model=EvaluationListResponse
)
async def get_evaluations(
    simulation_id: str,
    evaluator_name: str | None = Query(None, description="Filter by evaluator"),
    min_score: float | None = Query(None, ge=0.0, le=1.0, description="Minimum score filter"),
    max_score: float | None = Query(None, ge=0.0, le=1.0, description="Maximum score filter"),
):
    """Get evaluation results for a simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    evaluations = repo.get_evaluations_for_simulation(
        simulation_id,
        evaluator_name=evaluator_name
    )

    # Apply score filters
    if min_score is not None:
        evaluations = [e for e in evaluations if e.get("score", 0) >= min_score]
    if max_score is not None:
        evaluations = [e for e in evaluations if e.get("score", 1) <= max_score]

    responses = [
        EvaluationResultResponse(
            id=e.get("id", ""),
            message_id=e.get("message_id", ""),
            evaluator_name=e.get("evaluator_name", ""),
            score=e.get("score", 0.0),
            explanation=e.get("explanation"),
            evaluator_version=e.get("evaluator_version", "1.0.0"),
            judge_model=e.get("judge_model"),
            judge_prompt_hash=e.get("judge_prompt_hash"),
            input_hash=e.get("input_hash", ""),
            cost_usd=e.get("cost_usd", 0.0),
            latency_ms=e.get("latency_ms", 0),
            passed=e.get("passed", True),
            created_at=e.get("created_at"),
        )
        for e in evaluations
    ]

    return EvaluationListResponse(
        evaluations=responses,
        total=len(responses),
        simulation_id=simulation_id,
    )


@router.get(
    "/simulations/{simulation_id}/evaluations/summary",
    response_model=EvaluationSummary
)
async def get_evaluation_summary(simulation_id: str):
    """Get aggregated evaluation summary for a simulation."""
    repo = get_repo()
    sim = repo.get_simulation(simulation_id)

    if not sim:
        raise HTTPException(status_code=404, detail={
            "code": "SIMULATION_NOT_FOUND",
            "message": f"Simulation '{simulation_id}' not found",
        })

    evaluations = repo.get_evaluations_for_simulation(simulation_id)

    if not evaluations:
        return EvaluationSummary(
            simulation_id=simulation_id,
            evaluator_summaries={},
            total_evaluations=0,
            average_score=0.0,
            pass_rate=0.0,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )

    # Group by evaluator
    by_evaluator: dict[str, list] = {}
    for e in evaluations:
        name = e.get("evaluator_name", "unknown")
        if name not in by_evaluator:
            by_evaluator[name] = []
        by_evaluator[name].append(e)

    # Build summaries
    evaluator_summaries = {}
    total_score = 0.0
    total_passed = 0
    total_cost = 0.0
    total_latency = 0

    for name, evals in by_evaluator.items():
        scores = [e.get("score", 0.0) for e in evals]
        passed_count = sum(1 for e in evals if e.get("passed", False))
        cost = sum(e.get("cost_usd", 0.0) for e in evals)

        evaluator_summaries[name] = EvaluatorSummary(
            evaluator_name=name,
            count=len(evals),
            average_score=sum(scores) / len(scores) if scores else 0.0,
            min_score=min(scores) if scores else 0.0,
            max_score=max(scores) if scores else 0.0,
            pass_rate=passed_count / len(evals) if evals else 0.0,
            total_cost_usd=cost,
        )

        total_score += sum(scores)
        total_passed += passed_count
        total_cost += cost
        total_latency += sum(e.get("latency_ms", 0) for e in evals)

    return EvaluationSummary(
        simulation_id=simulation_id,
        evaluator_summaries=evaluator_summaries,
        total_evaluations=len(evaluations),
        average_score=total_score / len(evaluations) if evaluations else 0.0,
        pass_rate=total_passed / len(evaluations) if evaluations else 0.0,
        total_cost_usd=total_cost,
        total_latency_ms=total_latency,
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of an async evaluation job."""
    # TODO: Implement job tracking
    # For now, return a mock response
    return JobStatusResponse(
        job_id=job_id,
        status="pending",
        progress={"current": 0, "total": 0},
        created_at=datetime.utcnow(),
    )
