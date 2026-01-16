"""Plugin and extension model per ADR-014.

This module provides a plugin system for extending AgentWorld including:
- Protocol interfaces for different plugin types
- Plugin discovery via entry points
- Safe execution with sandboxing
- Lifecycle hooks for plugins
- CLI commands for plugin management
"""

from agentworld.plugins.hooks import HookablePlugin, PluginHooks
from agentworld.plugins.protocols import (
    AgentToolPlugin,
    ExtractorPlugin,
    LLMProviderPlugin,
    OutputFormatPlugin,
    ParameterSpec,
    ScenarioPlugin,
    TopologyPlugin,
    ValidationContext,
    ValidationResult,
    ValidatorPlugin,
)
from agentworld.plugins.registry import PluginRegistry, registry
from agentworld.plugins.sandbox import (
    PluginError,
    PluginExecutionError,
    PluginMemoryError,
    PluginSandbox,
    PluginTimeoutError,
    default_sandbox,
)

# Register built-in plugins
from agentworld.plugins.builtin import register_builtin_plugins

register_builtin_plugins()

__all__ = [
    # Protocols
    "TopologyPlugin",
    "ScenarioPlugin",
    "ValidatorPlugin",
    "ExtractorPlugin",
    "AgentToolPlugin",
    "LLMProviderPlugin",
    "OutputFormatPlugin",
    "ParameterSpec",
    "ValidationContext",
    "ValidationResult",
    # Registry
    "PluginRegistry",
    "registry",
    # Sandbox
    "PluginSandbox",
    "PluginError",
    "PluginTimeoutError",
    "PluginMemoryError",
    "PluginExecutionError",
    "default_sandbox",
    # Hooks
    "PluginHooks",
    "HookablePlugin",
]
