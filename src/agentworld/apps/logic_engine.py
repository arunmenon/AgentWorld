"""Logic engine for executing dynamic app logic.

This module implements the execution engine for JSON-defined business logic
per ADR-018 and ADR-019. It executes logic blocks against an execution context
and produces results.

Safety limits per ADR-019:
- MAX_LOOP_ITERATIONS = 1000
- MAX_NESTED_DEPTH = 10
- MAX_STATE_SIZE_BYTES = 1MB
"""

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from agentworld.apps.base import AppObservation, AppResult
from agentworld.apps.definition import (
    AppState,
    BranchBlock,
    ErrorBlock,
    LogicBlock,
    LoopBlock,
    NotifyBlock,
    ReturnBlock,
    UpdateBlock,
    UpdateOperation,
    ValidateBlock,
)
from agentworld.apps.expression import ExpressionEvaluator, ExpressionError

logger = logging.getLogger(__name__)


# ==============================================================================
# Constants
# ==============================================================================

MAX_LOOP_ITERATIONS = 1000
MAX_NESTED_DEPTH = 10
MAX_STATE_SIZE_BYTES = 1_000_000  # 1MB


# ==============================================================================
# Execution Context
# ==============================================================================


@dataclass
class ExecutionContext:
    """Context for logic execution.

    Contains all data available during action execution:
    - agent_id: The calling agent's ID
    - params: Action parameters passed by caller
    - state: The full AppState (per_agent + shared)
    - config: App configuration
    - observations: List to collect observations created during execution
    - loop_vars: Variables set by LOOP blocks (e.g., current item)
    """

    agent_id: str
    params: dict[str, Any]
    state: AppState
    config: dict[str, Any] = field(default_factory=dict)
    observations: list[AppObservation] = field(default_factory=list)
    loop_vars: dict[str, Any] = field(default_factory=dict)

    def to_eval_context(self) -> dict[str, Any]:
        """Convert to expression evaluator context.

        Per ADR-019, context variables are:
        - params: Action parameters
        - agent: Calling agent's per-agent state (with id injected)
        - agents: All agents' per-agent states
        - shared: Shared state
        - config: App configuration
        """
        # Get agent state and inject agent_id as "id" for expressions like agent.id
        agent_state = dict(self.state.get_agent_state(self.agent_id))
        agent_state["id"] = self.agent_id

        context = {
            "params": self.params,
            "agent": agent_state,
            "agents": self.state.per_agent,
            "shared": self.state.shared,
            "config": self.config,
        }
        # Add loop variables
        context.update(self.loop_vars)
        return context


# ==============================================================================
# Execution Result
# ==============================================================================


@dataclass
class BlockResult:
    """Result of executing a logic block."""

    should_return: bool = False  # If True, stop execution
    value: AppResult | None = None  # Return value if should_return
    error: str | None = None  # Error message if any


# ==============================================================================
# Logic Engine
# ==============================================================================


class LogicEngine:
    """Executes JSON-defined logic blocks.

    This is the core engine that interprets and executes the logic language
    defined in ADR-019.

    Example:
        engine = LogicEngine()
        context = ExecutionContext(
            agent_id="alice",
            params={"amount": 50, "to": "bob"},
            state=app_state,
        )
        result = await engine.execute(action.logic, context)
    """

    def __init__(self):
        """Initialize the logic engine."""
        self._evaluator = ExpressionEvaluator()

    async def execute(
        self,
        logic: list[LogicBlock],
        context: ExecutionContext,
        depth: int = 0,
    ) -> AppResult:
        """Execute a list of logic blocks.

        Args:
            logic: List of logic blocks to execute
            context: Execution context
            depth: Current nesting depth (for safety limit)

        Returns:
            AppResult with success/failure and data
        """
        if depth > MAX_NESTED_DEPTH:
            return AppResult.fail(f"Maximum nesting depth ({MAX_NESTED_DEPTH}) exceeded")

        for block in logic:
            result = await self._execute_block(block, context, depth)
            if result.should_return:
                return result.value or AppResult.ok()

        # If no RETURN or ERROR block was hit, return success
        return AppResult.ok()

    async def _execute_block(
        self,
        block: LogicBlock,
        context: ExecutionContext,
        depth: int,
    ) -> BlockResult:
        """Execute a single logic block.

        Args:
            block: The logic block to execute
            context: Execution context
            depth: Current nesting depth

        Returns:
            BlockResult indicating whether to continue or return
        """
        try:
            if isinstance(block, ValidateBlock):
                return await self._execute_validate(block, context)
            elif isinstance(block, UpdateBlock):
                return await self._execute_update(block, context)
            elif isinstance(block, NotifyBlock):
                return await self._execute_notify(block, context)
            elif isinstance(block, ReturnBlock):
                return await self._execute_return(block, context)
            elif isinstance(block, ErrorBlock):
                return await self._execute_error(block, context)
            elif isinstance(block, BranchBlock):
                return await self._execute_branch(block, context, depth)
            elif isinstance(block, LoopBlock):
                return await self._execute_loop(block, context, depth)
            else:
                logger.warning(f"Unknown block type: {type(block)}")
                return BlockResult()
        except ExpressionError as e:
            return BlockResult(
                should_return=True,
                value=AppResult.fail(f"Expression error: {e}"),
            )
        except Exception as e:
            logger.exception(f"Error executing block: {block}")
            return BlockResult(
                should_return=True,
                value=AppResult.fail(f"Internal error: {e}"),
            )

    async def _execute_validate(
        self,
        block: ValidateBlock,
        context: ExecutionContext,
    ) -> BlockResult:
        """Execute a VALIDATE block.

        If condition is false, returns an error and stops execution.
        """
        eval_context = context.to_eval_context()
        condition_result = self._evaluator.evaluate(block.condition, eval_context)

        if not self._is_truthy(condition_result):
            # Interpolate error message
            error_message = self._evaluator.evaluate_interpolated(
                block.error_message, eval_context
            )
            return BlockResult(
                should_return=True,
                value=AppResult.fail(error_message),
            )

        return BlockResult()

    async def _execute_update(
        self,
        block: UpdateBlock,
        context: ExecutionContext,
    ) -> BlockResult:
        """Execute an UPDATE block.

        Modifies state according to the operation.
        """
        eval_context = context.to_eval_context()

        # Evaluate the value
        value = self._evaluate_value(block.value, eval_context)

        # Parse target path and update state
        self._update_state(block.target, block.operation, value, context)

        # Check state size limit
        state_size = len(json.dumps(context.state.to_dict()))
        if state_size > MAX_STATE_SIZE_BYTES:
            return BlockResult(
                should_return=True,
                value=AppResult.fail(f"State size ({state_size} bytes) exceeds limit ({MAX_STATE_SIZE_BYTES} bytes)"),
            )

        return BlockResult()

    async def _execute_notify(
        self,
        block: NotifyBlock,
        context: ExecutionContext,
    ) -> BlockResult:
        """Execute a NOTIFY block.

        Creates an observation for the target agent.
        """
        eval_context = context.to_eval_context()

        # Evaluate target agent
        to_agent = self._evaluator.evaluate(block.to, eval_context)
        if not isinstance(to_agent, str):
            return BlockResult(
                should_return=True,
                value=AppResult.fail(f"NOTIFY 'to' must be a string, got {type(to_agent).__name__}"),
            )

        # Interpolate message
        message = self._evaluator.evaluate_interpolated(block.message, eval_context)

        # Evaluate data if present
        data = {}
        if block.data:
            data = self._evaluate_value(block.data, eval_context)
            if not isinstance(data, dict):
                data = {"value": data}

        # Create observation
        observation = AppObservation(
            app_id="",  # Will be set by DynamicApp
            message=message,
            data=data,
        )
        context.observations.append((to_agent, observation))

        return BlockResult()

    async def _execute_return(
        self,
        block: ReturnBlock,
        context: ExecutionContext,
    ) -> BlockResult:
        """Execute a RETURN block.

        Returns success with the evaluated value.
        """
        eval_context = context.to_eval_context()
        value = self._evaluate_value(block.value, eval_context)

        if not isinstance(value, dict):
            value = {"result": value}

        return BlockResult(
            should_return=True,
            value=AppResult.ok(value),
        )

    async def _execute_error(
        self,
        block: ErrorBlock,
        context: ExecutionContext,
    ) -> BlockResult:
        """Execute an ERROR block.

        Returns failure with the error message.
        """
        eval_context = context.to_eval_context()
        message = self._evaluator.evaluate_interpolated(block.message, eval_context)

        return BlockResult(
            should_return=True,
            value=AppResult.fail(message),
        )

    async def _execute_branch(
        self,
        block: BranchBlock,
        context: ExecutionContext,
        depth: int,
    ) -> BlockResult:
        """Execute a BRANCH block.

        Evaluates condition and executes then or else blocks.
        """
        eval_context = context.to_eval_context()
        condition_result = self._evaluator.evaluate(block.condition, eval_context)

        if self._is_truthy(condition_result):
            result = await self.execute(block.then_blocks, context, depth + 1)
        elif block.else_blocks:
            result = await self.execute(block.else_blocks, context, depth + 1)
        else:
            return BlockResult()

        # If nested execution returned, propagate it
        if not result.success or result.data is not None:
            return BlockResult(should_return=True, value=result)

        return BlockResult()

    async def _execute_loop(
        self,
        block: LoopBlock,
        context: ExecutionContext,
        depth: int,
    ) -> BlockResult:
        """Execute a LOOP block.

        Iterates over collection and executes body for each item.
        """
        eval_context = context.to_eval_context()
        collection = self._evaluator.evaluate(block.collection, eval_context)

        if collection is None:
            collection = []

        if not isinstance(collection, (list, tuple)):
            return BlockResult(
                should_return=True,
                value=AppResult.fail(f"LOOP collection must be an array, got {type(collection).__name__}"),
            )

        iterations = 0
        for item in collection:
            if iterations >= MAX_LOOP_ITERATIONS:
                return BlockResult(
                    should_return=True,
                    value=AppResult.fail(f"Maximum loop iterations ({MAX_LOOP_ITERATIONS}) exceeded"),
                )

            # Set loop variable
            context.loop_vars[block.item] = item

            # Execute body
            result = await self.execute(block.body, context, depth + 1)

            # If body returned, propagate
            if not result.success or result.data is not None:
                # Clean up loop variable
                del context.loop_vars[block.item]
                return BlockResult(should_return=True, value=result)

            iterations += 1

        # Clean up loop variable
        if block.item in context.loop_vars:
            del context.loop_vars[block.item]

        return BlockResult()

    def _evaluate_value(self, value: Any, eval_context: dict[str, Any]) -> Any:
        """Evaluate a value, which may be an expression string or nested structure.

        If value is a string that looks like an expression (contains operators or dots),
        it's evaluated. Otherwise, it's returned as-is.

        For dicts and lists, recursively evaluate string values.
        """
        if isinstance(value, str):
            # Check if it looks like an expression
            if self._is_expression(value):
                return self._evaluator.evaluate(value, eval_context)
            # Check for interpolation
            if "${" in value:
                return self._evaluator.evaluate_interpolated(value, eval_context)
            # Check if it's a bare identifier that exists in context (e.g., loop variables)
            stripped = value.strip()
            if stripped.isidentifier() and stripped in eval_context:
                return eval_context[stripped]
            return value

        if isinstance(value, dict):
            return {k: self._evaluate_value(v, eval_context) for k, v in value.items()}

        if isinstance(value, list):
            return [self._evaluate_value(v, eval_context) for v in value]

        return value

    def _is_expression(self, value: str) -> bool:
        """Check if a string looks like an expression to evaluate.

        Expressions contain paths (dots), operators, function calls,
        quoted string literals, number literals, or boolean/null literals.

        NOTE: Bare identifiers (like "ok" or "n") are NOT evaluated as expressions
        by default. Use quoted strings like "'ok'" for literals, or reference
        context variables with paths like "params.value".
        """
        value = value.strip()

        # Quoted strings are expressions (string literals)
        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return True

        # Numbers are expressions
        try:
            float(value)
            return True
        except ValueError:
            pass

        # Boolean and null literals
        if value in ("true", "false", "null"):
            return True

        # Simple heuristics for expression detection
        expression_indicators = [
            ".",  # path access
            "(",  # function call
            "+", "-", "*", "/",  # arithmetic
            "==", "!=", "<", ">", "<=", ">=",  # comparison
            "&&", "||", "!",  # logical
            "[",  # array access
        ]
        return any(ind in value for ind in expression_indicators)

    def _update_state(
        self,
        target: str,
        operation: UpdateOperation,
        value: Any,
        context: ExecutionContext,
    ) -> None:
        """Update state at the target path with the given operation.

        Target paths:
        - "agent.field" -> context.state.per_agent[agent_id].field
        - "agents[id].field" -> context.state.per_agent[id].field
        - "shared.field" -> context.state.shared.field
        """
        # Parse the target path
        parts = self._parse_path(target)
        if not parts:
            raise ValueError(f"Invalid target path: {target}")

        # Determine root and navigate to parent
        root_name = parts[0]
        eval_context = context.to_eval_context()

        if root_name == "agent":
            # Update current agent's state
            obj = context.state.per_agent.setdefault(context.agent_id, {})
            parts = parts[1:]  # Skip "agent"
        elif root_name == "agents":
            # Update specific agent's state
            if len(parts) < 2:
                raise ValueError("agents path requires agent ID")
            # Evaluate agent ID (could be expression like params.to)
            agent_id_expr = parts[1]
            if isinstance(agent_id_expr, tuple) and agent_id_expr[0] == "index":
                agent_id = self._evaluator.evaluate(agent_id_expr[1], eval_context)
            else:
                agent_id = agent_id_expr
            obj = context.state.per_agent.setdefault(agent_id, {})
            parts = parts[2:]  # Skip "agents" and agent ID
        elif root_name == "shared":
            obj = context.state.shared
            parts = parts[1:]  # Skip "shared"
        else:
            raise ValueError(f"Unknown root in target path: {root_name}")

        # Navigate to parent of target field
        for i, part in enumerate(parts[:-1]):
            if isinstance(part, tuple) and part[0] == "index":
                # Array index or dynamic key
                key = self._evaluator.evaluate(part[1], eval_context)
            else:
                key = part

            if isinstance(obj, dict):
                if key not in obj:
                    obj[key] = {}
                obj = obj[key]
            elif isinstance(obj, list):
                if isinstance(key, int) and 0 <= key < len(obj):
                    obj = obj[key]
                else:
                    raise ValueError(f"Invalid array index: {key}")
            else:
                raise ValueError(f"Cannot navigate through {type(obj).__name__}")

        # Get final key
        final_key = parts[-1] if parts else None
        if final_key is None:
            raise ValueError("Empty target path")

        if isinstance(final_key, tuple) and final_key[0] == "index":
            final_key = self._evaluator.evaluate(final_key[1], eval_context)

        # Apply operation
        self._apply_operation(obj, final_key, operation, value)

    def _parse_path(self, path: str) -> list[str | tuple]:
        """Parse a path string into components.

        Examples:
        - "agent.balance" -> ["agent", "balance"]
        - "agents[params.to].balance" -> ["agents", ("index", "params.to"), "balance"]
        - "shared.counter" -> ["shared", "counter"]
        """
        parts = []
        current = ""
        i = 0

        while i < len(path):
            ch = path[i]

            if ch == ".":
                if current:
                    parts.append(current)
                    current = ""
                i += 1
            elif ch == "[":
                if current:
                    parts.append(current)
                    current = ""
                # Find matching bracket
                bracket_count = 1
                j = i + 1
                while j < len(path) and bracket_count > 0:
                    if path[j] == "[":
                        bracket_count += 1
                    elif path[j] == "]":
                        bracket_count -= 1
                    j += 1
                # Extract index expression
                index_expr = path[i + 1 : j - 1]
                parts.append(("index", index_expr))
                i = j
            else:
                current += ch
                i += 1

        if current:
            parts.append(current)

        return parts

    def _apply_operation(
        self,
        obj: dict | list,
        key: str | int,
        operation: UpdateOperation,
        value: Any,
    ) -> None:
        """Apply an update operation to an object field."""
        if isinstance(obj, dict):
            current = obj.get(key)

            if operation == UpdateOperation.SET:
                obj[key] = value
            elif operation == UpdateOperation.ADD:
                obj[key] = (current or 0) + value
            elif operation == UpdateOperation.SUBTRACT:
                obj[key] = (current or 0) - value
            elif operation == UpdateOperation.APPEND:
                if current is None:
                    obj[key] = [value]
                elif isinstance(current, list):
                    current.append(value)
                else:
                    raise ValueError(f"Cannot append to {type(current).__name__}")
            elif operation == UpdateOperation.REMOVE:
                if isinstance(current, list):
                    if value in current:
                        current.remove(value)
                elif isinstance(current, dict) and isinstance(value, str):
                    current.pop(value, None)
                else:
                    raise ValueError(f"Cannot remove from {type(current).__name__}")
            elif operation == UpdateOperation.MERGE:
                if current is None:
                    obj[key] = dict(value) if isinstance(value, dict) else value
                elif isinstance(current, dict) and isinstance(value, dict):
                    current.update(value)
                else:
                    raise ValueError(f"Cannot merge {type(value).__name__} into {type(current).__name__}")
            else:
                raise ValueError(f"Unknown operation: {operation}")

        elif isinstance(obj, list):
            if not isinstance(key, int):
                raise ValueError("List index must be integer")
            if operation == UpdateOperation.SET:
                obj[key] = value
            else:
                raise ValueError(f"Operation {operation} not supported on list elements")

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy."""
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
