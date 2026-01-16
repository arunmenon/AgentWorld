"""Memory system base class.

Implements dual memory architecture with episodic observations and semantic reflections.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from agentworld.memory.observation import Observation
from agentworld.memory.reflection import Reflection, ReflectionConfig
from agentworld.memory.retrieval import MemoryRetrieval, RetrievalConfig
from agentworld.memory.importance import ImportanceRater
from agentworld.memory.embeddings import EmbeddingGenerator, EmbeddingConfig
from agentworld.llm.provider import LLMProvider


@dataclass
class RetentionPolicy:
    """Policy for managing memory growth in long-running simulations.

    Attributes:
        max_observations: Maximum observations per agent
        max_reflections: Maximum reflections per agent
        prune_strategy: How to select memories for pruning
    """
    max_observations: int = 1000
    max_reflections: int = 100
    prune_strategy: str = "importance_weighted"  # or "fifo", "recency"

    def should_prune(self, observation_count: int) -> bool:
        """Check if pruning is needed."""
        return observation_count > self.max_observations


@dataclass
class MemoryConfig:
    """Configuration for the memory system.

    Attributes:
        embedding_config: Configuration for embedding generation
        retrieval_config: Configuration for memory retrieval
        reflection_config: Configuration for reflection generation
        retention_policy: Policy for memory pruning
        use_llm_importance: Whether to use LLM for importance rating
    """
    embedding_config: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    retrieval_config: RetrievalConfig = field(default_factory=RetrievalConfig)
    reflection_config: ReflectionConfig = field(default_factory=ReflectionConfig)
    retention_policy: RetentionPolicy = field(default_factory=RetentionPolicy)
    use_llm_importance: bool = False  # Use heuristics by default for speed


QUESTION_GENERATION_PROMPT = """Given the following observations, generate {num_questions} high-level questions that could be answered by analyzing these observations. Focus on insights, patterns, and beliefs.

Recent observations:
{observations}

Generate {num_questions} questions, one per line."""

SYNTHESIS_PROMPT = """Based on the following memories, answer the question with an insightful reflection. Synthesize the information into a general insight or belief.

Question: {question}

Relevant memories:
{memories}

Provide a concise insight (1-2 sentences) that answers this question based on the memories."""


class Memory:
    """Dual memory system with episodic observations and semantic reflections.

    Implements the Generative Agents memory architecture with:
    - Observations: Raw experiences and events
    - Reflections: Synthesized insights from multiple observations
    - Retrieval: Combined scoring of recency, relevance, and importance
    - Reflection generation: Automatic synthesis when importance accumulates
    """

    def __init__(
        self,
        config: MemoryConfig | None = None,
        llm_provider: LLMProvider | None = None
    ):
        """Initialize memory system.

        Args:
            config: Memory system configuration
            llm_provider: LLM provider for importance rating and reflection
        """
        self.config = config or MemoryConfig()
        self.llm = llm_provider

        # Memory stores
        self._observations: List[Observation] = []
        self._reflections: List[Reflection] = []

        # Importance accumulator for triggering reflections
        self._importance_accumulator: float = 0.0

        # Components
        self._embeddings = EmbeddingGenerator(self.config.embedding_config)
        self._retrieval = MemoryRetrieval(
            self.config.retrieval_config,
            self._embeddings
        )
        self._importance = ImportanceRater(llm_provider)

    @property
    def observations(self) -> List[Observation]:
        """Get all observations."""
        return self._observations.copy()

    @property
    def reflections(self) -> List[Reflection]:
        """Get all reflections."""
        return self._reflections.copy()

    @property
    def all_memories(self) -> List[Observation | Reflection]:
        """Get all memories (observations + reflections)."""
        return self._observations + self._reflections

    async def add_observation(
        self,
        content: str,
        source: str = "",
        location: str = "",
        importance: float | None = None
    ) -> Observation:
        """Add a new observation to memory.

        Args:
            content: The observation text
            source: Who/what caused this observation
            location: Optional spatial context
            importance: Pre-computed importance (if None, will be computed)

        Returns:
            The created observation
        """
        # Compute importance if not provided
        if importance is None:
            importance = await self._importance.rate(
                content,
                use_llm=self.config.use_llm_importance
            )

        # Generate embedding
        embedding = await self._embeddings.embed(content)

        observation = Observation(
            content=content,
            source=source,
            location=location,
            importance=importance,
            embedding=embedding,
            embedding_model=self.config.embedding_config.model,
        )

        self._observations.append(observation)
        self._importance_accumulator += importance

        # Check if we should generate reflections
        if self.config.reflection_config.enabled:
            if self._importance_accumulator >= self.config.reflection_config.threshold:
                await self.generate_reflections()

        # Check if we need to prune
        self._maybe_prune()

        return observation

    async def retrieve(
        self,
        query: str,
        k: int = 10,
        include_reflections: bool = True
    ) -> List[Observation | Reflection]:
        """Retrieve relevant memories for a query.

        Args:
            query: Query text to find relevant memories for
            k: Number of memories to return
            include_reflections: Whether to include reflections in search

        Returns:
            Top-k relevant memories
        """
        memories = self._observations.copy()
        if include_reflections:
            memories.extend(self._reflections)

        return await self._retrieval.retrieve(query, memories, k)

    async def generate_reflections(self) -> List[Reflection]:
        """Generate reflections from accumulated observations.

        Called automatically when importance threshold is exceeded,
        or can be called manually.

        Returns:
            List of generated reflections
        """
        if not self.config.reflection_config.enabled:
            return []

        if not self._observations:
            return []

        if self.llm is None:
            # Can't generate reflections without LLM
            self._importance_accumulator = 0.0
            return []

        # Get recent observations for reflection
        recent = self._observations[-100:]

        # Generate questions about recent observations
        questions = await self._generate_questions(recent)

        # Generate reflections for each question
        reflections = []
        for question in questions[:self.config.reflection_config.questions_per_reflection]:
            # Retrieve relevant memories for this question
            relevant = await self._retrieval.retrieve(
                question,
                self.all_memories,
                k=self.config.reflection_config.memories_per_question
            )

            if not relevant:
                continue

            # Synthesize insight
            insight = await self._synthesize(question, relevant)

            if not insight:
                continue

            # Create reflection
            embedding = await self._embeddings.embed(insight)
            reflection = Reflection(
                content=insight,
                importance=self.config.reflection_config.min_reflection_importance,
                embedding=embedding,
                embedding_model=self.config.embedding_config.model,
                source_memories=[m.id for m in relevant],
                questions_addressed=[question],
            )
            reflections.append(reflection)
            self._reflections.append(reflection)

        # Reset accumulator
        self._importance_accumulator = 0.0

        return reflections

    async def _generate_questions(self, observations: List[Observation]) -> List[str]:
        """Generate reflection questions from observations.

        Args:
            observations: Recent observations to generate questions about

        Returns:
            List of question strings
        """
        if not self.llm:
            return []

        # Format observations for prompt
        obs_text = "\n".join(f"- {obs.content}" for obs in observations[-20:])
        num_questions = self.config.reflection_config.questions_per_reflection

        prompt = QUESTION_GENERATION_PROMPT.format(
            observations=obs_text,
            num_questions=num_questions
        )

        try:
            response = await self.llm.complete(prompt)
            questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
            return questions[:num_questions]
        except Exception:
            return []

    async def _synthesize(
        self,
        question: str,
        memories: List[Observation | Reflection]
    ) -> Optional[str]:
        """Synthesize an insight from memories answering a question.

        Args:
            question: The question to answer
            memories: Relevant memories to synthesize

        Returns:
            Insight string or None if synthesis fails
        """
        if not self.llm:
            return None

        # Format memories for prompt
        mem_text = "\n".join(f"- {m.content}" for m in memories)

        prompt = SYNTHESIS_PROMPT.format(
            question=question,
            memories=mem_text
        )

        try:
            response = await self.llm.complete(prompt)
            return response.content.strip()
        except Exception:
            return None

    def _maybe_prune(self) -> None:
        """Prune memories if over retention limits."""
        policy = self.config.retention_policy

        if not policy.should_prune(len(self._observations)):
            return

        if policy.prune_strategy == "importance_weighted":
            self._prune_importance_weighted()
        elif policy.prune_strategy == "fifo":
            self._prune_fifo()
        elif policy.prune_strategy == "recency":
            self._prune_recency()

    def _prune_importance_weighted(self) -> None:
        """Keep high-importance and recent memories."""
        policy = self.config.retention_policy
        now = datetime.now()

        # Score each observation
        scored = []
        for obs in self._observations:
            recency = self._retrieval._compute_recency(obs, now)
            importance_norm = (obs.importance - 1.0) / 9.0
            score = importance_norm * 0.7 + recency * 0.3
            scored.append((obs, score))

        # Sort by score and keep top max_observations
        scored.sort(key=lambda x: x[1], reverse=True)
        self._observations = [obs for obs, _ in scored[:policy.max_observations]]

    def _prune_fifo(self) -> None:
        """Keep most recent observations (first-in-first-out)."""
        policy = self.config.retention_policy
        self._observations = self._observations[-policy.max_observations:]

    def _prune_recency(self) -> None:
        """Keep most recent observations by timestamp."""
        policy = self.config.retention_policy
        sorted_obs = sorted(self._observations, key=lambda o: o.timestamp, reverse=True)
        self._observations = sorted_obs[:policy.max_observations]

    def get_context_for_prompt(
        self,
        recent_k: int = 5,
        format_template: str = "Recent memories:\n{memories}"
    ) -> str:
        """Get formatted memory context for inclusion in prompts.

        Simple utility for adding memory context to agent prompts.

        Args:
            recent_k: Number of recent memories to include
            format_template: Template with {memories} placeholder

        Returns:
            Formatted memory context string
        """
        recent = self._observations[-recent_k:]
        if not recent:
            return ""

        memories_text = "\n".join(f"- {obs.content}" for obs in recent)
        return format_template.format(memories=memories_text)

    def clear(self) -> None:
        """Clear all memories."""
        self._observations.clear()
        self._reflections.clear()
        self._importance_accumulator = 0.0
