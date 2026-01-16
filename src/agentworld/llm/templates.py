"""Prompt template system using Jinja2."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, BaseLoader, Template


class PromptTemplate:
    """A Jinja2-based prompt template."""

    def __init__(self, template: str | Template):
        """Initialize with a template string or Jinja2 Template.

        Args:
            template: Template string or compiled Template
        """
        if isinstance(template, str):
            self._template = Environment(loader=BaseLoader()).from_string(template)
        else:
            self._template = template

    def render(self, **kwargs: Any) -> str:
        """Render the template with given variables.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered template string
        """
        return self._template.render(**kwargs)

    @classmethod
    def from_file(cls, path: str | Path) -> "PromptTemplate":
        """Load a template from a file.

        Args:
            path: Path to template file

        Returns:
            PromptTemplate instance
        """
        path = Path(path)
        with open(path) as f:
            return cls(f.read())


class TemplateRegistry:
    """Registry for managing prompt templates."""

    def __init__(self, template_dir: str | Path | None = None):
        """Initialize the registry.

        Args:
            template_dir: Directory containing template files
        """
        self._templates: dict[str, PromptTemplate] = {}
        self._env: Environment | None = None

        if template_dir:
            template_dir = Path(template_dir)
            if template_dir.exists():
                self._env = Environment(
                    loader=FileSystemLoader(str(template_dir)),
                    trim_blocks=True,
                    lstrip_blocks=True,
                )

        # Register built-in templates
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in templates."""
        self.register("agent_system", PromptTemplate(AGENT_SYSTEM_TEMPLATE))
        self.register("agent_think", PromptTemplate(AGENT_THINK_TEMPLATE))
        self.register("agent_respond", PromptTemplate(AGENT_RESPOND_TEMPLATE))

    def register(self, name: str, template: PromptTemplate) -> None:
        """Register a template.

        Args:
            name: Template name
            template: PromptTemplate instance
        """
        self._templates[name] = template

    def get(self, name: str) -> PromptTemplate | None:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            PromptTemplate or None if not found
        """
        # Check registered templates first
        if name in self._templates:
            return self._templates[name]

        # Try loading from file system
        if self._env:
            try:
                jinja_template = self._env.get_template(f"{name}.jinja2")
                template = PromptTemplate(jinja_template)
                self._templates[name] = template
                return template
            except Exception:
                pass

        return None

    def render(self, name: str, **kwargs: Any) -> str:
        """Render a template by name.

        Args:
            name: Template name
            **kwargs: Template variables

        Returns:
            Rendered template string

        Raises:
            KeyError: If template not found
        """
        template = self.get(name)
        if template is None:
            raise KeyError(f"Template not found: {name}")
        return template.render(**kwargs)


# Built-in templates
AGENT_SYSTEM_TEMPLATE = """You are {{ name }}, a participant in a conversation.

{% if background %}
Background: {{ background }}
{% endif %}

{% if traits %}
Your personality traits:
{% for trait, value in traits.items() %}
- {{ trait }}: {{ "%.1f"|format(value) }}/1.0
{% endfor %}
{% endif %}

{% if trait_description %}
Personality: {{ trait_description }}
{% endif %}

Respond naturally and stay in character. Be concise but thoughtful.
"""

AGENT_THINK_TEMPLATE = """Given the following context, what are your thoughts?

Context:
{{ context }}

{% if recent_messages %}
Recent conversation:
{% for msg in recent_messages %}
{{ msg.sender }}: {{ msg.content }}
{% endfor %}
{% endif %}

Respond with your genuine thoughts and perspective based on your personality.
"""

AGENT_RESPOND_TEMPLATE = """You received a message from {{ sender }}:

"{{ message }}"

{% if context %}
Context from the conversation:
{{ context }}
{% endif %}

Respond naturally as {{ name }}. Be conversational and stay in character.
"""


# Global registry
_registry: TemplateRegistry | None = None


def get_registry() -> TemplateRegistry:
    """Get or create the global template registry."""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry


def render_template(name: str, **kwargs: Any) -> str:
    """Render a template using the global registry.

    Args:
        name: Template name
        **kwargs: Template variables

    Returns:
        Rendered template string
    """
    return get_registry().render(name, **kwargs)
