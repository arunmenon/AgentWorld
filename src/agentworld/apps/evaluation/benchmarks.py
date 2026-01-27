"""Benchmark suite for ADR-021.

This module provides:
- Standard benchmark app definitions
- Benchmark execution and metrics collection
- Performance and correctness measurement
"""

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class BenchmarkResult:
    """Result of running a benchmark.

    Attributes:
        app_id: App being benchmarked
        benchmark_name: Name of the benchmark
        timestamp: When benchmark was run

        # Performance metrics
        avg_action_latency_ms: Average action execution time
        p99_action_latency_ms: 99th percentile latency
        actions_per_second: Throughput

        # Correctness metrics
        scenario_pass_rate: Percentage of scenarios passed
        edge_case_coverage: Percentage of edge cases handled

        # Quality metrics
        quality_score: Overall quality score
        dimension_scores: Scores per quality dimension
    """
    app_id: str
    benchmark_name: str
    timestamp: str

    # Performance
    avg_action_latency_ms: float = 0
    p99_action_latency_ms: float = 0
    actions_per_second: float = 0

    # Correctness
    scenario_pass_rate: float = 0
    edge_case_coverage: float = 0
    scenarios_passed: int = 0
    scenarios_total: int = 0

    # Quality
    quality_score: float = 0
    dimension_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "benchmark_name": self.benchmark_name,
            "timestamp": self.timestamp,
            "performance": {
                "avg_action_latency_ms": self.avg_action_latency_ms,
                "p99_action_latency_ms": self.p99_action_latency_ms,
                "actions_per_second": self.actions_per_second,
            },
            "correctness": {
                "scenario_pass_rate": self.scenario_pass_rate,
                "edge_case_coverage": self.edge_case_coverage,
                "scenarios_passed": self.scenarios_passed,
                "scenarios_total": self.scenarios_total,
            },
            "quality": {
                "quality_score": self.quality_score,
                "dimension_scores": self.dimension_scores,
            },
        }


# =============================================================================
# Benchmark App Definitions
# =============================================================================

BENCH_COUNTER = {
    "app_id": "bench_counter",
    "name": "Benchmark Counter",
    "description": "Minimal app for baseline state mutation testing",
    "category": "custom",
    "icon": "🔢",
    "state_schema": [
        {"name": "count", "type": "number", "default": 0, "per_agent": True},
    ],
    "actions": [
        {
            "name": "increment",
            "description": "Increase counter by amount",
            "parameters": {
                "amount": {
                    "type": "number",
                    "required": False,
                    "default": 1,
                    "description": "Amount to increment by",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount >= 0",
                    "error_message": "Amount must be non-negative",
                },
                {
                    "type": "update",
                    "target": "agent.count",
                    "operation": "add",
                    "value": "params.amount || 1",
                },
                {
                    "type": "return",
                    "value": {"new_count": "agent.count"},
                },
            ],
        },
        {
            "name": "decrement",
            "description": "Decrease counter by amount",
            "parameters": {
                "amount": {
                    "type": "number",
                    "required": False,
                    "default": 1,
                    "description": "Amount to decrement by",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount >= 0",
                    "error_message": "Amount must be non-negative",
                },
                {
                    "type": "validate",
                    "condition": "agent.count >= (params.amount || 1)",
                    "error_message": "Cannot decrement below zero",
                },
                {
                    "type": "update",
                    "target": "agent.count",
                    "operation": "subtract",
                    "value": "params.amount || 1",
                },
                {
                    "type": "return",
                    "value": {"new_count": "agent.count"},
                },
            ],
        },
    ],
}

BENCH_WALLET = {
    "app_id": "bench_wallet",
    "name": "Benchmark Wallet",
    "description": "Standard payment flow for transfer testing",
    "category": "payment",
    "icon": "💰",
    "state_schema": [
        {"name": "balance", "type": "number", "default": 1000, "per_agent": True},
        {"name": "transactions", "type": "array", "default": [], "per_agent": True},
    ],
    "initial_config": {
        "initial_balance": 1000,
    },
    "actions": [
        {
            "name": "check_balance",
            "description": "View current balance",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"balance": "agent.balance"},
                },
            ],
        },
        {
            "name": "transfer",
            "description": "Send money to another user",
            "parameters": {
                "to": {
                    "type": "string",
                    "required": True,
                    "description": "Recipient agent ID",
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "min_value": 0.01,
                    "description": "Amount to transfer",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.to != agent.id",
                    "error_message": "Cannot transfer to yourself",
                },
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "validate",
                    "condition": "agent.balance >= params.amount",
                    "error_message": "Insufficient funds",
                },
                {
                    "type": "update",
                    "target": "agent.balance",
                    "operation": "subtract",
                    "value": "params.amount",
                },
                {
                    "type": "update",
                    "target": "agents[params.to].balance",
                    "operation": "add",
                    "value": "params.amount",
                },
                {
                    "type": "update",
                    "target": "agent.transactions",
                    "operation": "append",
                    "value": {
                        "type": "sent",
                        "to": "params.to",
                        "amount": "params.amount",
                        "timestamp": "timestamp()",
                    },
                },
                {
                    "type": "notify",
                    "to": "params.to",
                    "message": "You received ${params.amount} from ${agent.id}",
                },
                {
                    "type": "return",
                    "value": {
                        "transaction_id": "generate_id()",
                        "new_balance": "agent.balance",
                    },
                },
            ],
        },
        {
            "name": "deposit",
            "description": "Add funds to account",
            "parameters": {
                "amount": {
                    "type": "number",
                    "required": True,
                    "min_value": 0.01,
                    "description": "Amount to deposit",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "update",
                    "target": "agent.balance",
                    "operation": "add",
                    "value": "params.amount",
                },
                {
                    "type": "return",
                    "value": {"new_balance": "agent.balance"},
                },
            ],
        },
        {
            "name": "withdraw",
            "description": "Remove funds from account",
            "parameters": {
                "amount": {
                    "type": "number",
                    "required": True,
                    "min_value": 0.01,
                    "description": "Amount to withdraw",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "validate",
                    "condition": "agent.balance >= params.amount",
                    "error_message": "Insufficient funds",
                },
                {
                    "type": "update",
                    "target": "agent.balance",
                    "operation": "subtract",
                    "value": "params.amount",
                },
                {
                    "type": "return",
                    "value": {"new_balance": "agent.balance"},
                },
            ],
        },
    ],
}

BENCH_INVENTORY = {
    "app_id": "bench_inventory",
    "name": "Benchmark Inventory",
    "description": "CRUD operations with constraints for shopping testing",
    "category": "shopping",
    "icon": "📦",
    "state_schema": [
        {"name": "items", "type": "object", "default": {}, "per_agent": True},
        {"name": "total_value", "type": "number", "default": 0, "per_agent": True},
    ],
    "actions": [
        {
            "name": "add_item",
            "description": "Add item to inventory",
            "parameters": {
                "item_id": {"type": "string", "required": True, "description": "Item identifier"},
                "quantity": {"type": "number", "required": True, "min_value": 1, "description": "Quantity to add"},
                "price": {"type": "number", "required": True, "min_value": 0, "description": "Price per item"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.quantity > 0",
                    "error_message": "Quantity must be positive",
                },
                {
                    "type": "branch",
                    "condition": "agent.items[params.item_id] != null",
                    "then": [
                        {
                            "type": "update",
                            "target": "agent.items[params.item_id].quantity",
                            "operation": "add",
                            "value": "params.quantity",
                        },
                    ],
                    "else": [
                        {
                            "type": "update",
                            "target": "agent.items[params.item_id]",
                            "operation": "set",
                            "value": {
                                "item_id": "params.item_id",
                                "quantity": "params.quantity",
                                "price": "params.price",
                            },
                        },
                    ],
                },
                {
                    "type": "update",
                    "target": "agent.total_value",
                    "operation": "add",
                    "value": "params.quantity * params.price",
                },
                {
                    "type": "return",
                    "value": {"item": "agent.items[params.item_id]"},
                },
            ],
        },
        {
            "name": "remove_item",
            "description": "Remove item from inventory",
            "parameters": {
                "item_id": {"type": "string", "required": True, "description": "Item identifier"},
                "quantity": {"type": "number", "required": True, "min_value": 1, "description": "Quantity to remove"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "agent.items[params.item_id] != null",
                    "error_message": "Item not found",
                },
                {
                    "type": "validate",
                    "condition": "agent.items[params.item_id].quantity >= params.quantity",
                    "error_message": "Insufficient quantity",
                },
                {
                    "type": "update",
                    "target": "agent.items[params.item_id].quantity",
                    "operation": "subtract",
                    "value": "params.quantity",
                },
                {
                    "type": "update",
                    "target": "agent.total_value",
                    "operation": "subtract",
                    "value": "params.quantity * agent.items[params.item_id].price",
                },
                {
                    "type": "return",
                    "value": {"remaining": "agent.items[params.item_id].quantity"},
                },
            ],
        },
        {
            "name": "get_item",
            "description": "Get item details",
            "parameters": {
                "item_id": {"type": "string", "required": True, "description": "Item identifier"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "agent.items[params.item_id] != null",
                    "error_message": "Item not found",
                },
                {
                    "type": "return",
                    "value": {"item": "agent.items[params.item_id]"},
                },
            ],
        },
        {
            "name": "list_items",
            "description": "List all items in inventory",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "items": "agent.items",
                        "total_value": "agent.total_value",
                    },
                },
            ],
        },
        {
            "name": "transfer_item",
            "description": "Transfer item to another user",
            "parameters": {
                "to": {"type": "string", "required": True, "description": "Recipient"},
                "item_id": {"type": "string", "required": True, "description": "Item identifier"},
                "quantity": {"type": "number", "required": True, "min_value": 1, "description": "Quantity"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.to != agent.id",
                    "error_message": "Cannot transfer to yourself",
                },
                {
                    "type": "validate",
                    "condition": "agent.items[params.item_id] != null",
                    "error_message": "Item not found",
                },
                {
                    "type": "validate",
                    "condition": "agent.items[params.item_id].quantity >= params.quantity",
                    "error_message": "Insufficient quantity",
                },
                {
                    "type": "update",
                    "target": "agent.items[params.item_id].quantity",
                    "operation": "subtract",
                    "value": "params.quantity",
                },
                {
                    "type": "notify",
                    "to": "params.to",
                    "message": "You received ${params.quantity} of ${params.item_id}",
                },
                {
                    "type": "return",
                    "value": {"transferred": "params.quantity"},
                },
            ],
        },
        {
            "name": "clear_inventory",
            "description": "Remove all items",
            "parameters": {},
            "logic": [
                {
                    "type": "update",
                    "target": "agent.items",
                    "operation": "set",
                    "value": {},
                },
                {
                    "type": "update",
                    "target": "agent.total_value",
                    "operation": "set",
                    "value": 0,
                },
                {
                    "type": "return",
                    "value": {"cleared": True},
                },
            ],
        },
    ],
}

BENCH_MESSAGING = {
    "app_id": "bench_messaging",
    "name": "Benchmark Messaging",
    "description": "Multi-party interaction for communication testing",
    "category": "communication",
    "icon": "💬",
    "state_schema": [
        {"name": "inbox", "type": "array", "default": [], "per_agent": True},
        {"name": "sent", "type": "array", "default": [], "per_agent": True},
        {"name": "unread_count", "type": "number", "default": 0, "per_agent": True},
    ],
    "actions": [
        {
            "name": "send_message",
            "description": "Send a message to another user",
            "parameters": {
                "to": {"type": "string", "required": True, "description": "Recipient"},
                "content": {"type": "string", "required": True, "description": "Message content"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.to != agent.id",
                    "error_message": "Cannot send message to yourself",
                },
                {
                    "type": "validate",
                    "condition": "len(params.content) > 0",
                    "error_message": "Message cannot be empty",
                },
                {
                    "type": "update",
                    "target": "agent.sent",
                    "operation": "append",
                    "value": {
                        "id": "generate_id()",
                        "to": "params.to",
                        "content": "params.content",
                        "timestamp": "timestamp()",
                    },
                },
                {
                    "type": "notify",
                    "to": "params.to",
                    "message": "New message from ${agent.id}",
                    "data": {
                        "type": "message",
                        "from": "agent.id",
                        "content": "params.content",
                    },
                },
                {
                    "type": "return",
                    "value": {"message_id": "generate_id()"},
                },
            ],
        },
        {
            "name": "get_inbox",
            "description": "Get all received messages",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "messages": "agent.inbox",
                        "unread": "agent.unread_count",
                    },
                },
            ],
        },
        {
            "name": "get_sent",
            "description": "Get all sent messages",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"messages": "agent.sent"},
                },
            ],
        },
        {
            "name": "mark_read",
            "description": "Mark messages as read",
            "parameters": {},
            "logic": [
                {
                    "type": "update",
                    "target": "agent.unread_count",
                    "operation": "set",
                    "value": 0,
                },
                {
                    "type": "return",
                    "value": {"marked_read": True},
                },
            ],
        },
        {
            "name": "broadcast",
            "description": "Send message to all users",
            "parameters": {
                "content": {"type": "string", "required": True, "description": "Message content"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "len(params.content) > 0",
                    "error_message": "Message cannot be empty",
                },
                {
                    "type": "return",
                    "value": {"broadcast": True, "content": "params.content"},
                },
            ],
        },
    ],
}

BENCH_WORKFLOW = {
    "app_id": "bench_workflow",
    "name": "Benchmark Workflow",
    "description": "Complex branching logic for advanced testing",
    "category": "custom",
    "icon": "🔀",
    "state_schema": [
        {"name": "tasks", "type": "array", "default": [], "per_agent": True},
        {"name": "completed", "type": "number", "default": 0, "per_agent": True},
        {"name": "pending", "type": "number", "default": 0, "per_agent": True},
    ],
    "actions": [
        {
            "name": "create_task",
            "description": "Create a new task",
            "parameters": {
                "title": {"type": "string", "required": True, "description": "Task title"},
                "priority": {"type": "string", "required": False, "default": "medium", "description": "Priority level"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "len(params.title) > 0",
                    "error_message": "Title cannot be empty",
                },
                {
                    "type": "update",
                    "target": "agent.tasks",
                    "operation": "append",
                    "value": {
                        "id": "generate_id()",
                        "title": "params.title",
                        "priority": "params.priority || 'medium'",
                        "status": "pending",
                        "created": "timestamp()",
                    },
                },
                {
                    "type": "update",
                    "target": "agent.pending",
                    "operation": "add",
                    "value": 1,
                },
                {
                    "type": "return",
                    "value": {"task_id": "generate_id()"},
                },
            ],
        },
        {
            "name": "complete_task",
            "description": "Mark a task as complete",
            "parameters": {
                "task_index": {"type": "number", "required": True, "description": "Task index in list"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.task_index >= 0",
                    "error_message": "Invalid task index",
                },
                {
                    "type": "validate",
                    "condition": "params.task_index < len(agent.tasks)",
                    "error_message": "Task not found",
                },
                {
                    "type": "branch",
                    "condition": "agent.tasks[params.task_index].status == 'pending'",
                    "then": [
                        {
                            "type": "update",
                            "target": "agent.tasks[params.task_index].status",
                            "operation": "set",
                            "value": "completed",
                        },
                        {
                            "type": "update",
                            "target": "agent.pending",
                            "operation": "subtract",
                            "value": 1,
                        },
                        {
                            "type": "update",
                            "target": "agent.completed",
                            "operation": "add",
                            "value": 1,
                        },
                        {
                            "type": "return",
                            "value": {"completed": True},
                        },
                    ],
                    "else": [
                        {
                            "type": "error",
                            "message": "Task is not pending",
                        },
                    ],
                },
            ],
        },
        {
            "name": "list_tasks",
            "description": "List all tasks",
            "parameters": {
                "status": {"type": "string", "required": False, "description": "Filter by status"},
            },
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "tasks": "agent.tasks",
                        "pending": "agent.pending",
                        "completed": "agent.completed",
                    },
                },
            ],
        },
        {
            "name": "assign_task",
            "description": "Assign task to another user",
            "parameters": {
                "task_index": {"type": "number", "required": True, "description": "Task index"},
                "assignee": {"type": "string", "required": True, "description": "User to assign to"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.task_index >= 0",
                    "error_message": "Invalid task index",
                },
                {
                    "type": "validate",
                    "condition": "params.assignee != agent.id",
                    "error_message": "Cannot assign to yourself",
                },
                {
                    "type": "update",
                    "target": "agent.tasks[params.task_index].assignee",
                    "operation": "set",
                    "value": "params.assignee",
                },
                {
                    "type": "notify",
                    "to": "params.assignee",
                    "message": "You have been assigned a task",
                },
                {
                    "type": "return",
                    "value": {"assigned": True},
                },
            ],
        },
        {
            "name": "update_priority",
            "description": "Change task priority",
            "parameters": {
                "task_index": {"type": "number", "required": True, "description": "Task index"},
                "priority": {"type": "string", "required": True, "description": "New priority"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.task_index >= 0",
                    "error_message": "Invalid task index",
                },
                {
                    "type": "validate",
                    "condition": "params.priority == 'low' || params.priority == 'medium' || params.priority == 'high'",
                    "error_message": "Invalid priority (use low, medium, high)",
                },
                {
                    "type": "update",
                    "target": "agent.tasks[params.task_index].priority",
                    "operation": "set",
                    "value": "params.priority",
                },
                {
                    "type": "return",
                    "value": {"updated": True},
                },
            ],
        },
        {
            "name": "delete_task",
            "description": "Delete a task",
            "parameters": {
                "task_index": {"type": "number", "required": True, "description": "Task index"},
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.task_index >= 0",
                    "error_message": "Invalid task index",
                },
                {
                    "type": "branch",
                    "condition": "agent.tasks[params.task_index].status == 'pending'",
                    "then": [
                        {
                            "type": "update",
                            "target": "agent.pending",
                            "operation": "subtract",
                            "value": 1,
                        },
                    ],
                    "else": [
                        {
                            "type": "update",
                            "target": "agent.completed",
                            "operation": "subtract",
                            "value": 1,
                        },
                    ],
                },
                {
                    "type": "return",
                    "value": {"deleted": True},
                },
            ],
        },
        {
            "name": "get_stats",
            "description": "Get workflow statistics",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "total": "len(agent.tasks)",
                        "pending": "agent.pending",
                        "completed": "agent.completed",
                        "completion_rate": "agent.completed / (agent.completed + agent.pending)",
                    },
                },
            ],
        },
        {
            "name": "clear_completed",
            "description": "Remove all completed tasks",
            "parameters": {},
            "logic": [
                {
                    "type": "update",
                    "target": "agent.completed",
                    "operation": "set",
                    "value": 0,
                },
                {
                    "type": "return",
                    "value": {"cleared": True},
                },
            ],
        },
    ],
}

# All benchmark apps
BENCHMARK_APPS = {
    "bench_counter": BENCH_COUNTER,
    "bench_wallet": BENCH_WALLET,
    "bench_inventory": BENCH_INVENTORY,
    "bench_messaging": BENCH_MESSAGING,
    "bench_workflow": BENCH_WORKFLOW,
}


def get_benchmark_apps() -> dict[str, dict]:
    """Get all benchmark app definitions.

    Returns:
        Dictionary of benchmark app definitions
    """
    return BENCHMARK_APPS.copy()


def get_benchmark_app(app_id: str) -> dict | None:
    """Get a specific benchmark app definition.

    Args:
        app_id: Benchmark app ID

    Returns:
        App definition or None
    """
    return BENCHMARK_APPS.get(app_id)


class BenchmarkSuite:
    """Suite of benchmark tests for apps.

    Example:
        suite = BenchmarkSuite()
        result = await suite.run_benchmark("bench_wallet", app)
    """

    def __init__(self):
        """Initialize benchmark suite."""
        self.benchmark_apps = BENCHMARK_APPS

    async def run_benchmark(
        self,
        benchmark_name: str,
        app: Any,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """Run a benchmark against an app.

        Args:
            benchmark_name: Name of benchmark to run
            app: App instance to benchmark
            iterations: Number of iterations for performance test

        Returns:
            BenchmarkResult with metrics
        """
        from datetime import datetime
        from agentworld.apps.evaluation.quality import calculate_quality_score

        timestamp = datetime.now().isoformat()

        # Get app definition
        if hasattr(app, "_definition"):
            app_def = app._definition
            if hasattr(app_def, "to_dict"):
                app_def = app_def.to_dict()
        elif hasattr(app, "to_dict"):
            app_def = app.to_dict()
        else:
            app_def = {}

        # Calculate quality score
        quality_report = calculate_quality_score(app_def)

        # Performance metrics (placeholder - actual benchmark would run actions)
        latencies = []
        for _ in range(min(iterations, 10)):  # Limit for now
            start = time.time()
            # Would execute actual actions here
            latencies.append((time.time() - start) * 1000)

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        sorted_latencies = sorted(latencies)
        p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)] if latencies else 0

        return BenchmarkResult(
            app_id=app_def.get("app_id", "unknown"),
            benchmark_name=benchmark_name,
            timestamp=timestamp,
            avg_action_latency_ms=avg_latency,
            p99_action_latency_ms=p99_latency,
            actions_per_second=1000 / avg_latency if avg_latency > 0 else 0,
            scenario_pass_rate=0,  # Would run scenarios
            edge_case_coverage=0,
            scenarios_passed=0,
            scenarios_total=0,
            quality_score=quality_report.overall_score,
            dimension_scores=quality_report.dimension_scores,
        )


async def run_benchmark(
    benchmark_name: str,
    app: Any,
    iterations: int = 100,
) -> BenchmarkResult:
    """Convenience function to run a benchmark.

    Args:
        benchmark_name: Name of benchmark
        app: App instance
        iterations: Number of iterations

    Returns:
        BenchmarkResult
    """
    suite = BenchmarkSuite()
    return await suite.run_benchmark(benchmark_name, app, iterations)
