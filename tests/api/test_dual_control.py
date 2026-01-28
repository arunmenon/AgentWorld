"""Tests for dual-control task API endpoints (ADR-020.1).

Test Suites:
1. Dual-Control Task CRUD Operations (API-01 to API-14)
2. Static Routes - Regression Tests (API-15, API-16)
3. Coordination Events (API-17 to API-21)
4. Coordination Metrics (API-22 to API-24)
5. Solo vs Dual Comparison (API-25 to API-27)
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient

from agentworld.api.app import create_app
from agentworld.persistence.database import init_db


@pytest.fixture(scope="module")
def client():
    """Create a test client with fresh database."""
    test_db_path = f"/tmp/claude/agentworld_dual_control_test_{uuid.uuid4().hex[:8]}.db"

    os.environ["AGENTWORLD_DB_PATH"] = test_db_path

    init_db(path=test_db_path)

    app = create_app()
    with TestClient(app) as c:
        yield c

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def create_sample_task_payload(task_id: str = None) -> dict:
    """Create a sample dual-control task payload for testing."""
    return {
        "task_id": task_id or f"test_task_{uuid.uuid4().hex[:8]}",
        "name": "Test Dual-Control Task",
        "description": "A test task for API testing",
        "domain": "airlines",
        "difficulty": "easy",
        "simulation_config": {"topology": "direct", "max_turns": 15},
        "agent_id": "service_agent_1",
        "agent_role": "service_agent",
        "agent_instruction": "Help the customer with their request",
        "agent_apps": ["airlines_backend"],
        "agent_initial_state": {"airlines_backend": {"shared": {"bookings": {}}}},
        "agent_goal_state": {},
        "user_id": "customer_1",
        "user_role": "customer",
        "user_instruction": "Request help from the agent",
        "user_apps": ["airlines_app"],
        "user_initial_state": {"airlines_app": {"per_agent": {}}},
        "user_goal_state": {},
        "required_handoffs": [
            {
                "handoff_id": "test_handoff_1",
                "from_role": "service_agent",
                "to_role": "customer",
                "expected_action": "view_my_trips",
                "description": "Agent asks customer to check their app",
            }
        ],
        "max_turns": 15,
        "expected_coordination_count": 1,
        "tags": ["test", "airlines"],
    }


class TestDualControlTaskCRUD:
    """Test Suite 1: Dual-Control Task CRUD Operations (API-01 to API-14)."""

    created_task_id = None

    def test_api_01_create_task_valid(self, client):
        """API-01: Create task with valid data - should return 201."""
        payload = create_sample_task_payload("crud_test_task_001")

        response = client.post("/api/v1/dual-control-tasks", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["task_id"] == "crud_test_task_001"
        assert data["name"] == "Test Dual-Control Task"
        assert data["domain"] == "airlines"
        assert data["difficulty"] == "easy"
        assert "id" in data  # UUID assigned
        assert data["is_active"] is True

        TestDualControlTaskCRUD.created_task_id = data["task_id"]

    def test_api_02_create_duplicate_task(self, client):
        """API-02: Create duplicate task_id - should return 409 Conflict."""
        payload = create_sample_task_payload("crud_test_task_001")

        response = client.post("/api/v1/dual-control-tasks", json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_api_03_create_task_missing_required(self, client):
        """API-03: Missing required field - should return 422 Validation Error."""
        payload = {"task_id": "incomplete_task"}  # Missing required fields

        response = client.post("/api/v1/dual-control-tasks", json=payload)
        assert response.status_code == 422

    def test_api_04_list_all_tasks(self, client):
        """API-04: List all tasks - should return 200 with pagination."""
        response = client.get("/api/v1/dual-control-tasks")
        assert response.status_code == 200

        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)
        assert data["total"] >= 1  # At least the one we created

    def test_api_05_filter_by_domain(self, client):
        """API-05: Filter by domain - should return only matching tasks."""
        response = client.get("/api/v1/dual-control-tasks?domain=airlines")
        assert response.status_code == 200

        data = response.json()
        for task in data["tasks"]:
            assert task["domain"] == "airlines"

    def test_api_06_filter_by_difficulty(self, client):
        """API-06: Filter by difficulty - should return only matching tasks."""
        response = client.get("/api/v1/dual-control-tasks?difficulty=easy")
        assert response.status_code == 200

        data = response.json()
        for task in data["tasks"]:
            assert task["difficulty"] == "easy"

    def test_api_07_filter_by_tags(self, client):
        """API-07: Filter by tags - should return matching tasks."""
        response = client.get("/api/v1/dual-control-tasks?tags=test")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1

    def test_api_08_search_name_description(self, client):
        """API-08: Search in name/description - should return matching results."""
        response = client.get("/api/v1/dual-control-tasks?search=Dual-Control")
        assert response.status_code == 200

        data = response.json()
        # Should find tasks with "Dual-Control" in name or description
        assert isinstance(data["tasks"], list)

    def test_api_09_get_existing_task(self, client):
        """API-09: Get existing task - should return 200 with full object."""
        task_id = TestDualControlTaskCRUD.created_task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.get(f"/api/v1/dual-control-tasks/{task_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == task_id
        assert "required_handoffs" in data
        assert len(data["required_handoffs"]) == 1

    def test_api_10_get_nonexistent_task(self, client):
        """API-10: Get non-existent task - should return 404."""
        response = client.get("/api/v1/dual-control-tasks/nonexistent_task_xyz")
        assert response.status_code == 404

    def test_api_11_update_single_field(self, client):
        """API-11: Update name field - should return 200 with updated task."""
        task_id = TestDualControlTaskCRUD.created_task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.patch(
            f"/api/v1/dual-control-tasks/{task_id}",
            json={"name": "Updated Task Name"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Task Name"

    def test_api_12_update_multiple_fields(self, client):
        """API-12: Update multiple fields - should return 200 with all updated."""
        task_id = TestDualControlTaskCRUD.created_task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.patch(
            f"/api/v1/dual-control-tasks/{task_id}",
            json={
                "description": "Updated description",
                "difficulty": "medium",
                "max_turns": 20,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Updated description"
        assert data["difficulty"] == "medium"
        assert data["max_turns"] == 20

    def test_api_13_soft_delete(self, client):
        """API-13: Soft delete (default) - should return 204 and set is_active=0."""
        # Create a task to delete
        payload = create_sample_task_payload("soft_delete_test")
        create_resp = client.post("/api/v1/dual-control-tasks", json=payload)
        assert create_resp.status_code == 201

        # Soft delete
        response = client.delete("/api/v1/dual-control-tasks/soft_delete_test")
        assert response.status_code == 204

        # Task should not appear in list (is_active=0)
        list_resp = client.get("/api/v1/dual-control-tasks?search=soft_delete_test")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    def test_api_14_hard_delete(self, client):
        """API-14: Hard delete - should return 204 and remove from DB."""
        # Create a task to delete
        payload = create_sample_task_payload("hard_delete_test")
        create_resp = client.post("/api/v1/dual-control-tasks", json=payload)
        assert create_resp.status_code == 201

        # Hard delete
        response = client.delete("/api/v1/dual-control-tasks/hard_delete_test?hard=true")
        assert response.status_code == 204

        # Task should be completely gone
        get_resp = client.get("/api/v1/dual-control-tasks/hard_delete_test")
        assert get_resp.status_code == 404


class TestStaticRoutes:
    """Test Suite 2: Static Routes - Regression Tests (API-15, API-16).

    These tests verify the bug fix where static routes like /stats
    were incorrectly matching as /{task_id}.
    """

    def test_api_15_get_stats(self, client):
        """API-15: GET /stats - should return 200 with statistics (regression)."""
        response = client.get("/api/v1/dual-control-tasks/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_tasks" in data
        assert "total_coordination_events" in data
        assert "successful_handoffs" in data
        assert "handoff_success_rate" in data
        assert "total_comparisons" in data
        assert isinstance(data["total_tasks"], int)

    def test_api_16_list_domains(self, client):
        """API-16: GET /domains/list - should return 200 with domain array."""
        response = client.get("/api/v1/dual-control-tasks/domains/list")
        assert response.status_code == 200

        data = response.json()
        assert "domains" in data
        assert "count" in data
        assert isinstance(data["domains"], list)


class TestCoordinationEvents:
    """Test Suite 3: Coordination Events (API-17 to API-21)."""

    task_id = None
    event_id = None

    @pytest.fixture(autouse=True)
    def setup_task(self, client):
        """Create a task for event tests."""
        if TestCoordinationEvents.task_id is None:
            payload = create_sample_task_payload("event_test_task")
            response = client.post("/api/v1/dual-control-tasks", json=payload)
            if response.status_code == 201:
                TestCoordinationEvents.task_id = "event_test_task"

    def test_api_17_create_event_valid(self, client):
        """API-17: Create event (no task_id in body) - should return 201."""
        task_id = TestCoordinationEvents.task_id
        if not task_id:
            pytest.skip("No task created")

        event_payload = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "trial_id": "trial_001",
            "instructor_id": "service_agent_1",
            "instructor_role": "service_agent",
            "instruction_text": "Please check your booking in the app",
            "actor_id": "customer_1",
            "actor_role": "customer",
            "action_taken": "view_my_trips",
            "action_params": {},
            "matched_handoff_id": "test_handoff_1",
            "match_confidence": 0.95,
            "handoff_successful": True,
            "latency_turns": 2,
        }

        response = client.post(
            f"/api/v1/dual-control-tasks/{task_id}/events",
            json=event_payload,
        )
        assert response.status_code == 201

        data = response.json()
        assert data["task_id"] == task_id
        assert data["trial_id"] == "trial_001"
        assert data["handoff_successful"] is True
        assert data["match_confidence"] == 0.95

        TestCoordinationEvents.event_id = data["event_id"]

    def test_api_18_create_event_nonexistent_task(self, client):
        """API-18: Event for non-existent task - should return 404."""
        event_payload = {
            "event_id": "evt_invalid",
            "trial_id": "trial_001",
            "instructor_id": "agent_1",
            "instructor_role": "service_agent",
            "instruction_text": "Test instruction",
        }

        response = client.post(
            "/api/v1/dual-control-tasks/nonexistent_task/events",
            json=event_payload,
        )
        assert response.status_code == 404

    def test_api_19_list_events_for_task(self, client):
        """API-19: List events for task - should return 200 with event array."""
        task_id = TestCoordinationEvents.task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.get(f"/api/v1/dual-control-tasks/{task_id}/events")
        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
        assert data["total"] >= 1

    def test_api_20_filter_events_by_trial(self, client):
        """API-20: Filter by trial_id - should return filtered events."""
        task_id = TestCoordinationEvents.task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.get(
            f"/api/v1/dual-control-tasks/{task_id}/events?trial_id=trial_001"
        )
        assert response.status_code == 200

        data = response.json()
        for event in data["events"]:
            assert event["trial_id"] == "trial_001"

    def test_api_21_list_events_empty(self, client):
        """API-21: Events for task with none - should return 200 with empty array."""
        # Create a new task with no events
        payload = create_sample_task_payload("no_events_task")
        create_resp = client.post("/api/v1/dual-control-tasks", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("Could not create task")

        response = client.get("/api/v1/dual-control-tasks/no_events_task/events")
        assert response.status_code == 200

        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0


class TestCoordinationMetrics:
    """Test Suite 4: Coordination Metrics (API-22 to API-24)."""

    task_id = None

    @pytest.fixture(autouse=True)
    def setup_task(self, client):
        """Create a task with events for metrics tests."""
        if TestCoordinationMetrics.task_id is None:
            payload = create_sample_task_payload("metrics_test_task")
            payload["expected_coordination_count"] = 2
            response = client.post("/api/v1/dual-control-tasks", json=payload)
            if response.status_code == 201:
                TestCoordinationMetrics.task_id = "metrics_test_task"

                # Add some events for metrics calculation
                for i, success in enumerate([True, False]):
                    event = {
                        "event_id": f"metric_evt_{i}",
                        "trial_id": "metrics_trial",
                        "instructor_id": "agent_1",
                        "instructor_role": "service_agent",
                        "instruction_text": f"Instruction {i}",
                        "handoff_successful": success,
                        "match_confidence": 0.9 if success else 0.3,
                        "latency_turns": 2 if success else 0,
                    }
                    client.post(
                        f"/api/v1/dual-control-tasks/metrics_test_task/events",
                        json=event,
                    )

    def test_api_22_get_aggregate_metrics(self, client):
        """API-22: Get aggregate metrics - should return 200 with computed metrics."""
        task_id = TestCoordinationMetrics.task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.get(f"/api/v1/dual-control-tasks/{task_id}/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == task_id
        assert "total_handoffs_required" in data
        assert "handoffs_completed" in data
        assert "coordination_success_rate" in data
        assert "avg_instruction_to_action_turns" in data
        assert "user_confusion_count" in data
        assert "computed_at" in data

    def test_api_23_get_trial_metrics(self, client):
        """API-23: Trial-specific metrics - should return 200 with trial metrics."""
        task_id = TestCoordinationMetrics.task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.get(
            f"/api/v1/dual-control-tasks/{task_id}/metrics?trial_id=metrics_trial"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == task_id
        assert data["trial_id"] == "metrics_trial"

    def test_api_24_metrics_no_events(self, client):
        """API-24: Metrics with no events - should return 200 with zero values."""
        # Create a task with no events
        payload = create_sample_task_payload("empty_metrics_task")
        create_resp = client.post("/api/v1/dual-control-tasks", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("Could not create task")

        response = client.get("/api/v1/dual-control-tasks/empty_metrics_task/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["handoffs_completed"] == 0
        assert data["coordination_success_rate"] == 0.0


class TestSoloDualComparison:
    """Test Suite 5: Solo vs Dual Comparison (API-25 to API-27)."""

    task_id = None

    @pytest.fixture(autouse=True)
    def setup_task(self, client):
        """Create a task for comparison tests."""
        if TestSoloDualComparison.task_id is None:
            payload = create_sample_task_payload("comparison_test_task")
            response = client.post("/api/v1/dual-control-tasks", json=payload)
            if response.status_code == 201:
                TestSoloDualComparison.task_id = "comparison_test_task"

    def test_api_25_run_comparison(self, client):
        """API-25: Run comparison - should return 200 with comparison created."""
        task_id = TestSoloDualComparison.task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.post(
            f"/api/v1/dual-control-tasks/{task_id}/compare",
            json={"num_trials": 5},
        )
        assert response.status_code == 200

        data = response.json()
        assert "comparison" in data
        assert data["comparison"]["task_id"] == task_id
        assert data["comparison"]["solo_trials"] == 5
        assert data["comparison"]["dual_trials"] == 5
        assert "insight" in data

    def test_api_26_get_comparison(self, client):
        """API-26: Get latest comparison - should return 200 with comparison data."""
        task_id = TestSoloDualComparison.task_id
        if not task_id:
            pytest.skip("No task created")

        response = client.get(f"/api/v1/dual-control-tasks/{task_id}/comparison")
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == task_id
        assert "solo_pass_1" in data
        assert "dual_pass_1" in data
        assert "performance_drop" in data
        assert "step_increase" in data

    def test_api_27_get_comparison_not_exists(self, client):
        """API-27: No comparison exists - should return 404 with message."""
        # Create a task with no comparison
        payload = create_sample_task_payload("no_comparison_task")
        create_resp = client.post("/api/v1/dual-control-tasks", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("Could not create task")

        response = client.get("/api/v1/dual-control-tasks/no_comparison_task/comparison")
        assert response.status_code == 404
        assert "No comparison found" in response.json()["detail"]


class TestRegressionBugs:
    """Test Suite 6: Regression Tests for Fixed Bugs."""

    def test_reg_01_static_route_not_404(self, client):
        """REG-01: Static route /stats should not return 404."""
        response = client.get("/api/v1/dual-control-tasks/stats")
        # Should NOT be 404 (which would happen if matched as /{task_id})
        assert response.status_code != 404
        assert response.status_code == 200

    def test_reg_02_event_schema_no_task_id_in_body(self, client):
        """REG-02: Event creation should not require task_id in body."""
        # Create task first
        payload = create_sample_task_payload("reg_test_task")
        create_resp = client.post("/api/v1/dual-control-tasks", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("Could not create task")

        # Event payload WITHOUT task_id (it comes from URL path)
        event_payload = {
            "event_id": "reg_event_001",
            "trial_id": "trial_001",
            "instructor_id": "agent_1",
            "instructor_role": "service_agent",
            "instruction_text": "Test instruction",
            # Note: No task_id field
        }

        response = client.post(
            "/api/v1/dual-control-tasks/reg_test_task/events",
            json=event_payload,
        )
        assert response.status_code == 201

        data = response.json()
        # task_id should be set from URL path
        assert data["task_id"] == "reg_test_task"

    def test_reg_03_session_not_none(self, client):
        """REG-03: Any API call should not cause NoneType error from session."""
        # Multiple API calls to ensure session is properly managed
        responses = [
            client.get("/api/v1/dual-control-tasks"),
            client.get("/api/v1/dual-control-tasks/stats"),
            client.get("/api/v1/dual-control-tasks/domains/list"),
        ]

        for response in responses:
            # None of these should fail with 500 Internal Server Error
            assert response.status_code != 500
            # They should all return valid JSON
            data = response.json()
            assert data is not None


class TestPagination:
    """Additional tests for pagination functionality."""

    def test_pagination_default_values(self, client):
        """Test default pagination values."""
        response = client.get("/api/v1/dual-control-tasks")
        assert response.status_code == 200

        data = response.json()
        assert "tasks" in data
        assert "total" in data

    def test_pagination_custom_page(self, client):
        """Test custom page parameter."""
        response = client.get("/api/v1/dual-control-tasks?page=1&per_page=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data["tasks"]) <= 5

    def test_pagination_invalid_page(self, client):
        """Test invalid page parameter."""
        response = client.get("/api/v1/dual-control-tasks?page=0")
        assert response.status_code == 422

    def test_pagination_per_page_limit(self, client):
        """Test per_page limit (max 100)."""
        response = client.get("/api/v1/dual-control-tasks?per_page=150")
        assert response.status_code == 422
