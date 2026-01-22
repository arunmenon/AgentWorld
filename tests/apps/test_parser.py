"""Tests for action directive parser per ADR-017."""

import pytest

from agentworld.apps.parser import (
    parse_message,
    parse_action_directive,
    extract_actions,
    format_action,
    parse_value,
    parse_params,
    ParsedAction,
    ParseError,
)


class TestParseValue:
    """Tests for value parsing."""

    def test_parse_string_double_quotes(self):
        """Test parsing double-quoted strings."""
        assert parse_value('"hello world"') == "hello world"

    def test_parse_string_single_quotes(self):
        """Test parsing single-quoted strings."""
        assert parse_value("'hello world'") == "hello world"

    def test_parse_integer(self):
        """Test parsing integers."""
        assert parse_value("42") == 42
        assert parse_value("-10") == -10

    def test_parse_float(self):
        """Test parsing floats."""
        assert parse_value("3.14") == 3.14
        assert parse_value("-0.5") == -0.5

    def test_parse_boolean(self):
        """Test parsing booleans."""
        assert parse_value("true") is True
        assert parse_value("True") is True
        assert parse_value("false") is False
        assert parse_value("False") is False

    def test_parse_null(self):
        """Test parsing null values."""
        assert parse_value("null") is None
        assert parse_value("None") is None

    def test_parse_unquoted_string(self):
        """Test parsing unquoted strings."""
        assert parse_value("hello") == "hello"


class TestParseParams:
    """Tests for parameter parsing."""

    def test_empty_params(self):
        """Test parsing empty parameters."""
        assert parse_params("") == {}
        assert parse_params("  ") == {}

    def test_single_param(self):
        """Test parsing single parameter."""
        assert parse_params('to="bob"') == {"to": "bob"}
        assert parse_params("amount=50") == {"amount": 50}

    def test_multiple_params(self):
        """Test parsing multiple parameters."""
        result = parse_params('to="bob", amount=50, note="test"')
        assert result == {"to": "bob", "amount": 50, "note": "test"}

    def test_params_with_spaces(self):
        """Test parsing parameters with spaces."""
        result = parse_params('to = "bob" , amount = 50')
        assert result["to"] == "bob"
        assert result["amount"] == 50

    def test_params_with_special_chars_in_string(self):
        """Test parsing strings with special characters."""
        result = parse_params('note="Hello, World! How are you?"')
        assert result["note"] == "Hello, World! How are you?"


class TestParseActionDirective:
    """Tests for single action directive parsing."""

    def test_simple_action(self):
        """Test parsing simple action."""
        result = parse_action_directive("APP_ACTION: paypal.check_balance()")
        assert isinstance(result, ParsedAction)
        assert result.app_id == "paypal"
        assert result.action == "check_balance"
        assert result.params == {}

    def test_action_with_params(self):
        """Test parsing action with parameters."""
        result = parse_action_directive(
            'APP_ACTION: paypal.transfer(to="bob", amount=50)'
        )
        assert isinstance(result, ParsedAction)
        assert result.app_id == "paypal"
        assert result.action == "transfer"
        assert result.params["to"] == "bob"
        assert result.params["amount"] == 50

    def test_action_case_insensitive_prefix(self):
        """Test that APP_ACTION prefix is case-insensitive."""
        result = parse_action_directive("app_action: paypal.check_balance()")
        assert isinstance(result, ParsedAction)
        assert result.app_id == "paypal"

    def test_action_with_extra_text(self):
        """Test parsing action embedded in text."""
        result = parse_action_directive(
            "Sure, let me do that. APP_ACTION: paypal.check_balance()"
        )
        assert isinstance(result, ParsedAction)
        assert result.action == "check_balance"

    def test_invalid_syntax(self):
        """Test parsing invalid syntax."""
        result = parse_action_directive("APP_ACTION: invalid")
        assert isinstance(result, ParseError)
        assert "syntax" in result.message.lower()


class TestParseMessage:
    """Tests for full message parsing."""

    def test_message_without_actions(self):
        """Test message with no actions."""
        result = parse_message("Hello, how are you?")
        assert result.has_actions is False
        assert len(result.actions) == 0
        assert result.message_without_actions == "Hello, how are you?"

    def test_message_with_single_action(self):
        """Test message with one action."""
        message = """Sure, let me check my balance.
APP_ACTION: paypal.check_balance()
There you go!"""

        result = parse_message(message)
        assert result.has_actions is True
        assert len(result.actions) == 1
        assert result.actions[0].action == "check_balance"
        assert "APP_ACTION" not in result.message_without_actions
        assert "check my balance" in result.message_without_actions
        assert "There you go" in result.message_without_actions

    def test_message_with_multiple_actions(self):
        """Test message with multiple actions."""
        message = """Let me transfer some money.
APP_ACTION: paypal.transfer(to="bob", amount=25)
And also check my balance.
APP_ACTION: paypal.check_balance()"""

        result = parse_message(message)
        assert result.has_actions is True
        assert len(result.actions) == 2
        assert result.actions[0].action == "transfer"
        assert result.actions[1].action == "check_balance"

    def test_message_with_action_errors(self):
        """Test message with invalid action syntax."""
        message = """APP_ACTION: invalid
APP_ACTION: paypal.check_balance()"""

        result = parse_message(message)
        assert result.has_actions is True
        assert result.has_errors is True
        assert len(result.actions) == 1
        assert len(result.errors) == 1


class TestExtractActions:
    """Tests for extract_actions convenience function."""

    def test_extract_actions(self):
        """Test extracting actions from message."""
        message = """Hello!
APP_ACTION: paypal.check_balance()
Goodbye!"""

        actions = extract_actions(message)
        assert len(actions) == 1
        assert actions[0].action == "check_balance"


class TestFormatAction:
    """Tests for format_action helper."""

    def test_format_action_no_params(self):
        """Test formatting action without parameters."""
        result = format_action("paypal", "check_balance", {})
        assert result == "APP_ACTION: paypal.check_balance()"

    def test_format_action_with_params(self):
        """Test formatting action with parameters."""
        result = format_action("paypal", "transfer", {"to": "bob", "amount": 50})
        assert "APP_ACTION: paypal.transfer(" in result
        assert 'to="bob"' in result
        assert "amount=50" in result

    def test_format_action_roundtrip(self):
        """Test that formatted action can be parsed back."""
        original = {"to": "bob", "amount": 100.5, "note": "test"}
        formatted = format_action("paypal", "transfer", original)

        result = parse_action_directive(formatted)
        assert isinstance(result, ParsedAction)
        assert result.app_id == "paypal"
        assert result.action == "transfer"
        assert result.params["to"] == "bob"
        assert result.params["amount"] == 100.5
        assert result.params["note"] == "test"
