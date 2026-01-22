"""Action directive parser for simulated apps.

This module parses APP_ACTION directives from agent messages
per ADR-017.

Syntax:
    APP_ACTION: <app_id>.<action_name>(<param1>=<value1>, <param2>=<value2>)

Examples:
    APP_ACTION: paypal.transfer(to="bob@email.com", amount=50.00, note="Dinner")
    APP_ACTION: paypal.check_balance()
    APP_ACTION: amazon.search_products(query="laptop", max_price=1000)
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedAction:
    """A parsed action directive."""

    app_id: str
    action: str
    params: dict[str, Any]
    raw_text: str
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "action": self.action,
            "params": self.params,
            "raw_text": self.raw_text,
            "line_number": self.line_number,
        }


@dataclass
class ParseError:
    """An error encountered during parsing."""

    message: str
    raw_text: str
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "raw_text": self.raw_text,
            "line_number": self.line_number,
        }


@dataclass
class ParseResult:
    """Result of parsing a message for actions."""

    actions: list[ParsedAction]
    errors: list[ParseError]
    message_without_actions: str

    @property
    def has_actions(self) -> bool:
        """Check if any actions were found."""
        return len(self.actions) > 0

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0


# Pattern to match APP_ACTION directives
# Matches: APP_ACTION: app_id.action(params)
ACTION_PATTERN = re.compile(
    r"APP_ACTION:\s*"  # Prefix
    r"(\w+)\."  # App ID (captured)
    r"(\w+)"  # Action name (captured)
    r"\(([^)]*)\)",  # Parameters in parentheses (captured)
    re.IGNORECASE,
)

# Pattern to match full line containing APP_ACTION
ACTION_LINE_PATTERN = re.compile(
    r"^.*APP_ACTION:\s*\w+\.\w+\([^)]*\).*$",
    re.IGNORECASE | re.MULTILINE,
)

# Pattern to detect any APP_ACTION: prefix (for error detection)
APP_ACTION_PREFIX = re.compile(r"APP_ACTION:", re.IGNORECASE)


def parse_value(value_str: str) -> Any:
    """Parse a parameter value string into a Python value.

    Handles:
    - Strings (quoted)
    - Numbers (int and float)
    - Booleans
    - None/null

    Args:
        value_str: Value string to parse

    Returns:
        Parsed Python value
    """
    value_str = value_str.strip()

    # Empty string
    if not value_str:
        return ""

    # Try literal eval for Python literals (strings, numbers, lists, etc.)
    try:
        return ast.literal_eval(value_str)
    except (ValueError, SyntaxError):
        pass

    # Check for boolean-like values
    lower = value_str.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    if lower in ("null", "none"):
        return None

    # Try as number
    try:
        if "." in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Return as string (strip quotes if present)
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]

    return value_str


def parse_params(params_str: str) -> dict[str, Any]:
    """Parse parameter string into dictionary.

    Handles:
    - key=value pairs
    - key="value with spaces"
    - key=123 (numbers)
    - Empty params

    Args:
        params_str: Parameters string from inside parentheses

    Returns:
        Dictionary of parameter name -> value
    """
    params: dict[str, Any] = {}

    if not params_str.strip():
        return params

    # State machine for parsing
    current_key = ""
    current_value = ""
    in_string = False
    string_char = None
    depth = 0
    mode = "key"  # "key" or "value"

    i = 0
    while i < len(params_str):
        char = params_str[i]

        if in_string:
            current_value += char
            if char == string_char and (i == 0 or params_str[i - 1] != "\\"):
                in_string = False
        elif char in ('"', "'"):
            in_string = True
            string_char = char
            current_value += char
        elif char in ("[", "{", "("):
            depth += 1
            if mode == "value":
                current_value += char
        elif char in ("]", "}", ")"):
            depth -= 1
            if mode == "value":
                current_value += char
        elif char == "=" and mode == "key" and depth == 0:
            mode = "value"
        elif char == "," and depth == 0:
            # End of parameter
            if current_key.strip():
                params[current_key.strip()] = parse_value(current_value)
            current_key = ""
            current_value = ""
            mode = "key"
        else:
            if mode == "key":
                current_key += char
            else:
                current_value += char

        i += 1

    # Handle last parameter
    if current_key.strip():
        params[current_key.strip()] = parse_value(current_value)

    return params


def parse_action_directive(text: str, line_number: int | None = None) -> ParsedAction | ParseError:
    """Parse a single APP_ACTION directive.

    Args:
        text: Text containing the directive
        line_number: Optional line number for error reporting

    Returns:
        ParsedAction or ParseError
    """
    match = ACTION_PATTERN.search(text)
    if not match:
        return ParseError(
            message="Invalid action directive syntax",
            raw_text=text,
            line_number=line_number,
        )

    app_id = match.group(1).lower()
    action = match.group(2)
    params_str = match.group(3)

    try:
        params = parse_params(params_str)
    except Exception as e:
        return ParseError(
            message=f"Failed to parse parameters: {str(e)}",
            raw_text=text,
            line_number=line_number,
        )

    return ParsedAction(
        app_id=app_id,
        action=action,
        params=params,
        raw_text=match.group(0),
        line_number=line_number,
    )


def parse_message(message: str) -> ParseResult:
    """Parse a message for APP_ACTION directives.

    Extracts all action directives from the message and returns
    both the parsed actions and the message with actions removed.

    Args:
        message: Agent message text

    Returns:
        ParseResult with actions, errors, and cleaned message
    """
    actions: list[ParsedAction] = []
    errors: list[ParseError] = []

    # Find all action directives
    lines = message.split("\n")
    action_lines = set()

    for line_num, line in enumerate(lines, 1):
        # Check if this line has APP_ACTION: prefix
        has_prefix = APP_ACTION_PREFIX.search(line)

        # Find all valid action matches in this line
        matches = list(ACTION_PATTERN.finditer(line))

        if matches:
            # Process valid matches
            for match in matches:
                result = parse_action_directive(match.group(0), line_number=line_num)
                if isinstance(result, ParsedAction):
                    actions.append(result)
                else:
                    errors.append(result)
            action_lines.add(line_num - 1)  # 0-indexed for removal
        elif has_prefix:
            # Line has APP_ACTION: but didn't match valid pattern - it's an error
            errors.append(ParseError(
                message="Invalid action directive syntax",
                raw_text=line.strip(),
                line_number=line_num,
            ))
            action_lines.add(line_num - 1)  # Also remove malformed action lines

    # Remove action lines from message
    cleaned_lines = [
        line for i, line in enumerate(lines)
        if i not in action_lines
    ]
    message_without_actions = "\n".join(cleaned_lines).strip()

    return ParseResult(
        actions=actions,
        errors=errors,
        message_without_actions=message_without_actions,
    )


def extract_actions(message: str) -> list[ParsedAction]:
    """Extract just the actions from a message (convenience function).

    Args:
        message: Agent message text

    Returns:
        List of parsed actions (ignoring errors)
    """
    result = parse_message(message)
    return result.actions


def format_action(app_id: str, action: str, params: dict[str, Any]) -> str:
    """Format an action directive string.

    Useful for generating action directives programmatically.

    Args:
        app_id: App ID
        action: Action name
        params: Action parameters

    Returns:
        Formatted action directive string
    """
    param_parts = []
    for key, value in params.items():
        if isinstance(value, str):
            param_parts.append(f'{key}="{value}"')
        else:
            param_parts.append(f"{key}={value}")

    params_str = ", ".join(param_parts)
    return f"APP_ACTION: {app_id}.{action}({params_str})"
