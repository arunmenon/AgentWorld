"""Tests for WebSocket functionality."""

import os
import pytest
import json
from fastapi.testclient import TestClient

from agentworld.api.app import create_app
from agentworld.persistence.database import init_db
from agentworld.persistence.models import Base


@pytest.fixture(scope="module")
def client():
    """Create a test client."""
    # Use temp file for test database
    test_db_path = "/tmp/claude/agentworld_ws_test.db"
    os.environ["AGENTWORLD_DB_PATH"] = test_db_path
    init_db(path=test_db_path)

    app = create_app()
    with TestClient(app) as c:
        yield c

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


class TestWebSocketConnection:
    """Tests for WebSocket connections."""

    def test_global_websocket_connection(self, client):
        """Test connecting to the global WebSocket endpoint."""
        with client.websocket_connect("/ws") as websocket:
            # Should receive a welcome message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "message" in data

    def test_simulation_websocket_connection(self, client):
        """Test connecting to a simulation-specific WebSocket."""
        with client.websocket_connect("/ws/simulations/test-sim-id") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["simulation_id"] == "test-sim-id"

    def test_websocket_ping_pong(self, client):
        """Test ping/pong mechanism."""
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_invalid_json(self, client):
        """Test handling of invalid JSON."""
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome
            websocket.receive_json()

            # Send invalid JSON
            websocket.send_text("not valid json")

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "Invalid JSON" in data["message"]

    def test_websocket_subscription(self, client):
        """Test subscribing to a simulation from global connection."""
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome
            websocket.receive_json()

            # Subscribe to a simulation
            websocket.send_json({
                "type": "subscribe",
                "simulation_id": "test-sim-123",
            })

            # Should receive subscription confirmation
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["simulation_id"] == "test-sim-123"


class TestConnectionManager:
    """Tests for the connection manager."""

    def test_manager_exists(self):
        """Test that the connection manager is importable."""
        from agentworld.api.websocket import manager, ConnectionManager
        assert isinstance(manager, ConnectionManager)

    def test_event_types_exist(self):
        """Test that event types are defined."""
        from agentworld.api.websocket import EventType

        assert EventType.CONNECTED == "connected"
        assert EventType.SIMULATION_CREATED == "simulation.created"
        assert EventType.STEP_COMPLETED == "step.completed"
        assert EventType.MESSAGE_CREATED == "message.created"


class TestEventEmitter:
    """Tests for the event emitter."""

    def test_emitter_creation(self):
        """Test creating an event emitter."""
        from agentworld.api.events import get_emitter, SimulationEventEmitter

        emitter = get_emitter("test-sim-id")
        assert isinstance(emitter, SimulationEventEmitter)
        assert emitter.simulation_id == "test-sim-id"

    def test_emitter_methods_exist(self):
        """Test that all emitter methods exist."""
        from agentworld.api.events import get_emitter

        emitter = get_emitter("test-sim-id")

        # All these methods should exist
        assert hasattr(emitter, "simulation_started")
        assert hasattr(emitter, "simulation_paused")
        assert hasattr(emitter, "simulation_resumed")
        assert hasattr(emitter, "simulation_completed")
        assert hasattr(emitter, "simulation_error")
        assert hasattr(emitter, "step_started")
        assert hasattr(emitter, "step_completed")
        assert hasattr(emitter, "agent_thinking")
        assert hasattr(emitter, "agent_responded")
        assert hasattr(emitter, "message_created")
        assert hasattr(emitter, "memory_created")
