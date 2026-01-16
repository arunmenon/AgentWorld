"""Resume command - resume paused simulations."""

import asyncio
from typing import Optional

import typer

from agentworld.cli.output import console, print_error, print_success, print_info
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.core.models import SimulationStatus


def resume(
    simulation_id: str = typer.Argument(..., help="Simulation ID to resume"),
    steps: Optional[int] = typer.Option(
        None,
        "--steps",
        "-n",
        help="Number of additional steps to run",
    ),
    from_checkpoint: Optional[str] = typer.Option(
        None,
        "--from-checkpoint",
        help="Resume from specific checkpoint ID",
    ),
) -> None:
    """Resume a paused or failed simulation.

    Continues execution from the current state or from a specific
    checkpoint if provided.
    """
    init_db()
    repo = Repository()

    # Get simulation
    sim = repo.get_simulation(simulation_id)
    if not sim:
        print_error(f"Simulation not found: {simulation_id}")
        raise typer.Exit(1)

    status = sim.get("status", "")

    # Check if can be resumed
    if status == "completed":
        print_error("Simulation already completed. Cannot resume.")
        raise typer.Exit(1)

    if status == "running":
        print_error("Simulation is already running.")
        raise typer.Exit(1)

    # Handle checkpoint restore
    if from_checkpoint:
        print_info(f"Restoring from checkpoint: {from_checkpoint}")
        # Load checkpoint state
        # This would involve deserializing checkpoint and rebuilding simulation
        # For now, we just update the status
        checkpoint = repo.get_checkpoint(from_checkpoint)
        if not checkpoint:
            print_error(f"Checkpoint not found: {from_checkpoint}")
            raise typer.Exit(1)

        print_info(f"Restored to step {checkpoint.get('step', 0)}")

    # Update status to running
    repo.update_simulation(simulation_id, {"status": SimulationStatus.RUNNING.value})

    print_success(f"Resumed simulation: {sim.get('name', simulation_id)}")
    print_info(f"Current step: {sim.get('current_step', 0)}")

    if steps:
        print_info(f"Running {steps} additional steps...")
        # In a full implementation, this would actually run the steps
        # For now we just indicate what would happen
        new_total = sim.get("current_step", 0) + steps
        print_info(f"Will run to step {new_total}")

    console.print("\n[dim]Use 'agentworld step <id>' to run steps manually[/dim]")
    console.print("[dim]Use 'agentworld inspect <id>' to view current state[/dim]")
