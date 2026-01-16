"""Event emitter for simulation updates.

This module provides a clean interface for emitting WebSocket events
from anywhere in the codebase.
"""

import asyncio
from typing import Any, Dict, Optional

from agentworld.api.websocket import emit_event, EventType


class SimulationEventEmitter:
    """Event emitter for simulation-related events."""

    def __init__(self, simulation_id: str):
        """Initialize emitter for a specific simulation.

        Args:
            simulation_id: The simulation to emit events for
        """
        self.simulation_id = simulation_id

    def _emit(self, event_type: str, data: dict = None):
        """Emit an event (handles async context)."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(emit_event(event_type, self.simulation_id, data))
        except RuntimeError:
            # No running loop - create one for sync context
            asyncio.run(emit_event(event_type, self.simulation_id, data))

    def simulation_started(self):
        """Emit simulation started event."""
        self._emit(EventType.SIMULATION_STARTED)

    def simulation_paused(self):
        """Emit simulation paused event."""
        self._emit(EventType.SIMULATION_PAUSED)

    def simulation_resumed(self):
        """Emit simulation resumed event."""
        self._emit(EventType.SIMULATION_RESUMED)

    def simulation_completed(self, stats: dict = None):
        """Emit simulation completed event."""
        self._emit(EventType.SIMULATION_COMPLETED, {"stats": stats or {}})

    def simulation_error(self, error: str):
        """Emit simulation error event."""
        self._emit(EventType.SIMULATION_ERROR, {"error": error})

    def step_started(self, step: int, total_steps: int):
        """Emit step started event."""
        self._emit(EventType.STEP_STARTED, {
            "step": step,
            "total_steps": total_steps,
        })

    def step_completed(self, step: int, total_steps: int, messages_generated: int = 0):
        """Emit step completed event."""
        self._emit(EventType.STEP_COMPLETED, {
            "step": step,
            "total_steps": total_steps,
            "messages_generated": messages_generated,
        })

    def agent_thinking(self, agent_id: str, agent_name: str):
        """Emit agent thinking event."""
        self._emit(EventType.AGENT_THINKING, {
            "agent_id": agent_id,
            "agent_name": agent_name,
        })

    def agent_responded(self, agent_id: str, agent_name: str, response_preview: str = None):
        """Emit agent responded event."""
        self._emit(EventType.AGENT_RESPONDED, {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "response_preview": response_preview[:100] if response_preview else None,
        })

    def message_created(
        self,
        message_id: str,
        sender_id: str,
        sender_name: str,
        receiver_id: str = None,
        receiver_name: str = None,
        content_preview: str = None,
        step: int = None,
    ):
        """Emit message created event."""
        self._emit(EventType.MESSAGE_CREATED, {
            "message_id": message_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "receiver_id": receiver_id,
            "receiver_name": receiver_name,
            "content_preview": content_preview[:100] if content_preview else None,
            "step": step,
        })

    def memory_created(
        self,
        memory_id: str,
        agent_id: str,
        agent_name: str,
        memory_type: str,
        content_preview: str = None,
    ):
        """Emit memory created event."""
        self._emit(EventType.MEMORY_CREATED, {
            "memory_id": memory_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "memory_type": memory_type,
            "content_preview": content_preview[:100] if content_preview else None,
        })


def get_emitter(simulation_id: str) -> SimulationEventEmitter:
    """Get an event emitter for a simulation.

    Args:
        simulation_id: The simulation ID

    Returns:
        SimulationEventEmitter instance
    """
    return SimulationEventEmitter(simulation_id)


async def emit_simulation_created(simulation_id: str, name: str, agent_count: int):
    """Emit simulation created event (global event)."""
    await emit_event(EventType.SIMULATION_CREATED, data={
        "simulation_id": simulation_id,
        "name": name,
        "agent_count": agent_count,
    })
