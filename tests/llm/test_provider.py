"""Tests for LLM provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentworld.llm.provider import LLMProvider, get_provider
from agentworld.core.models import LLMResponse


class TestLLMProvider:
    """Tests for LLMProvider class."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return LLMProvider()

    def test_creation(self, provider):
        """Test provider creation."""
        assert provider is not None
        assert provider.default_model == "openai/gpt-4o-mini"

    def test_creation_with_custom_model(self):
        """Test provider with custom default model."""
        provider = LLMProvider(default_model="anthropic/claude-3-haiku")
        assert provider.default_model == "anthropic/claude-3-haiku"

    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(self, provider):
        """Test that complete returns an LLMResponse."""
        with patch("agentworld.llm.provider.acompletion") as mock_acompletion:
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 5
            mock_usage.completion_tokens = 5
            mock_usage.total_tokens = 10

            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
            mock_response.usage = mock_usage
            mock_acompletion.return_value = mock_response

            response = await provider.complete("Test prompt", use_cache=False)

            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.tokens_used == 10

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self, provider):
        """Test complete with system prompt."""
        with patch("agentworld.llm.provider.acompletion") as mock_acompletion:
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 10
            mock_usage.completion_tokens = 5
            mock_usage.total_tokens = 15

            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = mock_usage
            mock_acompletion.return_value = mock_response

            response = await provider.complete(
                "User prompt",
                system_prompt="You are helpful",
                use_cache=False
            )

            # Verify system prompt was included in call
            call_args = mock_acompletion.call_args
            messages = call_args.kwargs.get("messages", [])
            assert any(m.get("role") == "system" for m in messages)

    @pytest.mark.asyncio
    async def test_complete_with_custom_model(self, provider):
        """Test complete with custom model override."""
        with patch("agentworld.llm.provider.acompletion") as mock_acompletion:
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 5
            mock_usage.completion_tokens = 5
            mock_usage.total_tokens = 10

            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = mock_usage
            mock_acompletion.return_value = mock_response

            await provider.complete("Prompt", model="anthropic/claude-3-opus", use_cache=False)

            call_args = mock_acompletion.call_args
            assert call_args.kwargs.get("model") == "anthropic/claude-3-opus"

    @pytest.mark.asyncio
    async def test_complete_tracks_tokens(self, provider):
        """Test that token usage is tracked."""
        with patch("agentworld.llm.provider.acompletion") as mock_acompletion:
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 30
            mock_usage.completion_tokens = 20
            mock_usage.total_tokens = 50

            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = mock_usage
            mock_acompletion.return_value = mock_response

            response = await provider.complete("Prompt", use_cache=False)

            assert response.tokens_used == 50


class TestGetProvider:
    """Tests for get_provider function."""

    def test_get_provider_returns_instance(self):
        """Test get_provider returns a provider."""
        provider = get_provider()
        assert isinstance(provider, LLMProvider)

    def test_get_provider_singleton_like(self):
        """Test get_provider returns same instance."""
        provider1 = get_provider()
        provider2 = get_provider()
        # They should be the same instance (singleton pattern)
        assert provider1 is provider2
