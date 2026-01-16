"""Step command for advancing simulation steps."""

import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from agentworld.cli.output import print_error, print_success, print_info


console = Console()


def step(
    simulation_id: str = typer.Argument(..., help="Simulation ID"),
    count: int = typer.Option(1, "--count", "-c", help="Number of steps to advance"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Advance a simulation by one or more steps.

    This command executes the specified number of steps for a paused
    or running simulation.
    """
    from agentworld.persistence.repository import Repository
    from agentworld.persistence.database import init_db
    from agentworld.simulation.runner import Simulation
    from agentworld.core.models import SimulationStatus
    import json

    try:
        init_db()
        repo = Repository()

        # Load simulation
        sim_data = repo.get_simulation(simulation_id)
        if sim_data is None:
            print_error(f"Simulation '{simulation_id}' not found")
            raise typer.Exit(1)

        if sim_data["status"] == SimulationStatus.COMPLETED.value:
            print_error("Simulation is already completed")
            raise typer.Exit(1)

        if sim_data["status"] == SimulationStatus.FAILED.value:
            print_error("Simulation has failed and cannot continue")
            raise typer.Exit(1)

        # For now, just show info since we can't fully restore state without checkpoint
        print_info(f"Advancing simulation '{simulation_id}' by {count} step(s)...")

        # Show current state
        if json_output:
            result = {
                "simulation_id": simulation_id,
                "steps_requested": count,
                "current_step": sim_data["current_step"],
                "note": "Full step execution requires checkpoint restore (not yet implemented)",
            }
            console.print_json(data=result)
        else:
            table = Table(title="Step Command Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Simulation ID", simulation_id)
            table.add_row("Current Step", str(sim_data["current_step"]))
            table.add_row("Total Steps", str(sim_data["total_steps"]))
            table.add_row("Status", sim_data["status"])
            table.add_row("Steps Requested", str(count))
            console.print(table)

            print_info("Note: Full step execution requires loading simulation state")

    except Exception as e:
        print_error(f"Error: {e}")
        raise typer.Exit(1)
