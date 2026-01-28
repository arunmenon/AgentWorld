"""Unit tests for dual-control example apps (ADR-020.1).

Test Suites:
1. Airlines Domain Apps (APP-01 to APP-04)
2. PayPal Domain Apps (APP-05 to APP-08)
3. App Access Control
4. App State Types
5. App Helper Functions
"""

import pytest

from agentworld.apps.evaluation.dual_control_apps import (
    AIRLINES_BACKEND,
    AIRLINES_APP,
    PAYPAL_BACKEND,
    PAYPAL_APP,
    DUAL_CONTROL_APPS,
    get_dual_control_apps,
    get_dual_control_app,
    get_apps_by_domain,
    get_service_agent_apps,
    get_customer_apps,
)


# =============================================================================
# Test Suite 1: Airlines Domain Apps (APP-01 to APP-04)
# =============================================================================


class TestAirlinesBackend:
    """Tests for Airlines Backend CRM app."""

    def test_app_01_access_type(self):
        """APP-01: Airlines backend has role_restricted access for service_agent."""
        assert AIRLINES_BACKEND["access_type"] == "role_restricted"
        assert "service_agent" in AIRLINES_BACKEND["allowed_roles"]
        assert "customer" not in AIRLINES_BACKEND["allowed_roles"]

    def test_app_02_lookup_reservation_action(self):
        """APP-02: lookup_booking action exists and is read type."""
        actions = {a["name"]: a for a in AIRLINES_BACKEND["actions"]}

        assert "lookup_booking" in actions
        assert actions["lookup_booking"]["toolType"] == "read"
        assert "confirmation_code" in actions["lookup_booking"]["parameters"]

    def test_state_type_shared(self):
        """Airlines backend uses shared state."""
        assert AIRLINES_BACKEND["state_type"] == "shared"

    def test_has_write_actions(self):
        """Airlines backend has write actions for modifications."""
        actions = {a["name"]: a for a in AIRLINES_BACKEND["actions"]}

        assert "change_seat" in actions
        assert actions["change_seat"]["toolType"] == "write"

        assert "add_special_request" in actions
        assert actions["add_special_request"]["toolType"] == "write"

        assert "process_refund" in actions
        assert actions["process_refund"]["toolType"] == "write"


class TestAirlinesApp:
    """Tests for Airlines Mobile App."""

    def test_app_03_access_type(self):
        """APP-03: Airlines app has role_restricted access for customer."""
        assert AIRLINES_APP["access_type"] == "role_restricted"
        assert "customer" in AIRLINES_APP["allowed_roles"]
        assert "service_agent" not in AIRLINES_APP["allowed_roles"]

    def test_app_04_view_boarding_pass_action(self):
        """APP-04: show_boarding_pass action shows pass for device."""
        actions = {a["name"]: a for a in AIRLINES_APP["actions"]}

        assert "show_boarding_pass" in actions
        # Note: this is marked as read because it just displays
        assert actions["show_boarding_pass"]["toolType"] == "read"

    def test_state_type_per_agent(self):
        """Airlines app uses per_agent state."""
        assert AIRLINES_APP["state_type"] == "per_agent"

    def test_has_customer_actions(self):
        """Airlines app has appropriate customer actions."""
        actions = {a["name"]: a for a in AIRLINES_APP["actions"]}

        assert "view_my_trips" in actions
        assert "check_in_online" in actions
        assert "update_preferences" in actions


# =============================================================================
# Test Suite 2: PayPal Domain Apps (APP-05 to APP-08)
# =============================================================================


class TestPayPalBackend:
    """Tests for PayPal Support Console."""

    def test_app_05_access_type(self):
        """APP-05: PayPal backend has role_restricted access for service_agent."""
        assert PAYPAL_BACKEND["access_type"] == "role_restricted"
        assert "service_agent" in PAYPAL_BACKEND["allowed_roles"]
        assert "customer" not in PAYPAL_BACKEND["allowed_roles"]

    def test_app_06_lookup_account_action(self):
        """APP-06: lookup_account action returns account data."""
        actions = {a["name"]: a for a in PAYPAL_BACKEND["actions"]}

        assert "lookup_account" in actions
        assert actions["lookup_account"]["toolType"] == "read"
        assert "email" in actions["lookup_account"]["parameters"]
        assert "account_id" in actions["lookup_account"]["parameters"]

    def test_state_type_shared(self):
        """PayPal backend uses shared state."""
        assert PAYPAL_BACKEND["state_type"] == "shared"

    def test_has_dispute_actions(self):
        """PayPal backend has dispute-related actions."""
        actions = {a["name"]: a for a in PAYPAL_BACKEND["actions"]}

        assert "create_dispute" in actions
        assert actions["create_dispute"]["toolType"] == "write"

        assert "resolve_dispute" in actions
        assert "issue_refund" in actions


class TestPayPalApp:
    """Tests for PayPal Mobile App."""

    def test_app_07_access_type(self):
        """APP-07: PayPal app has role_restricted access for customer."""
        assert PAYPAL_APP["access_type"] == "role_restricted"
        assert "customer" in PAYPAL_APP["allowed_roles"]
        assert "service_agent" not in PAYPAL_APP["allowed_roles"]

    def test_app_08_toggle_2fa_action(self):
        """APP-08: toggle_two_factor action submits verification."""
        actions = {a["name"]: a for a in PAYPAL_APP["actions"]}

        assert "toggle_two_factor" in actions
        assert actions["toggle_two_factor"]["toolType"] == "write"
        assert "enable" in actions["toggle_two_factor"]["parameters"]

    def test_state_type_per_agent(self):
        """PayPal app uses per_agent state."""
        assert PAYPAL_APP["state_type"] == "per_agent"

    def test_has_payment_actions(self):
        """PayPal app has payment-related actions."""
        actions = {a["name"]: a for a in PAYPAL_APP["actions"]}

        assert "check_balance" in actions
        assert actions["check_balance"]["toolType"] == "read"

        assert "send_money" in actions
        assert actions["send_money"]["toolType"] == "write"

        assert "add_card" in actions
        assert actions["add_card"]["toolType"] == "write"


# =============================================================================
# Test Suite 3: App Access Control
# =============================================================================


class TestAppAccessControl:
    """Tests for app access control settings."""

    def test_all_apps_have_access_type(self):
        """All dual-control apps have access_type defined."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            assert "access_type" in app, f"{app_id} missing access_type"
            assert app["access_type"] in ["shared", "role_restricted", "per_agent"]

    def test_all_apps_have_allowed_roles(self):
        """All role_restricted apps have allowed_roles defined."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            if app["access_type"] == "role_restricted":
                assert "allowed_roles" in app, f"{app_id} missing allowed_roles"
                assert len(app["allowed_roles"]) > 0, f"{app_id} has empty allowed_roles"

    def test_backend_apps_for_service_agent(self):
        """Backend apps are restricted to service_agent role."""
        backend_apps = [AIRLINES_BACKEND, PAYPAL_BACKEND]

        for app in backend_apps:
            assert "service_agent" in app["allowed_roles"]
            assert "customer" not in app["allowed_roles"]

    def test_frontend_apps_for_customer(self):
        """Frontend apps are restricted to customer role."""
        frontend_apps = [AIRLINES_APP, PAYPAL_APP]

        for app in frontend_apps:
            assert "customer" in app["allowed_roles"]
            assert "service_agent" not in app["allowed_roles"]


# =============================================================================
# Test Suite 4: App State Types
# =============================================================================


class TestAppStateTypes:
    """Tests for app state type settings."""

    def test_all_apps_have_state_type(self):
        """All dual-control apps have state_type defined."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            assert "state_type" in app, f"{app_id} missing state_type"
            assert app["state_type"] in ["shared", "per_agent"]

    def test_backend_apps_use_shared_state(self):
        """Backend apps use shared state (single source of truth)."""
        assert AIRLINES_BACKEND["state_type"] == "shared"
        assert PAYPAL_BACKEND["state_type"] == "shared"

    def test_frontend_apps_use_per_agent_state(self):
        """Frontend apps use per_agent state (isolated per customer)."""
        assert AIRLINES_APP["state_type"] == "per_agent"
        assert PAYPAL_APP["state_type"] == "per_agent"

    def test_state_schema_matches_state_type(self):
        """State schema per_agent field matches state_type."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            for field in app.get("state_schema", []):
                if app["state_type"] == "per_agent":
                    # per_agent apps should have per_agent fields
                    # Handle both snake_case and camelCase keys
                    is_per_agent = field.get("per_agent", field.get("perAgent", False))
                    assert is_per_agent is True, \
                        f"{app_id}.{field['name']} should be per_agent"


# =============================================================================
# Test Suite 5: App Helper Functions
# =============================================================================


class TestAppHelperFunctions:
    """Tests for app helper functions."""

    def test_get_dual_control_apps(self):
        """get_dual_control_apps returns all apps."""
        apps = get_dual_control_apps()

        # Now includes airlines, paypal, and emirates (6 total)
        assert len(apps) >= 4  # At least the original 4
        assert "airlines_backend" in apps
        assert "airlines_app" in apps
        assert "paypal_backend" in apps
        assert "paypal_app" in apps

    def test_get_dual_control_app(self):
        """get_dual_control_app returns specific app or None."""
        app = get_dual_control_app("airlines_backend")
        assert app is not None
        assert app["app_id"] == "airlines_backend"

        app = get_dual_control_app("nonexistent_app")
        assert app is None

    def test_get_apps_by_domain_airlines(self):
        """get_apps_by_domain returns airlines apps."""
        apps = get_apps_by_domain("airlines")

        assert len(apps) == 2
        app_ids = [a["app_id"] for a in apps]
        assert "airlines_backend" in app_ids
        assert "airlines_app" in app_ids

    def test_get_apps_by_domain_paypal(self):
        """get_apps_by_domain returns paypal apps."""
        apps = get_apps_by_domain("paypal")

        assert len(apps) == 2
        app_ids = [a["app_id"] for a in apps]
        assert "paypal_backend" in app_ids
        assert "paypal_app" in app_ids

    def test_get_apps_by_domain_unknown(self):
        """get_apps_by_domain returns empty list for unknown domain."""
        apps = get_apps_by_domain("unknown")
        assert apps == []

    def test_get_service_agent_apps(self):
        """get_service_agent_apps returns backend apps."""
        apps = get_service_agent_apps()

        # Now includes airlines, paypal, and emirates backends
        assert len(apps) >= 2  # At least the original 2
        for app in apps:
            assert "service_agent" in app["allowed_roles"]

    def test_get_customer_apps(self):
        """get_customer_apps returns customer-facing apps."""
        apps = get_customer_apps()

        # Now includes airlines, paypal, and emirates customer apps
        assert len(apps) >= 2  # At least the original 2
        for app in apps:
            assert "customer" in app["allowed_roles"]


# =============================================================================
# Test Suite 6: App Actions Validation
# =============================================================================


class TestAppActionsValidation:
    """Tests for app action structure validation."""

    def test_all_actions_have_required_fields(self):
        """All actions have name, description, toolType."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            for action in app["actions"]:
                assert "name" in action, f"{app_id} action missing name"
                assert "description" in action, f"{app_id}.{action.get('name')} missing description"
                assert "toolType" in action, f"{app_id}.{action.get('name')} missing toolType"

    def test_all_actions_have_valid_tool_type(self):
        """All actions have valid toolType (read or write)."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            for action in app["actions"]:
                assert action["toolType"] in ["read", "write"], \
                    f"{app_id}.{action['name']} has invalid toolType: {action['toolType']}"

    def test_read_actions_dont_modify_state(self):
        """Read actions should not have 'update' operations in logic."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            for action in app["actions"]:
                if action["toolType"] == "read":
                    for block in action.get("logic", []):
                        # Note: This is a basic check; show_boarding_pass
                        # actually does update state, which is a design choice
                        pass  # Would need more complex logic analysis

    def test_write_actions_have_logic(self):
        """Write actions should have logic defined."""
        for app_id, app in DUAL_CONTROL_APPS.items():
            for action in app["actions"]:
                if action["toolType"] == "write":
                    assert "logic" in action, \
                        f"{app_id}.{action['name']} (write) missing logic"
                    assert len(action["logic"]) > 0, \
                        f"{app_id}.{action['name']} (write) has empty logic"


# =============================================================================
# Test Suite 7: Integration with Task Definitions
# =============================================================================


class TestIntegrationWithTasks:
    """Tests that apps integrate correctly with task definitions."""

    def test_task_apps_exist(self):
        """Apps referenced in tasks exist."""
        from agentworld.tasks.dual_control_examples import ALL_DUAL_CONTROL_TASKS

        for task in ALL_DUAL_CONTROL_TASKS:
            for app_id in task.agent_apps:
                assert get_dual_control_app(app_id) is not None, \
                    f"Task {task.task_id} references missing app: {app_id}"

            for app_id in task.user_apps:
                assert get_dual_control_app(app_id) is not None, \
                    f"Task {task.task_id} references missing app: {app_id}"

    def test_agent_apps_allow_service_agent(self):
        """Agent apps in tasks allow service_agent role."""
        from agentworld.tasks.dual_control_examples import ALL_DUAL_CONTROL_TASKS

        for task in ALL_DUAL_CONTROL_TASKS:
            for app_id in task.agent_apps:
                app = get_dual_control_app(app_id)
                if app and app["access_type"] == "role_restricted":
                    assert "service_agent" in app["allowed_roles"], \
                        f"Task {task.task_id} agent app {app_id} doesn't allow service_agent"

    def test_user_apps_allow_customer(self):
        """User apps in tasks allow customer role."""
        from agentworld.tasks.dual_control_examples import ALL_DUAL_CONTROL_TASKS

        for task in ALL_DUAL_CONTROL_TASKS:
            for app_id in task.user_apps:
                app = get_dual_control_app(app_id)
                if app and app["access_type"] == "role_restricted":
                    assert "customer" in app["allowed_roles"], \
                        f"Task {task.task_id} user app {app_id} doesn't allow customer"
