"""Focus group scenario implementation.

This module implements the TinyTroupe-style product feedback
simulation as specified in ADR-009.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agentworld.scenarios.base import (
    Scenario,
    ScenarioConfig,
    ScenarioResult,
    ScenarioStatus,
    AgentResponse,
    SystemEvent,
)
from agentworld.scenarios.moderator import (
    ModeratorConfig,
    create_moderator_for_focus_group,
)
from agentworld.scenarios.stimulus import (
    Stimulus,
    StimulusType,
    StimulusInjector,
    create_question,
)
from agentworld.simulation.runner import Simulation
from agentworld.agents.agent import Agent
from agentworld.topology.types import create_topology


@dataclass
class FocusGroupConfig(ScenarioConfig):
    """Configuration for focus group scenarios."""

    product_name: str = ""
    product_description: str = ""
    questions: list[str] = field(default_factory=list)
    discussion_rounds: int = 3
    moderator_config: ModeratorConfig | None = None
    allow_cross_talk: bool = True  # Allow participants to respond to each other

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "product_name": self.product_name,
            "product_description": self.product_description,
            "questions": self.questions,
            "discussion_rounds": self.discussion_rounds,
            "moderator_config": (
                self.moderator_config.to_dict() if self.moderator_config else None
            ),
            "allow_cross_talk": self.allow_cross_talk,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FocusGroupConfig":
        """Create from dictionary."""
        mod_config = data.get("moderator_config")
        if mod_config:
            mod_config = ModeratorConfig.from_dict(mod_config)

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            max_steps=data.get("max_steps", 100),
            seed=data.get("seed"),
            metadata=data.get("metadata", {}),
            product_name=data.get("product_name", ""),
            product_description=data.get("product_description", ""),
            questions=data.get("questions", []),
            discussion_rounds=data.get("discussion_rounds", 3),
            moderator_config=mod_config,
            allow_cross_talk=data.get("allow_cross_talk", True),
        )


@dataclass
class QuestionResult:
    """Result for a single question in a focus group."""

    question: str
    question_number: int
    responses: list[AgentResponse]
    discussion_rounds: int
    start_step: int
    end_step: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "question_number": self.question_number,
            "responses": [r.to_dict() for r in self.responses],
            "discussion_rounds": self.discussion_rounds,
            "start_step": self.start_step,
            "end_step": self.end_step,
        }


@dataclass
class FocusGroupResult:
    """Result container for focus group scenarios."""

    scenario_id: str
    product_name: str
    product_description: str
    questions: list[QuestionResult]
    agent_profiles: list[dict[str, Any]]
    moderator_id: str | None
    summary: str = ""
    themes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "product_name": self.product_name,
            "product_description": self.product_description,
            "questions": [q.to_dict() for q in self.questions],
            "agent_profiles": self.agent_profiles,
            "moderator_id": self.moderator_id,
            "summary": self.summary,
            "themes": self.themes,
        }


class FocusGroupScenario(Scenario):
    """TinyTroupe-style focus group scenario.

    This scenario simulates a moderated focus group discussion
    about a product or topic. It uses:
    - ADR-004: Diverse personas for varied feedback
    - ADR-005: Hub-spoke topology (moderator as hub)
    - ADR-006: Memory for consistent, context-aware responses
    """

    def __init__(
        self,
        simulation: Simulation,
        config: FocusGroupConfig,
    ):
        """Initialize focus group scenario.

        Args:
            simulation: Simulation instance with agents
            config: Focus group configuration
        """
        super().__init__(config)
        self.simulation = simulation
        self.focus_config = config
        self.moderator: Agent | None = None
        self.stimulus_injector = StimulusInjector()
        self._question_results: list[QuestionResult] = []

    @property
    def participants(self) -> list[Agent]:
        """Get non-moderator participants."""
        if self.moderator is None:
            return self.simulation.agents
        return [a for a in self.simulation.agents if a.id != self.moderator.id]

    async def setup(self) -> None:
        """Configure focus group with moderator as hub.

        Creates moderator agent and configures hub-spoke topology
        where moderator can communicate with all participants.
        """
        self.status = ScenarioStatus.SETTING_UP

        # Create moderator agent
        mod_config = self.focus_config.moderator_config or ModeratorConfig()
        self.moderator = create_moderator_for_focus_group(
            name=mod_config.name,
            style=mod_config.style,
            simulation_id=self.simulation.id,
        )
        self.simulation.add_agent(self.moderator)

        # Build hub-spoke topology with moderator as hub
        agent_ids = [a.id for a in self.simulation.agents]
        self.simulation.topology = create_topology(
            "hub_spoke",
            agent_ids,
            hub_id=self.moderator.id,
        )

        # Queue introduction stimulus
        intro_content = (
            f"Welcome everyone. Today we'll discuss: {self.focus_config.product_description}\n\n"
            f"I'm {self.moderator.name}, and I'll be facilitating our discussion. "
            f"Please feel free to share your honest thoughts and opinions."
        )
        self.stimulus_injector.queue_announcement(intro_content, source=self.moderator.name)

    async def run(self) -> ScenarioResult:
        """Execute the focus group scenario.

        Returns:
            ScenarioResult with all outputs
        """
        try:
            await self.setup()
            self._mark_started()

            current_step = 0

            # Inject introduction
            intro_stimulus = await self.stimulus_injector.inject_next(current_step)
            if intro_stimulus:
                self.log_event(SystemEvent(
                    content=intro_stimulus.content,
                    source=intro_stimulus.source,
                    event_type="introduction",
                ))

            # Run initial step for introduction
            messages = await self.simulation.step()
            for msg in messages:
                self.log_message(msg)
                self.log_response(AgentResponse(
                    agent_id=msg.sender_id,
                    content=msg.content,
                    step=msg.step,
                    message_type="speech",
                ))
            current_step += 1

            # Process each question
            for q_num, question in enumerate(self.focus_config.questions, start=1):
                question_result = await self._run_question(
                    question=question,
                    question_number=q_num,
                    start_step=current_step,
                )
                self._question_results.append(question_result)
                current_step = question_result.end_step + 1

            # Closing
            closing_content = (
                f"Thank you all for your valuable input today. "
                f"Your feedback about {self.focus_config.product_name} has been very helpful."
            )
            self.stimulus_injector.queue_announcement(closing_content, source=self.moderator.name)
            closing_stimulus = await self.stimulus_injector.inject_next(current_step)
            if closing_stimulus:
                self.log_event(SystemEvent(
                    content=closing_stimulus.content,
                    source=closing_stimulus.source,
                    event_type="closing",
                ))

            self._mark_completed()

            # Build focus group result
            focus_result = FocusGroupResult(
                scenario_id=self.scenario_id,
                product_name=self.focus_config.product_name,
                product_description=self.focus_config.product_description,
                questions=self._question_results,
                agent_profiles=[
                    p.to_dict() for p in self.participants
                ],
                moderator_id=self.moderator.id if self.moderator else None,
            )

            return self.build_result(extra_metadata={
                "focus_group_result": focus_result.to_dict(),
            })

        except Exception as e:
            self._mark_failed(str(e))
            return self.build_result(extra_metadata={"error": str(e)})

        finally:
            await self.teardown()

    async def _run_question(
        self,
        question: str,
        question_number: int,
        start_step: int,
    ) -> QuestionResult:
        """Run discussion for a single question.

        Args:
            question: Question text
            question_number: Question number
            start_step: Starting step number

        Returns:
            QuestionResult for this question
        """
        current_step = start_step
        responses: list[AgentResponse] = []

        # Moderator poses question
        question_stimulus = create_question(
            content=f"Question {question_number}: {question}",
            source=self.moderator.name if self.moderator else "Moderator",
        )
        await self.stimulus_injector.inject(question_stimulus, current_step)
        self.log_event(SystemEvent(
            content=question_stimulus.content,
            source=question_stimulus.source,
            event_type="question",
            metadata={"question_number": question_number},
        ))

        # Run discussion rounds
        for round_num in range(self.focus_config.discussion_rounds):
            messages = await self.simulation.step()

            for msg in messages:
                self.log_message(msg)

                # Only log participant responses (not moderator)
                if self.moderator is None or msg.sender_id != self.moderator.id:
                    response = AgentResponse(
                        agent_id=msg.sender_id,
                        content=msg.content,
                        step=msg.step,
                        message_type="speech",
                        metadata={"question_number": question_number, "round": round_num + 1},
                    )
                    responses.append(response)
                    self.log_response(response)

                # Track tokens/cost
                sender = self.simulation.get_agent(msg.sender_id)
                if sender:
                    self.add_tokens(sender.total_tokens)
                    self.add_cost(sender.total_cost)

            current_step += 1

        return QuestionResult(
            question=question,
            question_number=question_number,
            responses=responses,
            discussion_rounds=self.focus_config.discussion_rounds,
            start_step=start_step,
            end_step=current_step - 1,
        )

    async def inject_follow_up(
        self,
        question: str,
        target_agent_id: str | None = None,
    ) -> None:
        """Inject a follow-up question during the focus group.

        Args:
            question: Follow-up question text
            target_agent_id: Optional specific target agent
        """
        target_agents = [target_agent_id] if target_agent_id else None
        stimulus = create_question(
            content=question,
            target_agents=target_agents,
            source=self.moderator.name if self.moderator else "Moderator",
        )
        self.stimulus_injector.queue(stimulus)


def create_focus_group(
    name: str,
    product_name: str,
    product_description: str,
    questions: list[str],
    agents: list[Agent],
    discussion_rounds: int = 3,
    moderator_name: str = "Sarah",
    moderator_style: str = "friendly",
) -> FocusGroupScenario:
    """Convenience function to create a focus group scenario.

    Args:
        name: Scenario name
        product_name: Product being discussed
        product_description: Description of the product
        questions: List of discussion questions
        agents: List of participant agents
        discussion_rounds: Rounds per question
        moderator_name: Name for the moderator
        moderator_style: Moderation style

    Returns:
        Configured FocusGroupScenario
    """
    # Create simulation with agents
    simulation = Simulation(name=name)
    for agent in agents:
        simulation.add_agent(agent)

    # Create config
    config = FocusGroupConfig(
        name=name,
        product_name=product_name,
        product_description=product_description,
        questions=questions,
        discussion_rounds=discussion_rounds,
        moderator_config=ModeratorConfig(
            name=moderator_name,
            style=moderator_style,
        ),
    )

    return FocusGroupScenario(simulation=simulation, config=config)
