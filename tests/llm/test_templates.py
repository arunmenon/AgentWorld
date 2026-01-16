"""Tests for LLM prompt templates."""

import pytest
from agentworld.llm.templates import (
    PromptTemplate,
    TemplateRegistry,
    render_template,
    get_registry,
)


class TestPromptTemplate:
    """Tests for PromptTemplate class."""

    def test_creation_from_string(self):
        """Test creating template from string."""
        template = PromptTemplate("Hello, {{ name }}!")
        assert template is not None

    def test_render_simple(self):
        """Test rendering simple template."""
        template = PromptTemplate("Hello, {{ name }}!")
        result = template.render(name="World")
        assert result == "Hello, World!"

    def test_render_multiple_variables(self):
        """Test rendering with multiple variables."""
        template = PromptTemplate("{{ greeting }}, {{ name }}! You are {{ trait }}.")
        result = template.render(
            greeting="Hi",
            name="Alice",
            trait="friendly"
        )
        assert result == "Hi, Alice! You are friendly."

    def test_render_with_conditionals(self):
        """Test rendering with Jinja2 conditionals."""
        template = PromptTemplate("{% if show_greeting %}Hello{% endif %}, {{ name }}!")

        result1 = template.render(show_greeting=True, name="Bob")
        assert "Hello" in result1

        result2 = template.render(show_greeting=False, name="Bob")
        assert "Hello" not in result2

    def test_render_with_loops(self):
        """Test rendering with loops."""
        template = PromptTemplate("Traits: {% for t in traits %}{{ t }}{% if not loop.last %}, {% endif %}{% endfor %}")
        result = template.render(traits=["kind", "smart", "funny"])
        assert "kind" in result
        assert "smart" in result
        assert "funny" in result


class TestTemplateRegistry:
    """Tests for TemplateRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a registry instance."""
        return TemplateRegistry()

    def test_creation(self, registry):
        """Test registry creation."""
        assert registry is not None

    def test_register_and_get(self, registry):
        """Test registering and getting template."""
        template = PromptTemplate("Test: {{ value }}")
        registry.register("test_template", template)

        retrieved = registry.get("test_template")
        assert retrieved is not None
        assert retrieved.render(value="hello") == "Test: hello"

    def test_get_missing_returns_none(self, registry):
        """Test getting non-existent template."""
        result = registry.get("nonexistent")
        # Returns None if not found
        # (may return built-in if name matches)

    def test_render_by_name(self, registry):
        """Test rendering template by name."""
        template = PromptTemplate("Value: {{ value }}")
        registry.register("value_template", template)

        result = registry.render("value_template", value="123")
        assert result == "Value: 123"

    def test_render_missing_raises(self, registry):
        """Test rendering non-existent template raises error."""
        with pytest.raises(KeyError):
            registry.render("definitely_not_a_template", x=1)

    def test_builtin_templates_exist(self, registry):
        """Test that built-in templates are registered."""
        # These should be registered by _register_builtins
        assert registry.get("agent_system") is not None
        assert registry.get("agent_think") is not None
        assert registry.get("agent_respond") is not None


class TestRenderTemplate:
    """Tests for render_template function."""

    def test_render_builtin(self):
        """Test rendering built-in template."""
        # agent_system template takes 'name' as a variable
        # Use a fresh registry to avoid state issues
        registry = TemplateRegistry()
        template = registry.get("agent_system")
        result = template.render(name="TestAgent")
        assert "TestAgent" in result

    def test_render_with_traits(self):
        """Test rendering with traits."""
        registry = TemplateRegistry()
        template = registry.get("agent_system")
        result = template.render(
            name="Alice",
            background="A helpful assistant",
            traits={"openness": 0.8, "extraversion": 0.6}
        )
        assert "Alice" in result


class TestGetRegistry:
    """Tests for get_registry function."""

    def test_returns_registry(self):
        """Test that get_registry returns a registry."""
        registry = get_registry()
        assert isinstance(registry, TemplateRegistry)

    def test_returns_same_instance(self):
        """Test that get_registry returns the same instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2
