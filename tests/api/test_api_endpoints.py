"""Tests for REST API endpoints."""

import os
import pytest
from fastapi.testclient import TestClient

from agentworld.api.app import create_app
from agentworld.persistence.database import init_db, get_engine, reset_db
from agentworld.persistence.models import Base


@pytest.fixture(scope="module")
def client():
    """Create a test client."""
    # Use temp file for test database (to avoid readonly issues with in-memory across modules)
    test_db_path = "/tmp/claude/agentworld_test.db"

    # Set environment variable so Repository uses this DB
    os.environ["AGENTWORLD_DB_PATH"] = test_db_path

    # Initialize test database
    init_db(path=test_db_path)

    app = create_app()
    with TestClient(app) as c:
        yield c

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test the basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_api_health_check(self, client):
        """Test the API health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["api_version"] == "v1"


class TestSimulationEndpoints:
    """Tests for simulation API endpoints."""

    def test_list_simulations_empty(self, client):
        """Test listing simulations when none exist."""
        response = client.get("/api/v1/simulations")
        assert response.status_code == 200

        data = response.json()
        assert "simulations" in data
        assert "total" in data
        assert isinstance(data["simulations"], list)

    def test_create_simulation(self, client):
        """Test creating a new simulation."""
        payload = {
            "name": "Test Simulation",
            "steps": 5,
            "initial_prompt": "Hello world",
            "agents": [
                {
                    "name": "Alice",
                    "traits": {"openness": 0.8, "extraversion": 0.7},
                    "background": "A friendly AI assistant",
                },
                {
                    "name": "Bob",
                    "traits": {"openness": 0.6, "extraversion": 0.5},
                    "background": "A curious researcher",
                },
            ],
        }

        response = client.post("/api/v1/simulations", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Simulation"
        assert data["total_steps"] == 5
        assert data["agent_count"] == 2
        assert "id" in data

        # Store for subsequent tests
        TestSimulationEndpoints.simulation_id = data["id"]

    def test_get_simulation(self, client):
        """Test getting a simulation by ID."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.get(f"/api/v1/simulations/{sim_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sim_id
        assert data["name"] == "Test Simulation"

    def test_get_simulation_not_found(self, client):
        """Test getting a non-existent simulation."""
        response = client.get("/api/v1/simulations/nonexistent-id")
        assert response.status_code == 404

        data = response.json()
        assert data["detail"]["code"] == "SIMULATION_NOT_FOUND"

    def test_start_simulation(self, client):
        """Test starting a simulation."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.post(f"/api/v1/simulations/{sim_id}/start")
        assert response.status_code == 200

        data = response.json()
        assert data["simulation_id"] == sim_id
        assert data["status"] == "running"

    def test_pause_simulation(self, client):
        """Test pausing a simulation."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.post(f"/api/v1/simulations/{sim_id}/pause")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "paused"

    def test_resume_simulation(self, client):
        """Test resuming a simulation."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.post(f"/api/v1/simulations/{sim_id}/resume")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"

    def test_step_simulation(self, client):
        """Test executing a simulation step."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.post(f"/api/v1/simulations/{sim_id}/step", json={"count": 1})
        assert response.status_code == 200

        data = response.json()
        assert data["simulation_id"] == sim_id
        assert "steps_executed" in data
        assert "current_step" in data

    def test_inject_stimulus(self, client):
        """Test injecting a stimulus."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.post(
            f"/api/v1/simulations/{sim_id}/inject",
            json={"content": "A surprise event occurs!"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["injected"] is True
        assert data["content"] == "A surprise event occurs!"

    def test_list_agents(self, client):
        """Test listing agents in a simulation."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.get(f"/api/v1/simulations/{sim_id}/agents")
        assert response.status_code == 200

        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert len(data["agents"]) == 2

    def test_list_messages(self, client):
        """Test listing messages in a simulation."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.get(f"/api/v1/simulations/{sim_id}/messages")
        assert response.status_code == 200

        data = response.json()
        assert "messages" in data
        assert "total" in data

    def test_delete_simulation(self, client):
        """Test deleting a simulation."""
        sim_id = getattr(TestSimulationEndpoints, "simulation_id", None)
        if not sim_id:
            pytest.skip("No simulation created")

        response = client.delete(f"/api/v1/simulations/{sim_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify it's gone
        response = client.get(f"/api/v1/simulations/{sim_id}")
        assert response.status_code == 404


class TestPersonaEndpoints:
    """Tests for persona API endpoints."""

    def test_list_personas_empty(self, client):
        """Test listing personas when none exist."""
        response = client.get("/api/v1/personas")
        assert response.status_code == 200

        data = response.json()
        assert "personas" in data
        assert "total" in data

    def test_create_persona(self, client):
        """Test creating a new persona."""
        payload = {
            "name": "Test Persona",
            "description": "A test persona for API testing",
            "occupation": "Software Tester",
            "age": 30,
            "background": "Background story here",
            "traits": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.5,
                "neuroticism": 0.3,
            },
            "tags": ["test", "api"],
        }

        response = client.post("/api/v1/personas", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Persona"
        assert data["occupation"] == "Software Tester"
        assert "id" in data

        TestPersonaEndpoints.persona_id = data["id"]

    def test_create_duplicate_persona(self, client):
        """Test creating a persona with duplicate name."""
        payload = {
            "name": "Test Persona",
            "description": "Duplicate",
        }

        response = client.post("/api/v1/personas", json=payload)
        assert response.status_code == 409

        data = response.json()
        assert data["detail"]["code"] == "PERSONA_EXISTS"

    def test_get_persona(self, client):
        """Test getting a persona by ID."""
        persona_id = getattr(TestPersonaEndpoints, "persona_id", None)
        if not persona_id:
            pytest.skip("No persona created")

        response = client.get(f"/api/v1/personas/{persona_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == persona_id

    def test_get_persona_by_name(self, client):
        """Test getting a persona by name."""
        response = client.get("/api/v1/personas/Test Persona")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Test Persona"

    def test_search_personas(self, client):
        """Test searching personas."""
        response = client.get("/api/v1/personas/search?q=Test")
        assert response.status_code == 200

        data = response.json()
        assert "personas" in data
        assert len(data["personas"]) >= 1

    def test_update_persona(self, client):
        """Test updating a persona."""
        persona_id = getattr(TestPersonaEndpoints, "persona_id", None)
        if not persona_id:
            pytest.skip("No persona created")

        payload = {
            "description": "Updated description",
            "age": 35,
        }

        response = client.patch(f"/api/v1/personas/{persona_id}", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Updated description"
        assert data["age"] == 35

    def test_delete_persona(self, client):
        """Test deleting a persona."""
        persona_id = getattr(TestPersonaEndpoints, "persona_id", None)
        if not persona_id:
            pytest.skip("No persona created")

        response = client.delete(f"/api/v1/personas/{persona_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


class TestCollectionEndpoints:
    """Tests for collection API endpoints."""

    def test_list_collections_empty(self, client):
        """Test listing collections when none exist."""
        response = client.get("/api/v1/collections")
        assert response.status_code == 200

        data = response.json()
        assert "collections" in data
        assert "total" in data

    def test_create_collection(self, client):
        """Test creating a new collection."""
        payload = {
            "name": "Test Collection",
            "description": "A test collection",
            "tags": ["test"],
        }

        response = client.post("/api/v1/collections", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Collection"
        assert "id" in data

        TestCollectionEndpoints.collection_id = data["id"]

    def test_get_collection(self, client):
        """Test getting a collection by ID."""
        collection_id = getattr(TestCollectionEndpoints, "collection_id", None)
        if not collection_id:
            pytest.skip("No collection created")

        response = client.get(f"/api/v1/collections/{collection_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == collection_id

    def test_delete_collection(self, client):
        """Test deleting a collection."""
        collection_id = getattr(TestCollectionEndpoints, "collection_id", None)
        if not collection_id:
            pytest.skip("No collection created")

        response = client.delete(f"/api/v1/collections/{collection_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


class TestErrorHandling:
    """Tests for API error handling."""

    def test_invalid_pagination(self, client):
        """Test invalid pagination parameters."""
        response = client.get("/api/v1/simulations?page=0")
        assert response.status_code == 422  # Validation error

    def test_invalid_per_page(self, client):
        """Test invalid per_page parameter."""
        response = client.get("/api/v1/simulations?per_page=500")
        assert response.status_code == 422  # Validation error

    def test_missing_required_field(self, client):
        """Test missing required field in request."""
        response = client.post("/api/v1/simulations", json={})
        assert response.status_code == 422  # Validation error
