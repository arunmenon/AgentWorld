"""Tests for App Definitions API endpoints per ADR-018."""

import os
import pytest
from fastapi.testclient import TestClient

from agentworld.api.app import create_app
from agentworld.persistence.database import init_db


@pytest.fixture(scope="module")
def client():
    """Create a test client with fresh database."""
    test_db_path = "/tmp/claude/agentworld_app_def_test.db"

    # Remove existing test DB if present
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    os.environ["AGENTWORLD_DB_PATH"] = test_db_path
    init_db(path=test_db_path)

    app = create_app()
    with TestClient(app) as c:
        yield c

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def sample_app_definition():
    """Sample app definition for testing."""
    return {
        "app_id": "test_payment_app",
        "name": "Test Payment App",
        "description": "A test payment application",
        "category": "payment",
        "icon": "💳",
        "actions": [
            {
                "name": "check_balance",
                "description": "Check account balance",
                "parameters": {},
                "logic": [
                    {"type": "return", "value": {"balance": "agent.balance"}}
                ],
            },
            {
                "name": "transfer",
                "description": "Transfer money",
                "parameters": {
                    "to": {"type": "string", "required": True},
                    "amount": {"type": "number", "required": True, "min_value": 0.01},
                },
                "logic": [
                    {
                        "type": "validate",
                        "condition": "params.amount <= agent.balance",
                        "error_message": "Insufficient funds",
                    },
                    {
                        "type": "update",
                        "target": "agent.balance",
                        "operation": "subtract",
                        "value": "params.amount",
                    },
                    {
                        "type": "update",
                        "target": "agents[params.to].balance",
                        "operation": "add",
                        "value": "params.amount",
                    },
                    {
                        "type": "return",
                        "value": {"new_balance": "agent.balance"},
                    },
                ],
            },
        ],
        "state_schema": [
            {"name": "balance", "type": "number", "default": 1000},
        ],
        "initial_config": {"initial_balance": 1000},
    }


class TestListAppDefinitions:
    """Tests for GET /api/v1/app-definitions."""

    def test_list_empty(self, client):
        """Test listing when no app definitions exist."""
        response = client.get("/api/v1/app-definitions")
        assert response.status_code == 200

        data = response.json()
        assert "definitions" in data
        assert "total" in data
        assert isinstance(data["definitions"], list)

    def test_list_with_pagination(self, client, sample_app_definition):
        """Test pagination parameters."""
        # Create a few apps first
        for i in range(3):
            app_def = sample_app_definition.copy()
            app_def["app_id"] = f"pagination_test_{i}"
            app_def["name"] = f"Pagination Test {i}"
            client.post("/api/v1/app-definitions", json=app_def)

        # Test per_page limit
        response = client.get("/api/v1/app-definitions?per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["definitions"]) <= 2

        # Test page parameter
        response = client.get("/api/v1/app-definitions?page=1&per_page=10")
        assert response.status_code == 200


class TestCreateAppDefinition:
    """Tests for POST /api/v1/app-definitions."""

    def test_create_success(self, client, sample_app_definition):
        """Test creating a valid app definition."""
        # Use unique app_id
        sample_app_definition["app_id"] = "create_test_app"

        response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        assert response.status_code == 201

        data = response.json()
        assert data["app_id"] == "create_test_app"
        assert data["name"] == "Test Payment App"
        assert data["category"] == "payment"
        assert "id" in data
        assert "created_at" in data

    def test_create_minimal(self, client):
        """Test creating with minimal required fields."""
        minimal = {
            "app_id": "minimal_app",
            "name": "Minimal App",
            "category": "custom",
            "actions": [
                {
                    "name": "test_action",
                    "description": "A test action",
                    "logic": [{"type": "return", "value": {"result": "'ok'"}}],
                }
            ],
        }

        response = client.post("/api/v1/app-definitions", json=minimal)
        assert response.status_code == 201

    def test_create_duplicate_app_id(self, client, sample_app_definition):
        """Test that duplicate app_id returns conflict."""
        sample_app_definition["app_id"] = "duplicate_test"

        # Create first time
        response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        assert response.status_code == 201

        # Try to create again with same app_id
        response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        assert response.status_code == 409

    def test_create_invalid_app_id(self, client, sample_app_definition):
        """Test validation of app_id format."""
        sample_app_definition["app_id"] = "Invalid App ID!"  # Contains spaces and special chars

        response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        assert response.status_code == 422  # Validation error

    def test_create_missing_required(self, client):
        """Test missing required fields."""
        incomplete = {
            "name": "Incomplete App",
            # Missing app_id, category, actions
        }

        response = client.post("/api/v1/app-definitions", json=incomplete)
        assert response.status_code == 422


class TestGetAppDefinition:
    """Tests for GET /api/v1/app-definitions/:id."""

    def test_get_by_id(self, client, sample_app_definition):
        """Test getting app definition by ID."""
        sample_app_definition["app_id"] = "get_by_id_test"

        # Create first
        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/v1/app-definitions/{created_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == created_id
        assert data["app_id"] == "get_by_id_test"

    def test_get_nonexistent(self, client):
        """Test getting non-existent app definition."""
        response = client.get("/api/v1/app-definitions/nonexistent-uuid-here")
        assert response.status_code == 404


class TestUpdateAppDefinition:
    """Tests for PATCH /api/v1/app-definitions/:id."""

    def test_update_name(self, client, sample_app_definition):
        """Test updating app name."""
        sample_app_definition["app_id"] = "update_name_test"

        # Create
        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        # Update
        response = client.patch(
            f"/api/v1/app-definitions/{created_id}",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_description(self, client, sample_app_definition):
        """Test updating description."""
        sample_app_definition["app_id"] = "update_desc_test"

        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/app-definitions/{created_id}",
            json={"description": "New description"}
        )
        assert response.status_code == 200
        assert response.json()["description"] == "New description"

    def test_update_nonexistent(self, client):
        """Test updating non-existent app."""
        response = client.patch(
            "/api/v1/app-definitions/nonexistent-id",
            json={"name": "Won't work"}
        )
        assert response.status_code == 404


class TestDeleteAppDefinition:
    """Tests for DELETE /api/v1/app-definitions/:id."""

    def test_delete_success(self, client, sample_app_definition):
        """Test soft deleting an app definition."""
        sample_app_definition["app_id"] = "delete_test"

        # Create
        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/app-definitions/{created_id}")
        assert response.status_code == 200

        # Verify it's gone from list
        list_response = client.get("/api/v1/app-definitions")
        app_ids = [item["id"] for item in list_response.json()["definitions"]]
        assert created_id not in app_ids

    def test_delete_nonexistent(self, client):
        """Test deleting non-existent app."""
        response = client.delete("/api/v1/app-definitions/nonexistent-id")
        assert response.status_code == 404


class TestDuplicateAppDefinition:
    """Tests for POST /api/v1/app-definitions/:id/duplicate."""

    def test_duplicate_success(self, client, sample_app_definition):
        """Test duplicating an app definition."""
        sample_app_definition["app_id"] = "duplicate_source"

        # Create original
        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        original_id = create_response.json()["id"]

        # Duplicate
        response = client.post(
            f"/api/v1/app-definitions/{original_id}/duplicate",
            json={"new_app_id": "duplicate_copy", "new_name": "Duplicate Copy"}
        )
        assert response.status_code == 201

        data = response.json()
        assert data["app_id"] == "duplicate_copy"
        assert data["name"] == "Duplicate Copy"
        assert data["id"] != original_id


class TestTestEndpoint:
    """Tests for POST /api/v1/app-definitions/:id/test."""

    def test_test_action_success(self, client, sample_app_definition):
        """Test executing action in sandbox."""
        sample_app_definition["app_id"] = "test_endpoint_app"

        # Create app
        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        # Test check_balance action
        test_request = {
            "action": "check_balance",
            "agent_id": "alice",
            "params": {},
            "state": {
                "per_agent": {
                    "alice": {"balance": 500}
                },
                "shared": {}
            }
        }

        response = client.post(
            f"/api/v1/app-definitions/{created_id}/test",
            json=test_request
        )
        assert response.status_code == 200

        resp_data = response.json()
        assert resp_data["success"] is True
        assert resp_data["data"]["balance"] == 500

    def test_test_transfer_action(self, client, sample_app_definition):
        """Test transfer action with state changes."""
        sample_app_definition["app_id"] = "test_transfer_app"

        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        test_request = {
            "action": "transfer",
            "agent_id": "alice",
            "params": {"to": "bob", "amount": 100},
            "state": {
                "per_agent": {
                    "alice": {"balance": 500},
                    "bob": {"balance": 200}
                },
                "shared": {}
            }
        }

        response = client.post(
            f"/api/v1/app-definitions/{created_id}/test",
            json=test_request
        )
        assert response.status_code == 200

        resp_data = response.json()
        assert resp_data["success"] is True
        assert resp_data["data"]["new_balance"] == 400  # 500 - 100

        # Check state_after
        assert resp_data["state_after"]["per_agent"]["alice"]["balance"] == 400
        assert resp_data["state_after"]["per_agent"]["bob"]["balance"] == 300

    def test_test_action_validation_failure(self, client, sample_app_definition):
        """Test action that fails validation."""
        sample_app_definition["app_id"] = "test_validation_app"

        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        test_request = {
            "action": "transfer",
            "agent_id": "alice",
            "params": {"to": "bob", "amount": 1000},  # More than balance
            "state": {
                "per_agent": {
                    "alice": {"balance": 100},  # Only 100
                    "bob": {"balance": 200}
                },
                "shared": {}
            }
        }

        response = client.post(
            f"/api/v1/app-definitions/{created_id}/test",
            json=test_request
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert "Insufficient funds" in data["error"]

    def test_test_unknown_action(self, client, sample_app_definition):
        """Test calling unknown action."""
        sample_app_definition["app_id"] = "test_unknown_action_app"

        create_response = client.post("/api/v1/app-definitions", json=sample_app_definition)
        created_id = create_response.json()["id"]

        test_request = {
            "action": "nonexistent_action",
            "agent_id": "alice",
            "params": {},
            "state": {"per_agent": {"alice": {}}, "shared": {}}
        }

        response = client.post(
            f"/api/v1/app-definitions/{created_id}/test",
            json=test_request
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert "Unknown action" in data["error"]


class TestCategoryFilter:
    """Tests for category filtering."""

    def test_filter_by_category(self, client, sample_app_definition):
        """Test filtering apps by category."""
        # Create payment app
        sample_app_definition["app_id"] = "filter_payment"
        sample_app_definition["category"] = "payment"
        client.post("/api/v1/app-definitions", json=sample_app_definition)

        # Create shopping app
        sample_app_definition["app_id"] = "filter_shopping"
        sample_app_definition["category"] = "shopping"
        client.post("/api/v1/app-definitions", json=sample_app_definition)

        # Filter by payment
        response = client.get("/api/v1/app-definitions?category=payment")
        assert response.status_code == 200

        data = response.json()
        for item in data["definitions"]:
            if item["app_id"].startswith("filter_"):
                assert item["category"] == "payment"


class TestSearchFilter:
    """Tests for search filtering."""

    def test_search_by_name(self, client, sample_app_definition):
        """Test searching apps by name."""
        sample_app_definition["app_id"] = "searchable_app"
        sample_app_definition["name"] = "Unique Searchable Name"
        client.post("/api/v1/app-definitions", json=sample_app_definition)

        response = client.get("/api/v1/app-definitions?search=Unique%20Searchable")
        assert response.status_code == 200

        data = response.json()
        found = any(item["name"] == "Unique Searchable Name" for item in data["definitions"])
        assert found
