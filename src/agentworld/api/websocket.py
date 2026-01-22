"""WebSocket handler for real-time simulation updates."""

import asyncio
import json
import logging
from typing import Dict, Set
from dataclasses import dataclass, field

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState


router = APIRouter()
logger = logging.getLogger(__name__)


@dataclass
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    # Connections per simulation
    simulation_connections: Dict[str, Set[WebSocket]] = field(default_factory=dict)

    # Global connections (receive all events)
    global_connections: Set[WebSocket] = field(default_factory=set)

    async def connect(self, websocket: WebSocket, simulation_id: str = None):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self._add_connection(websocket, simulation_id)

    def _add_connection(self, websocket: WebSocket, simulation_id: str = None):
        """Add a websocket to the appropriate connection pool (internal use)."""
        if simulation_id:
            if simulation_id not in self.simulation_connections:
                self.simulation_connections[simulation_id] = set()
            self.simulation_connections[simulation_id].add(websocket)
        else:
            self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, simulation_id: str = None):
        """Remove a WebSocket connection."""
        if simulation_id and simulation_id in self.simulation_connections:
            self.simulation_connections[simulation_id].discard(websocket)
            if not self.simulation_connections[simulation_id]:
                del self.simulation_connections[simulation_id]
        else:
            self.global_connections.discard(websocket)

    async def broadcast_to_simulation(self, simulation_id: str, event: dict):
        """Send event to all connections watching a simulation."""
        message = json.dumps(event)

        # Send to simulation-specific connections
        if simulation_id in self.simulation_connections:
            disconnected = set()
            for connection in self.simulation_connections[simulation_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.add(connection)

            # Clean up disconnected
            for conn in disconnected:
                self.simulation_connections[simulation_id].discard(conn)

        # Also send to global connections
        await self.broadcast_global(event)

    async def broadcast_global(self, event: dict):
        """Send event to all global connections."""
        message = json.dumps(event)
        disconnected = set()

        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.global_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, event: dict):
        """Send event to a specific connection."""
        try:
            await websocket.send_text(json.dumps(event))
        except Exception:
            pass


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Global WebSocket endpoint for all simulation events."""
    await manager.connect(websocket)
    logger.info("Global WebSocket connection established")

    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "connected",
            "message": "Connected to AgentWorld event stream",
        })

        while True:
            try:
                # Use timeout to allow periodic keepalive checks
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )

                try:
                    message = json.loads(data)

                    # Handle ping/pong
                    if message.get("type") == "ping":
                        await manager.send_personal(websocket, {"type": "pong"})

                    # Handle subscription requests
                    elif message.get("type") == "subscribe":
                        sim_id = message.get("simulation_id")
                        if sim_id:
                            # Move from global to simulation-specific
                            manager.global_connections.discard(websocket)
                            manager._add_connection(websocket, sim_id)
                            await manager.send_personal(websocket, {
                                "type": "subscribed",
                                "simulation_id": sim_id,
                            })

                except json.JSONDecodeError:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "Invalid JSON",
                    })

            except asyncio.TimeoutError:
                # Send keepalive ping on timeout
                if websocket.client_state == WebSocketState.CONNECTED:
                    await manager.send_personal(websocket, {"type": "ping"})
                else:
                    break

    except WebSocketDisconnect:
        logger.info("Global WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Global WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/simulations/{simulation_id}")
async def websocket_simulation(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for a specific simulation's events."""
    await manager.connect(websocket, simulation_id)
    logger.info(f"Simulation WebSocket connection established for {simulation_id}")

    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "connected",
            "simulation_id": simulation_id,
            "message": f"Connected to simulation {simulation_id} event stream",
        })

        while True:
            try:
                # Use timeout to allow periodic keepalive checks
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )

                try:
                    message = json.loads(data)

                    # Handle ping/pong
                    if message.get("type") == "ping":
                        await manager.send_personal(websocket, {"type": "pong"})

                except json.JSONDecodeError:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "Invalid JSON",
                    })

            except asyncio.TimeoutError:
                # Send keepalive ping on timeout
                if websocket.client_state == WebSocketState.CONNECTED:
                    await manager.send_personal(websocket, {"type": "ping"})
                else:
                    break

    except WebSocketDisconnect:
        logger.info(f"Simulation WebSocket client disconnected for {simulation_id}")
    except Exception as e:
        logger.error(f"Simulation WebSocket error for {simulation_id}: {e}")
    finally:
        manager.disconnect(websocket, simulation_id)


def register_websocket(app):
    """Register WebSocket routes with the FastAPI app."""
    app.include_router(router, tags=["websocket"])


# Event types for type hints
class EventType:
    """WebSocket event types."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SUBSCRIBED = "subscribed"

    # Simulation events
    SIMULATION_CREATED = "simulation.created"
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_PAUSED = "simulation.paused"
    SIMULATION_RESUMED = "simulation.resumed"
    SIMULATION_COMPLETED = "simulation.completed"
    SIMULATION_ERROR = "simulation.error"

    # Step events
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"

    # Agent events
    AGENT_THINKING = "agent.thinking"
    AGENT_RESPONDED = "agent.responded"

    # Message events
    MESSAGE_CREATED = "message.created"

    # Memory events
    MEMORY_CREATED = "memory.created"

    # App events (per ADR-017)
    APP_INITIALIZED = "app.initialized"
    APP_ACTION_REQUESTED = "app.action.requested"
    APP_ACTION_EXECUTED = "app.action.executed"
    APP_ACTION_FAILED = "app.action.failed"
    APP_OBSERVATION_SENT = "app.observation.sent"


async def emit_event(event_type: str, simulation_id: str = None, data: dict = None):
    """Emit an event to connected clients.

    Args:
        event_type: The type of event (use EventType constants)
        simulation_id: Optional simulation ID to target specific connections
        data: Optional additional data to include in the event
    """
    event = {
        "type": event_type,
        **(data or {}),
    }

    if simulation_id:
        event["simulation_id"] = simulation_id
        await manager.broadcast_to_simulation(simulation_id, event)
    else:
        await manager.broadcast_global(event)
