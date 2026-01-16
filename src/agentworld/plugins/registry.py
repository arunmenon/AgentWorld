"""Plugin discovery and registry per ADR-014."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import Any

from agentworld.plugins.protocols import (
    AgentToolPlugin,
    ExtractorPlugin,
    LLMProviderPlugin,
    OutputFormatPlugin,
    ScenarioPlugin,
    TopologyPlugin,
    ValidatorPlugin,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for all plugins."""

    ENTRY_POINT_GROUPS = {
        "topologies": "agentworld.topologies",
        "scenarios": "agentworld.scenarios",
        "validators": "agentworld.validators",
        "extractors": "agentworld.extractors",
        "tools": "agentworld.tools",
        "llm_providers": "agentworld.llm_providers",
        "output_formats": "agentworld.output_formats",
    }

    # Protocol mapping for validation
    PROTOCOLS = {
        "topologies": TopologyPlugin,
        "scenarios": ScenarioPlugin,
        "validators": ValidatorPlugin,
        "extractors": ExtractorPlugin,
        "tools": AgentToolPlugin,
        "llm_providers": LLMProviderPlugin,
        "output_formats": OutputFormatPlugin,
    }

    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, Any]] = {
            group: {} for group in self.ENTRY_POINT_GROUPS
        }
        self._loaded = False
        self._load_errors: list[tuple[str, str, Exception]] = []

    def discover(self) -> None:
        """Discover all installed plugins via entry points."""
        if self._loaded:
            return

        for group_name, entry_point_name in self.ENTRY_POINT_GROUPS.items():
            try:
                eps = entry_points(group=entry_point_name)
            except TypeError:
                # Python < 3.10 compatibility
                all_eps = entry_points()
                eps = all_eps.get(entry_point_name, [])

            for ep in eps:
                try:
                    plugin_class = ep.load()
                    plugin = plugin_class()

                    # Validate plugin implements protocol
                    if self._validate_plugin(group_name, plugin):
                        plugin_name = getattr(plugin, "name", ep.name)
                        self._plugins[group_name][plugin_name] = plugin
                        logger.info(f"Loaded plugin: {group_name}/{plugin_name}")
                    else:
                        logger.warning(
                            f"Plugin {ep.name} does not implement required protocol"
                        )
                        self._load_errors.append(
                            (group_name, ep.name, ValueError("Protocol not implemented"))
                        )

                except Exception as e:
                    logger.error(f"Failed to load plugin {ep.name}: {e}")
                    self._load_errors.append((group_name, ep.name, e))

        self._loaded = True

    def _validate_plugin(self, group: str, plugin: Any) -> bool:
        """Validate plugin implements correct protocol."""
        protocol = self.PROTOCOLS.get(group)
        if protocol is None:
            return True  # No protocol to validate

        # Check if plugin implements the protocol
        return isinstance(plugin, protocol)

    def register(self, group: str, plugin: Any) -> bool:
        """
        Manually register a plugin.

        Args:
            group: Plugin group (e.g., "topologies", "validators")
            plugin: Plugin instance

        Returns:
            True if registered successfully
        """
        if group not in self.ENTRY_POINT_GROUPS:
            logger.error(f"Unknown plugin group: {group}")
            return False

        if not self._validate_plugin(group, plugin):
            logger.error(f"Plugin does not implement {group} protocol")
            return False

        plugin_name = getattr(plugin, "name", str(id(plugin)))
        self._plugins[group][plugin_name] = plugin
        logger.info(f"Registered plugin: {group}/{plugin_name}")
        return True

    def unregister(self, group: str, name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            group: Plugin group
            name: Plugin name

        Returns:
            True if unregistered successfully
        """
        if group not in self._plugins:
            return False

        if name in self._plugins[group]:
            del self._plugins[group][name]
            logger.info(f"Unregistered plugin: {group}/{name}")
            return True

        return False

    def get(self, group: str, name: str) -> Any | None:
        """
        Get a specific plugin by group and name.

        Args:
            group: Plugin group
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        self.discover()
        return self._plugins.get(group, {}).get(name)

    def list(self, group: str) -> list[str]:
        """
        List all plugin names in a group.

        Args:
            group: Plugin group

        Returns:
            List of plugin names
        """
        self.discover()
        return list(self._plugins.get(group, {}).keys())

    def get_all(self, group: str) -> dict[str, Any]:
        """
        Get all plugins in a group.

        Args:
            group: Plugin group

        Returns:
            Dictionary of plugin name -> instance
        """
        self.discover()
        return self._plugins.get(group, {}).copy()

    def get_plugin_info(self, group: str, name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a plugin.

        Args:
            group: Plugin group
            name: Plugin name

        Returns:
            Plugin info dictionary or None
        """
        plugin = self.get(group, name)
        if plugin is None:
            return None

        info = {
            "name": getattr(plugin, "name", name),
            "group": group,
            "description": getattr(plugin, "description", "No description"),
        }

        # Add parameters if available
        if hasattr(plugin, "get_parameters"):
            params = plugin.get_parameters()
            info["parameters"] = [p.to_dict() for p in params]

        # Add schema if available
        if hasattr(plugin, "get_schema"):
            info["schema"] = plugin.get_schema()

        if hasattr(plugin, "get_config_schema"):
            info["config_schema"] = plugin.get_config_schema()

        return info

    def get_all_info(self) -> dict[str, list[dict[str, Any]]]:
        """
        Get information about all plugins.

        Returns:
            Dictionary of group -> list of plugin info
        """
        self.discover()
        result = {}

        for group in self.ENTRY_POINT_GROUPS:
            plugins_info = []
            for name in self.list(group):
                info = self.get_plugin_info(group, name)
                if info:
                    plugins_info.append(info)
            result[group] = plugins_info

        return result

    def get_load_errors(self) -> list[tuple[str, str, Exception]]:
        """
        Get list of plugin load errors.

        Returns:
            List of (group, name, exception) tuples
        """
        return self._load_errors.copy()

    def reload(self) -> None:
        """Force reload of all plugins."""
        self._plugins = {group: {} for group in self.ENTRY_POINT_GROUPS}
        self._loaded = False
        self._load_errors.clear()
        self.discover()


# Global registry instance
registry = PluginRegistry()
