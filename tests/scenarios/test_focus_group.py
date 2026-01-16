"""Tests for focus group scenario implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentworld.scenarios.focus_group import (
    FocusGroupConfig,
    FocusGroupScenario,
    FocusGroupResult,
    QuestionResult,
    create_focus_group,
)
from agentworld.scenarios.base import ScenarioStatus, AgentResponse
from agentworld.scenarios.moderator import ModeratorConfig, ModeratorRole
from agentworld.agents.agent import Agent
from agentworld.personas.traits import TraitVector


class TestFocusGroupConfig:
    """Tests for FocusGroupConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = FocusGroupConfig(name="Test")

        assert config.name == "Test"
        assert config.product_name == ""
        assert config.product_description == ""
        assert config.questions == []
        assert config.discussion_rounds == 3
        assert config.moderator_config is None
        assert config.allow_cross_talk is True

    def test_custom_values(self):
        """Test custom values."""
        mod_config = ModeratorConfig(name="Sarah", style="probing")
        config = FocusGroupConfig(
            name="Product Test",
            product_name="Widget Pro",
            product_description="A revolutionary widget",
            questions=["What do you think?", "Would you buy it?"],
            discussion_rounds=5,
            moderator_config=mod_config,
            allow_cross_talk=False,
        )

        assert config.product_name == "Widget Pro"
        assert config.product_description == "A revolutionary widget"
        assert len(config.questions) == 2
        assert config.discussion_rounds == 5
        assert config.moderator_config.name == "Sarah"
        assert config.allow_cross_talk is False

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = FocusGroupConfig(
            name="Test",
            product_name="Widget",
            questions=["Q1", "Q2"],
        )
        data = config.to_dict()

        assert data["name"] == "Test"
        assert data["product_name"] == "Widget"
        assert data["questions"] == ["Q1", "Q2"]
        assert data["discussion_rounds"] == 3
        assert data["moderator_config"] is None

    def test_to_dict_with_moderator(self):
        """Test conversion with moderator config."""
        config = FocusGroupConfig(
            name="Test",
            moderator_config=ModeratorConfig(name="Alex"),
        )
        data = config.to_dict()

        assert data["moderator_config"] is not None
        assert data["moderator_config"]["name"] == "Alex"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "From Dict",
            "product_name": "Test Product",
            "product_description": "A test product",
            "questions": ["Q1", "Q2", "Q3"],
            "discussion_rounds": 4,
            "allow_cross_talk": False,
        }
        config = FocusGroupConfig.from_dict(data)

        assert config.name == "From Dict"
        assert config.product_name == "Test Product"
        assert len(config.questions) == 3
        assert config.discussion_rounds == 4
        assert config.allow_cross_talk is False

    def test_from_dict_with_moderator(self):
        """Test creation from dict with moderator."""
        data = {
            "name": "Test",
            "moderator_config": {
                "name": "Maria",
                "style": "formal",
                "role": "interviewer",
            },
        }
        config = FocusGroupConfig.from_dict(data)

        assert config.moderator_config is not None
        assert config.moderator_config.name == "Maria"
        assert config.moderator_config.style == "formal"
        assert config.moderator_config.role == ModeratorRole.INTERVIEWER


class TestQuestionResult:
    """Tests for QuestionResult dataclass."""

    def test_creation(self):
        """Test creating question result."""
        responses = [
            AgentResponse(agent_id="a1", content="Response 1", step=1),
            AgentResponse(agent_id="a2", content="Response 2", step=2),
        ]
        result = QuestionResult(
            question="What do you think?",
            question_number=1,
            responses=responses,
            discussion_rounds=3,
            start_step=0,
            end_step=2,
        )

        assert result.question == "What do you think?"
        assert result.question_number == 1
        assert len(result.responses) == 2
        assert result.discussion_rounds == 3
        assert result.start_step == 0
        assert result.end_step == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = QuestionResult(
            question="Test Q",
            question_number=2,
            responses=[AgentResponse(agent_id="a1", content="Test", step=1)],
            discussion_rounds=2,
            start_step=5,
            end_step=6,
        )
        data = result.to_dict()

        assert data["question"] == "Test Q"
        assert data["question_number"] == 2
        assert len(data["responses"]) == 1
        assert data["start_step"] == 5
        assert data["end_step"] == 6


class TestFocusGroupResult:
    """Tests for FocusGroupResult dataclass."""

    def test_creation(self):
        """Test creating focus group result."""
        questions = [
            QuestionResult(
                question="Q1",
                question_number=1,
                responses=[],
                discussion_rounds=3,
                start_step=0,
                end_step=2,
            ),
        ]
        result = FocusGroupResult(
            scenario_id="fg123",
            product_name="Widget",
            product_description="A widget",
            questions=questions,
            agent_profiles=[{"id": "a1", "name": "Agent1"}],
            moderator_id="mod1",
            summary="Good feedback",
            themes=["usability", "pricing"],
        )

        assert result.scenario_id == "fg123"
        assert result.product_name == "Widget"
        assert len(result.questions) == 1
        assert len(result.agent_profiles) == 1
        assert result.moderator_id == "mod1"
        assert result.summary == "Good feedback"
        assert len(result.themes) == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = FocusGroupResult(
            scenario_id="fg123",
            product_name="Test",
            product_description="Desc",
            questions=[],
            agent_profiles=[],
            moderator_id="mod1",
        )
        data = result.to_dict()

        assert data["scenario_id"] == "fg123"
        assert data["product_name"] == "Test"
        assert data["questions"] == []
        assert data["moderator_id"] == "mod1"


class TestFocusGroupScenario:
    """Tests for FocusGroupScenario class."""

    @pytest.fixture
    def mock_simulation(self):
        """Create mock simulation."""
        sim = MagicMock()
        sim.id = "sim123"
        sim.agents = []
        sim.add_agent = MagicMock()
        sim.get_agent = MagicMock(return_value=None)
        sim.step = AsyncMock(return_value=[])
        return sim

    @pytest.fixture
    def config(self):
        """Create focus group config."""
        return FocusGroupConfig(
            name="Test Focus Group",
            product_name="Widget Pro",
            product_description="A revolutionary widget",
            questions=["What do you think?"],
            discussion_rounds=2,
        )

    @pytest.fixture
    def scenario(self, mock_simulation, config):
        """Create scenario instance."""
        return FocusGroupScenario(simulation=mock_simulation, config=config)

    def test_creation(self, scenario, config):
        """Test creating scenario."""
        assert scenario.config.name == "Test Focus Group"
        assert scenario.focus_config.product_name == "Widget Pro"
        assert scenario.moderator is None
        assert scenario.stimulus_injector is not None
        assert len(scenario._question_results) == 0

    def test_participants_no_moderator(self, scenario, mock_simulation):
        """Test participants property without moderator."""
        agent1 = MagicMock()
        agent1.id = "a1"
        agent2 = MagicMock()
        agent2.id = "a2"
        mock_simulation.agents = [agent1, agent2]

        participants = scenario.participants

        assert len(participants) == 2

    def test_participants_with_moderator(self, scenario, mock_simulation):
        """Test participants property with moderator."""
        agent1 = MagicMock()
        agent1.id = "a1"
        moderator = MagicMock()
        moderator.id = "mod1"
        mock_simulation.agents = [agent1, moderator]
        scenario.moderator = moderator

        participants = scenario.participants

        assert len(participants) == 1
        assert participants[0].id == "a1"

    @pytest.mark.asyncio
    async def test_setup(self, scenario, mock_simulation):
        """Test setup creates moderator and topology."""
        with patch("agentworld.scenarios.focus_group.create_moderator_for_focus_group") as mock_create:
            mock_mod = MagicMock()
            mock_mod.id = "mod1"
            mock_mod.name = "Moderator"
            mock_create.return_value = mock_mod

            with patch("agentworld.scenarios.focus_group.create_topology") as mock_topo:
                await scenario.setup()

                mock_create.assert_called_once()
                mock_simulation.add_agent.assert_called_once_with(mock_mod)
                mock_topo.assert_called_once()
                assert scenario.moderator is mock_mod
                assert scenario.status == ScenarioStatus.SETTING_UP

    @pytest.mark.asyncio
    async def test_run_completes(self, scenario, mock_simulation):
        """Test run completes successfully."""
        with patch("agentworld.scenarios.focus_group.create_moderator_for_focus_group") as mock_create:
            mock_mod = MagicMock()
            mock_mod.id = "mod1"
            mock_mod.name = "Moderator"
            mock_create.return_value = mock_mod

            with patch("agentworld.scenarios.focus_group.create_topology"):
                result = await scenario.run()

                assert result.status == ScenarioStatus.COMPLETED
                assert "focus_group_result" in result.metadata

    @pytest.mark.asyncio
    async def test_run_with_messages(self, scenario, mock_simulation):
        """Test run processes messages."""
        # Create mock message
        mock_msg = MagicMock()
        mock_msg.sender_id = "a1"
        mock_msg.content = "Test response"
        mock_msg.step = 1
        mock_simulation.step = AsyncMock(return_value=[mock_msg])

        with patch("agentworld.scenarios.focus_group.create_moderator_for_focus_group") as mock_create:
            mock_mod = MagicMock()
            mock_mod.id = "mod1"
            mock_mod.name = "Moderator"
            mock_create.return_value = mock_mod

            with patch("agentworld.scenarios.focus_group.create_topology"):
                result = await scenario.run()

                assert result.status == ScenarioStatus.COMPLETED
                # Should have logged responses
                assert len(scenario.responses) > 0

    @pytest.mark.asyncio
    async def test_run_handles_error(self, scenario, mock_simulation):
        """Test run handles errors gracefully."""
        mock_simulation.step = AsyncMock(side_effect=Exception("Test error"))

        with patch("agentworld.scenarios.focus_group.create_moderator_for_focus_group") as mock_create:
            mock_mod = MagicMock()
            mock_mod.id = "mod1"
            mock_mod.name = "Moderator"
            mock_create.return_value = mock_mod

            with patch("agentworld.scenarios.focus_group.create_topology"):
                result = await scenario.run()

                assert result.status == ScenarioStatus.FAILED
                assert "error" in result.metadata

    @pytest.mark.asyncio
    async def test_inject_follow_up(self, scenario):
        """Test injecting follow-up question."""
        scenario.moderator = MagicMock()
        scenario.moderator.name = "Moderator"

        await scenario.inject_follow_up("Can you elaborate?")

        assert len(scenario.stimulus_injector.pending) == 1
        stimulus = scenario.stimulus_injector.pending[0]
        assert "elaborate" in stimulus.content

    @pytest.mark.asyncio
    async def test_inject_follow_up_targeted(self, scenario):
        """Test injecting targeted follow-up."""
        scenario.moderator = MagicMock()
        scenario.moderator.name = "Moderator"

        await scenario.inject_follow_up(
            "What about you specifically?",
            target_agent_id="a1",
        )

        stimulus = scenario.stimulus_injector.pending[0]
        assert stimulus.target_agents == ["a1"]


class TestCreateFocusGroup:
    """Tests for create_focus_group convenience function."""

    def test_creates_scenario(self):
        """Test that function creates valid scenario."""
        agents = [
            Agent(name="Agent1", traits=TraitVector()),
            Agent(name="Agent2", traits=TraitVector()),
        ]

        scenario = create_focus_group(
            name="Test Group",
            product_name="Widget",
            product_description="A widget",
            questions=["Q1", "Q2"],
            agents=agents,
        )

        assert isinstance(scenario, FocusGroupScenario)
        assert scenario.config.name == "Test Group"
        assert scenario.focus_config.product_name == "Widget"
        assert len(scenario.focus_config.questions) == 2

    def test_custom_moderator(self):
        """Test custom moderator settings."""
        agents = [Agent(name="Agent1", traits=TraitVector())]

        scenario = create_focus_group(
            name="Test",
            product_name="Product",
            product_description="Desc",
            questions=["Q1"],
            agents=agents,
            moderator_name="Maria",
            moderator_style="probing",
        )

        assert scenario.focus_config.moderator_config.name == "Maria"
        assert scenario.focus_config.moderator_config.style == "probing"

    def test_custom_rounds(self):
        """Test custom discussion rounds."""
        agents = [Agent(name="Agent1", traits=TraitVector())]

        scenario = create_focus_group(
            name="Test",
            product_name="Product",
            product_description="Desc",
            questions=["Q1"],
            agents=agents,
            discussion_rounds=5,
        )

        assert scenario.focus_config.discussion_rounds == 5

    def test_agents_added_to_simulation(self):
        """Test agents are added to simulation."""
        agents = [
            Agent(name="Agent1", traits=TraitVector()),
            Agent(name="Agent2", traits=TraitVector()),
            Agent(name="Agent3", traits=TraitVector()),
        ]

        scenario = create_focus_group(
            name="Test",
            product_name="Product",
            product_description="Desc",
            questions=["Q1"],
            agents=agents,
        )

        # Agents should be in the simulation
        assert len(scenario.simulation.agents) == 3
