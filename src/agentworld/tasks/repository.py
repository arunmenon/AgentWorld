"""Task repository for ADR-020.

This module provides data access for task definitions,
trial results, and metrics.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from agentworld.persistence.models import (
    FaultClassificationModel,
    PassKMetricsModel,
    PolicyRuleModel,
    TaskDefinitionModel,
    TaskSetModel,
    TrialResultModel,
)
from agentworld.tasks.definitions import (
    FaultClassification,
    PassKMetrics,
    PolicyRule,
    TaskDefinition,
    TaskSet,
    TrialResult,
)


class TaskRepository:
    """Repository for task-related data operations.

    Provides CRUD operations for:
    - Task definitions
    - Task sets (benchmarks)
    - Trial results
    - Pass^k metrics
    - Fault classifications
    - Policy rules
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self._session = session

    # =========================================================================
    # Task Definitions
    # =========================================================================

    def save_task_definition(self, task: TaskDefinition) -> TaskDefinition:
        """Save a task definition.

        Args:
            task: Task definition to save

        Returns:
            Saved task definition with ID
        """
        if not task.id:
            task.id = str(uuid.uuid4())

        # Check for existing
        existing = (
            self._session.query(TaskDefinitionModel)
            .filter_by(task_id=task.task_id)
            .first()
        )

        if existing:
            # Update existing
            existing.name = task.name
            existing.description = task.description
            existing.domain = task.domain
            existing.difficulty = task.difficulty
            existing.simulation_config_json = self._to_json(task.simulation_config)
            existing.initial_app_states_json = self._to_json(task.initial_app_states)
            existing.agent_instruction = task.agent_instruction
            existing.expected_final_states_json = self._to_json(task.expected_final_states)
            existing.expected_actions_json = self._to_json(
                [a.to_dict() for a in task.expected_actions]
            )
            existing.required_outputs_json = self._to_json(task.required_outputs)
            existing.policy_rules_json = self._to_json(task.policy_rules)
            existing.estimated_steps = task.estimated_steps
            existing.tags_json = self._to_json(task.tags)
            existing.is_active = int(task.is_active)
            task.id = existing.id
        else:
            # Create new
            model = TaskDefinitionModel.from_dict(task.to_dict())
            self._session.add(model)

        self._session.commit()

        # Reload timestamps
        model = self._session.query(TaskDefinitionModel).filter_by(id=task.id).first()
        if model:
            task.created_at = model.created_at
            task.updated_at = model.updated_at

        return task

    def get_task_definition(self, task_id: str) -> TaskDefinition | None:
        """Get a task definition by task_id.

        Args:
            task_id: Unique task identifier

        Returns:
            TaskDefinition or None if not found
        """
        model = (
            self._session.query(TaskDefinitionModel)
            .filter_by(task_id=task_id, is_active=1)
            .first()
        )

        if not model:
            return None

        return TaskDefinition.from_dict(model.to_dict())

    def get_task_definition_by_id(self, id: str) -> TaskDefinition | None:
        """Get a task definition by database ID.

        Args:
            id: Database ID

        Returns:
            TaskDefinition or None if not found
        """
        model = (
            self._session.query(TaskDefinitionModel)
            .filter_by(id=id)
            .first()
        )

        if not model:
            return None

        return TaskDefinition.from_dict(model.to_dict())

    def list_task_definitions(
        self,
        domain: str | None = None,
        difficulty: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskDefinition]:
        """List task definitions with optional filtering.

        Args:
            domain: Filter by domain
            difficulty: Filter by difficulty
            tags: Filter by tags (any match)
            search: Search in name/description
            include_inactive: Include soft-deleted tasks
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of TaskDefinitions
        """
        query = self._session.query(TaskDefinitionModel)

        if not include_inactive:
            query = query.filter(TaskDefinitionModel.is_active == 1)

        if domain:
            query = query.filter(TaskDefinitionModel.domain == domain)

        if difficulty:
            query = query.filter(TaskDefinitionModel.difficulty == difficulty)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TaskDefinitionModel.name.ilike(search_pattern),
                    TaskDefinitionModel.description.ilike(search_pattern),
                )
            )

        if tags:
            # Match any tag
            tag_conditions = [
                TaskDefinitionModel.tags_json.contains(f'"{tag}"')
                for tag in tags
            ]
            query = query.filter(or_(*tag_conditions))

        query = query.order_by(TaskDefinitionModel.created_at.desc())
        query = query.offset(offset).limit(limit)

        models = query.all()
        return [TaskDefinition.from_dict(m.to_dict()) for m in models]

    def count_task_definitions(
        self,
        domain: str | None = None,
        difficulty: str | None = None,
        include_inactive: bool = False,
    ) -> int:
        """Count task definitions.

        Args:
            domain: Filter by domain
            difficulty: Filter by difficulty
            include_inactive: Include soft-deleted

        Returns:
            Count of matching tasks
        """
        query = self._session.query(func.count(TaskDefinitionModel.id))

        if not include_inactive:
            query = query.filter(TaskDefinitionModel.is_active == 1)

        if domain:
            query = query.filter(TaskDefinitionModel.domain == domain)

        if difficulty:
            query = query.filter(TaskDefinitionModel.difficulty == difficulty)

        return query.scalar() or 0

    def delete_task_definition(self, task_id: str, hard: bool = False) -> bool:
        """Delete a task definition.

        Args:
            task_id: Task ID to delete
            hard: If True, permanently delete; otherwise soft delete

        Returns:
            True if deleted
        """
        model = (
            self._session.query(TaskDefinitionModel)
            .filter_by(task_id=task_id)
            .first()
        )

        if not model:
            return False

        if hard:
            self._session.delete(model)
        else:
            model.is_active = 0

        self._session.commit()
        return True

    # =========================================================================
    # Task Sets
    # =========================================================================

    def save_task_set(self, task_set: TaskSet) -> TaskSet:
        """Save a task set.

        Args:
            task_set: Task set to save

        Returns:
            Saved task set with ID
        """
        if not task_set.id:
            task_set.id = str(uuid.uuid4())

        existing = (
            self._session.query(TaskSetModel)
            .filter_by(name=task_set.name)
            .first()
        )

        if existing:
            existing.description = task_set.description
            existing.domain = task_set.domain
            existing.task_ids_json = self._to_json(task_set.task_ids)
            task_set.id = existing.id
        else:
            model = TaskSetModel.from_dict(task_set.to_dict())
            self._session.add(model)

        self._session.commit()

        model = self._session.query(TaskSetModel).filter_by(id=task_set.id).first()
        if model:
            task_set.created_at = model.created_at
            task_set.updated_at = model.updated_at

        return task_set

    def get_task_set(self, name: str) -> TaskSet | None:
        """Get a task set by name.

        Args:
            name: Task set name

        Returns:
            TaskSet or None
        """
        model = (
            self._session.query(TaskSetModel)
            .filter_by(name=name)
            .first()
        )

        if not model:
            return None

        return TaskSet.from_dict(model.to_dict())

    def list_task_sets(
        self,
        domain: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskSet]:
        """List task sets.

        Args:
            domain: Filter by domain
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of TaskSets
        """
        query = self._session.query(TaskSetModel)

        if domain:
            query = query.filter(TaskSetModel.domain == domain)

        query = query.order_by(TaskSetModel.created_at.desc())
        query = query.offset(offset).limit(limit)

        models = query.all()
        return [TaskSet.from_dict(m.to_dict()) for m in models]

    def delete_task_set(self, name: str) -> bool:
        """Delete a task set.

        Args:
            name: Task set name

        Returns:
            True if deleted
        """
        model = (
            self._session.query(TaskSetModel)
            .filter_by(name=name)
            .first()
        )

        if not model:
            return False

        self._session.delete(model)
        self._session.commit()
        return True

    # =========================================================================
    # Trial Results
    # =========================================================================

    def save_trial_result(self, result: TrialResult) -> TrialResult:
        """Save a trial result.

        Args:
            result: Trial result to save

        Returns:
            Saved trial result with ID
        """
        if not result.id:
            result.id = str(uuid.uuid4())

        model = TrialResultModel.from_dict(result.to_dict())
        self._session.add(model)
        self._session.commit()

        result.created_at = model.created_at
        return result

    def get_trial_results(
        self,
        task_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TrialResult]:
        """Get trial results for a task.

        Args:
            task_id: Task ID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of TrialResults
        """
        models = (
            self._session.query(TrialResultModel)
            .filter_by(task_id=task_id)
            .order_by(TrialResultModel.trial_number.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [TrialResult.from_dict(m.to_dict()) for m in models]

    def count_trial_results(self, task_id: str) -> int:
        """Count trial results for a task.

        Args:
            task_id: Task ID

        Returns:
            Count of trials
        """
        return (
            self._session.query(func.count(TrialResultModel.id))
            .filter_by(task_id=task_id)
            .scalar()
        ) or 0

    def get_trial_statistics(self, task_id: str) -> dict[str, Any]:
        """Get aggregated trial statistics.

        Args:
            task_id: Task ID

        Returns:
            Dict with total, successful, avg_duration, etc.
        """
        results = self.get_trial_results(task_id, limit=1000)

        if not results:
            return {
                "total_trials": 0,
                "successful_trials": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": None,
                "avg_token_count": None,
            }

        successful = sum(1 for r in results if r.success)
        durations = [r.duration_seconds for r in results if r.duration_seconds]
        tokens = [r.token_count for r in results if r.token_count]

        return {
            "total_trials": len(results),
            "successful_trials": successful,
            "success_rate": successful / len(results) if results else 0.0,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else None,
            "avg_token_count": sum(tokens) / len(tokens) if tokens else None,
        }

    # =========================================================================
    # Pass^k Metrics
    # =========================================================================

    def save_pass_k_metrics(self, metrics: PassKMetrics) -> PassKMetrics:
        """Save pass^k metrics.

        Args:
            metrics: Metrics to save

        Returns:
            Saved metrics with ID
        """
        if not metrics.id:
            metrics.id = str(uuid.uuid4())

        # Delete existing metrics for this task
        self._session.query(PassKMetricsModel).filter_by(
            task_id=metrics.task_id
        ).delete()

        model = PassKMetricsModel.from_dict(metrics.to_dict())
        self._session.add(model)
        self._session.commit()

        return metrics

    def get_pass_k_metrics(self, task_id: str) -> PassKMetrics | None:
        """Get pass^k metrics for a task.

        Args:
            task_id: Task ID

        Returns:
            PassKMetrics or None
        """
        model = (
            self._session.query(PassKMetricsModel)
            .filter_by(task_id=task_id)
            .order_by(PassKMetricsModel.computed_at.desc())
            .first()
        )

        if not model:
            return None

        return PassKMetrics.from_dict(model.to_dict())

    def compute_and_save_metrics(self, task_id: str) -> PassKMetrics | None:
        """Compute and save pass^k metrics from trial results.

        Args:
            task_id: Task ID

        Returns:
            Computed and saved metrics, or None if no trials
        """
        results = self.get_trial_results(task_id, limit=1000)

        if not results:
            return None

        metrics = PassKMetrics.from_trials(task_id, results)
        return self.save_pass_k_metrics(metrics)

    # =========================================================================
    # Fault Classifications
    # =========================================================================

    def save_fault_classification(
        self,
        classification: FaultClassification,
    ) -> FaultClassification:
        """Save a fault classification.

        Args:
            classification: Classification to save

        Returns:
            Saved classification with ID
        """
        if not classification.id:
            classification.id = str(uuid.uuid4())

        model = FaultClassificationModel.from_dict(classification.to_dict())
        self._session.add(model)
        self._session.commit()

        return classification

    def get_fault_classifications(
        self,
        task_id: str | None = None,
        trial_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FaultClassification]:
        """Get fault classifications.

        Args:
            task_id: Filter by task ID
            trial_id: Filter by trial ID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of FaultClassifications
        """
        query = self._session.query(FaultClassificationModel)

        if task_id:
            query = query.filter_by(task_id=task_id)

        if trial_id:
            query = query.filter_by(trial_id=trial_id)

        query = query.order_by(FaultClassificationModel.created_at.desc())
        query = query.offset(offset).limit(limit)

        models = query.all()
        return [FaultClassification.from_dict(m.to_dict()) for m in models]

    def get_fault_summary(self, task_id: str) -> dict[str, Any]:
        """Get summary of faults for a task.

        Args:
            task_id: Task ID

        Returns:
            Dict with counts by assignment and type
        """
        classifications = self.get_fault_classifications(task_id=task_id, limit=1000)

        by_assignment: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for c in classifications:
            assignment = c.fault_assignment.value
            fault_type = c.fault_type.value

            by_assignment[assignment] = by_assignment.get(assignment, 0) + 1
            by_type[fault_type] = by_type.get(fault_type, 0) + 1

        return {
            "total_faults": len(classifications),
            "by_assignment": by_assignment,
            "by_type": by_type,
        }

    # =========================================================================
    # Policy Rules
    # =========================================================================

    def save_policy_rule(self, rule: PolicyRule) -> PolicyRule:
        """Save a policy rule.

        Args:
            rule: Policy rule to save

        Returns:
            Saved rule with ID
        """
        if not rule.id:
            rule.id = str(uuid.uuid4())

        existing = (
            self._session.query(PolicyRuleModel)
            .filter_by(rule_id=rule.rule_id)
            .first()
        )

        if existing:
            existing.name = rule.name
            existing.description = rule.description
            existing.category = rule.category
            existing.domain = rule.domain
            existing.trigger_actions_json = self._to_json(rule.trigger_actions)
            existing.conditions_json = self._to_json(rule.conditions)
            existing.requirements_json = self._to_json(rule.requirements)
            existing.severity = rule.severity
            existing.is_active = int(rule.is_active)
            rule.id = existing.id
        else:
            model = PolicyRuleModel.from_dict(rule.to_dict())
            self._session.add(model)

        self._session.commit()

        model = self._session.query(PolicyRuleModel).filter_by(id=rule.id).first()
        if model:
            rule.created_at = model.created_at
            rule.updated_at = model.updated_at

        return rule

    def get_policy_rule(self, rule_id: str) -> PolicyRule | None:
        """Get a policy rule by rule_id.

        Args:
            rule_id: Unique rule identifier

        Returns:
            PolicyRule or None
        """
        model = (
            self._session.query(PolicyRuleModel)
            .filter_by(rule_id=rule_id, is_active=1)
            .first()
        )

        if not model:
            return None

        return PolicyRule.from_dict(model.to_dict())

    def list_policy_rules(
        self,
        domain: str | None = None,
        category: str | None = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PolicyRule]:
        """List policy rules.

        Args:
            domain: Filter by domain
            category: Filter by category
            include_inactive: Include inactive rules
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of PolicyRules
        """
        query = self._session.query(PolicyRuleModel)

        if not include_inactive:
            query = query.filter(PolicyRuleModel.is_active == 1)

        if domain:
            query = query.filter(
                or_(
                    PolicyRuleModel.domain == domain,
                    PolicyRuleModel.domain.is_(None),
                )
            )

        if category:
            query = query.filter(PolicyRuleModel.category == category)

        query = query.order_by(PolicyRuleModel.created_at.desc())
        query = query.offset(offset).limit(limit)

        models = query.all()
        return [PolicyRule.from_dict(m.to_dict()) for m in models]

    def delete_policy_rule(self, rule_id: str, hard: bool = False) -> bool:
        """Delete a policy rule.

        Args:
            rule_id: Rule ID to delete
            hard: If True, permanently delete

        Returns:
            True if deleted
        """
        model = (
            self._session.query(PolicyRuleModel)
            .filter_by(rule_id=rule_id)
            .first()
        )

        if not model:
            return False

        if hard:
            self._session.delete(model)
        else:
            model.is_active = 0

        self._session.commit()
        return True

    # =========================================================================
    # Helpers
    # =========================================================================

    def _to_json(self, obj: Any) -> str:
        """Convert object to JSON string."""
        import json
        return json.dumps(obj, default=str)
