"""Plugin lifecycle hooks per ADR-014."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agentworld.plugins.registry import registry

if TYPE_CHECKING:
    from agentworld.simulation.runner import Simulation

logger = logging.getLogger(__name__)


class PluginHooks:
    """Lifecycle hooks for plugins."""

    @staticmethod
    def on_simulation_start(simulation: "Simulation") -> None:
        """
        Called when simulation starts.

        Notifies all plugins that support the on_simulation_start hook.

        Args:
            simulation: The simulation that is starting
        """
        for group in ["tools", "validators", "extractors"]:
            for plugin in registry.get_all(group).values():
                if hasattr(plugin, "on_simulation_start"):
                    try:
                        plugin.on_simulation_start(simulation)
                    except Exception as e:
                        logger.warning(
                            f"Plugin {plugin.name} hook on_simulation_start failed: {e}"
                        )

    @staticmethod
    def on_step_start(step: int, world: Any) -> None:
        """
        Called before each simulation step.

        Args:
            step: Current step number
            world: The simulation world
        """
        for group in ["tools", "validators"]:
            for plugin in registry.get_all(group).values():
                if hasattr(plugin, "on_step_start"):
                    try:
                        plugin.on_step_start(step, world)
                    except Exception as e:
                        logger.warning(
                            f"Plugin {plugin.name} hook on_step_start failed: {e}"
                        )

    @staticmethod
    def on_step_complete(step: int, world: Any) -> None:
        """
        Called after each step completes.

        Args:
            step: Completed step number
            world: The simulation world
        """
        for group in ["validators", "extractors"]:
            for plugin in registry.get_all(group).values():
                if hasattr(plugin, "on_step_complete"):
                    try:
                        plugin.on_step_complete(step, world)
                    except Exception as e:
                        logger.warning(
                            f"Plugin {plugin.name} hook on_step_complete failed: {e}"
                        )

    @staticmethod
    def on_agent_action(agent_id: str, action: Any, world: Any) -> None:
        """
        Called after an agent takes an action.

        Args:
            agent_id: ID of the agent
            action: The action taken
            world: The simulation world
        """
        for plugin in registry.get_all("validators").values():
            if hasattr(plugin, "on_agent_action"):
                try:
                    plugin.on_agent_action(agent_id, action, world)
                except Exception as e:
                    logger.warning(
                        f"Plugin {plugin.name} hook on_agent_action failed: {e}"
                    )

    @staticmethod
    def on_message_sent(message: Any, world: Any) -> None:
        """
        Called when a message is sent between agents.

        Args:
            message: The message that was sent
            world: The simulation world
        """
        for plugin in registry.get_all("extractors").values():
            if hasattr(plugin, "on_message_sent"):
                try:
                    plugin.on_message_sent(message, world)
                except Exception as e:
                    logger.warning(
                        f"Plugin {plugin.name} hook on_message_sent failed: {e}"
                    )

    @staticmethod
    def on_simulation_end(simulation: "Simulation", result: Any) -> None:
        """
        Called when simulation ends.

        Args:
            simulation: The simulation that ended
            result: The simulation result
        """
        for group in ["tools", "validators", "extractors"]:
            for plugin in registry.get_all(group).values():
                if hasattr(plugin, "on_simulation_end"):
                    try:
                        plugin.on_simulation_end(simulation, result)
                    except Exception as e:
                        logger.warning(
                            f"Plugin {plugin.name} hook on_simulation_end failed: {e}"
                        )

    @staticmethod
    async def on_simulation_start_async(simulation: "Simulation") -> None:
        """Async version of on_simulation_start."""
        for group in ["tools", "validators", "extractors"]:
            for plugin in registry.get_all(group).values():
                if hasattr(plugin, "on_simulation_start_async"):
                    try:
                        await plugin.on_simulation_start_async(simulation)
                    except Exception as e:
                        logger.warning(
                            f"Plugin {plugin.name} async hook failed: {e}"
                        )

    @staticmethod
    async def on_simulation_end_async(simulation: "Simulation", result: Any) -> None:
        """Async version of on_simulation_end."""
        for group in ["tools", "validators", "extractors"]:
            for plugin in registry.get_all(group).values():
                if hasattr(plugin, "on_simulation_end_async"):
                    try:
                        await plugin.on_simulation_end_async(simulation, result)
                    except Exception as e:
                        logger.warning(
                            f"Plugin {plugin.name} async hook failed: {e}"
                        )


class HookablePlugin:
    """Base class for plugins that want to receive hooks."""

    def on_simulation_start(self, simulation: "Simulation") -> None:
        """Called when simulation starts."""
        pass

    def on_step_start(self, step: int, world: Any) -> None:
        """Called before each step."""
        pass

    def on_step_complete(self, step: int, world: Any) -> None:
        """Called after each step."""
        pass

    def on_agent_action(self, agent_id: str, action: Any, world: Any) -> None:
        """Called after an agent action."""
        pass

    def on_message_sent(self, message: Any, world: Any) -> None:
        """Called when a message is sent."""
        pass

    def on_simulation_end(self, simulation: "Simulation", result: Any) -> None:
        """Called when simulation ends."""
        pass
