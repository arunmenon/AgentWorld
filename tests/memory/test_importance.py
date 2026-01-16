"""Tests for importance scoring."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agentworld.memory.importance import ImportanceRater
from agentworld.core.models import LLMResponse


class TestImportanceRaterHeuristic:
    """Tests for heuristic importance rating."""

    @pytest.fixture
    def rater(self):
        """Create rater without LLM (heuristic only)."""
        return ImportanceRater(llm_provider=None)

    def test_heuristic_baseline(self, rater):
        """Test baseline score for short neutral text."""
        score = rater._rate_heuristic("Hello.")
        assert 1.0 <= score <= 10.0
        assert score >= 3.0  # Baseline is 3.0

    def test_heuristic_long_text(self, rater):
        """Test that longer text gets higher score."""
        short = rater._rate_heuristic("Short text.")
        long_text = "This is a much longer piece of text that should receive a higher importance score because it contains more detail and substance that could be relevant to the conversation."
        long_score = rater._rate_heuristic(long_text)

        assert long_score >= short

    def test_heuristic_important_keywords(self, rater):
        """Test that important keywords increase score."""
        neutral = rater._rate_heuristic("The weather is nice today.")
        important = rater._rate_heuristic("I believe this is a critical decision we need to make.")

        assert important > neutral

    def test_heuristic_exclamation(self, rater):
        """Test that exclamation marks add emphasis."""
        calm = rater._rate_heuristic("That is interesting.")
        excited = rater._rate_heuristic("That is interesting!")

        assert excited >= calm

    def test_heuristic_question(self, rater):
        """Test that questions add slight importance."""
        statement = rater._rate_heuristic("The sky is blue.")
        question = rater._rate_heuristic("Why is the sky blue?")

        assert question >= statement

    def test_heuristic_first_person(self, rater):
        """Test that first-person statements increase importance."""
        objective = rater._rate_heuristic("The project is going well.")
        subjective = rater._rate_heuristic("I think the project needs more work.")

        assert subjective > objective

    def test_heuristic_score_capped(self, rater):
        """Test that heuristic score is capped at 10."""
        # Create text with many importance signals
        text = "I believe this is absolutely critical! I think we need to make an important decision about our urgent problem and find a solution now!"
        score = rater._rate_heuristic(text)

        assert score <= 10.0


class TestImportanceRaterLLM:
    """Tests for LLM-based importance rating."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        mock = MagicMock()
        mock.complete = AsyncMock()
        return mock

    @pytest.fixture
    def rater_with_llm(self, mock_llm):
        """Create rater with mock LLM."""
        return ImportanceRater(llm_provider=mock_llm)

    @pytest.mark.asyncio
    async def test_rate_uses_llm(self, rater_with_llm, mock_llm):
        """Test that rate uses LLM when available and use_llm=True."""
        mock_llm.complete.return_value = MagicMock(content="7")

        score = await rater_with_llm.rate("Test content", use_llm=True)

        assert score == 7.0
        mock_llm.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_llm_clamps_score(self, rater_with_llm, mock_llm):
        """Test that LLM score is clamped to valid range."""
        mock_llm.complete.return_value = MagicMock(content="15")

        score = await rater_with_llm.rate("Test content", use_llm=True)

        assert score <= 10.0

    @pytest.mark.asyncio
    async def test_rate_llm_fallback_on_error(self, rater_with_llm, mock_llm):
        """Test that LLM errors fall back to heuristic."""
        mock_llm.complete.return_value = MagicMock(content="not a number")

        score = await rater_with_llm.rate("Test content", use_llm=True)

        # Should get a valid heuristic score
        assert 1.0 <= score <= 10.0

    @pytest.mark.asyncio
    async def test_rate_uses_heuristic_when_disabled(self, rater_with_llm):
        """Test that use_llm=False uses heuristic."""
        score = await rater_with_llm.rate("Test content", use_llm=False)

        assert 1.0 <= score <= 10.0


class TestImportanceRaterBatch:
    """Tests for batch importance rating."""

    @pytest.fixture
    def rater(self):
        """Create rater without LLM."""
        return ImportanceRater(llm_provider=None)

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        mock = MagicMock()
        mock.complete = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_batch_empty_list(self, rater):
        """Test batch rating with empty list."""
        result = await rater.rate_batch([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_heuristic(self, rater):
        """Test batch rating with heuristics."""
        contents = ["Short text.", "Another short text.", "Third item."]
        scores = await rater.rate_batch(contents, use_llm=False)

        assert len(scores) == 3
        assert all(1.0 <= s <= 10.0 for s in scores)

    @pytest.mark.asyncio
    async def test_batch_llm(self, mock_llm):
        """Test batch rating with LLM."""
        mock_llm.complete.return_value = MagicMock(content="7\n5\n8")
        rater = ImportanceRater(llm_provider=mock_llm)

        contents = ["Content 1", "Content 2", "Content 3"]
        scores = await rater.rate_batch(contents, use_llm=True)

        assert len(scores) == 3
        assert scores == [7.0, 5.0, 8.0]

    @pytest.mark.asyncio
    async def test_batch_llm_handles_various_formats(self, mock_llm):
        """Test batch LLM handles various output formats."""
        # LLM might return "1. 7" format
        mock_llm.complete.return_value = MagicMock(content="1. 7\n2. 5\n3. 8")
        rater = ImportanceRater(llm_provider=mock_llm)

        contents = ["A", "B", "C"]
        scores = await rater.rate_batch(contents, use_llm=True)

        assert len(scores) == 3
        assert all(1.0 <= s <= 10.0 for s in scores)

    @pytest.mark.asyncio
    async def test_batch_llm_pads_missing(self, mock_llm):
        """Test batch LLM pads missing scores with heuristics."""
        # LLM returns fewer scores than inputs
        mock_llm.complete.return_value = MagicMock(content="7\n5")
        rater = ImportanceRater(llm_provider=mock_llm)

        contents = ["Content 1", "Content 2", "Content 3"]
        scores = await rater.rate_batch(contents, use_llm=True)

        assert len(scores) == 3
        assert all(1.0 <= s <= 10.0 for s in scores)


class TestImportanceKeywords:
    """Tests for importance keyword detection."""

    def test_keyword_list_exists(self):
        """Test that keyword list is defined."""
        assert len(ImportanceRater.IMPORTANT_KEYWORDS) > 0

    def test_keywords_are_lowercase(self):
        """Test that keywords are lowercase for matching."""
        for keyword in ImportanceRater.IMPORTANT_KEYWORDS:
            assert keyword == keyword.lower()
