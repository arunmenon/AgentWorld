"""Plugin sandboxing and error handling per ADR-014."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PluginError(Exception):
    """Base exception for plugin errors."""

    def __init__(self, plugin_name: str, message: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Plugin '{plugin_name}': {message}")


class PluginTimeoutError(PluginError):
    """Raised when a plugin exceeds its execution timeout."""

    def __init__(self, plugin_name: str, timeout: float) -> None:
        self.timeout = timeout
        super().__init__(plugin_name, f"Timed out after {timeout}s")


class PluginMemoryError(PluginError):
    """Raised when a plugin exceeds memory limits."""

    def __init__(self, plugin_name: str, max_memory_mb: int) -> None:
        self.max_memory_mb = max_memory_mb
        super().__init__(plugin_name, f"Exceeded memory limit of {max_memory_mb}MB")


class PluginExecutionError(PluginError):
    """Raised when a plugin fails during execution."""

    def __init__(self, plugin_name: str, original_error: Exception) -> None:
        self.original_error = original_error
        super().__init__(plugin_name, f"Execution failed: {original_error}")


class PluginSandbox:
    """Execute plugin code with isolation and error handling."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_memory_mb: int = 512,
    ) -> None:
        """
        Initialize plugin sandbox.

        Args:
            timeout: Maximum execution time in seconds
            max_memory_mb: Maximum memory usage in MB (advisory)
        """
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    @asynccontextmanager
    async def execute(
        self, plugin_name: str
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for sandboxed plugin execution.

        Args:
            plugin_name: Name of the plugin being executed

        Yields:
            None

        Raises:
            PluginTimeoutError: If execution times out
            PluginMemoryError: If memory limit exceeded
            PluginExecutionError: If plugin raises an exception
        """
        try:
            yield
        except asyncio.TimeoutError:
            logger.error(f"Plugin {plugin_name} timed out after {self.timeout}s")
            raise PluginTimeoutError(plugin_name, self.timeout)
        except MemoryError:
            logger.error(f"Plugin {plugin_name} exceeded memory limit")
            raise PluginMemoryError(plugin_name, self.max_memory_mb)
        except PluginError:
            # Re-raise plugin errors as-is
            raise
        except Exception as e:
            logger.error(f"Plugin {plugin_name} failed: {e}")
            raise PluginExecutionError(plugin_name, e)

    async def run_with_timeout(
        self,
        coro: Awaitable[T],
        plugin_name: str,
        timeout: float | None = None,
    ) -> T:
        """
        Run coroutine with timeout.

        Args:
            coro: Coroutine to run
            plugin_name: Name of the plugin
            timeout: Optional custom timeout (uses default if None)

        Returns:
            Result of the coroutine

        Raises:
            PluginTimeoutError: If execution times out
            PluginExecutionError: If plugin raises an exception
        """
        effective_timeout = timeout or self.timeout

        async with self.execute(plugin_name):
            return await asyncio.wait_for(coro, timeout=effective_timeout)

    def run_sync_with_timeout(
        self,
        func: Callable[..., T],
        plugin_name: str,
        *args: Any,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Run synchronous function with timeout protection.

        Args:
            func: Function to run
            plugin_name: Name of the plugin
            *args: Positional arguments
            timeout: Optional custom timeout
            **kwargs: Keyword arguments

        Returns:
            Result of the function

        Raises:
            PluginTimeoutError: If execution times out
            PluginExecutionError: If plugin raises an exception
        """
        import concurrent.futures

        effective_timeout = timeout or self.timeout

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=effective_timeout)
            except concurrent.futures.TimeoutError:
                logger.error(f"Plugin {plugin_name} timed out after {effective_timeout}s")
                raise PluginTimeoutError(plugin_name, effective_timeout)
            except Exception as e:
                logger.error(f"Plugin {plugin_name} failed: {e}")
                raise PluginExecutionError(plugin_name, e)

    async def run_validator(
        self,
        validator: Any,
        agent: Any,
        response: str,
        context: Any,
    ) -> Any:
        """
        Run a validator plugin safely.

        Args:
            validator: Validator plugin instance
            agent: Agent being validated
            response: Response to validate
            context: Validation context

        Returns:
            Validation result
        """
        return await self.run_with_timeout(
            validator.validate(agent, response, context),
            plugin_name=validator.name,
        )

    async def run_extractor(
        self,
        extractor: Any,
        messages: list[Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run an extractor plugin safely.

        Args:
            extractor: Extractor plugin instance
            messages: Messages to extract from
            config: Extraction configuration

        Returns:
            Extracted data
        """
        return await self.run_with_timeout(
            extractor.extract(messages, config),
            plugin_name=extractor.name,
        )

    async def run_tool(
        self,
        tool: Any,
        **params: Any,
    ) -> str:
        """
        Run an agent tool plugin safely.

        Args:
            tool: Tool plugin instance
            **params: Tool parameters

        Returns:
            Tool execution result
        """
        return await self.run_with_timeout(
            tool.execute(**params),
            plugin_name=tool.name,
        )

    def build_topology(
        self,
        topology: Any,
        agent_ids: list[str],
        **kwargs: Any,
    ) -> Any:
        """
        Build a topology using a topology plugin safely.

        Args:
            topology: Topology plugin instance
            agent_ids: List of agent IDs
            **kwargs: Topology parameters

        Returns:
            NetworkX graph
        """
        return self.run_sync_with_timeout(
            topology.build,
            topology.name,
            agent_ids,
            **kwargs,
        )


# Default sandbox instance
default_sandbox = PluginSandbox()
