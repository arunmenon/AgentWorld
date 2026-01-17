"""Repository pattern for data access."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from agentworld.core.models import SimulationStatus
from agentworld.persistence.database import session_scope, get_session
from agentworld.persistence.models import (
    SimulationModel,
    AgentModel,
    MessageModel,
    MemoryModel,
    TopologyEdgeModel,
    TopologyConfigModel,
    CheckpointModel,
    MetricsModel,
    LLMCacheModel,
    PersonaLibraryModel,
    PersonaCollectionModel,
    PersonaCollectionMemberModel,
    PopulationTemplateModel,
    ExperimentModel,
    ExperimentVariantModel,
    ExperimentRunModel,
)


class Repository:
    """Data access repository for AgentWorld entities."""

    def __init__(self, session: Session | None = None):
        """Initialize the repository.

        Args:
            session: Optional SQLAlchemy session (creates new if not provided)
        """
        self._session = session
        self._owns_session = session is None

    @property
    def session(self) -> Session:
        """Get the database session."""
        if self._session is None:
            self._session = get_session()
        return self._session

    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()

    # Simulation methods

    def save_simulation(self, simulation_data: dict[str, Any]) -> str:
        """Save a simulation.

        Args:
            simulation_data: Simulation data dictionary

        Returns:
            Simulation ID
        """
        model = SimulationModel.from_dict(simulation_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        """Get a simulation by ID.

        Args:
            simulation_id: Simulation ID

        Returns:
            Simulation data or None if not found
        """
        model = self.session.query(SimulationModel).filter_by(id=simulation_id).first()
        if model is None:
            return None
        return model.to_dict()

    def list_simulations(
        self,
        status: SimulationStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List simulations.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of simulation dictionaries
        """
        query = self.session.query(SimulationModel)

        if status is not None:
            query = query.filter_by(status=status)

        query = query.order_by(SimulationModel.created_at.desc())
        query = query.limit(limit).offset(offset)

        return [model.to_dict() for model in query.all()]

    def update_simulation(self, simulation_id: str, updates: dict[str, Any]) -> bool:
        """Update a simulation.

        Args:
            simulation_id: Simulation ID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        model = self.session.query(SimulationModel).filter_by(id=simulation_id).first()
        if model is None:
            return False

        for key, value in updates.items():
            if key == "config":
                import json
                model.config_json = json.dumps(value)
            elif key == "status" and isinstance(value, str):
                model.status = SimulationStatus(value)
            elif hasattr(model, key):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        self.session.commit()
        return True

    def delete_simulation(self, simulation_id: str) -> bool:
        """Delete a simulation and all related data.

        Args:
            simulation_id: Simulation ID

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(SimulationModel).filter_by(id=simulation_id).first()
        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()
        return True

    # Agent methods

    def save_agent(self, agent_data: dict[str, Any]) -> str:
        """Save an agent.

        Args:
            agent_data: Agent data dictionary

        Returns:
            Agent ID
        """
        model = AgentModel.from_dict(agent_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent data or None if not found
        """
        model = self.session.query(AgentModel).filter_by(id=agent_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_agents_for_simulation(self, simulation_id: str) -> list[dict[str, Any]]:
        """Get all agents for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of agent dictionaries
        """
        models = self.session.query(AgentModel).filter_by(simulation_id=simulation_id).all()
        return [model.to_dict() for model in models]

    # Message methods

    def save_message(self, message_data: dict[str, Any]) -> str:
        """Save a message.

        Args:
            message_data: Message data dictionary

        Returns:
            Message ID
        """
        model = MessageModel.from_dict(message_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        """Get a message by ID.

        Args:
            message_id: Message ID

        Returns:
            Message data or None if not found
        """
        model = self.session.query(MessageModel).filter_by(id=message_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_messages_for_simulation(
        self,
        simulation_id: str,
        step: int | None = None,
        sender_id: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Get messages for a simulation.

        Args:
            simulation_id: Simulation ID
            step: Optional step filter
            sender_id: Optional sender filter
            limit: Maximum number of results

        Returns:
            List of message dictionaries
        """
        query = self.session.query(MessageModel).filter_by(simulation_id=simulation_id)

        if step is not None:
            query = query.filter_by(step=step)
        if sender_id is not None:
            query = query.filter_by(sender_id=sender_id)

        query = query.order_by(MessageModel.timestamp.asc())
        query = query.limit(limit)

        return [model.to_dict() for model in query.all()]

    def count_messages(self, simulation_id: str) -> int:
        """Count messages for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            Number of messages
        """
        return self.session.query(MessageModel).filter_by(simulation_id=simulation_id).count()

    # Memory methods

    def save_memory(self, memory_data: dict[str, Any]) -> str:
        """Save a memory (observation or reflection).

        Args:
            memory_data: Memory data dictionary

        Returns:
            Memory ID
        """
        model = MemoryModel.from_dict(memory_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        """Get a memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory data or None if not found
        """
        model = self.session.query(MemoryModel).filter_by(id=memory_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_memories_for_agent(
        self,
        agent_id: str,
        memory_type: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Get memories for an agent.

        Args:
            agent_id: Agent ID
            memory_type: Optional type filter ('observation' or 'reflection')
            limit: Maximum number of results

        Returns:
            List of memory dictionaries
        """
        query = self.session.query(MemoryModel).filter_by(agent_id=agent_id)

        if memory_type is not None:
            query = query.filter_by(memory_type=memory_type)

        query = query.order_by(MemoryModel.created_at.desc())
        query = query.limit(limit)

        return [model.to_dict() for model in query.all()]

    def delete_memories_for_agent(self, agent_id: str) -> int:
        """Delete all memories for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Number of deleted memories
        """
        count = self.session.query(MemoryModel).filter_by(agent_id=agent_id).delete()
        self.session.commit()
        return count

    def count_memories(self, agent_id: str, memory_type: str | None = None) -> int:
        """Count memories for an agent.

        Args:
            agent_id: Agent ID
            memory_type: Optional type filter

        Returns:
            Number of memories
        """
        query = self.session.query(MemoryModel).filter_by(agent_id=agent_id)
        if memory_type:
            query = query.filter_by(memory_type=memory_type)
        return query.count()

    # Topology methods

    def save_topology_config(self, config_data: dict[str, Any]) -> int:
        """Save topology configuration for a simulation.

        Args:
            config_data: Topology config dictionary

        Returns:
            Config ID
        """
        # Delete existing config for this simulation
        self.session.query(TopologyConfigModel).filter_by(
            simulation_id=config_data["simulation_id"]
        ).delete()

        model = TopologyConfigModel.from_dict(config_data)
        self.session.add(model)
        self.session.commit()
        return model.id

    def get_topology_config(self, simulation_id: str) -> dict[str, Any] | None:
        """Get topology configuration for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            Config data or None if not found
        """
        model = self.session.query(TopologyConfigModel).filter_by(
            simulation_id=simulation_id
        ).first()
        if model is None:
            return None
        return model.to_dict()

    def save_topology_edge(self, edge_data: dict[str, Any]) -> int:
        """Save a topology edge.

        Args:
            edge_data: Edge data dictionary

        Returns:
            Edge ID
        """
        model = TopologyEdgeModel.from_dict(edge_data)
        self.session.add(model)
        self.session.commit()
        return model.id

    def save_topology_edges(self, simulation_id: str, edges: list[tuple]) -> int:
        """Save multiple topology edges, replacing existing.

        Args:
            simulation_id: Simulation ID
            edges: List of (source_id, target_id, weight) tuples

        Returns:
            Number of edges saved
        """
        # Delete existing edges
        self.session.query(TopologyEdgeModel).filter_by(
            simulation_id=simulation_id
        ).delete()

        # Add new edges
        for edge in edges:
            source, target = edge[0], edge[1]
            weight = edge[2] if len(edge) > 2 else 1.0
            model = TopologyEdgeModel(
                simulation_id=simulation_id,
                source_id=source,
                target_id=target,
                weight=weight,
            )
            self.session.add(model)

        self.session.commit()
        return len(edges)

    def get_topology_edges(self, simulation_id: str) -> list[dict[str, Any]]:
        """Get all topology edges for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of edge dictionaries
        """
        models = self.session.query(TopologyEdgeModel).filter_by(
            simulation_id=simulation_id
        ).all()
        return [model.to_dict() for model in models]

    def delete_topology(self, simulation_id: str) -> tuple[int, int]:
        """Delete topology config and edges for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            Tuple of (edges_deleted, configs_deleted)
        """
        edges_deleted = self.session.query(TopologyEdgeModel).filter_by(
            simulation_id=simulation_id
        ).delete()
        configs_deleted = self.session.query(TopologyConfigModel).filter_by(
            simulation_id=simulation_id
        ).delete()
        self.session.commit()
        return edges_deleted, configs_deleted

    # Checkpoint methods

    def save_checkpoint(self, checkpoint_data: dict[str, Any]) -> str:
        """Save a checkpoint.

        Args:
            checkpoint_data: Checkpoint data dictionary

        Returns:
            Checkpoint ID
        """
        model = CheckpointModel.from_dict(checkpoint_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None:
        """Get a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint data or None if not found
        """
        model = self.session.query(CheckpointModel).filter_by(id=checkpoint_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_checkpoints_for_simulation(
        self,
        simulation_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get checkpoints for a simulation.

        Args:
            simulation_id: Simulation ID
            limit: Maximum number of results

        Returns:
            List of checkpoint dictionaries
        """
        models = (
            self.session.query(CheckpointModel)
            .filter_by(simulation_id=simulation_id)
            .order_by(CheckpointModel.step.desc())
            .limit(limit)
            .all()
        )
        return [model.to_dict() for model in models]

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(CheckpointModel).filter_by(id=checkpoint_id).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    # Metrics methods (per ADR-008)

    def save_metric(
        self,
        simulation_id: str,
        step: int,
        metric_name: str,
        metric_value: float,
    ) -> int:
        """Save a simulation metric.

        Args:
            simulation_id: Simulation ID
            step: Step number
            metric_name: Name of the metric
            metric_value: Value of the metric

        Returns:
            Metric ID
        """
        model = MetricsModel(
            simulation_id=simulation_id,
            step=step,
            metric_name=metric_name,
            metric_value=metric_value,
        )
        self.session.add(model)
        self.session.commit()
        return model.id

    def save_metrics_batch(
        self,
        simulation_id: str,
        step: int,
        metrics: dict[str, float],
    ) -> int:
        """Save multiple metrics for a step.

        Args:
            simulation_id: Simulation ID
            step: Step number
            metrics: Dictionary of metric_name -> metric_value

        Returns:
            Number of metrics saved
        """
        for name, value in metrics.items():
            model = MetricsModel(
                simulation_id=simulation_id,
                step=step,
                metric_name=name,
                metric_value=value,
            )
            self.session.add(model)
        self.session.commit()
        return len(metrics)

    def get_metrics_for_simulation(
        self,
        simulation_id: str,
        metric_name: str | None = None,
        step: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get metrics for a simulation.

        Args:
            simulation_id: Simulation ID
            metric_name: Optional filter by metric name
            step: Optional filter by step

        Returns:
            List of metric dictionaries
        """
        query = self.session.query(MetricsModel).filter_by(simulation_id=simulation_id)

        if metric_name is not None:
            query = query.filter_by(metric_name=metric_name)
        if step is not None:
            query = query.filter_by(step=step)

        query = query.order_by(MetricsModel.step.asc(), MetricsModel.metric_name.asc())
        return [model.to_dict() for model in query.all()]

    def get_metric_timeseries(
        self,
        simulation_id: str,
        metric_name: str,
    ) -> list[tuple[int, float]]:
        """Get time series data for a specific metric.

        Args:
            simulation_id: Simulation ID
            metric_name: Name of the metric

        Returns:
            List of (step, value) tuples
        """
        models = (
            self.session.query(MetricsModel)
            .filter_by(simulation_id=simulation_id, metric_name=metric_name)
            .order_by(MetricsModel.step.asc())
            .all()
        )
        return [(m.step, m.metric_value) for m in models]

    def delete_metrics_for_simulation(self, simulation_id: str) -> int:
        """Delete all metrics for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            Number of deleted metrics
        """
        count = self.session.query(MetricsModel).filter_by(simulation_id=simulation_id).delete()
        self.session.commit()
        return count

    # LLM Cache methods (per ADR-008)

    def save_llm_cache(
        self,
        cache_key: str,
        response_content: str,
        model: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        """Save an LLM response to cache.

        Args:
            cache_key: Unique cache key
            response_content: LLM response content
            model: Model used
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            expires_at: Optional expiration datetime

        Returns:
            Cache key
        """
        model_obj = LLMCacheModel(
            cache_key=cache_key,
            response_content=response_content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            expires_at=expires_at,
        )
        self.session.merge(model_obj)
        self.session.commit()
        return cache_key

    def get_llm_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Get cached LLM response.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        model = self.session.query(LLMCacheModel).filter_by(cache_key=cache_key).first()
        if model is None:
            return None

        # Check expiration
        if model.expires_at is not None and model.expires_at < datetime.utcnow():
            self.session.delete(model)
            self.session.commit()
            return None

        return model.to_dict()

    def delete_llm_cache(self, cache_key: str) -> bool:
        """Delete cached LLM response.

        Args:
            cache_key: Cache key

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(LLMCacheModel).filter_by(cache_key=cache_key).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def clear_expired_llm_cache(self) -> int:
        """Clear expired LLM cache entries.

        Returns:
            Number of deleted entries
        """
        count = (
            self.session.query(LLMCacheModel)
            .filter(LLMCacheModel.expires_at < datetime.utcnow())
            .delete()
        )
        self.session.commit()
        return count

    def clear_all_llm_cache(self) -> int:
        """Clear all LLM cache entries.

        Returns:
            Number of deleted entries
        """
        count = self.session.query(LLMCacheModel).delete()
        self.session.commit()
        return count

    # Persona Library methods (per ADR-008)

    def save_persona(self, persona_data: dict[str, Any]) -> str:
        """Save a persona to the library.

        Args:
            persona_data: Persona data dictionary

        Returns:
            Persona ID
        """
        model = PersonaLibraryModel.from_dict(persona_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_persona(self, persona_id: str) -> dict[str, Any] | None:
        """Get a persona by ID.

        Args:
            persona_id: Persona ID

        Returns:
            Persona data or None if not found
        """
        model = self.session.query(PersonaLibraryModel).filter_by(id=persona_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_persona_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a persona by name.

        Args:
            name: Persona name

        Returns:
            Persona data or None if not found
        """
        model = self.session.query(PersonaLibraryModel).filter_by(name=name).first()
        if model is None:
            return None
        return model.to_dict()

    def list_personas(
        self,
        tags: list[str] | None = None,
        occupation: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List personas from library.

        Args:
            tags: Optional filter by tags (any match)
            occupation: Optional filter by occupation
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of persona dictionaries
        """
        query = self.session.query(PersonaLibraryModel)

        if occupation is not None:
            query = query.filter_by(occupation=occupation)

        # Tag filtering requires JSON containment (simplified here)
        # In production, use proper JSON queries

        query = query.order_by(PersonaLibraryModel.name.asc())
        query = query.limit(limit).offset(offset)

        return [model.to_dict() for model in query.all()]

    def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona from library.

        Args:
            persona_id: Persona ID

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(PersonaLibraryModel).filter_by(id=persona_id).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def search_personas(self, query_text: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search personas by name or description.

        Args:
            query_text: Search query
            limit: Maximum number of results

        Returns:
            List of matching persona dictionaries
        """
        query = self.session.query(PersonaLibraryModel).filter(
            (PersonaLibraryModel.name.ilike(f"%{query_text}%")) |
            (PersonaLibraryModel.description.ilike(f"%{query_text}%")) |
            (PersonaLibraryModel.occupation.ilike(f"%{query_text}%"))
        )
        query = query.limit(limit)
        return [model.to_dict() for model in query.all()]

    # Experiment methods (per ADR-008)

    def save_experiment(self, experiment_data: dict[str, Any]) -> str:
        """Save an experiment.

        Args:
            experiment_data: Experiment data dictionary

        Returns:
            Experiment ID
        """
        model = ExperimentModel.from_dict(experiment_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        """Get an experiment by ID.

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment data or None if not found
        """
        model = self.session.query(ExperimentModel).filter_by(id=experiment_id).first()
        if model is None:
            return None
        return model.to_dict()

    def list_experiments(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List experiments.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of experiment dictionaries
        """
        query = self.session.query(ExperimentModel)

        if status is not None:
            query = query.filter_by(status=status)

        query = query.order_by(ExperimentModel.created_at.desc())
        query = query.limit(limit).offset(offset)

        return [model.to_dict() for model in query.all()]

    def update_experiment(self, experiment_id: str, updates: dict[str, Any]) -> bool:
        """Update an experiment.

        Args:
            experiment_id: Experiment ID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        model = self.session.query(ExperimentModel).filter_by(id=experiment_id).first()
        if model is None:
            return False

        import json
        for key, value in updates.items():
            if key == "config":
                model.config_json = json.dumps(value)
            elif key == "variables":
                model.variables_json = json.dumps(value)
            elif hasattr(model, key):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        self.session.commit()
        return True

    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment and its runs.

        Args:
            experiment_id: Experiment ID

        Returns:
            True if deleted, False if not found
        """
        # Delete runs first
        self.session.query(ExperimentRunModel).filter_by(experiment_id=experiment_id).delete()

        model = self.session.query(ExperimentModel).filter_by(id=experiment_id).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    # Experiment Run methods

    def save_experiment_run(self, run_data: dict[str, Any]) -> int:
        """Save an experiment run.

        Args:
            run_data: Run data dictionary

        Returns:
            Run ID
        """
        model = ExperimentRunModel.from_dict(run_data)
        self.session.add(model)
        self.session.commit()
        return model.id

    def get_experiment_run(self, run_id: int) -> dict[str, Any] | None:
        """Get an experiment run by ID.

        Args:
            run_id: Run ID

        Returns:
            Run data or None if not found
        """
        model = self.session.query(ExperimentRunModel).filter_by(id=run_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_runs_for_experiment(
        self,
        experiment_id: str,
        variant: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all runs for an experiment.

        Args:
            experiment_id: Experiment ID
            variant: Optional filter by variant

        Returns:
            List of run dictionaries
        """
        query = self.session.query(ExperimentRunModel).filter_by(experiment_id=experiment_id)

        if variant is not None:
            query = query.filter_by(variant=variant)

        query = query.order_by(ExperimentRunModel.run_number.asc())
        return [model.to_dict() for model in query.all()]

    def update_experiment_run(self, run_id: int, updates: dict[str, Any]) -> bool:
        """Update an experiment run.

        Args:
            run_id: Run ID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        model = self.session.query(ExperimentRunModel).filter_by(id=run_id).first()
        if model is None:
            return False

        import json
        for key, value in updates.items():
            if key == "parameters":
                model.parameters_json = json.dumps(value)
            elif key == "results":
                model.results_json = json.dumps(value)
            elif key == "metrics":
                model.metrics_json = json.dumps(value)
            elif key in ("started_at", "completed_at") and isinstance(value, str):
                setattr(model, key, datetime.fromisoformat(value))
            elif hasattr(model, key):
                setattr(model, key, value)

        self.session.commit()
        return True

    # Experiment Variant methods (per ADR-008)

    def save_experiment_variant(self, variant_data: dict[str, Any]) -> str:
        """Save an experiment variant.

        Args:
            variant_data: Variant data dictionary

        Returns:
            Variant ID
        """
        model = ExperimentVariantModel.from_dict(variant_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_experiment_variant(self, variant_id: str) -> dict[str, Any] | None:
        """Get an experiment variant by ID.

        Args:
            variant_id: Variant ID

        Returns:
            Variant data or None if not found
        """
        model = self.session.query(ExperimentVariantModel).filter_by(id=variant_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_variants_for_experiment(
        self,
        experiment_id: str,
    ) -> list[dict[str, Any]]:
        """Get all variants for an experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            List of variant dictionaries
        """
        models = (
            self.session.query(ExperimentVariantModel)
            .filter_by(experiment_id=experiment_id)
            .order_by(ExperimentVariantModel.order_index.asc())
            .all()
        )
        return [model.to_dict() for model in models]

    def update_experiment_variant(self, variant_id: str, updates: dict[str, Any]) -> bool:
        """Update an experiment variant.

        Args:
            variant_id: Variant ID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        model = self.session.query(ExperimentVariantModel).filter_by(id=variant_id).first()
        if model is None:
            return False

        import json
        for key, value in updates.items():
            if key == "config_override":
                model.config_override_json = json.dumps(value)
            elif key == "is_control":
                model.is_control = int(value)
            elif hasattr(model, key):
                setattr(model, key, value)

        self.session.commit()
        return True

    def delete_experiment_variant(self, variant_id: str) -> bool:
        """Delete an experiment variant.

        Args:
            variant_id: Variant ID

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(ExperimentVariantModel).filter_by(id=variant_id).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def delete_variants_for_experiment(self, experiment_id: str) -> int:
        """Delete all variants for an experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            Number of variants deleted
        """
        count = (
            self.session.query(ExperimentVariantModel)
            .filter_by(experiment_id=experiment_id)
            .delete()
        )
        self.session.commit()
        return count

    def get_runs_for_variant(self, variant_id: str) -> list[dict[str, Any]]:
        """Get all runs for a specific variant.

        Args:
            variant_id: Variant ID

        Returns:
            List of run dictionaries
        """
        models = (
            self.session.query(ExperimentRunModel)
            .filter_by(variant_id=variant_id)
            .order_by(ExperimentRunModel.run_number.asc())
            .all()
        )
        return [model.to_dict() for model in models]

    # Persona Collection methods (per ADR-008 Phase 4)

    def save_collection(self, collection_data: dict[str, Any]) -> str:
        """Save a persona collection.

        Args:
            collection_data: Collection data dictionary

        Returns:
            Collection ID
        """
        model = PersonaCollectionModel.from_dict(collection_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_collection(self, collection_id: str) -> dict[str, Any] | None:
        """Get a persona collection by ID.

        Args:
            collection_id: Collection ID

        Returns:
            Collection data or None if not found
        """
        model = self.session.query(PersonaCollectionModel).filter_by(id=collection_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_collection_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a persona collection by name.

        Args:
            name: Collection name

        Returns:
            Collection data or None if not found
        """
        model = self.session.query(PersonaCollectionModel).filter_by(name=name).first()
        if model is None:
            return None
        return model.to_dict()

    def list_collections(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List persona collections.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of collection dictionaries
        """
        query = self.session.query(PersonaCollectionModel)
        query = query.order_by(PersonaCollectionModel.name.asc())
        query = query.limit(limit).offset(offset)
        return [model.to_dict() for model in query.all()]

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a persona collection.

        Args:
            collection_id: Collection ID

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(PersonaCollectionModel).filter_by(id=collection_id).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def add_persona_to_collection(
        self,
        collection_id: str,
        persona_id: str,
        added_by: str | None = None,
    ) -> int:
        """Add a persona to a collection.

        Args:
            collection_id: Collection ID
            persona_id: Persona ID
            added_by: Optional user identifier

        Returns:
            Membership ID
        """
        # Check if already a member
        existing = (
            self.session.query(PersonaCollectionMemberModel)
            .filter_by(collection_id=collection_id, persona_id=persona_id)
            .first()
        )
        if existing:
            return existing.id

        model = PersonaCollectionMemberModel(
            collection_id=collection_id,
            persona_id=persona_id,
            added_by=added_by,
        )
        self.session.add(model)
        self.session.commit()
        return model.id

    def remove_persona_from_collection(
        self,
        collection_id: str,
        persona_id: str,
    ) -> bool:
        """Remove a persona from a collection.

        Args:
            collection_id: Collection ID
            persona_id: Persona ID

        Returns:
            True if removed, False if not found
        """
        model = (
            self.session.query(PersonaCollectionMemberModel)
            .filter_by(collection_id=collection_id, persona_id=persona_id)
            .first()
        )
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def get_personas_in_collection(self, collection_id: str) -> list[dict[str, Any]]:
        """Get all personas in a collection.

        Args:
            collection_id: Collection ID

        Returns:
            List of persona dictionaries
        """
        members = (
            self.session.query(PersonaCollectionMemberModel)
            .filter_by(collection_id=collection_id)
            .all()
        )
        personas = []
        for member in members:
            if member.persona:
                personas.append(member.persona.to_dict())
        return personas

    def get_collections_for_persona(self, persona_id: str) -> list[dict[str, Any]]:
        """Get all collections containing a persona.

        Args:
            persona_id: Persona ID

        Returns:
            List of collection dictionaries
        """
        members = (
            self.session.query(PersonaCollectionMemberModel)
            .filter_by(persona_id=persona_id)
            .all()
        )
        collections = []
        for member in members:
            if member.collection:
                collections.append(member.collection.to_dict())
        return collections

    # Population Template methods (per ADR-008 Phase 4)

    def save_population_template(self, template_data: dict[str, Any]) -> str:
        """Save a population template.

        Args:
            template_data: Template data dictionary

        Returns:
            Template ID
        """
        model = PopulationTemplateModel.from_dict(template_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_population_template(self, template_id: str) -> dict[str, Any] | None:
        """Get a population template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template data or None if not found
        """
        model = self.session.query(PopulationTemplateModel).filter_by(id=template_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_population_template_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a population template by name.

        Args:
            name: Template name

        Returns:
            Template data or None if not found
        """
        model = self.session.query(PopulationTemplateModel).filter_by(name=name).first()
        if model is None:
            return None
        return model.to_dict()

    def list_population_templates(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List population templates.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of template dictionaries
        """
        query = self.session.query(PopulationTemplateModel)
        query = query.order_by(PopulationTemplateModel.name.asc())
        query = query.limit(limit).offset(offset)
        return [model.to_dict() for model in query.all()]

    def delete_population_template(self, template_id: str) -> bool:
        """Delete a population template.

        Args:
            template_id: Template ID

        Returns:
            True if deleted, False if not found
        """
        model = self.session.query(PopulationTemplateModel).filter_by(id=template_id).first()
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def increment_template_usage(self, template_id: str) -> bool:
        """Increment the usage count for a population template.

        Args:
            template_id: Template ID

        Returns:
            True if updated, False if not found
        """
        model = self.session.query(PopulationTemplateModel).filter_by(id=template_id).first()
        if model is None:
            return False
        model.usage_count += 1
        self.session.commit()
        return True

    def increment_persona_usage(self, persona_id: str) -> bool:
        """Increment the usage count for a persona.

        Args:
            persona_id: Persona ID

        Returns:
            True if updated, False if not found
        """
        model = self.session.query(PersonaLibraryModel).filter_by(id=persona_id).first()
        if model is None:
            return False
        model.usage_count += 1
        self.session.commit()
        return True

    # Message Evaluation methods (for export service)

    def get_evaluations_for_simulation(
        self,
        simulation_id: str,
        evaluator_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get evaluations for messages in a simulation.

        Args:
            simulation_id: Simulation ID
            evaluator_name: Optional filter by evaluator

        Returns:
            List of evaluation dictionaries
        """
        # Check if MessageEvaluationModel exists
        try:
            from agentworld.persistence.models import MessageEvaluationModel
        except ImportError:
            # Model not yet created, return empty list
            return []

        # Get message IDs for simulation
        messages = self.get_messages_for_simulation(simulation_id)
        message_ids = [m["id"] for m in messages]

        if not message_ids:
            return []

        query = self.session.query(MessageEvaluationModel).filter(
            MessageEvaluationModel.message_id.in_(message_ids)
        )

        if evaluator_name is not None:
            query = query.filter_by(evaluator_name=evaluator_name)

        return [model.to_dict() for model in query.all()]

    def save_evaluation(self, evaluation_data: dict[str, Any]) -> str:
        """Save a message evaluation.

        Args:
            evaluation_data: Evaluation data dictionary

        Returns:
            Evaluation ID
        """
        try:
            from agentworld.persistence.models import MessageEvaluationModel
        except ImportError:
            raise RuntimeError("MessageEvaluationModel not yet available")

        model = MessageEvaluationModel.from_dict(evaluation_data)
        self.session.merge(model)
        self.session.commit()
        return model.id

    def get_evaluation(self, evaluation_id: str) -> dict[str, Any] | None:
        """Get an evaluation by ID.

        Args:
            evaluation_id: Evaluation ID

        Returns:
            Evaluation data or None if not found
        """
        try:
            from agentworld.persistence.models import MessageEvaluationModel
        except ImportError:
            return None

        model = self.session.query(MessageEvaluationModel).filter_by(id=evaluation_id).first()
        if model is None:
            return None
        return model.to_dict()

    def get_evaluations_for_message(self, message_id: str) -> list[dict[str, Any]]:
        """Get all evaluations for a specific message.

        Args:
            message_id: Message ID

        Returns:
            List of evaluation dictionaries
        """
        try:
            from agentworld.persistence.models import MessageEvaluationModel
        except ImportError:
            return []

        models = self.session.query(MessageEvaluationModel).filter_by(message_id=message_id).all()
        return [model.to_dict() for model in models]
