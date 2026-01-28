"""Coverage analysis for ADR-021 (REQ-21-06).

This module measures how thoroughly test scenarios exercise app logic:
- Action coverage: percentage of actions called
- Branch coverage: percentage of BRANCH paths taken
- Logic block coverage: percentage of logic blocks executed
- Recommendations for improving coverage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class BlockType(str, Enum):
    """Types of logic blocks."""
    VALIDATE = "validate"
    UPDATE = "update"
    NOTIFY = "notify"
    RETURN = "return"
    ERROR = "error"
    BRANCH = "branch"
    LOOP = "loop"


@dataclass
class BranchInfo:
    """Information about an uncovered branch.

    Attributes:
        action_name: Name of the action containing the branch
        block_index: Index of the branch block in action logic
        branch_type: Which branch is uncovered ("then" or "else")
        condition: The branch condition expression
    """
    action_name: str
    block_index: int
    branch_type: str  # "then" | "else"
    condition: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_name": self.action_name,
            "block_index": self.block_index,
            "branch_type": self.branch_type,
            "condition": self.condition,
        }


@dataclass
class ExecutionStep:
    """A single step in an execution trace.

    Attributes:
        action: Action name executed
        block_index: Index of the block executed
        block_type: Type of the block
        path_id: Unique identifier for this execution path
        branch_taken: For branches, which path was taken
    """
    action: str
    block_index: int
    block_type: str
    path_id: str = ""
    branch_taken: str | None = None  # "then" | "else" for branches

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "block_index": self.block_index,
            "block_type": self.block_type,
            "path_id": self.path_id,
            "branch_taken": self.branch_taken,
        }


@dataclass
class ExecutionTrace:
    """Complete execution trace for a test run.

    Attributes:
        scenario_name: Name of the test scenario
        steps: List of execution steps
        actions_called: Set of action names that were called
        timestamp: When the trace was recorded
    """
    scenario_name: str
    steps: list[ExecutionStep] = field(default_factory=list)
    actions_called: set[str] = field(default_factory=set)
    timestamp: float = 0.0

    def __post_init__(self):
        """Extract actions_called from steps if not provided."""
        if not self.actions_called and self.steps:
            self.actions_called = {s.action for s in self.steps}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "steps": [s.to_dict() for s in self.steps],
            "actions_called": list(self.actions_called),
            "timestamp": self.timestamp,
        }


@dataclass
class CFGNode:
    """Node in a control flow graph.

    Attributes:
        id: Unique node identifier
        block_type: Type of logic block
        block_index: Index in the action's logic list
        edges: Outgoing edges (node_id -> label)
        is_entry: Whether this is the entry node
        is_exit: Whether this is an exit node
    """
    id: str
    block_type: str = ""
    block_index: int = -1
    edges: dict[str, str] = field(default_factory=dict)  # target_id -> label
    is_entry: bool = False
    is_exit: bool = False


@dataclass
class ControlFlowGraph:
    """Control flow graph for an action.

    Attributes:
        action_name: Name of the action
        nodes: All nodes in the graph
        entry_node: Entry node ID
        exit_nodes: Exit node IDs
    """
    action_name: str
    nodes: dict[str, CFGNode] = field(default_factory=dict)
    entry_node: str = ""
    exit_nodes: list[str] = field(default_factory=list)

    def add_node(self, node: CFGNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.is_entry:
            self.entry_node = node.id
        if node.is_exit:
            self.exit_nodes.append(node.id)

    def get_all_paths(self) -> list[str]:
        """Enumerate all paths through the graph (DFS)."""
        if not self.entry_node:
            return []

        paths: list[str] = []

        def dfs(node_id: str, path: list[str]) -> None:
            path = path + [node_id]
            node = self.nodes.get(node_id)

            if not node or node.is_exit or not node.edges:
                paths.append(":".join(path))
                return

            for target_id, label in node.edges.items():
                dfs(target_id, path)

        dfs(self.entry_node, [])
        return paths


@dataclass
class CoverageReport:
    """Coverage analysis results.

    Attributes:
        app_id: App being analyzed
        action_coverage: Percentage of actions called (0.0-1.0)
        branch_coverage: Percentage of branch paths taken (0.0-1.0)
        logic_block_coverage: Percentage of logic blocks executed (0.0-1.0)
        uncovered_actions: Actions that were never called
        uncovered_branches: Branch paths that were never taken
        uncovered_blocks: Logic blocks that were never executed
        recommendations: Suggestions for improving coverage
        total_actions: Total number of actions
        total_branches: Total number of branch paths
        total_blocks: Total number of logic blocks
        scenarios_analyzed: Number of scenarios in the analysis
    """
    app_id: str
    action_coverage: float = 0.0
    branch_coverage: float = 0.0
    logic_block_coverage: float = 0.0
    uncovered_actions: list[str] = field(default_factory=list)
    uncovered_branches: list[BranchInfo] = field(default_factory=list)
    uncovered_blocks: list[tuple[str, int]] = field(default_factory=list)  # (action, block_index)
    recommendations: list[str] = field(default_factory=list)
    total_actions: int = 0
    total_branches: int = 0
    total_blocks: int = 0
    scenarios_analyzed: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "action_coverage": self.action_coverage,
            "branch_coverage": self.branch_coverage,
            "logic_block_coverage": self.logic_block_coverage,
            "uncovered_actions": self.uncovered_actions,
            "uncovered_branches": [b.to_dict() for b in self.uncovered_branches],
            "uncovered_blocks": self.uncovered_blocks,
            "recommendations": self.recommendations,
            "total_actions": self.total_actions,
            "total_branches": self.total_branches,
            "total_blocks": self.total_blocks,
            "scenarios_analyzed": self.scenarios_analyzed,
        }

    @property
    def overall_coverage(self) -> float:
        """Calculate weighted overall coverage score."""
        # Weight: actions 30%, branches 40%, blocks 30%
        return (
            self.action_coverage * 0.3 +
            self.branch_coverage * 0.4 +
            self.logic_block_coverage * 0.3
        )


def build_control_flow_graph(action_name: str, logic: list[dict]) -> ControlFlowGraph:
    """Build CFG from action logic blocks.

    Args:
        action_name: Name of the action
        logic: List of logic block definitions

    Returns:
        ControlFlowGraph for the action
    """
    cfg = ControlFlowGraph(action_name=action_name)

    # Add entry node
    entry = CFGNode(id="entry", is_entry=True)
    cfg.add_node(entry)

    prev_node_id = "entry"

    for i, block in enumerate(logic):
        block_type = block.get("type", "unknown")
        node_id = f"{action_name}:{i}"

        node = CFGNode(
            id=node_id,
            block_type=block_type,
            block_index=i,
        )

        if block_type == "branch":
            # Branch creates two paths
            then_id = f"{action_name}:{i}:then"
            else_id = f"{action_name}:{i}:else"
            merge_id = f"{action_name}:{i}:merge"

            then_node = CFGNode(id=then_id, block_type="then", block_index=i)
            else_node = CFGNode(id=else_id, block_type="else", block_index=i)
            merge_node = CFGNode(id=merge_id, block_type="merge", block_index=i)

            # Connect previous to branch
            if prev_node_id in cfg.nodes:
                cfg.nodes[prev_node_id].edges[node_id] = ""

            # Branch to then/else
            node.edges[then_id] = "then"
            node.edges[else_id] = "else"

            # then/else to merge
            then_node.edges[merge_id] = ""
            else_node.edges[merge_id] = ""

            cfg.add_node(node)
            cfg.add_node(then_node)
            cfg.add_node(else_node)
            cfg.add_node(merge_node)

            prev_node_id = merge_id

        elif block_type in ("return", "error"):
            # Terminal nodes
            node.is_exit = True

            if prev_node_id in cfg.nodes:
                cfg.nodes[prev_node_id].edges[node_id] = ""

            cfg.add_node(node)
            prev_node_id = ""  # No more connections after terminal

        else:
            # Regular sequential block
            if prev_node_id in cfg.nodes:
                cfg.nodes[prev_node_id].edges[node_id] = ""

            cfg.add_node(node)
            prev_node_id = node_id

    # If last block wasn't terminal, add implicit exit
    if prev_node_id and prev_node_id in cfg.nodes:
        exit_node = CFGNode(id="exit", is_exit=True)
        cfg.nodes[prev_node_id].edges["exit"] = ""
        cfg.add_node(exit_node)

    return cfg


def count_branches(logic: list[dict]) -> int:
    """Count total branch paths in logic.

    Each BRANCH block has 2 paths (then/else).

    Args:
        logic: List of logic blocks

    Returns:
        Total number of branch paths
    """
    count = 0
    for block in logic:
        if block.get("type") == "branch":
            count += 2  # then + else
    return count


def count_blocks(logic: list[dict]) -> int:
    """Count total logic blocks.

    Args:
        logic: List of logic blocks

    Returns:
        Total number of blocks
    """
    return len(logic)


def _extract_executed_paths(
    action_name: str,
    traces: list[ExecutionTrace],
) -> set[str]:
    """Extract all executed paths for an action from traces.

    Args:
        action_name: Action to analyze
        traces: Execution traces

    Returns:
        Set of path identifiers that were executed
    """
    executed = set()

    for trace in traces:
        for step in trace.steps:
            if step.action == action_name:
                executed.add(step.path_id)

                # Track branch paths
                if step.branch_taken:
                    executed.add(f"{action_name}:{step.block_index}:{step.branch_taken}")

    return executed


def analyze_coverage(
    app: Any,
    execution_traces: list[ExecutionTrace],
) -> CoverageReport:
    """Analyze test coverage using execution traces.

    Algorithm:
    1. Build control flow graph for each action
    2. Track which paths were executed in traces
    3. Calculate coverage percentages
    4. Identify uncovered items
    5. Generate recommendations

    Args:
        app: App definition (or object with .definition)
        execution_traces: List of execution traces from test runs

    Returns:
        CoverageReport with coverage metrics and recommendations
    """
    # Get app definition
    if hasattr(app, "definition"):
        definition = app.definition
    else:
        definition = app

    # Get actions from definition
    if hasattr(definition, "actions"):
        actions = definition.actions
    else:
        actions = definition.get("actions", [])

    app_id = getattr(definition, "app_id", definition.get("app_id", "unknown"))

    # Track coverage
    all_actions = set()
    executed_actions = set()
    all_branches: list[tuple[str, int, str]] = []  # (action, index, branch_type)
    executed_branches: set[str] = set()
    all_blocks: list[tuple[str, int]] = []  # (action, index)
    executed_blocks: set[str] = set()

    # Collect actions called from traces
    for trace in execution_traces:
        executed_actions.update(trace.actions_called)
        for step in trace.steps:
            executed_blocks.add(f"{step.action}:{step.block_index}")
            if step.branch_taken:
                executed_branches.add(f"{step.action}:{step.block_index}:{step.branch_taken}")

    # Analyze each action
    for action in actions:
        if hasattr(action, "name"):
            action_name = action.name
            logic = action.logic if hasattr(action, "logic") else []
        else:
            action_name = action.get("name", "")
            logic = action.get("logic", [])

        all_actions.add(action_name)

        # Count blocks and branches
        for i, block in enumerate(logic):
            all_blocks.append((action_name, i))

            block_type = block.get("type", "") if isinstance(block, dict) else getattr(block, "type", "")
            if block_type == "branch":
                all_branches.append((action_name, i, "then"))
                all_branches.append((action_name, i, "else"))

    # Calculate coverage
    total_actions = len(all_actions)
    covered_actions = len(executed_actions & all_actions)
    action_coverage = covered_actions / total_actions if total_actions > 0 else 1.0

    total_branches = len(all_branches)
    covered_branches = sum(
        1 for a, i, b in all_branches
        if f"{a}:{i}:{b}" in executed_branches
    )
    branch_coverage = covered_branches / total_branches if total_branches > 0 else 1.0

    total_blocks = len(all_blocks)
    covered_blocks = sum(
        1 for a, i in all_blocks
        if f"{a}:{i}" in executed_blocks
    )
    block_coverage = covered_blocks / total_blocks if total_blocks > 0 else 1.0

    # Find uncovered items
    uncovered_actions = list(all_actions - executed_actions)

    uncovered_branches = []
    for action_name, block_index, branch_type in all_branches:
        path_key = f"{action_name}:{block_index}:{branch_type}"
        if path_key not in executed_branches:
            # Get condition from logic
            condition = ""
            for action in actions:
                a_name = action.name if hasattr(action, "name") else action.get("name", "")
                if a_name == action_name:
                    logic = action.logic if hasattr(action, "logic") else action.get("logic", [])
                    if block_index < len(logic):
                        block = logic[block_index]
                        condition = block.get("condition", "") if isinstance(block, dict) else getattr(block, "condition", "")
                    break

            uncovered_branches.append(BranchInfo(
                action_name=action_name,
                block_index=block_index,
                branch_type=branch_type,
                condition=condition,
            ))

    uncovered_blocks = [
        (a, i) for a, i in all_blocks
        if f"{a}:{i}" not in executed_blocks
    ]

    # Generate recommendations
    recommendations = generate_coverage_recommendations(
        uncovered_actions,
        uncovered_branches,
        uncovered_blocks,
        action_coverage,
        branch_coverage,
    )

    return CoverageReport(
        app_id=app_id,
        action_coverage=action_coverage,
        branch_coverage=branch_coverage,
        logic_block_coverage=block_coverage,
        uncovered_actions=uncovered_actions,
        uncovered_branches=uncovered_branches,
        uncovered_blocks=uncovered_blocks,
        recommendations=recommendations,
        total_actions=total_actions,
        total_branches=total_branches,
        total_blocks=total_blocks,
        scenarios_analyzed=len(execution_traces),
    )


def generate_coverage_recommendations(
    uncovered_actions: list[str],
    uncovered_branches: list[BranchInfo],
    uncovered_blocks: list[tuple[str, int]],
    action_coverage: float,
    branch_coverage: float,
) -> list[str]:
    """Generate recommendations for improving coverage.

    Args:
        uncovered_actions: List of actions never called
        uncovered_branches: List of branch paths never taken
        uncovered_blocks: List of blocks never executed
        action_coverage: Current action coverage
        branch_coverage: Current branch coverage

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Action coverage recommendations
    if uncovered_actions:
        actions_str = ", ".join(uncovered_actions[:3])
        if len(uncovered_actions) > 3:
            actions_str += f" (+{len(uncovered_actions) - 3} more)"
        recommendations.append(f"Add tests that call: {actions_str}")

    if action_coverage < 0.8:
        recommendations.append(
            f"Action coverage is {action_coverage:.0%}. "
            "Consider adding a test scenario for each action."
        )

    # Branch coverage recommendations
    if uncovered_branches:
        # Group by action
        by_action: dict[str, list[BranchInfo]] = {}
        for branch in uncovered_branches:
            if branch.action_name not in by_action:
                by_action[branch.action_name] = []
            by_action[branch.action_name].append(branch)

        for action_name, branches in list(by_action.items())[:2]:
            branch_types = [b.branch_type for b in branches]
            recommendations.append(
                f"Add tests for '{action_name}' that cover {'/'.join(branch_types)} branches"
            )

    if branch_coverage < 0.7:
        recommendations.append(
            f"Branch coverage is {branch_coverage:.0%}. "
            "Add tests with different inputs to cover more paths."
        )

    # General recommendations
    if not recommendations:
        if action_coverage == 1.0 and branch_coverage == 1.0:
            recommendations.append("Excellent coverage! All actions and branches are tested.")
        else:
            recommendations.append("Coverage is good. Consider edge case testing.")

    return recommendations


def format_coverage_report(report: CoverageReport) -> str:
    """Format coverage report as human-readable text.

    Args:
        report: Coverage report to format

    Returns:
        Formatted string
    """
    lines = [
        "=" * 60,
        "COVERAGE REPORT",
        "=" * 60,
        f"App: {report.app_id}",
        f"Scenarios analyzed: {report.scenarios_analyzed}",
        "",
        "COVERAGE METRICS",
        "-" * 40,
        f"  Action coverage:    {report.action_coverage:6.1%} ({report.total_actions - len(report.uncovered_actions)}/{report.total_actions})",
        f"  Branch coverage:    {report.branch_coverage:6.1%} ({report.total_branches - len(report.uncovered_branches)}/{report.total_branches})",
        f"  Block coverage:     {report.logic_block_coverage:6.1%} ({report.total_blocks - len(report.uncovered_blocks)}/{report.total_blocks})",
        f"  Overall coverage:   {report.overall_coverage:6.1%}",
        "",
    ]

    if report.uncovered_actions:
        lines.extend([
            "UNCOVERED ACTIONS",
            "-" * 40,
        ])
        for action in report.uncovered_actions:
            lines.append(f"  ○ {action}")
        lines.append("")

    if report.uncovered_branches:
        lines.extend([
            "UNCOVERED BRANCHES",
            "-" * 40,
        ])
        for branch in report.uncovered_branches:
            lines.append(f"  ○ {branch.action_name}[{branch.block_index}].{branch.branch_type}")
            if branch.condition:
                lines.append(f"    Condition: {branch.condition}")
        lines.append("")

    if report.recommendations:
        lines.extend([
            "RECOMMENDATIONS",
            "-" * 40,
        ])
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def create_trace_from_scenario_result(
    scenario_name: str,
    step_results: list[dict],
) -> ExecutionTrace:
    """Create an ExecutionTrace from scenario test results.

    Helper function to convert test scenario results into
    execution traces for coverage analysis.

    Args:
        scenario_name: Name of the scenario
        step_results: List of step result dictionaries

    Returns:
        ExecutionTrace with steps extracted from results
    """
    steps = []
    actions_called = set()

    for result in step_results:
        action_result = result.get("action_result", {})

        # Extract action name from the step
        # This assumes the test runner includes action info in results
        action_name = result.get("action", result.get("step_name", "unknown"))
        actions_called.add(action_name)

        # Create execution step
        # In real usage, the logic engine would provide detailed path info
        step = ExecutionStep(
            action=action_name,
            block_index=0,  # Would be populated by instrumented execution
            block_type="unknown",
            path_id=f"{action_name}:0",
        )
        steps.append(step)

    return ExecutionTrace(
        scenario_name=scenario_name,
        steps=steps,
        actions_called=actions_called,
    )
