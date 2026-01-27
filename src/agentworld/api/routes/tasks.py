"""API routes for task-based evaluation (ADR-020).

This module provides REST endpoints for:
- Task definitions (CRUD)
- Task sets / benchmarks
- Trial execution and results
- Pass^k metrics
- Fault classifications
- Policy rules and compliance checking
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from agentworld.api.dependencies import get_repository
from agentworld.api.schemas.tasks import (
    BenchmarkReportResponse,
    BenchmarkTaskMetrics,
    CheckComplianceRequest,
    CreatePolicyRuleRequest,
    CreateTaskDefinitionRequest,
    CreateTaskSetRequest,
    EvaluateTaskResponse,
    FaultClassificationListResponse,
    FaultClassificationResponse,
    FaultSummaryResponse,
    PassKMetricsResponse,
    PolicyComplianceResponse,
    PolicyRuleListResponse,
    PolicyRuleResponse,
    PolicyViolationResponse,
    RunTrialRequest,
    RunTrialsRequest,
    TaskDefinitionListResponse,
    TaskDefinitionResponse,
    TaskDefinitionSummaryResponse,
    TaskSetListResponse,
    TaskSetResponse,
    TrialResultListResponse,
    TrialResultResponse,
    UpdatePolicyRuleRequest,
    UpdateTaskDefinitionRequest,
    UpdateTaskSetRequest,
)
from agentworld.evaluation.fault_classifier import FaultClassifier, FaultSummary
from agentworld.evaluation.policy_engine import PolicyEngine, get_default_policies
from agentworld.evaluation.reliability import interpret_reliability
from agentworld.persistence.repository import Repository
from agentworld.tasks.definitions import (
    ExpectedAction,
    PassKMetrics,
    PolicyRule,
    TaskDefinition,
    TaskSet,
)
from agentworld.tasks.repository import TaskRepository
from agentworld.tasks.runner import TaskExecutionConfig, TaskRunner

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])


def get_task_repository(repo: Repository = Depends(get_repository)) -> TaskRepository:
    """Get TaskRepository from Repository."""
    return TaskRepository(repo._session)


# =============================================================================
# Task Definitions
# =============================================================================


@router.post("/tasks", response_model=TaskDefinitionResponse, status_code=201)
async def create_task_definition(
    request: CreateTaskDefinitionRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskDefinitionResponse:
    """Create a new task definition.

    Task definitions specify:
    - Simulation configuration (agents, apps, topology)
    - Agent instruction (what to accomplish)
    - Ground truth (expected final state, actions, outputs)
    - Policy rules to enforce
    """
    # Check for duplicate task_id
    existing = task_repo.get_task_definition(request.task_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Task with ID '{request.task_id}' already exists",
        )

    # Create task definition
    task = TaskDefinition(
        task_id=request.task_id,
        name=request.name,
        description=request.description or "",
        domain=request.domain,
        difficulty=request.difficulty,
        simulation_config=request.simulation_config,
        initial_app_states=request.initial_app_states or {},
        agent_instruction=request.agent_instruction,
        expected_final_states=request.expected_final_states,
        expected_actions=[
            ExpectedAction.from_dict(a.model_dump()) for a in request.expected_actions
        ],
        required_outputs=request.required_outputs,
        policy_rules=request.policy_rules,
        estimated_steps=request.estimated_steps,
        tags=request.tags,
    )

    saved = task_repo.save_task_definition(task)
    return TaskDefinitionResponse(**saved.to_dict())


@router.get("/tasks", response_model=TaskDefinitionListResponse)
async def list_task_definitions(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskDefinitionListResponse:
    """List task definitions with optional filtering."""
    tag_list = tags.split(",") if tags else None
    offset = (page - 1) * per_page

    tasks = task_repo.list_task_definitions(
        domain=domain,
        difficulty=difficulty,
        tags=tag_list,
        search=search,
        limit=per_page,
        offset=offset,
    )

    total = task_repo.count_task_definitions(domain=domain, difficulty=difficulty)

    return TaskDefinitionListResponse(
        items=[
            TaskDefinitionSummaryResponse(
                id=t.id or "",
                task_id=t.task_id,
                name=t.name,
                description=t.description,
                domain=t.domain,
                difficulty=t.difficulty,
                estimated_steps=t.estimated_steps,
                tags=t.tags,
                is_active=t.is_active,
                created_at=t.created_at,
            )
            for t in tasks
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/tasks/{task_id}", response_model=TaskDefinitionResponse)
async def get_task_definition(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskDefinitionResponse:
    """Get a task definition by task_id."""
    task = task_repo.get_task_definition(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return TaskDefinitionResponse(**task.to_dict())


@router.patch("/tasks/{task_id}", response_model=TaskDefinitionResponse)
async def update_task_definition(
    task_id: str,
    request: UpdateTaskDefinitionRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskDefinitionResponse:
    """Update a task definition."""
    task = task_repo.get_task_definition(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    # Apply updates
    if request.name is not None:
        task.name = request.name
    if request.description is not None:
        task.description = request.description
    if request.difficulty is not None:
        task.difficulty = request.difficulty
    if request.simulation_config is not None:
        task.simulation_config = request.simulation_config
    if request.initial_app_states is not None:
        task.initial_app_states = request.initial_app_states
    if request.agent_instruction is not None:
        task.agent_instruction = request.agent_instruction
    if request.expected_final_states is not None:
        task.expected_final_states = request.expected_final_states
    if request.expected_actions is not None:
        task.expected_actions = [
            ExpectedAction.from_dict(a.model_dump()) for a in request.expected_actions
        ]
    if request.required_outputs is not None:
        task.required_outputs = request.required_outputs
    if request.policy_rules is not None:
        task.policy_rules = request.policy_rules
    if request.estimated_steps is not None:
        task.estimated_steps = request.estimated_steps
    if request.tags is not None:
        task.tags = request.tags

    saved = task_repo.save_task_definition(task)
    return TaskDefinitionResponse(**saved.to_dict())


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task_definition(
    task_id: str,
    hard: bool = Query(False, description="Permanently delete"),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> None:
    """Delete a task definition (soft delete by default)."""
    deleted = task_repo.delete_task_definition(task_id, hard=hard)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")


# =============================================================================
# Task Sets (Benchmarks)
# =============================================================================


@router.post("/task-sets", response_model=TaskSetResponse, status_code=201)
async def create_task_set(
    request: CreateTaskSetRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskSetResponse:
    """Create a new task set (benchmark)."""
    task_set = TaskSet(
        name=request.name,
        description=request.description or "",
        domain=request.domain,
        task_ids=request.task_ids,
    )

    saved = task_repo.save_task_set(task_set)
    return TaskSetResponse(
        id=saved.id or "",
        name=saved.name,
        description=saved.description,
        domain=saved.domain,
        task_ids=saved.task_ids,
        task_count=len(saved.task_ids),
        created_at=saved.created_at,
        updated_at=saved.updated_at,
    )


@router.get("/task-sets", response_model=TaskSetListResponse)
async def list_task_sets(
    domain: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskSetListResponse:
    """List task sets."""
    task_sets = task_repo.list_task_sets(domain=domain, limit=limit, offset=offset)

    return TaskSetListResponse(
        items=[
            TaskSetResponse(
                id=ts.id or "",
                name=ts.name,
                description=ts.description,
                domain=ts.domain,
                task_ids=ts.task_ids,
                task_count=len(ts.task_ids),
                created_at=ts.created_at,
                updated_at=ts.updated_at,
            )
            for ts in task_sets
        ],
        total=len(task_sets),
    )


@router.get("/task-sets/{name}", response_model=TaskSetResponse)
async def get_task_set(
    name: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskSetResponse:
    """Get a task set by name."""
    task_set = task_repo.get_task_set(name)
    if not task_set:
        raise HTTPException(status_code=404, detail=f"Task set '{name}' not found")

    return TaskSetResponse(
        id=task_set.id or "",
        name=task_set.name,
        description=task_set.description,
        domain=task_set.domain,
        task_ids=task_set.task_ids,
        task_count=len(task_set.task_ids),
        created_at=task_set.created_at,
        updated_at=task_set.updated_at,
    )


@router.delete("/task-sets/{name}", status_code=204)
async def delete_task_set(
    name: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> None:
    """Delete a task set."""
    deleted = task_repo.delete_task_set(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task set '{name}' not found")


# =============================================================================
# Trial Execution
# =============================================================================


@router.post("/tasks/{task_id}/run", response_model=TrialResultResponse)
async def run_single_trial(
    task_id: str,
    request: RunTrialRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TrialResultResponse:
    """Run a single trial of a task."""
    task = task_repo.get_task_definition(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    config = TaskExecutionConfig(
        timeout_seconds=request.timeout_seconds,
        capture_trajectory=request.capture_trajectory,
    )
    runner = TaskRunner(config=config)

    # Get next trial number
    trial_count = task_repo.count_trial_results(task_id)
    trial_number = trial_count + 1

    result = await runner.run_trial(task, trial_number)
    saved = task_repo.save_trial_result(result)

    # Classify failure if needed
    if not result.success:
        classifier = FaultClassifier()
        classification = classifier.classify(task, result)
        if classification:
            task_repo.save_fault_classification(classification)

    return TrialResultResponse(**saved.to_dict())


@router.post("/tasks/{task_id}/evaluate", response_model=EvaluateTaskResponse)
async def evaluate_task(
    task_id: str,
    request: RunTrialsRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> EvaluateTaskResponse:
    """Run k trials and compute pass^k metrics."""
    task = task_repo.get_task_definition(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    config = TaskExecutionConfig(
        timeout_seconds=request.timeout_seconds,
        capture_trajectory=request.capture_trajectory,
        parallel_trials=request.parallel_trials,
    )
    runner = TaskRunner(config=config)

    results, metrics = await runner.evaluate_task(task, k=request.k)

    # Save results
    for result in results:
        task_repo.save_trial_result(result)

        # Classify failures
        if not result.success:
            classifier = FaultClassifier()
            classification = classifier.classify(task, result)
            if classification:
                task_repo.save_fault_classification(classification)

    # Save metrics
    task_repo.save_pass_k_metrics(metrics)

    return EvaluateTaskResponse(
        task_id=task_id,
        trials=[TrialResultResponse(**r.to_dict()) for r in results],
        metrics=PassKMetricsResponse(
            id=metrics.id,
            task_id=metrics.task_id,
            total_trials=metrics.total_trials,
            successful_trials=metrics.successful_trials,
            pass_1=metrics.pass_1,
            pass_2=metrics.pass_2,
            pass_4=metrics.pass_4,
            pass_8=metrics.pass_8,
            reliability_gap=metrics.reliability_gap,
            mean_duration_seconds=metrics.mean_duration_seconds,
            mean_token_count=metrics.mean_token_count,
            computed_at=metrics.computed_at,
            interpretation=interpret_reliability(metrics.pass_1, metrics.pass_8),
        ),
    )


# =============================================================================
# Trial Results
# =============================================================================


@router.get("/tasks/{task_id}/results", response_model=TrialResultListResponse)
async def get_trial_results(
    task_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TrialResultListResponse:
    """Get trial results for a task."""
    results = task_repo.get_trial_results(task_id, limit=limit, offset=offset)
    total = task_repo.count_trial_results(task_id)

    return TrialResultListResponse(
        items=[TrialResultResponse(**r.to_dict()) for r in results],
        total=total,
    )


# =============================================================================
# Pass^k Metrics
# =============================================================================


@router.get("/tasks/{task_id}/metrics", response_model=PassKMetricsResponse)
async def get_pass_k_metrics(
    task_id: str,
    recompute: bool = Query(False, description="Recompute from trial results"),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> PassKMetricsResponse:
    """Get pass^k metrics for a task."""
    if recompute:
        metrics = task_repo.compute_and_save_metrics(task_id)
    else:
        metrics = task_repo.get_pass_k_metrics(task_id)

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for task '{task_id}'. Run trials first.",
        )

    return PassKMetricsResponse(
        id=metrics.id,
        task_id=metrics.task_id,
        total_trials=metrics.total_trials,
        successful_trials=metrics.successful_trials,
        pass_1=metrics.pass_1,
        pass_2=metrics.pass_2,
        pass_4=metrics.pass_4,
        pass_8=metrics.pass_8,
        reliability_gap=metrics.reliability_gap,
        mean_duration_seconds=metrics.mean_duration_seconds,
        mean_token_count=metrics.mean_token_count,
        computed_at=metrics.computed_at,
        interpretation=interpret_reliability(metrics.pass_1, metrics.pass_8),
    )


# =============================================================================
# Fault Classifications
# =============================================================================


@router.get("/tasks/{task_id}/faults", response_model=FaultClassificationListResponse)
async def get_fault_classifications(
    task_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> FaultClassificationListResponse:
    """Get fault classifications for a task."""
    classifications = task_repo.get_fault_classifications(
        task_id=task_id,
        limit=limit,
        offset=offset,
    )

    return FaultClassificationListResponse(
        items=[FaultClassificationResponse(**c.to_dict()) for c in classifications],
        total=len(classifications),
    )


@router.get("/tasks/{task_id}/faults/summary", response_model=FaultSummaryResponse)
async def get_fault_summary(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> FaultSummaryResponse:
    """Get fault summary for a task."""
    classifications = task_repo.get_fault_classifications(task_id=task_id, limit=1000)
    summary = FaultSummary.from_classifications(classifications)

    return FaultSummaryResponse(
        total_failures=summary.total_failures,
        by_assignment=summary.by_assignment,
        by_type=summary.by_type,
        common_patterns=summary.common_patterns,
        most_common_cause=summary.get_most_common_cause(),
    )


# =============================================================================
# Policy Rules
# =============================================================================


@router.post("/policies", response_model=PolicyRuleResponse, status_code=201)
async def create_policy_rule(
    request: CreatePolicyRuleRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> PolicyRuleResponse:
    """Create a new policy rule."""
    existing = task_repo.get_policy_rule(request.rule_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Policy rule '{request.rule_id}' already exists",
        )

    rule = PolicyRule(
        rule_id=request.rule_id,
        name=request.name,
        description=request.description or "",
        category=request.category,
        domain=request.domain,
        trigger_actions=request.trigger_actions,
        conditions=[c.model_dump() for c in request.conditions],
        requirements=request.requirements,
        severity=request.severity,
    )

    saved = task_repo.save_policy_rule(rule)
    return PolicyRuleResponse(**saved.to_dict())


@router.get("/policies", response_model=PolicyRuleListResponse)
async def list_policy_rules(
    domain: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> PolicyRuleListResponse:
    """List policy rules."""
    rules = task_repo.list_policy_rules(
        domain=domain,
        category=category,
        limit=limit,
        offset=offset,
    )

    return PolicyRuleListResponse(
        items=[PolicyRuleResponse(**r.to_dict()) for r in rules],
        total=len(rules),
    )


@router.get("/policies/{rule_id}", response_model=PolicyRuleResponse)
async def get_policy_rule(
    rule_id: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> PolicyRuleResponse:
    """Get a policy rule by rule_id."""
    rule = task_repo.get_policy_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Policy rule '{rule_id}' not found")

    return PolicyRuleResponse(**rule.to_dict())


@router.patch("/policies/{rule_id}", response_model=PolicyRuleResponse)
async def update_policy_rule(
    rule_id: str,
    request: UpdatePolicyRuleRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> PolicyRuleResponse:
    """Update a policy rule."""
    rule = task_repo.get_policy_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Policy rule '{rule_id}' not found")

    if request.name is not None:
        rule.name = request.name
    if request.description is not None:
        rule.description = request.description
    if request.category is not None:
        rule.category = request.category
    if request.trigger_actions is not None:
        rule.trigger_actions = request.trigger_actions
    if request.conditions is not None:
        rule.conditions = [c.model_dump() for c in request.conditions]
    if request.requirements is not None:
        rule.requirements = request.requirements
    if request.severity is not None:
        rule.severity = request.severity
    if request.is_active is not None:
        rule.is_active = request.is_active

    saved = task_repo.save_policy_rule(rule)
    return PolicyRuleResponse(**saved.to_dict())


@router.delete("/policies/{rule_id}", status_code=204)
async def delete_policy_rule(
    rule_id: str,
    hard: bool = Query(False),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> None:
    """Delete a policy rule."""
    deleted = task_repo.delete_policy_rule(rule_id, hard=hard)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Policy rule '{rule_id}' not found")


# =============================================================================
# Policy Compliance
# =============================================================================


@router.post("/policies/check", response_model=PolicyComplianceResponse)
async def check_policy_compliance(
    request: CheckComplianceRequest,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> PolicyComplianceResponse:
    """Check trajectory against policy rules."""
    # Get applicable rules
    rules = task_repo.list_policy_rules(domain=request.domain, limit=1000)

    # If no custom rules, use defaults
    if not rules:
        rules = [PolicyRule.from_dict(r.to_dict()) for r in get_default_policies(request.domain)]

    engine = PolicyEngine(rules)
    result = engine.check_trajectory(
        request.trajectory,
        context={"domain": request.domain} if request.domain else {},
    )

    return PolicyComplianceResponse(
        compliant=result.compliant,
        violations=[
            PolicyViolationResponse(
                rule_id=v.rule.rule_id,
                rule_name=v.rule.name,
                severity=v.rule.severity,
                action_index=v.action_index,
                description=v.description,
            )
            for v in result.violations
        ],
        warnings=[
            PolicyViolationResponse(
                rule_id=w.rule.rule_id,
                rule_name=w.rule.name,
                severity=w.rule.severity,
                action_index=w.action_index,
                description=w.description,
            )
            for w in result.warnings
        ],
        compliance_rate=result.compliance_rate,
        total_violations=len(result.violations),
        total_warnings=len(result.warnings),
    )


# =============================================================================
# Benchmark Execution
# =============================================================================


@router.post("/task-sets/{name}/run", response_model=BenchmarkReportResponse)
async def run_benchmark(
    name: str,
    k: int = Query(default=8, ge=1, le=100),
    timeout_seconds: float = Query(default=300.0, ge=10.0, le=3600.0),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> BenchmarkReportResponse:
    """Run a full benchmark (all tasks in set)."""
    task_set = task_repo.get_task_set(name)
    if not task_set:
        raise HTTPException(status_code=404, detail=f"Task set '{name}' not found")

    config = TaskExecutionConfig(timeout_seconds=timeout_seconds)
    runner = TaskRunner(config=config)

    task_metrics_list: list[BenchmarkTaskMetrics] = []
    total_trials = 0
    total_successes = 0
    pass_1_sum = 0.0
    pass_8_sum = 0.0

    for task_id in task_set.task_ids:
        task = task_repo.get_task_definition(task_id)
        if not task:
            logger.warning(f"Task '{task_id}' not found, skipping")
            continue

        results, metrics = await runner.evaluate_task(task, k=k)

        # Save results
        for result in results:
            task_repo.save_trial_result(result)

        task_repo.save_pass_k_metrics(metrics)

        task_metrics_list.append(BenchmarkTaskMetrics(
            task_id=task_id,
            task_name=task.name,
            total_trials=metrics.total_trials,
            successful_trials=metrics.successful_trials,
            pass_1=metrics.pass_1,
            pass_8=metrics.pass_8,
            mean_duration_seconds=metrics.mean_duration_seconds,
        ))

        total_trials += metrics.total_trials
        total_successes += metrics.successful_trials
        pass_1_sum += metrics.pass_1
        pass_8_sum += metrics.pass_8

    completed_tasks = len(task_metrics_list)
    mean_pass_1 = pass_1_sum / completed_tasks if completed_tasks > 0 else 0.0
    mean_pass_8 = pass_8_sum / completed_tasks if completed_tasks > 0 else 0.0

    return BenchmarkReportResponse(
        task_set_name=task_set.name,
        task_set_description=task_set.description,
        total_tasks=len(task_set.task_ids),
        completed_tasks=completed_tasks,
        task_metrics=task_metrics_list,
        mean_pass_1=mean_pass_1,
        mean_pass_8=mean_pass_8,
        mean_reliability_gap=mean_pass_1 - mean_pass_8,
        total_trials=total_trials,
        total_successes=total_successes,
        interpretation=interpret_reliability(mean_pass_1, mean_pass_8),
        computed_at=datetime.now(),
    )


@router.get("/task-sets/{name}/report", response_model=BenchmarkReportResponse)
async def get_benchmark_report(
    name: str,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> BenchmarkReportResponse:
    """Get cached benchmark report (from previous runs)."""
    task_set = task_repo.get_task_set(name)
    if not task_set:
        raise HTTPException(status_code=404, detail=f"Task set '{name}' not found")

    task_metrics_list: list[BenchmarkTaskMetrics] = []
    total_trials = 0
    total_successes = 0
    pass_1_sum = 0.0
    pass_8_sum = 0.0
    latest_computed: datetime | None = None

    for task_id in task_set.task_ids:
        task = task_repo.get_task_definition(task_id)
        metrics = task_repo.get_pass_k_metrics(task_id)

        if not task or not metrics:
            continue

        task_metrics_list.append(BenchmarkTaskMetrics(
            task_id=task_id,
            task_name=task.name,
            total_trials=metrics.total_trials,
            successful_trials=metrics.successful_trials,
            pass_1=metrics.pass_1,
            pass_8=metrics.pass_8,
            mean_duration_seconds=metrics.mean_duration_seconds,
        ))

        total_trials += metrics.total_trials
        total_successes += metrics.successful_trials
        pass_1_sum += metrics.pass_1
        pass_8_sum += metrics.pass_8

        if metrics.computed_at:
            if latest_computed is None or metrics.computed_at > latest_computed:
                latest_computed = metrics.computed_at

    if not task_metrics_list:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for task set '{name}'. Run the benchmark first.",
        )

    completed_tasks = len(task_metrics_list)
    mean_pass_1 = pass_1_sum / completed_tasks if completed_tasks > 0 else 0.0
    mean_pass_8 = pass_8_sum / completed_tasks if completed_tasks > 0 else 0.0

    return BenchmarkReportResponse(
        task_set_name=task_set.name,
        task_set_description=task_set.description,
        total_tasks=len(task_set.task_ids),
        completed_tasks=completed_tasks,
        task_metrics=task_metrics_list,
        mean_pass_1=mean_pass_1,
        mean_pass_8=mean_pass_8,
        mean_reliability_gap=mean_pass_1 - mean_pass_8,
        total_trials=total_trials,
        total_successes=total_successes,
        interpretation=interpret_reliability(mean_pass_1, mean_pass_8),
        computed_at=latest_computed or datetime.now(),
    )
