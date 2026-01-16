"""Show command - display detailed simulation information."""

import json
from typing import Optional

import typer

from agentworld.cli.output import console, print_error, print_json
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


def show(
    simulation_id: str = typer.Argument(..., help="Simulation ID to show"),
    format: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Output format: rich, json, yaml",
    ),
    include_memory: bool = typer.Option(
        False,
        "--include-memory",
        help="Include agent memories in output",
    ),
    include_messages: bool = typer.Option(
        True,
        "--include-messages",
        help="Include recent messages in output",
    ),
    step: Optional[int] = typer.Option(
        None,
        "--step",
        "-s",
        help="Show state at specific step",
    ),
) -> None:
    """Show detailed information about a simulation.

    Displays comprehensive information about a simulation including
    agents, messages, metrics, and optionally memories.
    """
    init_db()
    repo = Repository()

    # Get simulation
    sim = repo.get_simulation(simulation_id)
    if not sim:
        print_error(f"Simulation not found: {simulation_id}")
        raise typer.Exit(1)

    # Get agents
    agents = repo.get_agents_for_simulation(simulation_id)

    # Get messages
    messages = []
    if include_messages:
        messages = repo.get_messages_for_simulation(simulation_id)

    # Get memories if requested
    memories = {}
    if include_memory:
        for agent in agents:
            agent_memories = repo.get_memories_for_agent(agent["id"])
            memories[agent["id"]] = agent_memories

    if format == "json":
        output = {
            "simulation": sim,
            "agents": agents,
            "messages": messages[-20:] if messages else [],  # Last 20
            "metrics": {
                "total_messages": len(messages),
                "total_agents": len(agents),
            },
        }
        if include_memory:
            output["memories"] = memories
        print_json(output)
        return

    # Rich output
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    # Header
    status_color = {
        "pending": "yellow",
        "running": "blue",
        "paused": "cyan",
        "completed": "green",
        "failed": "red",
    }.get(sim.get("status", ""), "white")

    header = Text()
    header.append("Simulation: ", style="bold")
    header.append(sim.get("name", "Unknown"), style="cyan bold")
    header.append(f"\nID: ", style="dim")
    header.append(sim.get("id", ""), style="dim")
    header.append(f"\nStatus: ")
    header.append(sim.get("status", "unknown"), style=status_color)
    header.append(f"\nStep: {sim.get('current_step', 0)}/{sim.get('total_steps', 0)}")

    console.print(Panel(header, title="Overview"))

    # Agents table
    if agents:
        agents_table = Table(title="Agents")
        agents_table.add_column("ID", style="cyan")
        agents_table.add_column("Name", style="white")
        agents_table.add_column("Model", style="dim")

        for agent in agents:
            agents_table.add_row(
                agent.get("id", ""),
                agent.get("name", ""),
                agent.get("model", "default"),
            )
        console.print(agents_table)

    # Metrics
    metrics_table = Table(title="Metrics", show_header=False)
    metrics_table.add_column("Label", style="dim")
    metrics_table.add_column("Value")

    metrics_table.add_row("Messages", str(len(messages)))
    metrics_table.add_row("Tokens", f"{sim.get('total_tokens', 0):,}")
    metrics_table.add_row("Cost", f"${sim.get('total_cost', 0):.4f}")
    console.print(metrics_table)

    # Recent messages
    if messages and include_messages:
        console.print("\n[bold]Recent Messages:[/bold]")
        for msg in messages[-10:]:
            sender_name = msg.get("sender_id", "unknown")
            for agent in agents:
                if agent.get("id") == sender_name:
                    sender_name = agent.get("name", sender_name)
                    break
            content = msg.get("content", "")[:100]
            step_num = msg.get("step", 0)
            console.print(f"  [dim]Step {step_num}[/dim] [cyan]{sender_name}:[/cyan] {content}...")

    # Memories
    if include_memory and memories:
        console.print("\n[bold]Agent Memories:[/bold]")
        for agent_id, agent_memories in memories.items():
            agent_name = agent_id
            for agent in agents:
                if agent.get("id") == agent_id:
                    agent_name = agent.get("name", agent_id)
                    break
            console.print(f"\n  [cyan]{agent_name}[/cyan] ({len(agent_memories)} memories)")
            for mem in agent_memories[:5]:
                mem_type = mem.get("memory_type", "observation")
                content = mem.get("content", "")[:80]
                importance = mem.get("importance", 5)
                console.print(f"    [{mem_type}] {content}... (importance: {importance}/10)")
