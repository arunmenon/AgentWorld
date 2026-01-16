"""AgentWorld exception hierarchy."""


class AgentWorldError(Exception):
    """Base exception for all AgentWorld errors."""

    pass


class ConfigurationError(AgentWorldError):
    """Raised when configuration is invalid or missing."""

    pass


class LLMError(AgentWorldError):
    """Raised when LLM operations fail."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    pass


class PersistenceError(AgentWorldError):
    """Raised when database operations fail."""

    pass


class SimulationError(AgentWorldError):
    """Raised when simulation operations fail."""

    pass


class AgentError(AgentWorldError):
    """Raised when agent operations fail."""

    pass


class ValidationError(AgentWorldError):
    """Raised when validation fails."""

    pass
