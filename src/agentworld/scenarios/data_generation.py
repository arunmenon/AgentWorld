"""Data generation scenario for synthetic data creation.

This module implements CAMEL-style synthetic data generation
as specified in ADR-009.
"""

from dataclasses import dataclass, field
from typing import Any

from agentworld.scenarios.base import (
    Scenario,
    ScenarioConfig,
    ScenarioResult,
    ScenarioStatus,
    AgentResponse,
    SystemEvent,
)
from agentworld.scenarios.stimulus import StimulusInjector, create_question
from agentworld.agents.agent import Agent
from agentworld.personas.traits import TraitVector
from agentworld.simulation.runner import Simulation
from agentworld.topology.types import create_topology


@dataclass
class DataGenerationConfig(ScenarioConfig):
    """Configuration for data generation scenarios.

    Supports various output formats and quality controls
    for synthetic data generation.
    """

    # Output format
    output_format: str = "jsonl"  # jsonl, csv, huggingface

    # Generation parameters
    min_turns: int = 5
    max_turns: int = 20
    num_conversations: int = 10

    # Conversation setup
    topic: str = ""
    system_prompt: str = ""
    role_a: str = "assistant"  # First agent's role
    role_b: str = "user"  # Second agent's role

    # Quality controls
    diversity_threshold: float = 0.7  # Min embedding distance
    max_retries: int = 3
    quality_filters: list[str] = field(default_factory=lambda: [
        "length_check",
        "repetition_check",
    ])

    # Custom roles/personas
    role_a_traits: dict[str, float] | None = None
    role_b_traits: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "output_format": self.output_format,
            "min_turns": self.min_turns,
            "max_turns": self.max_turns,
            "num_conversations": self.num_conversations,
            "topic": self.topic,
            "system_prompt": self.system_prompt,
            "role_a": self.role_a,
            "role_b": self.role_b,
            "diversity_threshold": self.diversity_threshold,
            "max_retries": self.max_retries,
            "quality_filters": self.quality_filters,
            "role_a_traits": self.role_a_traits,
            "role_b_traits": self.role_b_traits,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataGenerationConfig":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            max_steps=data.get("max_steps", 100),
            seed=data.get("seed"),
            metadata=data.get("metadata", {}),
            output_format=data.get("output_format", "jsonl"),
            min_turns=data.get("min_turns", 5),
            max_turns=data.get("max_turns", 20),
            num_conversations=data.get("num_conversations", 10),
            topic=data.get("topic", ""),
            system_prompt=data.get("system_prompt", ""),
            role_a=data.get("role_a", "assistant"),
            role_b=data.get("role_b", "user"),
            diversity_threshold=data.get("diversity_threshold", 0.7),
            max_retries=data.get("max_retries", 3),
            quality_filters=data.get("quality_filters", ["length_check", "repetition_check"]),
            role_a_traits=data.get("role_a_traits"),
            role_b_traits=data.get("role_b_traits"),
        )


@dataclass
class ConversationTurn:
    """A single turn in a generated conversation."""

    role: str
    content: str
    turn_number: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "turn_number": self.turn_number,
        }


@dataclass
class GeneratedConversation:
    """A complete generated conversation."""

    conversation_id: str
    topic: str
    turns: list[ConversationTurn]
    quality_passed: bool = True
    quality_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "topic": self.topic,
            "turns": [t.to_dict() for t in self.turns],
            "quality_passed": self.quality_passed,
            "quality_scores": self.quality_scores,
        }


@dataclass
class DataGenerationResult:
    """Result of data generation scenario."""

    scenario_id: str
    topic: str
    conversations: list[GeneratedConversation]
    total_turns: int
    passed_quality: int
    failed_quality: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "topic": self.topic,
            "conversations": [c.to_dict() for c in self.conversations],
            "total_turns": self.total_turns,
            "passed_quality": self.passed_quality,
            "failed_quality": self.failed_quality,
        }


class DataGenerationScenario(Scenario):
    """CAMEL-style synthetic data generation scenario.

    Generates multi-turn conversations between two role-playing agents.
    Supports quality filtering and diversity checks.
    """

    def __init__(
        self,
        simulation: Simulation,
        config: DataGenerationConfig,
    ):
        """Initialize data generation scenario.

        Args:
            simulation: Simulation instance to use
            config: Data generation configuration
        """
        super().__init__(config)
        self.simulation = simulation
        self.data_config = config
        self.agent_a: Agent | None = None
        self.agent_b: Agent | None = None
        self.stimulus_injector = StimulusInjector()
        self._conversations: list[GeneratedConversation] = []

    async def setup(self) -> None:
        """Set up agents and topology for data generation."""
        self.status = ScenarioStatus.SETTING_UP

        # Create traits for agents
        traits_a = TraitVector(**(self.data_config.role_a_traits or {}))
        traits_b = TraitVector(**(self.data_config.role_b_traits or {}))

        # Create role A agent
        self.agent_a = Agent(
            name=f"Agent_{self.data_config.role_a}",
            traits=traits_a,
            simulation_id=self.simulation.id,
            system_prompt=self._build_role_prompt(self.data_config.role_a),
        )
        self.simulation.add_agent(self.agent_a)

        # Create role B agent
        self.agent_b = Agent(
            name=f"Agent_{self.data_config.role_b}",
            traits=traits_b,
            simulation_id=self.simulation.id,
            system_prompt=self._build_role_prompt(self.data_config.role_b),
        )
        self.simulation.add_agent(self.agent_b)

        # Create pair topology (each agent can communicate with the other)
        agent_ids = [self.agent_a.id, self.agent_b.id]
        self.simulation.topology = create_topology("mesh", agent_ids)

    def _build_role_prompt(self, role: str) -> str:
        """Build system prompt for a role.

        Args:
            role: Role name

        Returns:
            System prompt string
        """
        base = f"You are playing the role of '{role}' in a conversation."
        if self.data_config.system_prompt:
            base = f"{self.data_config.system_prompt}\n\n{base}"
        if self.data_config.topic:
            base = f"{base}\n\nThe topic of discussion is: {self.data_config.topic}"
        return base

    def _check_quality(self, content: str) -> tuple[bool, dict[str, float]]:
        """Check quality of generated content.

        Args:
            content: Generated content to check

        Returns:
            Tuple of (passed, scores dict)
        """
        scores = {}

        # Length check
        if "length_check" in self.data_config.quality_filters:
            length = len(content)
            # Score based on reasonable length (50-500 chars)
            if length < 20:
                scores["length_check"] = 0.0
            elif length < 50:
                scores["length_check"] = 0.5
            elif length > 1000:
                scores["length_check"] = 0.5
            else:
                scores["length_check"] = 1.0

        # Repetition check (simple heuristic)
        if "repetition_check" in self.data_config.quality_filters:
            words = content.lower().split()
            if len(words) > 5:
                unique_ratio = len(set(words)) / len(words)
                scores["repetition_check"] = unique_ratio
            else:
                scores["repetition_check"] = 1.0

        # Pass if all scores are above threshold
        passed = all(s >= 0.5 for s in scores.values()) if scores else True
        return passed, scores

    async def _generate_conversation(self, conv_id: str) -> GeneratedConversation:
        """Generate a single conversation.

        Args:
            conv_id: Unique conversation ID

        Returns:
            GeneratedConversation instance
        """
        turns: list[ConversationTurn] = []
        current_agent = self.agent_a
        other_agent = self.agent_b
        current_role = self.data_config.role_a

        # Initial prompt
        if self.data_config.topic:
            starter = f"Let's discuss: {self.data_config.topic}. Please start the conversation."
        else:
            starter = "Please start the conversation."

        # Generate turns
        for turn_num in range(self.data_config.max_turns):
            if turn_num == 0:
                prompt = starter
            else:
                # Use last turn as context
                prompt = f"Continue the conversation. Previous message: {turns[-1].content}"

            # Generate response
            message = await current_agent.generate_message(
                prompt=prompt,
                receiver_id=other_agent.id,
                step=turn_num,
            )

            # Check quality
            passed, scores = self._check_quality(message.content)
            if not passed and turn_num >= self.data_config.min_turns:
                # Stop if quality fails after min turns
                break

            # Record turn
            turns.append(ConversationTurn(
                role=current_role,
                content=message.content,
                turn_number=turn_num,
            ))

            # Log response
            self.log_response(AgentResponse(
                agent_id=current_agent.id,
                content=message.content,
                step=turn_num,
            ))

            # Swap agents
            current_agent, other_agent = other_agent, current_agent
            current_role = (
                self.data_config.role_b
                if current_role == self.data_config.role_a
                else self.data_config.role_a
            )

            # Check if min turns reached
            if turn_num >= self.data_config.min_turns - 1:
                # Random chance to end based on natural conversation flow
                import random
                if random.random() < 0.2:
                    break

        # Final quality check on conversation
        all_content = " ".join(t.content for t in turns)
        final_passed, final_scores = self._check_quality(all_content)

        return GeneratedConversation(
            conversation_id=conv_id,
            topic=self.data_config.topic,
            turns=turns,
            quality_passed=final_passed,
            quality_scores=final_scores,
        )

    async def run(self) -> ScenarioResult:
        """Execute the data generation scenario.

        Returns:
            ScenarioResult containing all generated conversations
        """
        try:
            await self.setup()
            self._mark_started()

            # Generate conversations
            for i in range(self.data_config.num_conversations):
                conv_id = f"{self.scenario_id}_conv_{i + 1}"
                conv = await self._generate_conversation(conv_id)
                self._conversations.append(conv)

                # Log event
                self.log_event(SystemEvent(
                    content=f"Generated conversation {i + 1}/{self.data_config.num_conversations}",
                    event_type="progress",
                ))

            self._mark_completed()

            # Build result
            passed = sum(1 for c in self._conversations if c.quality_passed)
            failed = len(self._conversations) - passed
            total_turns = sum(len(c.turns) for c in self._conversations)

            data_result = DataGenerationResult(
                scenario_id=self.scenario_id,
                topic=self.data_config.topic,
                conversations=self._conversations,
                total_turns=total_turns,
                passed_quality=passed,
                failed_quality=failed,
            )

            return self.build_result(extra_metadata={
                "data_generation_result": data_result.to_dict(),
            })

        except Exception as e:
            self._mark_failed(str(e))
            return self.build_result(extra_metadata={"error": str(e)})

    async def teardown(self) -> None:
        """Clean up after scenario execution."""
        pass

    @property
    def conversations(self) -> list[GeneratedConversation]:
        """Get generated conversations."""
        return self._conversations.copy()


@dataclass
class DataSafetyFilter:
    """Filter for ensuring data safety and quality.

    Applies content moderation and safety checks to generated data
    per ADR-009 requirements.
    """

    # Filter configuration
    check_pii: bool = True
    check_toxicity: bool = True
    check_bias: bool = False
    min_quality_score: float = 0.5
    blocked_patterns: list[str] = field(default_factory=list)

    def check_content(self, content: str) -> tuple[bool, dict[str, Any]]:
        """Check content for safety issues.

        Args:
            content: Content to check

        Returns:
            Tuple of (is_safe, details dict)
        """
        issues = []
        scores = {}

        # PII check (basic patterns)
        if self.check_pii:
            import re
            pii_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{16}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            ]
            pii_found = any(re.search(p, content) for p in pii_patterns)
            if pii_found:
                issues.append("potential_pii")
            scores["pii_check"] = 0.0 if pii_found else 1.0

        # Toxicity check (basic keyword heuristic)
        if self.check_toxicity:
            # In production, use a proper toxicity classifier
            toxic_keywords = ["hate", "kill", "attack", "destroy"]
            content_lower = content.lower()
            toxic_found = any(kw in content_lower for kw in toxic_keywords)
            scores["toxicity_check"] = 0.3 if toxic_found else 1.0
            if toxic_found:
                issues.append("potential_toxicity")

        # Blocked patterns check
        if self.blocked_patterns:
            import re
            for pattern in self.blocked_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"blocked_pattern:{pattern}")
                    scores["blocked_patterns"] = 0.0
                    break
            else:
                scores["blocked_patterns"] = 1.0

        # Calculate overall safety score
        avg_score = sum(scores.values()) / len(scores) if scores else 1.0
        is_safe = avg_score >= self.min_quality_score and not issues

        return is_safe, {
            "is_safe": is_safe,
            "score": avg_score,
            "scores": scores,
            "issues": issues,
        }

    def filter_conversations(
        self,
        conversations: list[GeneratedConversation],
    ) -> list[GeneratedConversation]:
        """Filter a list of conversations for safety.

        Args:
            conversations: List of conversations to filter

        Returns:
            Filtered list of safe conversations
        """
        safe_conversations = []
        for conv in conversations:
            # Check all turns
            all_safe = True
            for turn in conv.turns:
                is_safe, _ = self.check_content(turn.content)
                if not is_safe:
                    all_safe = False
                    break

            if all_safe:
                safe_conversations.append(conv)

        return safe_conversations


@dataclass
class DataExporter:
    """Export generated data to various formats.

    Supports JSONL, CSV, and HuggingFace dataset formats
    per ADR-009 requirements.
    """

    output_dir: str = "."
    include_metadata: bool = True
    anonymize: bool = False

    def export_jsonl(
        self,
        conversations: list[GeneratedConversation],
        filename: str = "data.jsonl",
    ) -> str:
        """Export conversations to JSONL format.

        Args:
            conversations: Conversations to export
            filename: Output filename

        Returns:
            Path to exported file
        """
        import json
        from pathlib import Path

        output_path = Path(self.output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            for conv in conversations:
                record = {
                    "conversation_id": conv.conversation_id,
                    "messages": [
                        {"role": t.role, "content": t.content}
                        for t in conv.turns
                    ],
                }
                if self.include_metadata:
                    record["topic"] = conv.topic
                    record["quality_passed"] = conv.quality_passed
                    record["quality_scores"] = conv.quality_scores
                f.write(json.dumps(record) + "\n")

        return str(output_path)

    def export_csv(
        self,
        conversations: list[GeneratedConversation],
        filename: str = "data.csv",
    ) -> str:
        """Export conversations to CSV format.

        Args:
            conversations: Conversations to export
            filename: Output filename

        Returns:
            Path to exported file
        """
        import csv
        from pathlib import Path

        output_path = Path(self.output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "conversation_id", "turn_number", "role", "content", "topic"
            ])
            for conv in conversations:
                for turn in conv.turns:
                    writer.writerow([
                        conv.conversation_id,
                        turn.turn_number,
                        turn.role,
                        turn.content,
                        conv.topic,
                    ])

        return str(output_path)

    def export_huggingface(
        self,
        conversations: list[GeneratedConversation],
        dataset_name: str = "dataset",
    ) -> str:
        """Export conversations to HuggingFace dataset format.

        Args:
            conversations: Conversations to export
            dataset_name: Name for the dataset directory

        Returns:
            Path to dataset directory
        """
        import json
        from pathlib import Path

        dataset_dir = Path(self.output_dir) / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)

        # Write data file
        data_file = dataset_dir / "data.jsonl"
        with open(data_file, "w") as f:
            for conv in conversations:
                record = {
                    "messages": [
                        {"role": t.role, "content": t.content}
                        for t in conv.turns
                    ],
                }
                f.write(json.dumps(record) + "\n")

        # Write dataset card
        readme = dataset_dir / "README.md"
        readme.write_text(f"""---
dataset_info:
  features:
  - name: messages
    sequence:
      struct:
      - name: role
        dtype: string
      - name: content
        dtype: string
  num_rows: {len(conversations)}
---

# Generated Dataset

This dataset was generated using AgentWorld's DataGenerationScenario.

## Statistics

- Total conversations: {len(conversations)}
- Total turns: {sum(len(c.turns) for c in conversations)}

## Usage

```python
from datasets import load_dataset
dataset = load_dataset('{dataset_dir}')
```
""")

        return str(dataset_dir)


def create_data_generation(
    name: str,
    topic: str,
    num_conversations: int = 10,
    min_turns: int = 5,
    max_turns: int = 20,
    role_a: str = "assistant",
    role_b: str = "user",
    system_prompt: str = "",
    output_format: str = "jsonl",
) -> DataGenerationScenario:
    """Create a data generation scenario.

    Convenience function for creating data generation scenarios
    without manually constructing configs.

    Args:
        name: Scenario name
        topic: Conversation topic
        num_conversations: Number of conversations to generate
        min_turns: Minimum turns per conversation
        max_turns: Maximum turns per conversation
        role_a: First agent's role
        role_b: Second agent's role
        system_prompt: Custom system prompt
        output_format: Output format (jsonl, csv, huggingface)

    Returns:
        DataGenerationScenario instance
    """
    config = DataGenerationConfig(
        name=name,
        description=f"Generate {num_conversations} conversations about {topic}",
        topic=topic,
        num_conversations=num_conversations,
        min_turns=min_turns,
        max_turns=max_turns,
        role_a=role_a,
        role_b=role_b,
        system_prompt=system_prompt,
        output_format=output_format,
    )

    simulation = Simulation(name=f"datagen_{name}")

    return DataGenerationScenario(simulation=simulation, config=config)


@dataclass
class QAPair:
    """A question-answer pair for training data."""

    question: str
    answer: str
    context: str | None = None
    difficulty: str = "medium"  # easy, medium, hard
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "answer": self.answer,
            "context": self.context,
            "difficulty": self.difficulty,
            "category": self.category,
        }


@dataclass
class DebateResult:
    """Result of a debate generation."""

    topic: str
    positions: list[str]
    arguments: list[dict[str, Any]]
    conclusion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "positions": self.positions,
            "arguments": self.arguments,
            "conclusion": self.conclusion,
        }


async def generate_qa_pairs(
    topic: str,
    num_pairs: int = 10,
    difficulty: str = "medium",
    include_context: bool = True,
    model: str | None = None,
) -> list[QAPair]:
    """Generate question-answer pairs for a topic.

    Creates synthetic QA data suitable for training
    question-answering models per ADR-009.

    Args:
        topic: Topic to generate QA pairs about
        num_pairs: Number of QA pairs to generate
        difficulty: Difficulty level (easy, medium, hard)
        include_context: Whether to include context with answers
        model: LLM model to use

    Returns:
        List of QAPair instances
    """
    from agentworld.llm.provider import get_provider

    provider = get_provider()
    qa_pairs: list[QAPair] = []

    # Generate questions first
    question_prompt = f"""Generate {num_pairs} diverse questions about: {topic}

Difficulty level: {difficulty}

Format each question on a new line, numbered 1-{num_pairs}.
Questions should be {difficulty} difficulty - {"simple factual questions" if difficulty == "easy" else "analytical questions requiring explanation" if difficulty == "medium" else "complex questions requiring deep understanding"}.
"""

    response = await provider.complete(
        prompt=question_prompt,
        model=model,
        system_prompt="You are an expert at creating educational questions.",
    )

    # Parse questions
    questions = []
    for line in response.content.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            # Remove numbering
            parts = line.split(".", 1)
            if len(parts) > 1:
                questions.append(parts[1].strip())
            else:
                questions.append(line)

    # Generate answers for each question
    for i, question in enumerate(questions[:num_pairs]):
        answer_prompt = f"""Topic: {topic}

Question: {question}

Provide a clear, accurate answer to this question.
{"Also provide relevant context that helps understand the answer." if include_context else ""}
"""

        answer_response = await provider.complete(
            prompt=answer_prompt,
            model=model,
            system_prompt="You are a knowledgeable expert providing accurate information.",
        )

        qa_pairs.append(QAPair(
            question=question,
            answer=answer_response.content,
            context=f"Topic: {topic}" if include_context else None,
            difficulty=difficulty,
            category=topic,
        ))

    return qa_pairs


async def generate_debate(
    topic: str,
    num_positions: int = 2,
    rounds: int = 3,
    model: str | None = None,
) -> DebateResult:
    """Generate a multi-perspective debate on a topic.

    Creates synthetic debate data with multiple viewpoints
    per ADR-009 requirements.

    Args:
        topic: Topic to debate
        num_positions: Number of different positions (2-4)
        rounds: Number of argument rounds per position
        model: LLM model to use

    Returns:
        DebateResult with arguments from all positions
    """
    from agentworld.llm.provider import get_provider

    provider = get_provider()
    num_positions = min(max(num_positions, 2), 4)  # Clamp to 2-4

    # Generate positions
    position_prompt = f"""Topic for debate: {topic}

Generate {num_positions} distinct, well-reasoned positions on this topic.
Each position should be a clear stance that can be argued.

Format:
Position 1: [stance]
Position 2: [stance]
{"Position 3: [stance]" if num_positions >= 3 else ""}
{"Position 4: [stance]" if num_positions >= 4 else ""}
"""

    response = await provider.complete(
        prompt=position_prompt,
        model=model,
        system_prompt="You are a debate moderator creating balanced discussion.",
    )

    # Parse positions
    positions = []
    for line in response.content.strip().split("\n"):
        if line.strip().startswith("Position"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                positions.append(parts[1].strip())

    positions = positions[:num_positions]
    if len(positions) < num_positions:
        # Fallback positions
        positions.extend([f"Position {i+1}" for i in range(len(positions), num_positions)])

    # Generate arguments for each position over multiple rounds
    arguments: list[dict[str, Any]] = []
    for round_num in range(rounds):
        for pos_idx, position in enumerate(positions):
            # Build context from previous arguments
            prev_args = [a for a in arguments if a["round"] == round_num - 1] if round_num > 0 else []
            context = ""
            if prev_args:
                context = "\nPrevious arguments:\n" + "\n".join(
                    f"- {a['position']}: {a['argument'][:200]}..."
                    for a in prev_args
                )

            arg_prompt = f"""Debate topic: {topic}

Your position: {position}

Round {round_num + 1} of {rounds}.
{context}

Make a compelling argument for your position. {"Address counter-arguments from previous round." if round_num > 0 else ""}
Keep your argument focused and persuasive.
"""

            arg_response = await provider.complete(
                prompt=arg_prompt,
                model=model,
                system_prompt=f"You are a skilled debater arguing for: {position}",
            )

            arguments.append({
                "round": round_num,
                "position_index": pos_idx,
                "position": position,
                "argument": arg_response.content,
            })

    # Generate conclusion
    conclusion_prompt = f"""Debate topic: {topic}

Positions debated:
{chr(10).join(f"- {p}" for p in positions)}

Summary of key arguments from the debate:
{chr(10).join(f"Round {a['round']+1}, {a['position']}: {a['argument'][:150]}..." for a in arguments[:6])}

Provide a balanced conclusion summarizing the debate and the strongest points from each side.
"""

    conclusion_response = await provider.complete(
        prompt=conclusion_prompt,
        model=model,
        system_prompt="You are a neutral debate moderator providing a fair summary.",
    )

    return DebateResult(
        topic=topic,
        positions=positions,
        arguments=arguments,
        conclusion=conclusion_response.content,
    )
