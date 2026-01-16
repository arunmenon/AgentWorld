"""Tests for cost estimation."""

import pytest
from agentworld.llm.cost import (
    estimate_cost,
    get_pricing,
    format_cost,
    MODEL_PRICING,
    ModelPricing,
)


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_basic_calculation(self):
        """Test basic cost calculation."""
        cost = estimate_cost(
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert cost >= 0

    def test_zero_tokens(self):
        """Test cost with zero tokens."""
        cost = estimate_cost(
            model="gpt-4o-mini",
            prompt_tokens=0,
            completion_tokens=0
        )
        assert cost == 0.0

    def test_large_token_count(self):
        """Test cost with large token counts."""
        cost = estimate_cost(
            model="gpt-4o",
            prompt_tokens=1_000_000,
            completion_tokens=500_000
        )
        assert cost > 0

    def test_unknown_model_uses_default(self):
        """Test that unknown model uses default pricing."""
        cost = estimate_cost(
            model="unknown/model",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert cost > 0  # Should use default pricing


class TestGetPricing:
    """Tests for get_pricing function."""

    def test_known_model(self):
        """Test getting pricing for known model."""
        pricing = get_pricing("gpt-4o-mini")
        assert isinstance(pricing, ModelPricing)
        assert pricing.input >= 0
        assert pricing.output >= 0

    def test_model_with_provider_prefix(self):
        """Test model name with provider prefix."""
        pricing = get_pricing("openai/gpt-4o-mini")
        assert pricing is not None

    def test_unknown_model_returns_default(self):
        """Test unknown model returns default pricing."""
        pricing = get_pricing("completely-unknown-model")
        assert pricing is not None
        assert pricing.input > 0  # Default pricing

    def test_local_model_free(self):
        """Test that local models are free."""
        pricing = get_pricing("ollama/llama2")
        assert pricing.input == 0
        assert pricing.output == 0


class TestModelPricing:
    """Tests for MODEL_PRICING configuration."""

    def test_pricing_exists(self):
        """Test that MODEL_PRICING is defined."""
        assert MODEL_PRICING is not None
        assert isinstance(MODEL_PRICING, dict)

    def test_common_models_have_pricing(self):
        """Test that common models have pricing entries."""
        common_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        for model in common_models:
            assert model in MODEL_PRICING

    def test_pricing_values_reasonable(self):
        """Test that pricing values are reasonable."""
        for model, pricing in MODEL_PRICING.items():
            assert pricing.input >= 0
            assert pricing.output >= 0
            # Output generally more expensive or equal
            # (not always true, so just check they're valid)


class TestFormatCost:
    """Tests for format_cost function."""

    def test_format_small_cost(self):
        """Test formatting small costs."""
        formatted = format_cost(0.0001)
        assert "$" in formatted
        assert "0.0001" in formatted

    def test_format_larger_cost(self):
        """Test formatting larger costs."""
        formatted = format_cost(1.23)
        assert formatted == "$1.23"

    def test_format_zero_cost(self):
        """Test formatting zero cost."""
        formatted = format_cost(0.0)
        assert "$" in formatted
