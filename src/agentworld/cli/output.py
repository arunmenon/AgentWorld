"""Rich output formatting for CLI."""

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout

from agentworld.core.models import SimulationStatus
from agentworld.llm.cost import format_cost


console = Console()
error_console = Console(stderr=True)


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: Error message
    """
    error_console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Success message
    """
    console.print(f"[green]{message}[/green]")


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Warning message
    """
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an informational message.

    Args:
        message: Info message
    """
    console.print(f"[blue]{message}[/blue]")


def print_json(data: Any) -> None:
    """Print data as JSON.

    Args:
        data: Data to print
    """
    print(json.dumps(data, indent=2, default=str))


def status_color(status: SimulationStatus | str) -> str:
    """Get the color for a simulation status.

    Args:
        status: Simulation status

    Returns:
        Rich color name
    """
    if isinstance(status, SimulationStatus):
        status = status.value

    return {
        "pending": "yellow",
        "running": "blue",
        "paused": "cyan",
        "completed": "green",
        "failed": "red",
        "cancelled": "dim",
    }.get(status, "white")


def print_simulation_table(simulations: list[dict[str, Any]]) -> None:
    """Print simulations as a table.

    Args:
        simulations: List of simulation dictionaries
    """
    if not simulations:
        console.print("[dim]No simulations found.[/dim]")
        return

    table = Table(title="Simulations")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Status", no_wrap=True)
    table.add_column("Steps", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Created", style="dim")

    for sim in simulations:
        status = sim.get("status", "unknown")
        color = status_color(status)
        status_text = f"[{color}]{status}[/{color}]"

        steps = f"{sim.get('current_step', 0)}/{sim.get('total_steps', 0)}"
        cost = format_cost(sim.get("total_cost", 0))
        created = sim.get("created_at", "")[:10] if sim.get("created_at") else ""

        table.add_row(
            sim.get("id", ""),
            sim.get("name", ""),
            status_text,
            steps,
            cost,
            created,
        )

    console.print(table)


def print_simulation_detail(simulation: dict[str, Any], agents: list[dict], messages: list[dict]) -> None:
    """Print detailed simulation information.

    Args:
        simulation: Simulation dictionary
        agents: List of agent dictionaries
        messages: List of message dictionaries
    """
    # Header panel
    status = simulation.get("status", "unknown")
    color = status_color(status)

    header = Text()
    header.append(f"Simulation: ", style="bold")
    header.append(simulation.get("name", "Unknown"), style="cyan bold")
    header.append(f"\nID: ", style="dim")
    header.append(simulation.get("id", ""), style="dim")
    header.append(f"\nStatus: ")
    header.append(status, style=color)

    console.print(Panel(header, title="Overview"))

    # Stats
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Label", style="dim")
    stats_table.add_column("Value")

    stats_table.add_row("Steps", f"{simulation.get('current_step', 0)} / {simulation.get('total_steps', 0)}")
    stats_table.add_row("Tokens", f"{simulation.get('total_tokens', 0):,}")
    stats_table.add_row("Cost", format_cost(simulation.get("total_cost", 0)))
    stats_table.add_row("Messages", str(len(messages)))
    stats_table.add_row("Agents", str(len(agents)))

    console.print(Panel(stats_table, title="Statistics"))

    # Agents
    if agents:
        agents_table = Table(title="Agents")
        agents_table.add_column("ID", style="cyan", no_wrap=True)
        agents_table.add_column("Name", style="white")
        agents_table.add_column("Model", style="dim")

        for agent in agents:
            agents_table.add_row(
                agent.get("id", ""),
                agent.get("name", ""),
                agent.get("model", "default"),
            )

        console.print(agents_table)

    # Recent messages
    if messages:
        console.print("\n[bold]Recent Messages:[/bold]")
        recent = messages[-10:]  # Last 10 messages

        for msg in recent:
            sender_id = msg.get("sender_id", "unknown")
            # Try to find sender name
            sender_name = sender_id
            for agent in agents:
                if agent.get("id") == sender_id:
                    sender_name = agent.get("name", sender_id)
                    break

            step = msg.get("step", 0)
            content = msg.get("content", "")

            console.print(f"  [dim]Step {step}[/dim] [cyan]{sender_name}:[/cyan] {content[:100]}{'...' if len(content) > 100 else ''}")


def print_message(sender: str, content: str, step: int, color: str = "cyan") -> None:
    """Print a single message.

    Args:
        sender: Sender name
        content: Message content
        step: Step number
        color: Color for sender name
    """
    console.print(f"[dim]Step {step}[/dim] [{color}]{sender}:[/{color}] {content}")


def create_progress() -> Progress:
    """Create a progress bar for simulation.

    Returns:
        Rich Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
