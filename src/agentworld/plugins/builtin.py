"""Built-in example plugins per ADR-014."""

from __future__ import annotations

from typing import Any

from agentworld.plugins.protocols import ParameterSpec


class CalculatorTool:
    """Tool allowing agents to perform calculations."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform mathematical calculations. Input: mathematical expression."

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')",
                }
            },
            "required": ["expression"],
        }

    async def execute(self, expression: str = "", **kwargs: Any) -> str:
        """Safely evaluate mathematical expression."""
        try:
            # Safe evaluation with limited operations
            allowed_names = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {e}"


class CurrentTimeTool:
    """Tool that returns the current time."""

    @property
    def name(self) -> str:
        return "current_time"

    @property
    def description(self) -> str:
        return "Get the current date and time."

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Optional datetime format string",
                    "default": "%Y-%m-%d %H:%M:%S",
                }
            },
            "required": [],
        }

    async def execute(self, format: str = "%Y-%m-%d %H:%M:%S", **kwargs: Any) -> str:
        """Return current time."""
        from datetime import datetime

        try:
            now = datetime.now()
            return now.strftime(format)
        except Exception as e:
            return f"Error: {e}"


class RandomNumberTool:
    """Tool that generates random numbers."""

    @property
    def name(self) -> str:
        return "random_number"

    @property
    def description(self) -> str:
        return "Generate a random number within a specified range."

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "min": {
                    "type": "number",
                    "description": "Minimum value (inclusive)",
                    "default": 0,
                },
                "max": {
                    "type": "number",
                    "description": "Maximum value (inclusive)",
                    "default": 100,
                },
                "integer": {
                    "type": "boolean",
                    "description": "Whether to return an integer",
                    "default": True,
                },
            },
            "required": [],
        }

    async def execute(
        self,
        min: float = 0,
        max: float = 100,
        integer: bool = True,
        **kwargs: Any,
    ) -> str:
        """Generate random number."""
        import random

        try:
            if integer:
                result = random.randint(int(min), int(max))
            else:
                result = random.uniform(min, max)
            return str(result)
        except Exception as e:
            return f"Error: {e}"


class JSONOutputFormat:
    """JSON output format plugin."""

    @property
    def name(self) -> str:
        return "json"

    @property
    def description(self) -> str:
        return "Export data as JSON format."

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, data: Any, path: str, **kwargs: Any) -> None:
        """Export data to JSON file."""
        import json

        indent = kwargs.get("indent", 2)
        with open(path, "w") as f:
            json.dump(data, f, indent=indent, default=str)

    def load(self, path: str, **kwargs: Any) -> Any:
        """Load data from JSON file."""
        import json

        with open(path) as f:
            return json.load(f)


class JSONLOutputFormat:
    """JSON Lines output format plugin."""

    @property
    def name(self) -> str:
        return "jsonl"

    @property
    def description(self) -> str:
        return "Export data as JSON Lines format (one JSON object per line)."

    @property
    def file_extension(self) -> str:
        return ".jsonl"

    def export(self, data: Any, path: str, **kwargs: Any) -> None:
        """Export data to JSONL file."""
        import json

        with open(path, "w") as f:
            if isinstance(data, list):
                for item in data:
                    f.write(json.dumps(item, default=str) + "\n")
            else:
                f.write(json.dumps(data, default=str) + "\n")

    def load(self, path: str, **kwargs: Any) -> list[Any]:
        """Load data from JSONL file."""
        import json

        result = []
        with open(path) as f:
            for line in f:
                if line.strip():
                    result.append(json.loads(line))
        return result


class CSVOutputFormat:
    """CSV output format plugin."""

    @property
    def name(self) -> str:
        return "csv"

    @property
    def description(self) -> str:
        return "Export data as CSV format."

    @property
    def file_extension(self) -> str:
        return ".csv"

    def export(self, data: Any, path: str, **kwargs: Any) -> None:
        """Export data to CSV file."""
        import csv

        if not isinstance(data, list) or not data:
            return

        # Flatten nested dicts for CSV
        if isinstance(data[0], dict):
            fieldnames = list(data[0].keys())
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        else:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                for row in data:
                    if isinstance(row, (list, tuple)):
                        writer.writerow(row)
                    else:
                        writer.writerow([row])

    def load(self, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Load data from CSV file."""
        import csv

        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)


# Register built-in plugins on import
def register_builtin_plugins() -> None:
    """Register all built-in plugins."""
    from agentworld.plugins.registry import registry

    # Tools
    registry.register("tools", CalculatorTool())
    registry.register("tools", CurrentTimeTool())
    registry.register("tools", RandomNumberTool())

    # Output formats
    registry.register("output_formats", JSONOutputFormat())
    registry.register("output_formats", JSONLOutputFormat())
    registry.register("output_formats", CSVOutputFormat())
