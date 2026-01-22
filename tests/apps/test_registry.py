"""Tests for AppRegistry with database fallback per ADR-018."""

import os
import pytest

from agentworld.apps.base import AppRegistry, get_app_registry
from agentworld.apps.dynamic import DynamicApp
from agentworld.apps.definition import AppDefinition, ActionDefinition, ParamType
from agentworld.apps.paypal import register_paypal_app
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


@pytest.fixture(scope="module")
def setup_db():
    """Set up test database."""
    test_db_path = "/tmp/claude/agentworld_registry_test.db"

    # Remove existing test DB if present
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    os.environ["AGENTWORLD_DB_PATH"] = test_db_path
    init_db(path=test_db_path)

    yield test_db_path

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope="module")
def registry(setup_db):
    """Get registry instance with PayPal registered."""
    reg = get_app_registry()
    register_paypal_app()
    return reg


@pytest.fixture
def repo(setup_db):
    """Get repository instance."""
    return Repository()


class TestAppRegistryBasics:
    """Basic tests for AppRegistry."""

    def test_get_python_plugin(self, registry):
        """Test loading Python-defined apps (PayPal)."""
        app = registry.get("paypal")
        assert app is not None
        assert app.app_id == "paypal"
        assert app.name == "PayPal"

    def test_list_includes_python_plugins(self, registry):
        """Test that list_apps includes Python plugins."""
        apps = registry.list_apps()
        app_ids = [a["id"] for a in apps]
        assert "paypal" in app_ids

    def test_get_nonexistent(self, registry):
        """Test getting non-existent app returns None."""
        app = registry.get("nonexistent_app_xyz")
        assert app is None


class TestAppRegistryDBFallback:
    """Tests for database fallback functionality."""

    def test_db_enabled_by_default(self, registry):
        """Test that DB fallback is enabled by default."""
        # Save current state
        original = registry._db_enabled

        # Reset to default
        registry._db_enabled = True
        assert registry._db_enabled is True

        # Restore
        registry._db_enabled = original

    def test_db_can_be_disabled(self, registry):
        """Test that DB fallback can be disabled."""
        original = registry._db_enabled

        registry.set_db_enabled(False)
        assert registry._db_enabled is False

        # Restore
        registry._db_enabled = original

    def test_get_from_db(self, registry, repo):
        """Test loading app from database."""
        # Create a definition in DB
        definition_dict = {
            "app_id": "db_test_app",
            "name": "DB Test App",
            "description": "App for testing DB fallback",
            "category": "custom",
            "icon": "🧪",
            "actions": [
                {
                    "name": "test_action",
                    "description": "A test action",
                    "parameters": {},
                    "logic": [{"type": "return", "value": {"result": "'success'"}}],
                }
            ],
            "state_schema": [],
            "initial_config": {},
        }

        import uuid
        definition_id = str(uuid.uuid4())
        definition_data = {
            "id": definition_id,
            "app_id": "db_test_app",
            "name": "DB Test App",
            "description": "App for testing DB fallback",
            "category": "custom",
            "icon": "🧪",
            "version": 1,
            "definition": definition_dict,
            "is_builtin": False,
            "is_active": True,
        }
        repo.save_app_definition(definition_data)

        # Enable DB fallback
        registry.set_db_enabled(True)

        # Get app from registry
        app = registry.get("db_test_app")
        assert app is not None
        assert isinstance(app, DynamicApp)
        assert app.app_id == "db_test_app"
        assert app.name == "DB Test App"

    def test_python_plugin_takes_priority(self, registry, repo):
        """Test that Python plugins take priority over DB definitions."""
        # Create a DB definition with same app_id as PayPal
        definition_dict = {
            "app_id": "paypal",  # Same as Python plugin
            "name": "Fake PayPal",
            "description": "This should not be loaded",
            "category": "payment",
            "icon": "💰",
            "actions": [],
            "state_schema": [],
            "initial_config": {},
        }

        import uuid
        definition_id = str(uuid.uuid4())
        definition_data = {
            "id": definition_id,
            "app_id": "paypal",
            "name": "Fake PayPal",
            "description": "This should not be loaded",
            "category": "payment",
            "icon": "💰",
            "version": 1,
            "definition": definition_dict,
            "is_builtin": False,
            "is_active": True,
        }
        repo.save_app_definition(definition_data)

        # Enable DB fallback
        registry.set_db_enabled(True)

        # Get app - should be Python version, not DB version
        app = registry.get("paypal")
        assert app is not None
        assert app.name == "PayPal"  # Python plugin name
        assert app.name != "Fake PayPal"  # Not DB version

    def test_is_python_plugin(self, registry):
        """Test is_python_plugin method."""
        assert registry.is_python_plugin("paypal") is True
        assert registry.is_python_plugin("db_test_app") is False
        assert registry.is_python_plugin("nonexistent") is False

    def test_list_includes_db_apps(self, registry, repo):
        """Test that list_apps includes DB-defined apps."""
        # Create another DB app
        definition_dict = {
            "app_id": "db_list_test_app",
            "name": "DB List Test App",
            "description": "App for testing list",
            "category": "custom",
            "icon": "📝",
            "actions": [
                {
                    "name": "test",
                    "description": "Test",
                    "parameters": {},
                    "logic": [{"type": "return", "value": {}}],
                }
            ],
            "state_schema": [],
            "initial_config": {},
        }

        import uuid
        definition_id = str(uuid.uuid4())
        definition_data = {
            "id": definition_id,
            "app_id": "db_list_test_app",
            "name": "DB List Test App",
            "description": "App for testing list",
            "category": "custom",
            "icon": "📝",
            "version": 1,
            "definition": definition_dict,
            "is_builtin": False,
            "is_active": True,
        }
        repo.save_app_definition(definition_data)

        # Enable DB fallback
        registry.set_db_enabled(True)

        # List should include both Python and DB apps
        apps = registry.list_apps()
        app_ids = [a["id"] for a in apps]

        assert "paypal" in app_ids  # Python plugin
        assert "db_list_test_app" in app_ids  # DB app

    def test_inactive_apps_not_loaded(self, registry, repo):
        """Test that inactive (soft-deleted) apps are not loaded."""
        # Create an inactive app
        definition_dict = {
            "app_id": "inactive_app",
            "name": "Inactive App",
            "description": "This should not be loaded",
            "category": "custom",
            "icon": "🚫",
            "actions": [
                {
                    "name": "test",
                    "description": "Test",
                    "parameters": {},
                    "logic": [{"type": "return", "value": {}}],
                }
            ],
            "state_schema": [],
            "initial_config": {},
        }

        import uuid
        definition_id = str(uuid.uuid4())
        definition_data = {
            "id": definition_id,
            "app_id": "inactive_app",
            "name": "Inactive App",
            "description": "This should not be loaded",
            "category": "custom",
            "icon": "🚫",
            "version": 1,
            "definition": definition_dict,
            "is_builtin": False,
            "is_active": False,  # Inactive!
        }
        repo.save_app_definition(definition_data)

        # Enable DB fallback
        registry.set_db_enabled(True)

        # Should not be found
        app = registry.get("inactive_app")
        assert app is None

        # Should not be in list
        apps = registry.list_apps()
        app_ids = [a["id"] for a in apps]
        assert "inactive_app" not in app_ids


class TestDynamicAppExecution:
    """Tests for DynamicApp execution via registry."""

    @pytest.mark.asyncio
    async def test_execute_db_app_action(self, registry, repo):
        """Test executing action on DB-loaded app."""
        # Create an app with actual logic
        definition_dict = {
            "app_id": "exec_test_app",
            "name": "Execution Test App",
            "description": "App for testing execution",
            "category": "custom",
            "icon": "🎯",
            "actions": [
                {
                    "name": "add_numbers",
                    "description": "Add two numbers",
                    "parameters": {
                        "a": {"type": "number", "required": True},
                        "b": {"type": "number", "required": True},
                    },
                    "logic": [
                        {"type": "return", "value": {"sum": "params.a + params.b"}}
                    ],
                }
            ],
            "state_schema": [],
            "initial_config": {},
        }

        import uuid
        definition_id = str(uuid.uuid4())
        definition_data = {
            "id": definition_id,
            "app_id": "exec_test_app",
            "name": "Execution Test App",
            "description": "App for testing execution",
            "category": "custom",
            "icon": "🎯",
            "version": 1,
            "definition": definition_dict,
            "is_builtin": False,
            "is_active": True,
        }
        repo.save_app_definition(definition_data)

        # Enable DB fallback
        registry.set_db_enabled(True)

        # Get and initialize app
        app = registry.get("exec_test_app")
        assert app is not None

        await app.initialize("test_sim", ["alice"], {})

        # Execute action
        result = await app.execute("alice", "add_numbers", {"a": 5, "b": 3})

        assert result.success is True
        assert result.data["sum"] == 8
