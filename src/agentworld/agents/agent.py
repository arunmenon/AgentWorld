"""Agent implementation."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from agentworld.core.models import Message, AgentConfig, LLMResponse
from agentworld.personas.traits import TraitVector
from agentworld.personas.prompts import generate_system_prompt
from agentworld.llm.provider import LLMProvider, get_provider
from agentworld.memory.base import Memory, MemoryConfig
from agentworld.memory.observation import Observation


@dataclass
class Agent:
    """An agent that can participate in conversations.

    Agents have personalities defined by trait vectors and can
    generate responses using LLM providers. They also have memory
    systems for storing observations and generating reflections.
    """

    name: str
    traits: TraitVector
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    background: str = ""
    system_prompt: str | None = None
    model: str | None = None
    simulation_id: str | None = None
    memory_config: MemoryConfig | None = None

    # Runtime state
    _provider: LLMProvider | None = field(default=None, repr=False)
    _memory: Memory | None = field(default=None, repr=False)
    _message_history: list[Message] = field(default_factory=list, repr=False)
    _total_tokens: int = field(default=0, repr=False)
    _total_cost: float = field(default=0.0, repr=False)

    def __post_init__(self) -> None:
        """Initialize agent after dataclass creation."""
        # Generate system prompt if not provided
        if self.system_prompt is None:
            self.system_prompt = generate_system_prompt(
                traits=self.traits,
                name=self.name,
                background=self.background,
            )

    @property
    def provider(self) -> LLMProvider:
        """Get the LLM provider."""
        if self._provider is None:
            self._provider = get_provider()
        return self._provider

    @provider.setter
    def provider(self, value: LLMProvider) -> None:
        """Set the LLM provider."""
        self._provider = value

    @property
    def memory(self) -> Memory:
        """Get the memory system."""
        if self._memory is None:
            config = self.memory_config or MemoryConfig()
            self._memory = Memory(config=config, llm_provider=self._provider)
        return self._memory

    @memory.setter
    def memory(self, value: Memory) -> None:
        """Set the memory system."""
        self._memory = value

    @property
    def observations(self) -> list[Observation]:
        """Get all observations from memory."""
        return self.memory.observations

    @property
    def reflections(self) -> list:
        """Get all reflections from memory."""
        return self.memory.reflections

    @property
    def message_history(self) -> list[Message]:
        """Get the message history."""
        return self._message_history.copy()

    @property
    def total_tokens(self) -> int:
        """Total tokens used by this agent."""
        return self._total_tokens

    @property
    def total_cost(self) -> float:
        """Total cost incurred by this agent."""
        return self._total_cost

    @classmethod
    def from_config(cls, config: AgentConfig, simulation_id: str | None = None) -> "Agent":
        """Create an agent from configuration.

        Args:
            config: AgentConfig instance
            simulation_id: Optional simulation ID

        Returns:
            Agent instance
        """
        traits = TraitVector.from_dict(config.traits)
        return cls(
            name=config.name,
            traits=traits,
            background=config.background,
            system_prompt=config.system_prompt,
            model=config.model,
            simulation_id=simulation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "traits": self.traits.to_dict(),
            "background": self.background,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "simulation_id": self.simulation_id,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
        }

    async def think(self, context: str, step: int = 0) -> str:
        """Generate a thought based on context.

        Args:
            context: Context to think about
            step: Current simulation step

        Returns:
            Generated thought/response
        """
        response = await self.provider.complete(
            prompt=context,
            model=self.model,
            system_prompt=self.system_prompt,
            agent_id=self.id,
            step=step,
        )

        self._total_tokens += response.tokens_used
        self._total_cost += response.cost

        return response.content

    async def respond_to(
        self,
        message: Message,
        context: str = "",
        step: int = 0,
    ) -> Message:
        """Generate a response to a message.

        Args:
            message: Message to respond to
            context: Additional context
            step: Current simulation step

        Returns:
            Response message
        """
        # Add observation about received message
        await self.memory.add_observation(
            content=f"Received message from {message.sender_id}: {message.content}",
            source=message.sender_id,
        )

        # Build prompt with memory context
        prompt_parts = []
        if context:
            prompt_parts.append(f"Context:\n{context}\n")

        # Add relevant memories to prompt
        memory_context = self.memory.get_context_for_prompt(recent_k=3)
        if memory_context:
            prompt_parts.append(memory_context)
            prompt_parts.append("")

        prompt_parts.append(f"{message.sender_id} said: \"{message.content}\"")
        prompt_parts.append(f"\nRespond as {self.name}:")

        prompt = "\n".join(prompt_parts)

        # Generate response
        content = await self.think(prompt, step=step)

        # Create response message
        response = Message(
            sender_id=self.id,
            receiver_id=message.sender_id,
            content=content,
            step=step,
            simulation_id=self.simulation_id,
        )

        # Add observation about own response
        await self.memory.add_observation(
            content=f"I responded to {message.sender_id}: {content}",
            source="self",
        )

        # Track message
        self._message_history.append(message)
        self._message_history.append(response)

        return response

    async def generate_message(
        self,
        prompt: str,
        receiver_id: str | None = None,
        step: int = 0,
    ) -> Message:
        """Generate a new message.

        Args:
            prompt: Prompt for message generation
            receiver_id: Optional receiver ID
            step: Current simulation step

        Returns:
            Generated message
        """
        content = await self.think(prompt, step=step)

        message = Message(
            sender_id=self.id,
            receiver_id=receiver_id,
            content=content,
            step=step,
            simulation_id=self.simulation_id,
        )

        self._message_history.append(message)
        return message

    def receive_message(self, message: Message) -> None:
        """Record a received message.

        Args:
            message: Message received
        """
        self._message_history.append(message)

    async def receive_message_async(self, message: Message) -> None:
        """Record a received message and add to memory.

        Args:
            message: Message received
        """
        self._message_history.append(message)
        # Add observation about the message
        await self.memory.add_observation(
            content=f"Observed {message.sender_id} say: {message.content}",
            source=message.sender_id,
        )

    def get_recent_messages(self, count: int = 10) -> list[Message]:
        """Get recent messages.

        Args:
            count: Number of messages to return

        Returns:
            List of recent messages
        """
        return self._message_history[-count:]

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()

    def clear_memory(self) -> None:
        """Clear all memory (observations and reflections)."""
        self.memory.clear()

    async def retrieve_memories(self, query: str, k: int = 5) -> list:
        """Retrieve relevant memories for a query.

        Args:
            query: Query text
            k: Number of memories to retrieve

        Returns:
            List of relevant memories (observations and reflections)
        """
        return await self.memory.retrieve(query, k=k)

    def __repr__(self) -> str:
        """String representation."""
        return f"Agent(id={self.id!r}, name={self.name!r}, traits={self.traits})"
