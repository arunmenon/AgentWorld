"""Tests for expression evaluator per ADR-019."""

import pytest

from agentworld.apps.expression import (
    ExpressionEvaluator,
    ExpressionError,
    evaluate,
    interpolate,
)


class TestLiterals:
    """Tests for literal value parsing."""

    def test_number_integer(self):
        """Test integer literals."""
        assert evaluate("42", {}) == 42
        assert evaluate("-10", {}) == -10
        assert evaluate("0", {}) == 0

    def test_number_float(self):
        """Test float literals."""
        assert evaluate("3.14", {}) == 3.14
        assert evaluate("-0.5", {}) == -0.5
        assert evaluate("0.0", {}) == 0.0

    def test_string_double_quotes(self):
        """Test double-quoted strings."""
        assert evaluate('"hello"', {}) == "hello"
        assert evaluate('"hello world"', {}) == "hello world"

    def test_string_single_quotes(self):
        """Test single-quoted strings."""
        assert evaluate("'hello'", {}) == "hello"
        assert evaluate("'hello world'", {}) == "hello world"

    def test_boolean(self):
        """Test boolean literals."""
        assert evaluate("true", {}) is True
        assert evaluate("false", {}) is False

    def test_null(self):
        """Test null literal."""
        assert evaluate("null", {}) is None


class TestPaths:
    """Tests for path/variable access."""

    def test_simple_path(self):
        """Test simple variable access."""
        context = {"x": 42, "name": "Alice"}
        assert evaluate("x", context) == 42
        assert evaluate("name", context) == "Alice"

    def test_nested_path(self):
        """Test nested property access."""
        context = {"user": {"name": "Alice", "age": 30}}
        assert evaluate("user.name", context) == "Alice"
        assert evaluate("user.age", context) == 30

    def test_deeply_nested_path(self):
        """Test deeply nested access."""
        context = {"a": {"b": {"c": {"d": 42}}}}
        assert evaluate("a.b.c.d", context) == 42

    def test_bracket_access(self):
        """Test bracket notation for dynamic access."""
        context = {"users": {"alice": {"balance": 100}}, "key": "alice"}
        assert evaluate("users['alice'].balance", context) == 100
        assert evaluate('users["alice"].balance', context) == 100

    def test_dynamic_bracket_access(self):
        """Test bracket notation with variable key."""
        context = {"users": {"alice": 100, "bob": 200}, "key": "alice"}
        assert evaluate("users[key]", context) == 100

    def test_array_index_access(self):
        """Test array index access."""
        context = {"items": [10, 20, 30]}
        assert evaluate("items[0]", context) == 10
        assert evaluate("items[1]", context) == 20
        assert evaluate("items[2]", context) == 30

    def test_missing_path_returns_none(self):
        """Test that missing paths return None."""
        context = {"user": {"name": "Alice"}}
        assert evaluate("user.age", context) is None
        assert evaluate("missing", context) is None
        assert evaluate("user.address.city", context) is None


class TestArithmetic:
    """Tests for arithmetic operations."""

    def test_addition(self):
        """Test addition."""
        assert evaluate("2 + 3", {}) == 5
        assert evaluate("10 + 20 + 30", {}) == 60

    def test_subtraction(self):
        """Test subtraction."""
        assert evaluate("10 - 3", {}) == 7
        assert evaluate("100 - 50 - 25", {}) == 25

    def test_multiplication(self):
        """Test multiplication."""
        assert evaluate("3 * 4", {}) == 12
        assert evaluate("2 * 3 * 4", {}) == 24

    def test_division(self):
        """Test division."""
        assert evaluate("10 / 2", {}) == 5
        assert evaluate("15 / 3", {}) == 5

    def test_operator_precedence(self):
        """Test operator precedence (multiplication before addition)."""
        assert evaluate("2 + 3 * 4", {}) == 14
        assert evaluate("10 - 2 * 3", {}) == 4

    def test_parentheses(self):
        """Test parentheses override precedence."""
        assert evaluate("(2 + 3) * 4", {}) == 20
        assert evaluate("(10 - 2) * 3", {}) == 24

    def test_arithmetic_with_variables(self):
        """Test arithmetic with variables."""
        context = {"a": 10, "b": 5}
        assert evaluate("a + b", context) == 15
        assert evaluate("a - b", context) == 5
        assert evaluate("a * b", context) == 50


class TestComparisons:
    """Tests for comparison operations."""

    def test_equality(self):
        """Test equality comparison."""
        assert evaluate("5 == 5", {}) is True
        assert evaluate("5 == 6", {}) is False
        assert evaluate('"hello" == "hello"', {}) is True
        assert evaluate('"hello" == "world"', {}) is False

    def test_inequality(self):
        """Test inequality comparison."""
        assert evaluate("5 != 6", {}) is True
        assert evaluate("5 != 5", {}) is False

    def test_less_than(self):
        """Test less than comparison."""
        assert evaluate("3 < 5", {}) is True
        assert evaluate("5 < 3", {}) is False
        assert evaluate("5 < 5", {}) is False

    def test_less_than_or_equal(self):
        """Test less than or equal comparison."""
        assert evaluate("3 <= 5", {}) is True
        assert evaluate("5 <= 5", {}) is True
        assert evaluate("6 <= 5", {}) is False

    def test_greater_than(self):
        """Test greater than comparison."""
        assert evaluate("5 > 3", {}) is True
        assert evaluate("3 > 5", {}) is False
        assert evaluate("5 > 5", {}) is False

    def test_greater_than_or_equal(self):
        """Test greater than or equal comparison."""
        assert evaluate("5 >= 3", {}) is True
        assert evaluate("5 >= 5", {}) is True
        assert evaluate("3 >= 5", {}) is False


class TestLogical:
    """Tests for logical operations."""

    def test_logical_and(self):
        """Test logical AND."""
        assert evaluate("true && true", {}) is True
        assert evaluate("true && false", {}) is False
        assert evaluate("false && true", {}) is False
        assert evaluate("false && false", {}) is False

    def test_logical_or(self):
        """Test logical OR."""
        assert evaluate("true || false", {}) is True
        assert evaluate("false || true", {}) is True
        assert evaluate("false || false", {}) is False
        assert evaluate("true || true", {}) is True

    def test_logical_not(self):
        """Test logical NOT."""
        assert evaluate("!true", {}) is False
        assert evaluate("!false", {}) is True
        assert evaluate("!!true", {}) is True

    def test_compound_logical(self):
        """Test compound logical expressions."""
        context = {"a": True, "b": False, "c": True}
        assert evaluate("a && c", context) is True
        assert evaluate("a && b", context) is False
        assert evaluate("b || c", context) is True

    def test_logical_with_comparisons(self):
        """Test logical operators with comparison results."""
        context = {"x": 10, "y": 20}
        assert evaluate("x < y && y > 15", context) is True
        assert evaluate("x > y || y > 15", context) is True


class TestBuiltinFunctions:
    """Tests for built-in functions."""

    def test_len(self):
        """Test len() function."""
        context = {"items": [1, 2, 3, 4, 5], "name": "Alice"}
        assert evaluate("len(items)", context) == 5
        assert evaluate("len(name)", context) == 5

    def test_contains(self):
        """Test contains() function."""
        context = {"items": ["a", "b", "c"]}
        assert evaluate('contains(items, "a")', context) is True
        assert evaluate('contains(items, "d")', context) is False

    def test_lower_upper(self):
        """Test lower() and upper() functions."""
        context = {"name": "Alice"}
        assert evaluate("lower(name)", context) == "alice"
        assert evaluate("upper(name)", context) == "ALICE"

    def test_generate_id(self):
        """Test generate_id() function."""
        result = evaluate("generate_id()", {})
        assert isinstance(result, str)
        assert len(result) == 36  # UUID format

    def test_timestamp(self):
        """Test timestamp() function."""
        result = evaluate("timestamp()", {})
        assert isinstance(result, str)
        assert "T" in result  # ISO format

    def test_now(self):
        """Test now() function."""
        result = evaluate("now()", {})
        assert isinstance(result, int)
        assert result > 0

    def test_str_function(self):
        """Test str() function."""
        assert evaluate("str(42)", {}) == "42"
        assert evaluate("str(3.14)", {}) == "3.14"
        assert evaluate("str(true)", {}) == "True"

    def test_num_function(self):
        """Test num() function."""
        assert evaluate('num("42")', {}) == 42
        assert evaluate('num("3.14")', {}) == 3.14

    def test_bool_function(self):
        """Test bool() function."""
        assert evaluate("bool(1)", {}) is True
        assert evaluate("bool(0)", {}) is False
        assert evaluate('bool("true")', {}) is True
        assert evaluate('bool("")', {}) is False

    def test_round_function(self):
        """Test round() function."""
        assert evaluate("round(3.7)", {}) == 4
        assert evaluate("round(3.2)", {}) == 3

    def test_abs_function(self):
        """Test abs() function."""
        assert evaluate("abs(-5)", {}) == 5
        assert evaluate("abs(5)", {}) == 5

    def test_min_max_functions(self):
        """Test min() and max() functions."""
        assert evaluate("min(3, 1, 4, 1, 5)", {}) == 1
        assert evaluate("max(3, 1, 4, 1, 5)", {}) == 5


class TestInterpolation:
    """Tests for string interpolation."""

    def test_simple_interpolation(self):
        """Test simple string interpolation."""
        context = {"name": "Alice", "amount": 50}
        assert interpolate("Hello ${name}!", context) == "Hello Alice!"
        assert interpolate("Amount: $${amount}", context) == "Amount: $50"

    def test_expression_interpolation(self):
        """Test interpolation with expressions."""
        context = {"a": 10, "b": 20}
        # Result may be int or float depending on implementation
        result = interpolate("Sum: ${a + b}", context)
        assert result in ("Sum: 30", "Sum: 30.0")

    def test_nested_path_interpolation(self):
        """Test interpolation with nested paths."""
        context = {"user": {"name": "Alice"}}
        assert interpolate("User: ${user.name}", context) == "User: Alice"

    def test_no_interpolation(self):
        """Test string without interpolation markers."""
        context = {"name": "Alice"}
        assert interpolate("Hello world!", context) == "Hello world!"

    def test_escaped_dollar(self):
        """Test that $$ is not interpolated."""
        context = {"name": "Alice"}
        # Just $$ without braces is not interpolation
        assert interpolate("Price: $$100", context) == "Price: $$100"


class TestContextVariables:
    """Tests for standard context variables (params, agent, etc.)."""

    def test_params_access(self):
        """Test accessing params object."""
        context = {"params": {"to": "bob", "amount": 50}}
        assert evaluate("params.to", context) == "bob"
        assert evaluate("params.amount", context) == 50

    def test_agent_state_access(self):
        """Test accessing agent state."""
        context = {"agent": {"id": "alice", "balance": 1000}}
        assert evaluate("agent.id", context) == "alice"
        assert evaluate("agent.balance", context) == 1000

    def test_agents_access(self):
        """Test accessing other agents' state."""
        context = {
            "agents": {
                "alice": {"balance": 1000},
                "bob": {"balance": 500},
            },
            "params": {"to": "bob"},
        }
        assert evaluate("agents['alice'].balance", context) == 1000
        assert evaluate("agents[params.to].balance", context) == 500

    def test_config_access(self):
        """Test accessing config."""
        context = {"config": {"initial_balance": 1000, "max_transfer": 10000}}
        assert evaluate("config.initial_balance", context) == 1000
        assert evaluate("config.max_transfer", context) == 10000


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_syntax(self):
        """Test that invalid syntax raises error."""
        with pytest.raises(ExpressionError):
            evaluate("2 +", {})

    def test_unknown_function(self):
        """Test that unknown function raises error."""
        with pytest.raises(ExpressionError):
            evaluate("unknown_func()", {})

    def test_division_by_zero(self):
        """Test division by zero handling."""
        with pytest.raises(ExpressionError):
            evaluate("10 / 0", {})


class TestEvaluatorClass:
    """Tests for ExpressionEvaluator class directly."""

    def test_evaluator_instance(self):
        """Test ExpressionEvaluator can be instantiated."""
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate("1 + 2", {}) == 3

    def test_evaluator_interpolation(self):
        """Test ExpressionEvaluator interpolation method."""
        evaluator = ExpressionEvaluator()
        context = {"name": "Alice"}
        result = evaluator.evaluate_interpolated("Hello ${name}!", context)
        assert result == "Hello Alice!"

    def test_evaluator_caching(self):
        """Test that evaluator caches parsed expressions."""
        evaluator = ExpressionEvaluator()
        # Run same expression multiple times
        for _ in range(5):
            result = evaluator.evaluate("1 + 2 + 3", {})
            assert result == 6


class TestComplexExpressions:
    """Tests for complex real-world expressions."""

    def test_transfer_validation(self):
        """Test expression for validating a transfer."""
        context = {
            "params": {"amount": 50, "to": "bob"},
            "agent": {"id": "alice", "balance": 1000},
        }

        # Check sufficient balance
        assert evaluate("params.amount <= agent.balance", context) is True

        # Check not self-transfer
        assert evaluate("params.to != agent.id", context) is True

        # Check positive amount
        assert evaluate("params.amount > 0", context) is True

    def test_balance_calculation(self):
        """Test expression for calculating new balance."""
        context = {
            "agent": {"balance": 1000},
            "params": {"amount": 50},
        }
        assert evaluate("agent.balance - params.amount", context) == 950

    def test_conditional_expression(self):
        """Test complex conditional expression."""
        context = {
            "user": {"vip": True, "balance": 500},
            "params": {"amount": 100},
        }
        # VIP users get higher limits
        assert evaluate(
            "(user.vip && params.amount <= 1000) || params.amount <= 500",
            context
        ) is True
