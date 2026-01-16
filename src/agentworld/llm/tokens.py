"""Token counting utilities."""

from functools import lru_cache

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# Model to encoding mapping
MODEL_ENCODINGS = {
    "gpt-4": "cl100k_base",
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "claude": "cl100k_base",  # Approximate
    "claude-3": "cl100k_base",  # Approximate
}


@lru_cache(maxsize=10)
def get_encoding(model: str) -> "tiktoken.Encoding | None":
    """Get the tiktoken encoding for a model.

    Args:
        model: Model name (can include provider prefix)

    Returns:
        tiktoken Encoding or None if not available
    """
    if not TIKTOKEN_AVAILABLE:
        return None

    # Strip provider prefix
    model_name = model.split("/")[-1] if "/" in model else model

    # Find matching encoding
    encoding_name = "cl100k_base"  # Default
    for prefix, enc in MODEL_ENCODINGS.items():
        if model_name.startswith(prefix):
            encoding_name = enc
            break

    try:
        return tiktoken.get_encoding(encoding_name)
    except Exception:
        return None


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens in text for a given model.

    Args:
        text: Text to count tokens for
        model: Model name for encoding selection

    Returns:
        Approximate token count
    """
    encoding = get_encoding(model)
    if encoding:
        return len(encoding.encode(text))

    # Fallback: rough approximation (4 chars per token)
    return len(text) // 4


def count_message_tokens(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
) -> int:
    """Count tokens in a list of messages.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name for encoding selection

    Returns:
        Approximate token count including message overhead
    """
    total = 0
    for message in messages:
        # Add tokens for message structure (role, content keys, etc.)
        total += 4  # Approximate overhead per message
        total += count_tokens(message.get("role", ""), model)
        total += count_tokens(message.get("content", ""), model)

    # Add tokens for reply priming
    total += 2

    return total
