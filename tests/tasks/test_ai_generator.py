"""Tests for AI task generator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentworld.tasks.ai_generator import AITaskGenerator


class TestAITaskGenerator:
    """Tests for AITaskGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a generator with mocked provider."""
        mock_provider = MagicMock()
        return AITaskGenerator(llm_provider=mock_provider)

    def test_parse_response_valid_json(self, generator):
        """Test parsing valid JSON response."""
        content = '{"name": "Test Task", "domain": "paypal"}'
        result = generator._parse_response(content)
        assert result["name"] == "Test Task"
        assert result["domain"] == "paypal"

    def test_parse_response_with_markdown(self, generator):
        """Test parsing JSON wrapped in markdown code blocks."""
        content = '''```json
{"name": "Test Task", "domain": "paypal"}
```'''
        result = generator._parse_response(content)
        assert result["name"] == "Test Task"

    def test_parse_response_with_extra_text(self, generator):
        """Test parsing JSON with surrounding text."""
        content = 'Here is the task:\n{"name": "Test Task"}\nDone!'
        result = generator._parse_response(content)
        assert result["name"] == "Test Task"

    def test_parse_response_invalid_json(self, generator):
        """Test error handling for invalid JSON."""
        content = "This is not JSON at all"
        with pytest.raises(ValueError, match="Failed to parse"):
            generator._parse_response(content)

    def test_ensure_required_fields_adds_defaults(self, generator):
        """Test that missing fields get default values."""
        task_data = {"name": "My Task"}
        result = generator._ensure_required_fields(task_data, "Test description")

        assert result["name"] == "My Task"  # Preserved
        assert result["domain"] == "general"  # Default
        assert result["difficulty"] == "medium"  # Default
        assert result["max_turns"] == 10  # Default
        assert result["required_handoffs"] == []  # Default
        assert result["goal_conditions"] == []  # Default

    def test_ensure_required_fields_preserves_existing(self, generator):
        """Test that existing fields are not overwritten."""
        task_data = {
            "name": "My Task",
            "domain": "paypal",
            "difficulty": "hard",
            "max_turns": 20,
        }
        result = generator._ensure_required_fields(task_data, "Test")

        assert result["domain"] == "paypal"
        assert result["difficulty"] == "hard"
        assert result["max_turns"] == 20

    def test_ensure_required_fields_generates_handoff_ids(self, generator):
        """Test that handoff IDs are generated if missing."""
        task_data = {
            "required_handoffs": [
                {"from_role": "service_agent", "to_role": "customer"},
                {"from_role": "customer", "to_role": "service_agent"},
            ]
        }
        result = generator._ensure_required_fields(task_data, "Test")

        assert result["required_handoffs"][0]["handoff_id"] == "handoff_1"
        assert result["required_handoffs"][1]["handoff_id"] == "handoff_2"

    def test_build_prompt_basic(self, generator):
        """Test building prompt without domain hint."""
        prompt = generator._build_prompt("Customer wants to transfer money", None)
        assert "Customer wants to transfer money" in prompt
        assert "Domain hint" not in prompt

    def test_build_prompt_with_domain_hint(self, generator):
        """Test building prompt with domain hint."""
        prompt = generator._build_prompt("Customer wants to transfer money", "paypal")
        assert "Customer wants to transfer money" in prompt
        assert "Domain hint: paypal" in prompt

    @pytest.mark.asyncio
    async def test_generate_task_integration(self, generator):
        """Test full generation flow with mocked LLM."""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = '''{
            "name": "PayPal Dispute",
            "description": "Customer files a dispute",
            "domain": "paypal",
            "difficulty": "medium",
            "agent_role": "service_agent",
            "agent_instruction": "Help file dispute",
            "user_role": "customer",
            "user_instruction": "File a dispute for $50",
            "user_apps": ["paypal_test"],
            "initial_state": {},
            "goal_state": {},
            "required_handoffs": [
                {
                    "from_role": "service_agent",
                    "to_role": "customer",
                    "expected_action": "file_dispute"
                }
            ],
            "goal_conditions": [
                {
                    "goal_type": "action_executed",
                    "description": "Dispute filed",
                    "app_id": "paypal_test",
                    "expected_value": "file_dispute"
                }
            ],
            "scenario_prompt": "Customer wants to dispute a charge",
            "max_turns": 10,
            "tags": ["paypal", "dispute"]
        }'''

        generator.provider.complete = AsyncMock(return_value=mock_response)

        result = await generator.generate_task(
            description="Customer wants to dispute a $50 charge",
            domain_hint="paypal",
        )

        assert result["name"] == "PayPal Dispute"
        assert result["domain"] == "paypal"
        assert len(result["required_handoffs"]) == 1
        assert result["required_handoffs"][0]["handoff_id"] == "handoff_1"
        assert len(result["goal_conditions"]) == 1


class TestSimulationGenerator:
    """Tests for AISimulationGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a generator with mocked provider."""
        from agentworld.simulation.ai_generator import AISimulationGenerator
        mock_provider = MagicMock()
        return AISimulationGenerator(llm_provider=mock_provider)

    def test_parse_response_valid_json(self, generator):
        """Test parsing valid JSON response."""
        content = '{"name": "Panel Discussion", "steps": 15}'
        result = generator._parse_response(content)
        assert result["name"] == "Panel Discussion"
        assert result["steps"] == 15

    def test_ensure_required_fields_adds_defaults(self, generator):
        """Test that missing fields get default values."""
        config = {"name": "My Sim"}
        result = generator._ensure_required_fields(config, "Test description")

        assert result["name"] == "My Sim"
        assert result["steps"] == 10  # Default
        assert result["apps"] == []  # Default
        assert len(result["agents"]) == 2  # Default agents

    def test_ensure_required_fields_fills_agent_traits(self, generator):
        """Test that agent traits are filled with defaults."""
        config = {
            "agents": [
                {"name": "Alice"},  # No traits
                {"name": "Bob", "traits": {"openness": 0.8}},  # Partial traits
            ]
        }
        result = generator._ensure_required_fields(config, "Test")

        # Alice should have all default traits
        assert result["agents"][0]["traits"]["openness"] == 0.5
        assert result["agents"][0]["traits"]["conscientiousness"] == 0.5

        # Bob should have openness preserved, others filled
        assert result["agents"][1]["traits"]["openness"] == 0.8
        assert result["agents"][1]["traits"]["conscientiousness"] == 0.5

    def test_default_traits(self, generator):
        """Test default trait values."""
        traits = generator._default_traits()
        assert traits["openness"] == 0.5
        assert traits["conscientiousness"] == 0.5
        assert traits["extraversion"] == 0.5
        assert traits["agreeableness"] == 0.5
        assert traits["neuroticism"] == 0.3

    @pytest.mark.asyncio
    async def test_generate_simulation_integration(self, generator):
        """Test full generation flow with mocked LLM."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "name": "Expert Panel",
            "description": "Experts discuss AI",
            "initial_prompt": "Welcome to the panel on AI ethics",
            "steps": 20,
            "agents": [
                {
                    "name": "Dr. Smith",
                    "role": "peer",
                    "background": "AI researcher",
                    "traits": {
                        "openness": 0.9,
                        "conscientiousness": 0.7,
                        "extraversion": 0.6,
                        "agreeableness": 0.5,
                        "neuroticism": 0.2
                    }
                },
                {
                    "name": "Prof. Jones",
                    "role": "peer",
                    "background": "Ethics professor",
                    "traits": {
                        "openness": 0.8,
                        "conscientiousness": 0.8,
                        "extraversion": 0.4,
                        "agreeableness": 0.7,
                        "neuroticism": 0.3
                    }
                }
            ],
            "apps": []
        }'''

        generator.provider.complete = AsyncMock(return_value=mock_response)

        result = await generator.generate_simulation(
            description="Experts discussing AI ethics",
            num_agents_hint=2,
        )

        assert result["name"] == "Expert Panel"
        assert result["steps"] == 20
        assert len(result["agents"]) == 2
        assert result["agents"][0]["name"] == "Dr. Smith"
        assert result["agents"][0]["traits"]["openness"] == 0.9
