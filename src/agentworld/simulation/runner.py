"""Simulation runner."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable, Optional, TYPE_CHECKING

from agentworld.core.models import Message, SimulationConfig, SimulationStatus
from agentworld.core.exceptions import SimulationError
from agentworld.agents.agent import Agent
from agentworld.persistence.repository import Repository
from agentworld.persistence.database import init_db
from agentworld.topology.base import Topology, RoutingMode
from agentworld.topology.types import MeshTopology, create_topology
from agentworld.topology.graph import TopologyGraph
from agentworld.simulation.control import (
    ExecutionPhase,
    ThreePhaseExecutor,
    StepPhaseResults,
    PhaseResult,
)
from agentworld.plugins.hooks import PluginHooks
from agentworld.api.events import SimulationEventEmitter
from agentworld.apps.manager import SimulationAppManager

if TYPE_CHECKING:
    from agentworld.agents.external import InjectedAgentManager

logger = logging.getLogger(__name__)


# Type alias for step callbacks
StepCallback = Callable[[int, list[Message]], Awaitable[None] | None]


@dataclass
class Simulation:
    """Multi-agent simulation runner.

    Manages agents and orchestrates conversations between them.
    Supports topology-constrained communication.
    """

    name: str
    agents: list[Agent] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: SimulationStatus = SimulationStatus.PENDING
    config: SimulationConfig | None = None
    current_step: int = 0
    total_steps: int = 10
    initial_prompt: str = ""
    model: str = "openai/gpt-4o-mini"
    topology_type: str = "mesh"  # Default to full mesh
    topology_config: dict = field(default_factory=dict)
    routing_mode: RoutingMode = RoutingMode.DIRECT_ONLY

    # Runtime state
    _messages: list[Message] = field(default_factory=list, repr=False)
    _repository: Repository | None = field(default=None, repr=False)
    _step_callbacks: list[StepCallback] = field(default_factory=list, repr=False)
    _total_tokens: int = field(default=0, repr=False)
    _total_cost: float = field(default=0.0, repr=False)
    _topology: Topology | None = field(default=None, repr=False)
    _topology_graph: TopologyGraph | None = field(default=None, repr=False)
    _emitter: SimulationEventEmitter | None = field(default=None, repr=False)
    _injection_manager: "InjectedAgentManager | None" = field(default=None, repr=False)
    _app_manager: SimulationAppManager | None = field(default=None, repr=False)

    # τ²-bench state-constrained mode (ADR-020.1)
    state_constrained_mode: bool = False
    _state_constrained_agents: set[str] = field(default_factory=set, repr=False)

    @classmethod
    def from_config(cls, config: SimulationConfig) -> "Simulation":
        """Create a simulation from configuration.

        Args:
            config: SimulationConfig instance

        Returns:
            Simulation instance
        """
        # Extract topology config if present
        topology_type = getattr(config, "topology_type", None) or "mesh"
        topology_config = getattr(config, "topology_config", None) or {}

        sim = cls(
            name=config.name,
            config=config,
            total_steps=config.steps,
            initial_prompt=config.initial_prompt,
            model=config.model,
            topology_type=topology_type,
            topology_config=topology_config,
        )

        # Create agents
        for agent_config in config.agents:
            agent = Agent.from_config(agent_config, simulation_id=sim.id)
            if agent.model is None:
                agent.model = config.model
            sim.agents.append(agent)

        return sim

    @property
    def repository(self) -> Repository:
        """Get the repository, creating if needed."""
        if self._repository is None:
            init_db()
            self._repository = Repository()
        return self._repository

    @repository.setter
    def repository(self, value: Repository) -> None:
        """Set the repository."""
        self._repository = value

    @property
    def topology(self) -> Topology:
        """Get the topology, creating if needed."""
        if self._topology is None:
            self._initialize_topology()
        return self._topology

    @topology.setter
    def topology(self, value: Topology) -> None:
        """Set the topology."""
        self._topology = value
        self._topology_graph = TopologyGraph(value, self.routing_mode)

    @property
    def topology_graph(self) -> TopologyGraph:
        """Get the topology graph wrapper."""
        if self._topology_graph is None:
            self._topology_graph = TopologyGraph(self.topology, self.routing_mode)
        return self._topology_graph

    @property
    def emitter(self) -> SimulationEventEmitter:
        """Get the event emitter for real-time updates."""
        if self._emitter is None:
            self._emitter = SimulationEventEmitter(self.id)
        return self._emitter

    @property
    def injection_manager(self) -> "InjectedAgentManager | None":
        """Get the injection manager for external agents."""
        return self._injection_manager

    @injection_manager.setter
    def injection_manager(self, value: "InjectedAgentManager") -> None:
        """Set the injection manager."""
        self._injection_manager = value

    @property
    def app_manager(self) -> SimulationAppManager | None:
        """Get the app manager for simulated apps."""
        return self._app_manager

    async def initialize_apps(self, app_configs: list[dict[str, Any]] | None = None) -> None:
        """Initialize simulated apps for this simulation.

        Args:
            app_configs: Optional list of app configurations.
                         If not provided, uses config.apps if available.
        """
        # Get app configs from simulation config if not provided
        if app_configs is None and self.config is not None:
            config_dict = self.config.to_dict() if hasattr(self.config, 'to_dict') else {}
            app_configs = config_dict.get("apps", [])

        if not app_configs:
            return

        # Create app manager
        self._app_manager = SimulationAppManager(simulation_id=self.id)
        self._app_manager.set_repository(self.repository)

        # Initialize apps with agent name mapping for name resolution
        agent_ids = [agent.id for agent in self.agents]
        agent_names = {agent.id: agent.name for agent in self.agents}
        await self._app_manager.initialize_apps(app_configs, agent_ids, agent_names)

        logger.info(f"Initialized {len(self._app_manager.get_app_ids())} apps for simulation {self.id}")

        # Add app instructions to agent system prompts
        app_prompt = self._app_manager.get_available_apps_prompt()
        if app_prompt:
            # Add final mandatory instruction
            final_instruction = (
                "\n\n---\n"
                "CRITICAL OUTPUT REQUIREMENT: When you want to perform an action like transferring money, "
                "you MUST include the APP_ACTION directive in your response. "
                "Saying 'I will send money' does NOTHING. You must ACTUALLY output:\n"
                'APP_ACTION: paypal_test.transfer(to="recipient_name", amount=50)\n'
                "Include this on its own line in your message. This is mandatory, not optional.\n"
                "---"
            )
            for agent in self.agents:
                if agent.system_prompt:
                    agent.system_prompt = f"{agent.system_prompt}\n\n{app_prompt}{final_instruction}"
                else:
                    agent.system_prompt = f"{app_prompt}{final_instruction}"
            logger.info(f"Added app instructions to {len(self.agents)} agents")

    def _initialize_topology(self) -> None:
        """Initialize topology based on configuration."""
        agent_ids = [agent.id for agent in self.agents]
        self._topology = create_topology(
            self.topology_type,
            agent_ids,
            **self.topology_config
        )
        self._topology_graph = TopologyGraph(self._topology, self.routing_mode)

    def can_communicate(self, sender_id: str, receiver_id: str) -> bool:
        """Check if sender can communicate with receiver.

        Args:
            sender_id: Sending agent ID
            receiver_id: Receiving agent ID

        Returns:
            True if communication is allowed
        """
        return self.topology_graph.can_send_message(sender_id, receiver_id)

    def get_valid_recipients(self, sender_id: str) -> list[str]:
        """Get valid recipients for a sender based on topology.

        Args:
            sender_id: Sending agent ID

        Returns:
            List of valid recipient agent IDs
        """
        return self.topology_graph.get_valid_recipients(sender_id)

    @property
    def messages(self) -> list[Message]:
        """Get all messages."""
        return self._messages.copy()

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all agents."""
        return sum(a.total_tokens for a in self.agents)

    @property
    def total_cost(self) -> float:
        """Total cost across all agents."""
        return sum(a.total_cost for a in self.agents)

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the simulation.

        Args:
            agent: Agent to add
        """
        agent.simulation_id = self.id
        self.agents.append(agent)

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent or None if not found
        """
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def get_agent_by_name(self, name: str) -> Agent | None:
        """Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent or None if not found
        """
        for agent in self.agents:
            if agent.name.lower() == name.lower():
                return agent
        return None

    def on_step(self, callback: StepCallback) -> None:
        """Register a step callback.

        Args:
            callback: Function called after each step with (step_number, messages)
        """
        self._step_callbacks.append(callback)

    async def _notify_step(self, step: int, messages: list[Message]) -> None:
        """Notify all step callbacks.

        Args:
            step: Step number
            messages: Messages from this step
        """
        for callback in self._step_callbacks:
            result = callback(step, messages)
            if asyncio.iscoroutine(result):
                await result

    def _save_state(self) -> None:
        """Save current state to repository."""
        # Save simulation
        sim_data = {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "config": self.config.to_dict() if self.config else None,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }
        self.repository.save_simulation(sim_data)

        # Save agents
        for agent in self.agents:
            agent_data = {
                "id": agent.id,
                "simulation_id": self.id,
                "name": agent.name,
                "traits": agent.traits.to_dict(),
                "background": agent.background,
                "system_prompt": agent.system_prompt,
                "model": agent.model,
            }
            self.repository.save_agent(agent_data)

        # Save topology configuration
        if self._topology is not None:
            self.repository.save_topology_config({
                "simulation_id": self.id,
                "topology_type": self.topology_type,
                "directed": isinstance(self._topology.graph, type(self._topology.graph)),
                "config": self.topology_config,
            })

            # Save topology edges
            edges = [
                (source, target, data.get("weight", 1.0))
                for source, target, data in self._topology.graph.edges(data=True)
            ]
            self.repository.save_topology_edges(self.id, edges)

    def _save_message(self, message: Message) -> None:
        """Save a message to repository.

        Args:
            message: Message to save
        """
        message_data = {
            "id": message.id,
            "simulation_id": self.id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "step": message.step,
            "timestamp": message.timestamp.isoformat(),
        }
        self.repository.save_message(message_data)

    async def _generate_message_with_injection(
        self,
        agent: Agent,
        prompt: str,
        receiver_id: str | None,
        step: int,
    ) -> Message:
        """Generate a message, using external agent if injected.

        Args:
            agent: The agent generating the message
            prompt: The prompt/context for generation
            receiver_id: Target receiver ID
            step: Current simulation step

        Returns:
            Generated message
        """
        # Check if agent has an injected external endpoint
        if self._injection_manager and self._injection_manager.is_injected(agent.id):
            provider = self._injection_manager.get(agent.id)
            if provider:
                try:
                    # Build conversation history
                    conversation_history = [
                        {
                            "sender_id": msg.sender_id,
                            "sender": self.get_agent(msg.sender_id).name if self.get_agent(msg.sender_id) else msg.sender_id,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat(),
                        }
                        for msg in self._messages[-10:]
                    ]

                    # Call external agent
                    response_text, metrics = await provider.generate_response(
                        agent=agent,
                        stimulus=prompt,
                        conversation_history=conversation_history,
                        run_id=self.id,
                        turn_id=str(uuid.uuid4()),
                        simulation_config=self.config.to_dict() if self.config else None,
                    )

                    # If we got a response, create message from it
                    if response_text:
                        logger.info(
                            f"External agent response for {agent.name}: {response_text[:100]}..."
                        )
                        return Message(
                            id=str(uuid.uuid4())[:8],
                            sender_id=agent.id,
                            receiver_id=receiver_id,
                            content=response_text,
                            step=step,
                            timestamp=datetime.now(),
                        )

                    # Empty response means fallback to simulated agent
                    logger.info(
                        f"External agent returned empty response for {agent.name}, "
                        f"falling back to simulated agent"
                    )

                except Exception as e:
                    logger.warning(
                        f"External agent error for {agent.name}: {e}, "
                        f"falling back to simulated agent"
                    )

        # Use internal agent (either no injection or fallback)
        return await agent.generate_message(
            prompt=prompt,
            receiver_id=receiver_id,
            step=step,
        )

    async def _build_context_with_apps(self, for_agent: Agent, recent_count: int = 5) -> str:
        """Build context string for an agent, including app observations.

        Args:
            for_agent: Agent to build context for
            recent_count: Number of recent messages to include

        Returns:
            Context string with app observations
        """
        lines = []

        # Add app observations if app manager exists
        if self._app_manager is not None:
            observations = await self._app_manager.get_agent_observations(for_agent.id)
            if observations:
                obs_text = self._app_manager.format_observations_for_context(observations)
                lines.append(obs_text)

        # Add observable state for state-constrained agents (τ²-bench)
        if (
            self.state_constrained_mode
            and for_agent.id in self._state_constrained_agents
            and self._app_manager is not None
        ):
            observable_state = await self._app_manager.get_observable_state(for_agent.id)
            if observable_state:
                lines.append("\n[Your Observable Device State]")
                lines.append("(You can ONLY report information shown below)")
                lines.append("---")
                for app_id, app_state in observable_state.items():
                    lines.append(f"  [{app_id}]")
                    for field_name, field_value in app_state.items():
                        if isinstance(field_value, bool):
                            display = "Yes" if field_value else "No"
                        elif field_value is None:
                            display = "(not shown)"
                        else:
                            display = str(field_value)
                        lines.append(f"    • {field_name}: {display}")
                lines.append("---")
                lines.append("IMPORTANT: Only report what you can see above. Do not invent information.")
                lines.append("")

        # Add topic
        if self.initial_prompt:
            lines.append(f"Topic: {self.initial_prompt}\n")

        # Add recent conversation
        recent = self._messages[-recent_count:] if self._messages else []
        if recent:
            lines.append("Recent conversation:")
            for msg in recent:
                sender = self.get_agent(msg.sender_id)
                sender_name = sender.name if sender else msg.sender_id
                lines.append(f"  {sender_name}: {msg.content}")

        # Add few-shot example if app manager has apps
        if self._app_manager is not None and self._app_manager.get_app_ids():
            lines.append("")
            lines.append("---")
            lines.append("EXAMPLE of a proper response when paying someone:")
            lines.append('"""')
            lines.append("Hey Alice, sending the money now!")
            lines.append("")
            lines.append('APP_ACTION: paypal_test.transfer(to="alice", amount=50)')
            lines.append('"""')
            lines.append("")
            lines.append("Your response MUST follow this format if you're performing an action.")
            lines.append("---")

        return "\n".join(lines) if lines else self.initial_prompt

    def enable_state_constrained_mode(self, agent_ids: list[str] | None = None) -> None:
        """Enable τ²-bench state-constrained mode for specified agents.

        In state-constrained mode, user agents can only report information
        that is marked as observable in the app state schema. This prevents
        user simulators from hallucinating device information.

        Args:
            agent_ids: List of agent IDs to constrain. If None, constrains
                all agents with role=CUSTOMER.
        """
        self.state_constrained_mode = True

        if agent_ids is not None:
            self._state_constrained_agents = set(agent_ids)
        else:
            # Default: constrain all CUSTOMER role agents
            from agentworld.apps.definition import AgentRole
            for agent in self.agents:
                # Check if agent has a role attribute or tag
                agent_role = getattr(agent, "role", None)
                if agent_role == AgentRole.CUSTOMER or agent_role == "customer":
                    self._state_constrained_agents.add(agent.id)
                # Also check role_tags
                role_tags = getattr(agent, "role_tags", []) or []
                if "customer" in role_tags or "user" in role_tags:
                    self._state_constrained_agents.add(agent.id)

        logger.info(
            f"Enabled state-constrained mode for {len(self._state_constrained_agents)} agents"
        )

    def disable_state_constrained_mode(self) -> None:
        """Disable τ²-bench state-constrained mode."""
        self.state_constrained_mode = False
        self._state_constrained_agents.clear()
        logger.info("Disabled state-constrained mode")

    def _build_context(self, for_agent: Agent, recent_count: int = 5) -> str:
        """Build context string for an agent (sync version).

        Args:
            for_agent: Agent to build context for
            recent_count: Number of recent messages to include

        Returns:
            Context string
        """
        recent = self._messages[-recent_count:] if self._messages else []
        if not recent:
            return self.initial_prompt

        lines = []
        if self.initial_prompt:
            lines.append(f"Topic: {self.initial_prompt}\n")

        lines.append("Recent conversation:")
        for msg in recent:
            sender = self.get_agent(msg.sender_id)
            sender_name = sender.name if sender else msg.sender_id
            lines.append(f"  {sender_name}: {msg.content}")

        return "\n".join(lines)

    async def step(self, use_three_phase: bool = False) -> list[Message]:
        """Execute one simulation step.

        Args:
            use_three_phase: If True, use three-phase execution model (PERCEIVE, ACT, COMMIT)
                           per ADR-011 for deterministic ordering

        Returns:
            List of messages generated in this step

        Raises:
            SimulationError: If simulation cannot step
        """
        if self.status == SimulationStatus.COMPLETED:
            raise SimulationError("Simulation already completed")

        if self.status == SimulationStatus.FAILED:
            raise SimulationError("Simulation failed")

        if not self.agents:
            raise SimulationError("No agents in simulation")

        # Update status
        if self.status == SimulationStatus.PENDING:
            self.status = SimulationStatus.RUNNING
            self._save_state()
            # Emit simulation started event
            self.emitter.simulation_started()

        self.current_step += 1
        step_messages: list[Message] = []

        # Initialize topology if needed
        if self._topology is None and self.agents:
            self._initialize_topology()

        # Emit step started event
        self.emitter.step_started(self.current_step, self.total_steps)

        # Plugin hook: step start (per ADR-014)
        PluginHooks.on_step_start(self.current_step, self)

        # Update app manager step
        if self._app_manager is not None:
            self._app_manager.set_current_step(self.current_step)

        if use_three_phase:
            # Three-phase execution per ADR-011
            step_messages = await self._step_three_phase()
        else:
            # Standard sequential execution
            step_messages = await self._step_sequential()

        # Plugin hook: step complete (per ADR-014)
        PluginHooks.on_step_complete(self.current_step, self)

        # Emit step completed event
        self.emitter.step_completed(
            self.current_step,
            self.total_steps,
            messages_generated=len(step_messages)
        )

        # Notify callbacks
        await self._notify_step(self.current_step, step_messages)

        # Check if completed
        if self.current_step >= self.total_steps:
            self.status = SimulationStatus.COMPLETED
            self.emitter.simulation_completed({
                "total_messages": len(self._messages),
                "total_tokens": self.total_tokens,
                "total_cost": self.total_cost,
            })

        # Update state
        self.repository.update_simulation(self.id, {
            "status": self.status.value,
            "current_step": self.current_step,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        })

        return step_messages

    async def _step_sequential(self) -> list[Message]:
        """Execute step with sequential agent processing.

        Returns:
            List of messages generated
        """
        step_messages: list[Message] = []

        for i, agent in enumerate(self.agents):
            # Build context (with app observations if available)
            if self._app_manager is not None:
                context = await self._build_context_with_apps(agent)
            else:
                context = self._build_context(agent)

            # Determine receiver based on topology
            valid_recipients = self.get_valid_recipients(agent.id)
            if valid_recipients:
                receiver_id = valid_recipients[i % len(valid_recipients)]
            else:
                receiver_id = None

            # Get receiver name if available
            receiver = self.get_agent(receiver_id) if receiver_id else None
            receiver_name = receiver.name if receiver else None

            # Emit agent thinking event
            self.emitter.agent_thinking(agent.id, agent.name)

            # Generate message
            if self.current_step == 1 and i == 0:
                prompt = f"Start a conversation about: {self.initial_prompt}\n\nBegin by sharing your initial thoughts."
            else:
                prompt = f"{context}\n\nContinue the conversation naturally. Respond to what others have said or add your own perspective."

            # Use injection-aware message generation
            message = await self._generate_message_with_injection(
                agent=agent,
                prompt=prompt,
                receiver_id=receiver_id,
                step=self.current_step,
            )

            # Process app actions in message (per ADR-017)
            if self._app_manager is not None:
                cleaned_content, execution_results = await self._app_manager.process_message(
                    agent.id, message.content
                )
                # Update message content if actions were extracted
                if execution_results:
                    # Keep the cleaned message content (without action directives)
                    message.content = cleaned_content
                    # Log action results
                    for result in execution_results:
                        if result.result.success:
                            logger.info(
                                f"App action {result.action.app_id}.{result.action.action} "
                                f"succeeded for {agent.name}"
                            )
                        else:
                            logger.warning(
                                f"App action {result.action.app_id}.{result.action.action} "
                                f"failed for {agent.name}: {result.result.error}"
                            )

            # Emit agent responded event
            self.emitter.agent_responded(agent.id, agent.name, message.content)

            # Track message
            self._messages.append(message)
            step_messages.append(message)
            self._save_message(message)

            # Emit message created event
            self.emitter.message_created(
                message_id=message.id,
                sender_id=agent.id,
                sender_name=agent.name,
                receiver_id=receiver_id,
                receiver_name=receiver_name,
                content_preview=message.content,
                step=self.current_step,
            )

            # Plugin hook: message sent (per ADR-014)
            PluginHooks.on_message_sent(message, self)

            # Notify other agents based on topology
            for other_agent in self.agents:
                if other_agent.id != agent.id:
                    if self.can_communicate(agent.id, other_agent.id):
                        other_agent.receive_message(message)

        return step_messages

    async def _step_three_phase(self) -> list[Message]:
        """Execute step using three-phase model per ADR-011.

        Phase 1 (PERCEIVE): All agents observe current state
        Phase 2 (ACT): All agents decide on actions concurrently
        Phase 3 (COMMIT): All actions applied atomically

        Returns:
            List of messages generated
        """
        executor = ThreePhaseExecutor()
        step_messages: list[Message] = []
        phase_results = StepPhaseResults(step_number=self.current_step)

        # ===== PHASE 1: PERCEIVE =====
        # All agents observe the current state (read-only)
        perceptions: dict[str, dict] = {}

        async def perceive_for_agent(agent: Agent) -> dict:
            """Gather perception data for an agent."""
            # Use async context builder if app manager is available
            if self._app_manager is not None:
                context = await self._build_context_with_apps(agent)
            else:
                context = self._build_context(agent)
            valid_recipients = self.get_valid_recipients(agent.id)
            recent_msgs = self._messages[-10:] if self._messages else []
            return {
                "context": context,
                "valid_recipients": valid_recipients,
                "recent_messages": recent_msgs,
                "step": self.current_step,
            }

        for agent in self.agents:
            result = await executor.execute_perceive(
                agent_id=agent.id,
                perceive_fn=lambda a=agent: perceive_for_agent(a),
            )
            phase_results.perceive_results.append(result)
            if result.success:
                perceptions[agent.id] = result.data

        # ===== PHASE 2: ACT =====
        # All agents decide on actions based on perceptions
        actions: dict[str, Message | None] = {}

        async def act_for_agent(agent: Agent, perception: dict) -> Message | None:
            """Generate action (message) for an agent."""
            idx = self.agents.index(agent)
            valid_recipients = perception.get("valid_recipients", [])
            if valid_recipients:
                receiver_id = valid_recipients[idx % len(valid_recipients)]
            else:
                receiver_id = None

            context = perception.get("context", "")
            if self.current_step == 1 and idx == 0:
                prompt = f"Start a conversation about: {self.initial_prompt}\n\nBegin by sharing your initial thoughts."
            else:
                prompt = f"{context}\n\nContinue the conversation naturally. Respond to what others have said or add your own perspective."

            # Use injection-aware message generation
            return await self._generate_message_with_injection(
                agent=agent,
                prompt=prompt,
                receiver_id=receiver_id,
                step=self.current_step,
            )

        for agent in self.agents:
            perception = perceptions.get(agent.id, {})
            # Emit agent thinking event
            self.emitter.agent_thinking(agent.id, agent.name)
            result = await executor.execute_act(
                agent_id=agent.id,
                act_fn=lambda p=perception, a=agent: act_for_agent(a, p),
                perception_data=perception,
            )
            phase_results.act_results.append(result)
            if result.success and result.data:
                actions[agent.id] = result.data
                # Emit agent responded event
                self.emitter.agent_responded(agent.id, agent.name, result.data.content)

        # ===== PHASE 3: COMMIT =====
        # Apply all actions atomically
        async def commit_message(agent_id: str, message: Message) -> Message:
            """Commit a message to the simulation state."""
            # Process app actions in message (per ADR-017)
            if self._app_manager is not None:
                cleaned_content, execution_results = await self._app_manager.process_message(
                    agent_id, message.content
                )
                # Update message content if actions were extracted
                if execution_results:
                    message.content = cleaned_content
                    # Log action results
                    for exec_result in execution_results:
                        if exec_result.result.success:
                            logger.info(
                                f"App action {exec_result.action.app_id}.{exec_result.action.action} "
                                f"succeeded for agent {agent_id}"
                            )
                        else:
                            logger.warning(
                                f"App action {exec_result.action.app_id}.{exec_result.action.action} "
                                f"failed for agent {agent_id}: {exec_result.result.error}"
                            )

            self._messages.append(message)
            self._save_message(message)
            return message

        for agent_id, message in actions.items():
            if message:
                result = await executor.execute_commit(
                    agent_id=agent_id,
                    commit_fn=lambda m=message, aid=agent_id: commit_message(aid, m),
                    action_data=message,
                )
                phase_results.commit_results.append(result)
                if result.success:
                    step_messages.append(message)
                    # Emit message created event
                    agent = self.get_agent(agent_id)
                    receiver = self.get_agent(message.receiver_id) if message.receiver_id else None
                    self.emitter.message_created(
                        message_id=message.id,
                        sender_id=agent_id,
                        sender_name=agent.name if agent else agent_id,
                        receiver_id=message.receiver_id,
                        receiver_name=receiver.name if receiver else None,
                        content_preview=message.content,
                        step=self.current_step,
                    )

        # Plugin hook: message sent for each committed message (per ADR-014)
        for message in step_messages:
            PluginHooks.on_message_sent(message, self)

        # Notify agents of all committed messages
        for message in step_messages:
            for agent in self.agents:
                if agent.id != message.sender_id:
                    if self.can_communicate(message.sender_id, agent.id):
                        agent.receive_message(message)

        return step_messages

    async def run(self, steps: int | None = None) -> list[Message]:
        """Run the simulation for multiple steps.

        Args:
            steps: Number of steps to run (defaults to remaining steps)

        Returns:
            All messages generated

        Raises:
            SimulationError: If simulation cannot run
        """
        if steps is None:
            steps = self.total_steps - self.current_step

        all_messages: list[Message] = []

        # Initialize apps if not already done (per ADR-017)
        if self._app_manager is None and self.config is not None:
            await self.initialize_apps()

        # Plugin hook: simulation start (per ADR-014)
        PluginHooks.on_simulation_start(self)

        for _ in range(steps):
            if self.status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED):
                break

            step_messages = await self.step()
            all_messages.extend(step_messages)

        # Plugin hook: simulation end (per ADR-014)
        result = {"messages": all_messages, "status": self.status}
        PluginHooks.on_simulation_end(self, result)

        return all_messages

    def to_dict(self) -> dict[str, Any]:
        """Convert simulation to dictionary.

        Returns:
            Dictionary representation
        """
        topology_info = None
        if self._topology is not None:
            metrics = self._topology.get_metrics()
            topology_info = {
                "type": self.topology_type,
                "node_count": metrics.node_count,
                "edge_count": metrics.edge_count,
                "density": metrics.density,
                "is_connected": metrics.is_connected,
            }

        # Get app info if available (per ADR-017)
        apps_info = None
        if self._app_manager is not None:
            apps_info = {
                "active_apps": self._app_manager.get_app_ids(),
                "states": self._app_manager.get_all_states(),
            }

        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "agents": [a.to_dict() for a in self.agents],
            "message_count": len(self._messages),
            "topology": topology_info,
            "apps": apps_info,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Simulation(id={self.id!r}, name={self.name!r}, "
            f"status={self.status.value}, agents={len(self.agents)})"
        )
