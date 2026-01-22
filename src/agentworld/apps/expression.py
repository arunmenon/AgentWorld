"""Expression evaluator for dynamic app logic.

This module implements the expression language defined in ADR-019,
supporting path access, operators, function calls, and interpolation.

Operator precedence (highest to lowest):
1. () parentheses
2. . [] property access
3. () function call
4. ! unary not, - unary minus
5. * / multiplication/division
6. + - addition/subtraction
7. < > <= >= comparison
8. == != equality
9. && logical and
10. || logical or
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Callable


# ==============================================================================
# Errors
# ==============================================================================


class ExpressionError(Exception):
    """Error during expression evaluation."""

    pass


class ParseError(ExpressionError):
    """Error during expression parsing."""

    pass


# ==============================================================================
# Tokens
# ==============================================================================


class TokenType(Enum):
    """Token types for the expression lexer."""

    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"

    # Identifiers
    IDENTIFIER = "IDENTIFIER"

    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    AND = "&&"
    OR = "||"
    NOT = "!"

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    DOT = "."
    COMMA = ","
    COLON = ":"
    LBRACE = "{"
    RBRACE = "}"

    # Special
    EOF = "EOF"


@dataclass
class Token:
    """A lexical token."""

    type: TokenType
    value: Any
    position: int


# ==============================================================================
# Lexer
# ==============================================================================


class Lexer:
    """Tokenizes expression strings."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0

    def tokenize(self) -> list[Token]:
        """Tokenize the source string."""
        tokens = []
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break

            token = self._next_token()
            if token:
                tokens.append(token)

        tokens.append(Token(TokenType.EOF, None, self.pos))
        return tokens

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < len(self.source) and self.source[self.pos] in " \t\n\r":
            self.pos += 1

    def _next_token(self) -> Token | None:
        """Get the next token."""
        ch = self.source[self.pos]
        start = self.pos

        # Two-character operators
        if self.pos + 1 < len(self.source):
            two_char = self.source[self.pos : self.pos + 2]
            if two_char == "==":
                self.pos += 2
                return Token(TokenType.EQ, "==", start)
            elif two_char == "!=":
                self.pos += 2
                return Token(TokenType.NE, "!=", start)
            elif two_char == "<=":
                self.pos += 2
                return Token(TokenType.LE, "<=", start)
            elif two_char == ">=":
                self.pos += 2
                return Token(TokenType.GE, ">=", start)
            elif two_char == "&&":
                self.pos += 2
                return Token(TokenType.AND, "&&", start)
            elif two_char == "||":
                self.pos += 2
                return Token(TokenType.OR, "||", start)

        # Single-character operators and delimiters
        single_char_tokens = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "!": TokenType.NOT,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ".": TokenType.DOT,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
        }

        if ch in single_char_tokens:
            self.pos += 1
            return Token(single_char_tokens[ch], ch, start)

        # Numbers
        if ch.isdigit() or (ch == "." and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
            return self._read_number()

        # Strings
        if ch == '"' or ch == "'":
            return self._read_string(ch)

        # Backtick strings (template literals)
        if ch == "`":
            return self._read_template_string()

        # Identifiers and keywords
        if ch.isalpha() or ch == "_":
            return self._read_identifier()

        raise ParseError(f"Unexpected character '{ch}' at position {self.pos}")

    def _read_number(self) -> Token:
        """Read a numeric literal."""
        start = self.pos
        has_dot = False

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isdigit():
                self.pos += 1
            elif ch == "." and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break

        value_str = self.source[start : self.pos]
        value = float(value_str) if has_dot else int(value_str)
        return Token(TokenType.NUMBER, value, start)

    def _read_string(self, quote: str) -> Token:
        """Read a string literal."""
        start = self.pos
        self.pos += 1  # Skip opening quote
        result = []

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == quote:
                self.pos += 1
                return Token(TokenType.STRING, "".join(result), start)
            elif ch == "\\":
                self.pos += 1
                if self.pos < len(self.source):
                    escape_ch = self.source[self.pos]
                    escape_map = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", quote: quote}
                    result.append(escape_map.get(escape_ch, escape_ch))
                    self.pos += 1
            else:
                result.append(ch)
                self.pos += 1

        raise ParseError(f"Unterminated string starting at position {start}")

    def _read_template_string(self) -> Token:
        """Read a template string (backtick).

        Template strings support ${expression} interpolation.
        We return them as STRING tokens; interpolation is handled later.
        """
        start = self.pos
        self.pos += 1  # Skip opening backtick
        result = []

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == "`":
                self.pos += 1
                return Token(TokenType.STRING, "".join(result), start)
            elif ch == "\\":
                self.pos += 1
                if self.pos < len(self.source):
                    result.append(self.source[self.pos])
                    self.pos += 1
            else:
                result.append(ch)
                self.pos += 1

        raise ParseError(f"Unterminated template string starting at position {start}")

    def _read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start = self.pos

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isalnum() or ch == "_":
                self.pos += 1
            else:
                break

        value = self.source[start : self.pos]

        # Check for keywords
        if value == "true":
            return Token(TokenType.BOOLEAN, True, start)
        elif value == "false":
            return Token(TokenType.BOOLEAN, False, start)
        elif value == "null":
            return Token(TokenType.NULL, None, start)

        return Token(TokenType.IDENTIFIER, value, start)


# ==============================================================================
# Parser
# ==============================================================================


class Parser:
    """Recursive descent parser for expressions."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Any:
        """Parse and return an AST node."""
        result = self._parse_or()
        if self.current().type != TokenType.EOF:
            raise ParseError(f"Unexpected token after expression: {self.current()}")
        return result

    def current(self) -> Token:
        """Get current token."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        """Advance to next token and return previous."""
        token = self.current()
        self.pos += 1
        return token

    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current().type in types

    def expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type."""
        if self.current().type != token_type:
            raise ParseError(f"Expected {token_type}, got {self.current().type}")
        return self.advance()

    # Precedence levels (lowest to highest)

    def _parse_or(self) -> Any:
        """Parse || (lowest precedence)."""
        left = self._parse_and()
        while self.match(TokenType.OR):
            self.advance()
            right = self._parse_and()
            left = ("or", left, right)
        return left

    def _parse_and(self) -> Any:
        """Parse &&."""
        left = self._parse_equality()
        while self.match(TokenType.AND):
            self.advance()
            right = self._parse_equality()
            left = ("and", left, right)
        return left

    def _parse_equality(self) -> Any:
        """Parse == !=."""
        left = self._parse_comparison()
        while self.match(TokenType.EQ, TokenType.NE):
            op = self.advance()
            right = self._parse_comparison()
            left = ("eq" if op.type == TokenType.EQ else "ne", left, right)
        return left

    def _parse_comparison(self) -> Any:
        """Parse < > <= >=."""
        left = self._parse_additive()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op = self.advance()
            right = self._parse_additive()
            op_map = {
                TokenType.LT: "lt",
                TokenType.GT: "gt",
                TokenType.LE: "le",
                TokenType.GE: "ge",
            }
            left = (op_map[op.type], left, right)
        return left

    def _parse_additive(self) -> Any:
        """Parse + -."""
        left = self._parse_multiplicative()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self._parse_multiplicative()
            left = ("add" if op.type == TokenType.PLUS else "sub", left, right)
        return left

    def _parse_multiplicative(self) -> Any:
        """Parse * /."""
        left = self._parse_unary()
        while self.match(TokenType.STAR, TokenType.SLASH):
            op = self.advance()
            right = self._parse_unary()
            left = ("mul" if op.type == TokenType.STAR else "div", left, right)
        return left

    def _parse_unary(self) -> Any:
        """Parse ! and unary -."""
        if self.match(TokenType.NOT):
            self.advance()
            operand = self._parse_unary()
            return ("not", operand)
        if self.match(TokenType.MINUS):
            self.advance()
            operand = self._parse_unary()
            return ("neg", operand)
        return self._parse_postfix()

    def _parse_postfix(self) -> Any:
        """Parse . [] and ()."""
        left = self._parse_primary()

        while True:
            if self.match(TokenType.DOT):
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    raise ParseError("Expected identifier after '.'")
                prop = self.advance().value
                left = ("get", left, ("literal", prop))
            elif self.match(TokenType.LBRACKET):
                self.advance()
                index = self._parse_or()
                self.expect(TokenType.RBRACKET)
                left = ("get", left, index)
            elif self.match(TokenType.LPAREN):
                # Function call
                if isinstance(left, tuple) and left[0] == "var":
                    func_name = left[1]
                    self.advance()
                    args = self._parse_args()
                    self.expect(TokenType.RPAREN)
                    left = ("call", func_name, args)
                else:
                    break
            else:
                break

        return left

    def _parse_args(self) -> list[Any]:
        """Parse function arguments."""
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self._parse_or())
            while self.match(TokenType.COMMA):
                self.advance()
                args.append(self._parse_or())
        return args

    def _parse_primary(self) -> Any:
        """Parse primary expressions (literals, identifiers, parenthesized)."""
        token = self.current()

        if token.type == TokenType.NUMBER:
            self.advance()
            return ("literal", token.value)

        if token.type == TokenType.STRING:
            self.advance()
            return ("literal", token.value)

        if token.type == TokenType.BOOLEAN:
            self.advance()
            return ("literal", token.value)

        if token.type == TokenType.NULL:
            self.advance()
            return ("literal", None)

        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return ("var", token.value)

        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self._parse_or()
            self.expect(TokenType.RPAREN)
            return expr

        if token.type == TokenType.LBRACE:
            return self._parse_object()

        if token.type == TokenType.LBRACKET:
            return self._parse_array()

        raise ParseError(f"Unexpected token: {token}")

    def _parse_object(self) -> Any:
        """Parse object literal { key: value, ... }."""
        self.expect(TokenType.LBRACE)
        pairs = []

        if not self.match(TokenType.RBRACE):
            # First pair
            key = self._parse_key()
            self.expect(TokenType.COLON)
            value = self._parse_or()
            pairs.append((key, value))

            while self.match(TokenType.COMMA):
                self.advance()
                if self.match(TokenType.RBRACE):
                    break  # Trailing comma
                key = self._parse_key()
                self.expect(TokenType.COLON)
                value = self._parse_or()
                pairs.append((key, value))

        self.expect(TokenType.RBRACE)
        return ("object", pairs)

    def _parse_key(self) -> str:
        """Parse object key (identifier or string)."""
        if self.match(TokenType.IDENTIFIER):
            return self.advance().value
        elif self.match(TokenType.STRING):
            return self.advance().value
        else:
            raise ParseError("Expected object key")

    def _parse_array(self) -> Any:
        """Parse array literal [ item, ... ]."""
        self.expect(TokenType.LBRACKET)
        items = []

        if not self.match(TokenType.RBRACKET):
            items.append(self._parse_or())
            while self.match(TokenType.COMMA):
                self.advance()
                if self.match(TokenType.RBRACKET):
                    break  # Trailing comma
                items.append(self._parse_or())

        self.expect(TokenType.RBRACKET)
        return ("array", items)


# ==============================================================================
# Built-in Functions
# ==============================================================================


def _builtin_generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def _builtin_timestamp() -> str:
    """Get current ISO 8601 timestamp."""
    return datetime.now(UTC).isoformat()


def _builtin_now() -> int:
    """Get current Unix timestamp in milliseconds."""
    return int(datetime.now(UTC).timestamp() * 1000)


def _builtin_len(value: Any) -> int:
    """Get length of array or string."""
    if value is None:
        return 0
    if isinstance(value, (list, str, dict)):
        return len(value)
    raise ExpressionError(f"len() expects array, string, or object, got {type(value).__name__}")


def _builtin_contains(collection: Any, value: Any) -> bool:
    """Check if collection contains value."""
    if collection is None:
        return False
    if isinstance(collection, (list, str)):
        return value in collection
    if isinstance(collection, dict):
        return value in collection
    raise ExpressionError(f"contains() expects array, string, or object, got {type(collection).__name__}")


def _builtin_lower(value: str) -> str:
    """Convert string to lowercase."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ExpressionError(f"lower() expects string, got {type(value).__name__}")
    return value.lower()


def _builtin_upper(value: str) -> str:
    """Convert string to uppercase."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ExpressionError(f"upper() expects string, got {type(value).__name__}")
    return value.upper()


def _builtin_str(value: Any) -> str:
    """Convert value to string."""
    if value is None:
        return ""
    return str(value)


def _builtin_num(value: Any) -> float:
    """Convert value to number."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise ExpressionError(f"Cannot convert '{value}' to number")
    raise ExpressionError(f"Cannot convert {type(value).__name__} to number")


def _builtin_bool(value: Any) -> bool:
    """Convert value to boolean."""
    return bool(value)


def _builtin_round(value: float, digits: int = 0) -> float:
    """Round a number to specified digits."""
    if not isinstance(value, (int, float)):
        raise ExpressionError(f"round() expects number, got {type(value).__name__}")
    return round(value, int(digits))


def _builtin_abs(value: float) -> float:
    """Get absolute value."""
    if not isinstance(value, (int, float)):
        raise ExpressionError(f"abs() expects number, got {type(value).__name__}")
    return abs(value)


def _builtin_min(*values: float) -> float:
    """Get minimum value."""
    if not values:
        raise ExpressionError("min() requires at least one argument")
    return min(values)


def _builtin_max(*values: float) -> float:
    """Get maximum value."""
    if not values:
        raise ExpressionError("max() requires at least one argument")
    return max(values)


BUILTIN_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "generate_id": _builtin_generate_id,
    "timestamp": _builtin_timestamp,
    "now": _builtin_now,
    "len": _builtin_len,
    "contains": _builtin_contains,
    "lower": _builtin_lower,
    "upper": _builtin_upper,
    "str": _builtin_str,
    "num": _builtin_num,
    "bool": _builtin_bool,
    "round": _builtin_round,
    "abs": _builtin_abs,
    "min": _builtin_min,
    "max": _builtin_max,
}


# ==============================================================================
# Expression Evaluator
# ==============================================================================


class ExpressionEvaluator:
    """Evaluates expressions against a context.

    Context variables (per ADR-019):
    - params: Action parameters from caller
    - agent: Calling agent's per-agent state
    - agents: All agents' per-agent states (keyed by ID)
    - shared: Shared state accessible to all
    - config: App configuration

    Example:
        evaluator = ExpressionEvaluator()
        context = {
            "params": {"amount": 50},
            "agent": {"balance": 1000},
        }
        result = evaluator.evaluate("params.amount <= agent.balance", context)
        # result = True
    """

    def __init__(self, extra_functions: dict[str, Callable[..., Any]] | None = None):
        """Initialize evaluator with optional extra functions."""
        self.functions = dict(BUILTIN_FUNCTIONS)
        if extra_functions:
            self.functions.update(extra_functions)

    def evaluate(self, expression: str, context: dict[str, Any]) -> Any:
        """Evaluate an expression string.

        Args:
            expression: Expression string to evaluate
            context: Variable context for evaluation

        Returns:
            Evaluated result

        Raises:
            ExpressionError: If evaluation fails
        """
        try:
            lexer = Lexer(expression)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            return self._eval(ast, context)
        except ExpressionError:
            raise
        except Exception as e:
            raise ExpressionError(f"Failed to evaluate '{expression}': {e}") from e

    def evaluate_interpolated(self, template: str, context: dict[str, Any]) -> str:
        """Evaluate a string with ${...} interpolations.

        Args:
            template: String with ${expression} placeholders
            context: Variable context for evaluation

        Returns:
            Interpolated string
        """
        # Pattern to match ${...} but handle nested braces
        def replace_match(match: re.Match) -> str:
            expr = match.group(1)
            try:
                result = self.evaluate(expr, context)
                return str(result) if result is not None else ""
            except ExpressionError:
                return match.group(0)  # Keep original on error

        # Simple regex for ${...} - doesn't handle nested braces well
        pattern = r"\$\{([^}]+)\}"
        return re.sub(pattern, replace_match, template)

    def _eval(self, ast: Any, context: dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""
        if not isinstance(ast, tuple):
            return ast

        op = ast[0]

        # Literal
        if op == "literal":
            return ast[1]

        # Variable
        if op == "var":
            name = ast[1]
            if name in context:
                return context[name]
            # Return None for unknown variables (null-safe)
            return None

        # Property access
        if op == "get":
            obj = self._eval(ast[1], context)
            key = self._eval(ast[2], context)
            return self._get_property(obj, key)

        # Function call
        if op == "call":
            func_name = ast[1]
            args = [self._eval(arg, context) for arg in ast[2]]

            if func_name not in self.functions:
                raise ExpressionError(f"Unknown function: {func_name}")

            try:
                return self.functions[func_name](*args)
            except TypeError as e:
                raise ExpressionError(f"Error calling {func_name}: {e}")

        # Binary operators
        if op == "add":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._add(left, right)

        if op == "sub":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._coerce_number(left) - self._coerce_number(right)

        if op == "mul":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._coerce_number(left) * self._coerce_number(right)

        if op == "div":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            divisor = self._coerce_number(right)
            if divisor == 0:
                raise ExpressionError("Division by zero")
            return self._coerce_number(left) / divisor

        # Comparison operators
        if op == "eq":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._equals(left, right)

        if op == "ne":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return not self._equals(left, right)

        if op == "lt":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._compare(left, right) < 0

        if op == "gt":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._compare(left, right) > 0

        if op == "le":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._compare(left, right) <= 0

        if op == "ge":
            left = self._eval(ast[1], context)
            right = self._eval(ast[2], context)
            return self._compare(left, right) >= 0

        # Logical operators (short-circuit)
        if op == "and":
            left = self._eval(ast[1], context)
            if not self._is_truthy(left):
                return left
            return self._eval(ast[2], context)

        if op == "or":
            left = self._eval(ast[1], context)
            if self._is_truthy(left):
                return left
            return self._eval(ast[2], context)

        # Unary operators
        if op == "not":
            operand = self._eval(ast[1], context)
            return not self._is_truthy(operand)

        if op == "neg":
            operand = self._eval(ast[1], context)
            return -self._coerce_number(operand)

        # Object literal
        if op == "object":
            pairs = ast[1]
            result = {}
            for key, value_ast in pairs:
                result[key] = self._eval(value_ast, context)
            return result

        # Array literal
        if op == "array":
            items = ast[1]
            return [self._eval(item, context) for item in items]

        raise ExpressionError(f"Unknown AST node type: {op}")

    def _get_property(self, obj: Any, key: Any) -> Any:
        """Get a property from an object or array."""
        if obj is None:
            return None

        if isinstance(obj, dict):
            return obj.get(key)

        if isinstance(obj, list):
            if isinstance(key, int):
                if 0 <= key < len(obj):
                    return obj[key]
                return None
            return None

        # Try attribute access for objects
        if hasattr(obj, str(key)):
            return getattr(obj, str(key))

        return None

    def _coerce_number(self, value: Any) -> float:
        """Coerce a value to a number."""
        if value is None:
            return 0
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise ExpressionError(f"Cannot convert '{value}' to number")
        raise ExpressionError(f"Cannot convert {type(value).__name__} to number")

    def _add(self, left: Any, right: Any) -> Any:
        """Add two values (number addition or string concatenation)."""
        if isinstance(left, str) or isinstance(right, str):
            return str(left if left is not None else "") + str(right if right is not None else "")
        return self._coerce_number(left) + self._coerce_number(right)

    def _equals(self, left: Any, right: Any) -> bool:
        """Check equality with type coercion per ADR-019."""
        # Strict equality for same types
        if type(left) == type(right):
            return left == right

        # null comparisons
        if left is None or right is None:
            return left is None and right is None

        # Number comparisons with string coercion
        if isinstance(left, (int, float)) and isinstance(right, str):
            try:
                return left == float(right)
            except ValueError:
                return False

        if isinstance(right, (int, float)) and isinstance(left, str):
            try:
                return float(left) == right
            except ValueError:
                return False

        # Boolean coercion
        if isinstance(left, bool) or isinstance(right, bool):
            return self._is_truthy(left) == self._is_truthy(right)

        return left == right

    def _compare(self, left: Any, right: Any) -> int:
        """Compare two values, returning -1, 0, or 1."""
        # Handle nulls
        if left is None and right is None:
            return 0
        if left is None:
            return -1
        if right is None:
            return 1

        # String comparison
        if isinstance(left, str) and isinstance(right, str):
            if left < right:
                return -1
            elif left > right:
                return 1
            return 0

        # Numeric comparison (with coercion)
        left_num = self._coerce_number(left)
        right_num = self._coerce_number(right)

        if left_num < right_num:
            return -1
        elif left_num > right_num:
            return 1
        return 0

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy per ADR-019."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True


# ==============================================================================
# Convenience Functions
# ==============================================================================


def evaluate(expression: str, context: dict[str, Any]) -> Any:
    """Evaluate an expression with the default evaluator.

    Args:
        expression: Expression string
        context: Variable context

    Returns:
        Evaluated result
    """
    evaluator = ExpressionEvaluator()
    return evaluator.evaluate(expression, context)


def interpolate(template: str, context: dict[str, Any]) -> str:
    """Interpolate a template string.

    Args:
        template: String with ${expression} placeholders
        context: Variable context

    Returns:
        Interpolated string
    """
    evaluator = ExpressionEvaluator()
    return evaluator.evaluate_interpolated(template, context)
