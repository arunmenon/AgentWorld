"""Tests for token counting."""

import pytest
from agentworld.llm.tokens import count_tokens, count_message_tokens


class TestCountTokens:
    """Tests for count_tokens function."""

    def test_empty_string(self):
        """Test counting tokens in empty string."""
        count = count_tokens("")
        assert count == 0

    def test_simple_text(self):
        """Test counting tokens in simple text."""
        count = count_tokens("Hello, world!")
        assert count > 0
        assert count < 10  # Should be just a few tokens

    def test_longer_text(self):
        """Test that longer text has more tokens."""
        short_count = count_tokens("Hi")
        long_count = count_tokens("This is a much longer piece of text that should have more tokens.")
        assert long_count > short_count

    def test_with_special_characters(self):
        """Test counting with special characters."""
        count = count_tokens("Hello! @#$%^&*()")
        assert count > 0

    def test_deterministic(self):
        """Test that counting is deterministic."""
        text = "The quick brown fox jumps over the lazy dog."
        count1 = count_tokens(text)
        count2 = count_tokens(text)
        assert count1 == count2

    def test_with_model_parameter(self):
        """Test counting with specific model."""
        count = count_tokens("Test text", model="gpt-4o-mini")
        assert count > 0


class TestCountMessageTokens:
    """Tests for count_message_tokens function."""

    def test_simple_messages(self):
        """Test counting tokens in message format."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ]
        count = count_message_tokens(messages)
        assert count > 0

    def test_empty_messages(self):
        """Test counting with empty message list."""
        count = count_message_tokens([])
        assert count >= 0  # Should have minimal overhead

    def test_multiple_messages(self):
        """Test counting multiple messages."""
        few_messages = [{"role": "user", "content": "Hi"}]
        many_messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks!"},
        ]

        few_count = count_message_tokens(few_messages)
        many_count = count_message_tokens(many_messages)
        assert many_count > few_count

    def test_includes_overhead(self):
        """Test that message counting includes overhead."""
        text = "Hello"
        raw_count = count_tokens(text)
        message_count = count_message_tokens([{"role": "user", "content": text}])

        # Message count should include overhead
        assert message_count > raw_count
