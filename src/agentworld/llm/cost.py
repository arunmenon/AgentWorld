"""Cost estimation for LLM calls."""

from typing import NamedTuple


class ModelPricing(NamedTuple):
    """Pricing per 1M tokens."""

    input: float  # $ per 1M input tokens
    output: float  # $ per 1M output tokens


# Pricing as of 2024 ($ per 1M tokens)
# Update these as pricing changes
MODEL_PRICING: dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4o": ModelPricing(2.50, 10.00),
    "gpt-4o-mini": ModelPricing(0.15, 0.60),
    "gpt-4-turbo": ModelPricing(10.00, 30.00),
    "gpt-4": ModelPricing(30.00, 60.00),
    "gpt-3.5-turbo": ModelPricing(0.50, 1.50),
    # Anthropic
    "claude-3-opus": ModelPricing(15.00, 75.00),
    "claude-3-sonnet": ModelPricing(3.00, 15.00),
    "claude-3-haiku": ModelPricing(0.25, 1.25),
    "claude-3-5-sonnet": ModelPricing(3.00, 15.00),
    # Google
    "gemini-pro": ModelPricing(0.50, 1.50),
    "gemini-1.5-pro": ModelPricing(3.50, 10.50),
    "gemini-1.5-flash": ModelPricing(0.075, 0.30),
    # Open source (free when self-hosted)
    "llama": ModelPricing(0.0, 0.0),
    "mistral": ModelPricing(0.0, 0.0),
    "ollama": ModelPricing(0.0, 0.0),
}

# Default pricing for unknown models
DEFAULT_PRICING = ModelPricing(1.00, 2.00)


def get_pricing(model: str) -> ModelPricing:
    """Get pricing for a model.

    Args:
        model: Model name (can include provider prefix)

    Returns:
        ModelPricing tuple with input/output costs per 1M tokens
    """
    # Strip provider prefix
    model_name = model.split("/")[-1] if "/" in model else model
    model_lower = model_name.lower()

    # Check exact match
    if model_lower in MODEL_PRICING:
        return MODEL_PRICING[model_lower]

    # Check prefix match
    for prefix, pricing in MODEL_PRICING.items():
        if model_lower.startswith(prefix):
            return pricing

    # Check if it's a local/free model
    if any(free in model_lower for free in ["ollama", "local", "llama", "mistral"]):
        return ModelPricing(0.0, 0.0)

    return DEFAULT_PRICING


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Estimate the cost of an LLM call.

    Args:
        model: Model name
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    pricing = get_pricing(model)
    input_cost = (prompt_tokens / 1_000_000) * pricing.input
    output_cost = (completion_tokens / 1_000_000) * pricing.output
    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string (e.g., "$0.0012" or "$1.23")
    """
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.2f}"
