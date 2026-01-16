# ADR-009: Use Case Scenarios

## Status
Accepted

## Dependencies
- **[ADR-004](./ADR-004-trait-vector-persona.md)**: Scenarios use persona/trait system for agent behavior
- **[ADR-005](./ADR-005-network-topology.md)**: Scenarios use topology for communication patterns
- **[ADR-006](./ADR-006-dual-memory.md)**: Scenarios use memory for context-aware responses

## Context

**User Requirement:**
> "Product Testing + Data Generation" as primary use cases

**Product Testing Patterns (from TinyTroupe - ADR-001):**
- **Ad Testing**: Simulated audience evaluates advertisements before budget spend
- **UX Testing**: Diverse user agents interact with product prototypes
- **Focus Groups**: Panel of persona agents discuss proposals
- **Interview Studies**: One-on-one structured interviews for feedback
- **A/B Testing**: Compare agent responses across variants

**Data Generation Patterns (from CAMEL - ADR-001):**
- **Role-Playing Conversations**: Two agents generate Q&A pairs
- **Self-Instruct**: Agents generate training examples
- **Chain-of-Thought**: Agents produce reasoning traces
- **Multi-Turn Dialogue**: Extended conversations for fine-tuning
- **Debate/Discussion**: Opposing viewpoints generate balanced data

## Decision

Implement **two primary scenario types** with shared infrastructure, leveraging **[ADR-004](./ADR-004-trait-vector-persona.md)** personas, **[ADR-005](./ADR-005-network-topology.md)** topologies, and **[ADR-006](./ADR-006-dual-memory.md)** memory.

### Moderator Agent Design

> **Clarification**: The "moderator" in focus group scenarios is a **real agent** with its own persona, not a system role. This ensures consistent behavior and enables moderator-participant interactions through the topology.

```python
def create_moderator_agent(config: ModeratorConfig) -> Agent:
    """
    Create a moderator agent for focus group scenarios.

    The moderator is a full Agent with:
    - Neutral persona optimized for facilitation
    - Access to the question list
    - Hub position in topology
    """
    return Agent(
        id="moderator",
        persona=PersonaProfile(
            name=config.name or "Moderator",
            traits=TraitVector(
                openness=0.7,        # Open to all responses
                conscientiousness=0.9,  # Follows structure
                extraversion=0.6,    # Engaged but not dominant
                agreeableness=0.8,   # Non-confrontational
                neuroticism=0.2,     # Calm under pressure
            ),
            occupation="Focus Group Moderator",
            description="You facilitate discussions, ask probing questions, "
                       "and ensure all participants have a chance to speak."
        ),
        behavior_mode="moderator"  # Special mode: poses questions, doesn't debate
    )
```

### Base Scenario Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from copy import deepcopy
import uuid

@dataclass
class ScenarioConfig:
    """Base configuration for all scenarios."""
    name: str
    description: str = ""
    max_steps: int = 100
    seed: Optional[int] = None  # For reproducibility

@dataclass
class ScenarioResult:
    """Standard result container for scenario outputs."""
    scenario_id: str
    scenario_type: str
    config: ScenarioConfig
    messages: List[Message]
    events: List[Event]
    metadata: Dict[str, Any] = field(default_factory=dict)

class Scenario(ABC):
    """Base class for simulation scenarios."""

    def __init__(self, world: World, config: ScenarioConfig):
        self.world = world
        self.config = config
        self.scenario_id = str(uuid.uuid4())
        self._message_log: List[Message] = []
        self._event_log: List[Event] = []

    @abstractmethod
    async def setup(self) -> None:
        """Configure world and agents for this scenario."""
        pass

    @abstractmethod
    async def run(self) -> ScenarioResult:
        """Execute the scenario."""
        pass

    async def inject_system_event(self, content: str,
                                   target_agents: List[str] = None) -> None:
        """
        Inject a system event (not from any agent) into the simulation.

        System events bypass topology constraints - they represent
        external stimuli like announcements, environment changes, etc.

        For agent-to-agent communication that must respect topology,
        use World.send_message() instead.
        """
        targets = target_agents or list(self.world.agents.keys())
        for agent_id in targets:
            await self.world.agents[agent_id].perceive(
                SystemEvent(content=content, source="system")
            )
            self._event_log.append(SystemEvent(
                content=content,
                target=agent_id,
                source="system"
            ))

    def _extract_responses(self, since_step: int = 0,
                          filter_type: str = "speech") -> List[AgentResponse]:
        """
        Extract agent responses from message log.

        Args:
            since_step: Only include messages from this step onward
            filter_type: Message type to filter (speech, thought, action)

        Returns:
            List of AgentResponse objects with agent_id, content, step
        """
        return [
            AgentResponse(
                agent_id=msg.sender,
                content=msg.content,
                step=msg.step,
                message_type=msg.message_type
            )
            for msg in self._message_log
            if msg.step >= since_step and msg.message_type == filter_type
        ]
```

### Subworld Creation

```python
class World:
    """Main simulation world (partial definition for subworld semantics)."""

    def create_subworld(self, agent_ids: List[str],
                        share_memory: bool = False) -> "World":
        """
        Create an isolated subworld with a subset of agents.

        Args:
            agent_ids: IDs of agents to include in subworld
            share_memory: If True, agents share memory with main world.
                         If False (default), agents get memory snapshots
                         that diverge from main world.

        Returns:
            New World instance with cloned or shared agents

        Note:
            Subworlds are useful for:
            - Parallel conversations (data generation)
            - Isolated experiments (A/B testing)
            - Breakout groups in larger simulations
        """
        subworld = World(
            config=deepcopy(self.config),
            topology=None  # Must be set by caller
        )

        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not in main world")

            if share_memory:
                # Shared reference - changes visible in main world
                subworld.agents[agent_id] = self.agents[agent_id]
            else:
                # Deep copy - isolated from main world
                subworld.agents[agent_id] = deepcopy(self.agents[agent_id])

        return subworld
```

### Product Testing Scenario

```python
@dataclass
class ProductTestConfig(ScenarioConfig):
    """Configuration for product testing scenarios."""
    product_name: str = ""
    product_description: str = ""
    test_type: str = "focus_group"  # focus_group, interview, survey
    questions: List[str] = field(default_factory=list)
    discussion_rounds: int = 3
    moderator_config: Optional[ModeratorConfig] = None

class ProductTestScenario(Scenario):
    """
    TinyTroupe-style product feedback simulation.

    Uses:
    - ADR-004: Diverse personas for varied feedback
    - ADR-005: Hub-spoke topology (moderator as hub)
    - ADR-006: Memory for consistent, context-aware responses
    """

    def __init__(self, world: World, config: ProductTestConfig):
        super().__init__(world, config)
        self.product_description = config.product_description
        self.test_type = config.test_type
        self.questions = config.questions
        self.moderator: Optional[Agent] = None

    async def setup(self) -> None:
        """
        Set up focus group with moderator as hub.

        Creates moderator agent and configures hub-spoke topology
        where moderator can communicate with all participants.
        """
        # Create moderator agent (not just a system role)
        self.moderator = create_moderator_agent(
            self.config.moderator_config or ModeratorConfig()
        )
        self.world.add_agent(self.moderator)

        # Build hub-spoke topology with moderator as hub (ADR-005)
        self.world.topology = HubSpokeTopology()
        self.world.topology.build(
            list(self.world.agents.keys()),
            hub_id=self.moderator.id  # Now guaranteed to exist
        )

    async def run_focus_group(self) -> FocusGroupResult:
        """Moderated group discussion with structured questions."""
        results = []
        current_step = 0

        # Moderator introduces the product (via agent action, respects topology)
        intro_msg = f"Welcome everyone. Today we'll discuss: {self.product_description}"
        await self.moderator.speak(intro_msg, broadcast=True)
        await self.world.step()
        current_step += 1

        for question in self.questions:
            question_start_step = current_step

            # Moderator poses question (as agent, through topology)
            await self.moderator.speak(f"Let me ask: {question}", broadcast=True)
            current_step += 1

            # Run multiple steps for discussion
            for _ in range(self.config.discussion_rounds):
                events = await self.world.step()
                self._event_log.extend(events)
                self._message_log.extend([e for e in events if isinstance(e, Message)])
                current_step += 1

            # Collect responses since this question started
            responses = self._extract_responses(since_step=question_start_step)
            results.append(QuestionResult(
                question=question,
                responses=responses,
                discussion_rounds=self.config.discussion_rounds
            ))

        return FocusGroupResult(
            scenario_id=self.scenario_id,
            product=self.product_description,
            questions=results,
            agent_profiles=[a.persona.to_dict() for a in self.world.agents.values()
                          if a.id != self.moderator.id],  # Exclude moderator
            moderator_id=self.moderator.id
        )

    async def run_interview(self, agent_id: str) -> InterviewResult:
        """One-on-one structured interview."""
        if agent_id not in self.world.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.world.agents[agent_id]
        responses = []

        for question in self.questions:
            # Interviewer (system or moderator) asks question
            await agent.perceive(Message(
                sender="interviewer",
                receiver=agent_id,
                content=question,
                message_type="speech"
            ))
            action = await agent.act()
            responses.append(InterviewResponse(
                question=question,
                answer=action.content,
                latency_ms=action.latency_ms
            ))

        return InterviewResult(
            scenario_id=self.scenario_id,
            agent_id=agent_id,
            agent_persona=agent.persona.to_dict(),
            responses=responses
        )

    async def run(self) -> ScenarioResult:
        """Execute scenario based on test_type."""
        await self.setup()

        if self.test_type == "focus_group":
            result = await self.run_focus_group()
        elif self.test_type == "interview":
            # Interview all participants
            results = []
            for agent_id in self.world.agents.keys():
                if agent_id != self.moderator.id:
                    results.append(await self.run_interview(agent_id))
            result = InterviewBatchResult(interviews=results)
        else:
            raise ValueError(f"Unknown test_type: {self.test_type}")

        return ScenarioResult(
            scenario_id=self.scenario_id,
            scenario_type=f"product_test_{self.test_type}",
            config=self.config,
            messages=self._message_log,
            events=self._event_log,
            metadata={"result": result}
        )
```

### Data Generation Scenario

```python
@dataclass
class DataGenerationConfig(ScenarioConfig):
    """Configuration for data generation scenarios."""
    output_format: str = "jsonl"  # jsonl, csv, huggingface
    min_turns: int = 5
    max_turns: int = 20
    diversity_threshold: float = 0.7  # Min embedding distance between outputs
    max_retries: int = 3  # Retries for low-quality outputs
    quality_filters: List[str] = field(default_factory=lambda: [
        "length_check",      # Min/max length
        "repetition_check",  # Avoid repetitive content
        "coherence_check",   # Basic coherence validation
    ])

@dataclass
class QualityCheckResult:
    """Result of quality filtering on generated data."""
    passed: bool
    check_name: str
    score: float
    reason: str = ""

class DataGenerationScenario(Scenario):
    """
    CAMEL-style synthetic data generation.

    Uses:
    - ADR-004: Role-specific personas (expert, questioner)
    - ADR-005: Pair topology for dialogues, mesh for debates
    - ADR-006: Memory enables coherent multi-turn conversations
    """

    def __init__(self, world: World, config: DataGenerationConfig):
        super().__init__(world, config)
        self._generated_embeddings: List[np.ndarray] = []  # For diversity check

    def _check_diversity(self, new_content: str) -> bool:
        """
        Check if new content is sufficiently different from existing outputs.
        Uses embedding distance to prevent repetitive generation.
        """
        if not self._generated_embeddings:
            return True

        new_embedding = self.world.embedding_provider.embed(new_content)

        for existing in self._generated_embeddings:
            similarity = cosine_similarity(new_embedding, existing)
            if similarity > self.config.diversity_threshold:
                return False  # Too similar to existing

        self._generated_embeddings.append(new_embedding)
        return True

    def _apply_quality_filters(self, content: str) -> List[QualityCheckResult]:
        """Apply configured quality filters to generated content."""
        results = []

        for filter_name in self.config.quality_filters:
            if filter_name == "length_check":
                passed = 50 <= len(content) <= 2000
                results.append(QualityCheckResult(
                    passed=passed,
                    check_name=filter_name,
                    score=1.0 if passed else 0.0,
                    reason="" if passed else f"Length {len(content)} out of bounds"
                ))
            elif filter_name == "repetition_check":
                # Check for repeated phrases
                words = content.lower().split()
                unique_ratio = len(set(words)) / len(words) if words else 0
                passed = unique_ratio > 0.5
                results.append(QualityCheckResult(
                    passed=passed,
                    check_name=filter_name,
                    score=unique_ratio,
                    reason="" if passed else "Too much repetition"
                ))
            elif filter_name == "coherence_check":
                # Basic coherence: has sentences, not just fragments
                has_sentences = ". " in content or content.endswith(".")
                results.append(QualityCheckResult(
                    passed=has_sentences,
                    check_name=filter_name,
                    score=1.0 if has_sentences else 0.0,
                    reason="" if has_sentences else "No complete sentences"
                ))

        return results

    async def generate_conversations(
        self,
        agent_pairs: List[Tuple[str, str]],
        topic: str,
        turns: int = 10
    ) -> List[Conversation]:
        """Generate multi-turn conversations between agent pairs."""
        conversations = []

        for agent_a_id, agent_b_id in agent_pairs:
            for retry in range(self.config.max_retries):
                # Create isolated subworld for this conversation
                pair_world = self.world.create_subworld(
                    [agent_a_id, agent_b_id],
                    share_memory=False  # Isolated to prevent leakage
                )
                pair_world.topology = MeshTopology()
                pair_world.topology.build([agent_a_id, agent_b_id])

                # Seed conversation with topic
                await pair_world.agents[agent_a_id].perceive(
                    SystemEvent(content=f"Start a conversation about: {topic}")
                )

                # Run conversation with dynamic stopping
                messages = []
                consecutive_short = 0

                for turn in range(self.config.max_turns):
                    events = await pair_world.step()
                    turn_messages = [e for e in events if isinstance(e, Message)]
                    messages.extend(turn_messages)

                    # Dynamic stopping: end if responses become too short
                    if turn_messages:
                        avg_len = sum(len(m.content) for m in turn_messages) / len(turn_messages)
                        if avg_len < 20:
                            consecutive_short += 1
                            if consecutive_short >= 2:
                                break  # Conversation exhausted
                        else:
                            consecutive_short = 0

                    # Minimum turns check
                    if turn >= self.config.min_turns - 1 and len(messages) >= turns:
                        break

                # Quality check
                full_content = " ".join(m.content for m in messages)
                quality_results = self._apply_quality_filters(full_content)

                if all(r.passed for r in quality_results) and self._check_diversity(full_content):
                    conversations.append(Conversation(
                        id=str(uuid.uuid4()),
                        participants=[agent_a_id, agent_b_id],
                        topic=topic,
                        messages=messages,
                        quality_scores={r.check_name: r.score for r in quality_results}
                    ))
                    break
                # else: retry with fresh subworld

        return conversations

    async def generate_qa_pairs(
        self,
        expert_agent_id: str,
        questioner_agent_id: str,
        domain: str,
        count: int = 100
    ) -> List[QAPair]:
        """Generate question-answer pairs for training data."""
        pairs = []
        expert = self.world.agents[expert_agent_id]
        questioner = self.world.agents[questioner_agent_id]

        # Configure questioner to ask about domain
        await questioner.perceive(SystemEvent(
            content=f"You are interviewing an expert about {domain}. "
                   f"Ask insightful, varied questions. Avoid repeating topics."
        ))

        questions_asked = set()  # Track for diversity

        for i in range(count):
            for retry in range(self.config.max_retries):
                # Questioner generates question
                q_action = await questioner.act()
                question = q_action.content

                # Diversity check: skip if too similar to previous questions
                if question.lower().strip() in questions_asked:
                    continue

                # Expert answers using memory (ADR-006)
                await expert.perceive(Message(
                    sender=questioner.id,
                    receiver=expert.id,
                    content=question,
                    message_type="speech"
                ))
                a_action = await expert.act()
                answer = a_action.content

                # Quality filter
                combined = f"Q: {question}\nA: {answer}"
                quality_results = self._apply_quality_filters(combined)

                if all(r.passed for r in quality_results):
                    questions_asked.add(question.lower().strip())
                    pairs.append(QAPair(
                        id=str(uuid.uuid4()),
                        question=question,
                        answer=answer,
                        domain=domain,
                        expert_persona=expert.persona.to_dict(),
                        quality_scores={r.check_name: r.score for r in quality_results}
                    ))
                    break

        return pairs

    async def generate_debate(
        self,
        topic: str,
        positions: Dict[str, str],  # agent_id -> position
        rounds: int = 5
    ) -> DebateResult:
        """Generate balanced debate data from opposing viewpoints."""
        # Use mesh topology so all can respond to all (ADR-005)
        self.world.topology = MeshTopology()
        self.world.topology.build(list(positions.keys()))

        # Assign positions to agents
        for agent_id, position in positions.items():
            agent = self.world.agents[agent_id]
            await agent.perceive(SystemEvent(
                content=f"Your position on '{topic}': {position}. "
                       f"Defend your position with reasoned arguments."
            ))

        # Run debate
        all_arguments = []
        for round_num in range(rounds):
            events = await self.world.step()
            for event in events:
                if isinstance(event, Message):
                    all_arguments.append(Argument(
                        round=round_num,
                        speaker=event.sender,
                        position=positions.get(event.sender, "unknown"),
                        content=event.content,
                        timestamp=event.timestamp
                    ))

        return DebateResult(
            scenario_id=self.scenario_id,
            topic=topic,
            positions=positions,
            arguments=all_arguments,
            total_rounds=rounds
        )

    async def setup(self) -> None:
        """Set up data generation environment."""
        # Default to mesh topology for flexibility
        if self.world.topology is None:
            self.world.topology = MeshTopology()
            self.world.topology.build(list(self.world.agents.keys()))

    async def run(self) -> ScenarioResult:
        """Execute data generation (override in subclass for specific task)."""
        await self.setup()
        return ScenarioResult(
            scenario_id=self.scenario_id,
            scenario_type="data_generation",
            config=self.config,
            messages=self._message_log,
            events=self._event_log,
            metadata={}
        )
```

### YAML Configuration and Parsing

```yaml
# config/examples/product_test.yaml
scenario:
  type: product_test
  name: "AI Writing Assistant Focus Group"
  test_type: focus_group
  discussion_rounds: 3
  seed: 42  # For reproducibility

product:
  name: "AI Writing Assistant"
  description: |
    An AI-powered tool that helps users write emails,
    documents, and social media posts.

questions:
  - "What's your first impression of this product concept?"
  - "How would this fit into your daily workflow?"
  - "What concerns do you have about using AI for writing?"
  - "Would you pay $10/month for this? Why or why not?"

moderator:
  name: "Sarah"
  style: "friendly"  # friendly, formal, probing

agents:
  count: 8
  diversity:
    occupations: ["engineer", "teacher", "marketer", "writer", "manager"]
    age_range: [25, 55]
    custom_traits:
      tech_savviness: [0.3, 0.9]  # Range for sampling (ADR-004)

topology:
  type: hub_spoke  # ADR-005
  # hub is automatically set to moderator
```

**Config Parser:**
```python
@dataclass
class ModeratorConfig:
    """Configuration for moderator agent."""
    name: str = "Moderator"
    style: str = "friendly"  # friendly, formal, probing

def parse_product_test_config(yaml_data: dict) -> ProductTestConfig:
    """
    Parse YAML config into ProductTestConfig.

    Maps YAML structure to config fields with sensible defaults.
    """
    scenario = yaml_data.get("scenario", {})
    product = yaml_data.get("product", {})

    moderator_data = yaml_data.get("moderator", {})
    moderator_config = ModeratorConfig(
        name=moderator_data.get("name", "Moderator"),
        style=moderator_data.get("style", "friendly")
    )

    return ProductTestConfig(
        name=scenario.get("name", "Untitled"),
        description=scenario.get("description", ""),
        max_steps=scenario.get("max_steps", 100),
        seed=scenario.get("seed"),
        product_name=product.get("name", ""),
        product_description=product.get("description", ""),
        test_type=scenario.get("test_type", "focus_group"),
        questions=yaml_data.get("questions", []),
        discussion_rounds=scenario.get("discussion_rounds", 3),
        moderator_config=moderator_config
    )

def parse_data_generation_config(yaml_data: dict) -> DataGenerationConfig:
    """Parse YAML config for data generation scenarios."""
    scenario = yaml_data.get("scenario", {})
    quality = yaml_data.get("quality", {})

    return DataGenerationConfig(
        name=scenario.get("name", "Untitled"),
        description=scenario.get("description", ""),
        max_steps=scenario.get("max_steps", 100),
        seed=scenario.get("seed"),
        output_format=scenario.get("output_format", "jsonl"),
        min_turns=quality.get("min_turns", 5),
        max_turns=quality.get("max_turns", 20),
        diversity_threshold=quality.get("diversity_threshold", 0.7),
        max_retries=quality.get("max_retries", 3),
        quality_filters=quality.get("filters", [
            "length_check", "repetition_check", "coherence_check"
        ])
    )
```

### Data Quality and Safety Filtering

```python
class DataSafetyFilter:
    """
    Filter generated data for quality and safety.

    Applied before persisting or exporting generated datasets.
    """

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()
        self._blocked_patterns: List[re.Pattern] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.blocked_patterns
        ]

    def filter_content(self, content: str) -> Tuple[bool, str]:
        """
        Check content against safety filters.

        Returns:
            (passed, reason) tuple
        """
        # Check blocked patterns
        for pattern in self._blocked_patterns:
            if pattern.search(content):
                return False, f"Blocked pattern: {pattern.pattern}"

        # Check minimum quality
        if len(content.strip()) < self.config.min_length:
            return False, f"Too short: {len(content)} < {self.config.min_length}"

        # Check for excessive repetition
        words = content.split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < self.config.min_unique_ratio:
                return False, f"Low diversity: {unique_ratio:.2f}"

        return True, ""

    def filter_dataset(self, records: List[dict],
                       content_field: str = "content") -> List[dict]:
        """Filter a dataset, removing records that fail safety checks."""
        filtered = []
        for record in records:
            content = record.get(content_field, "")
            passed, reason = self.filter_content(content)
            if passed:
                filtered.append(record)
        return filtered

@dataclass
class SafetyConfig:
    """Configuration for data safety filtering."""
    min_length: int = 10
    max_length: int = 10000
    min_unique_ratio: float = 0.3
    blocked_patterns: List[str] = field(default_factory=list)
```

### Export Formats

```python
class DataExporter:
    """Export generated data to various formats."""

    def export_jsonl(self, records: List[dict], path: str) -> None:
        """Export to JSON Lines format."""
        with open(path, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

    def export_csv(self, records: List[dict], path: str) -> None:
        """Export to CSV format."""
        if not records:
            return
        fieldnames = records[0].keys()
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def export_huggingface(self, records: List[dict],
                           dataset_name: str,
                           token: str = None) -> str:
        """Export to HuggingFace Hub as a dataset."""
        from datasets import Dataset
        dataset = Dataset.from_list(records)
        dataset.push_to_hub(dataset_name, token=token)
        return f"https://huggingface.co/datasets/{dataset_name}"
```

## Consequences

**Positive:**
- Clear abstractions for common use cases
- Reusable scenario infrastructure
- Easy to add new scenario types
- YAML config for non-developers
- Leverages ADR-004, ADR-005, ADR-006 for rich behavior
- Moderator is a real agent, enabling consistent behavior
- Quality filters prevent degenerate outputs
- Subworld isolation prevents data leakage

**Negative:**
- Opinionated structure may not fit all needs
- Scenarios add abstraction layer over raw simulation
- Quality filtering adds overhead to data generation

**Extensibility:**
- Base `Scenario` class allows custom implementations
- Scenarios can be composed (product test using generated conversations)
- Config-driven for flexibility without code changes
- Custom quality filters can be added

## Related ADRs
- [ADR-004](./ADR-004-trait-vector-persona.md): Persona system for agent behavior
- [ADR-005](./ADR-005-network-topology.md): Topology for communication patterns
- [ADR-006](./ADR-006-dual-memory.md): Memory for context-aware responses
- [ADR-010](./ADR-010-evaluation-metrics.md): Evaluates scenario outputs
