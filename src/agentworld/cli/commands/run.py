"""Run command for executing simulations."""

import asyncio
from pathlib import Path
from typing import Optional

import typer

from agentworld.cli.config import load_simulation_config
from agentworld.cli.output import (
    console,
    print_error,
    print_success,
    print_message,
    print_json,
    create_progress,
)
from agentworld.core.exceptions import ConfigurationError, AgentWorldError
from agentworld.simulation.runner import Simulation
from agentworld.persistence.database import init_db
from agentworld.llm.cost import format_cost


def run(
    config_path: Path = typer.Argument(
        ...,
        help="Path to simulation configuration YAML file",
        exists=True,
        readable=True,
    ),
    steps: Optional[int] = typer.Option(
        None,
        "--steps",
        "-s",
        help="Number of steps to run (overrides config)",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress progress output",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Override model for all agents",
    ),
) -> None:
    """Run a simulation from a configuration file.

    Example:
        agentworld run simulation.yaml
        agentworld run simulation.yaml --steps 5
        agentworld run simulation.yaml --json
    """
    try:
        # Load configuration
        config = load_simulation_config(config_path)

        # Apply overrides
        if steps is not None:
            config.steps = steps
        if model is not None:
            config.model = model

        # Initialize database
        init_db()

        # Create simulation
        simulation = Simulation.from_config(config)

        if not quiet and not output_json:
            console.print(f"[bold]Starting simulation:[/bold] {simulation.name}")
            console.print(f"[dim]ID: {simulation.id}[/dim]")
            console.print(f"[dim]Agents: {', '.join(a.name for a in simulation.agents)}[/dim]")
            console.print(f"[dim]Steps: {simulation.total_steps}[/dim]")
            console.print()

        # Run simulation
        async def run_simulation():
            messages = []

            if quiet or output_json:
                # Run without progress display
                messages = await simulation.run()
            else:
                # Run with live output
                with create_progress() as progress:
                    task = progress.add_task(
                        f"Running simulation...",
                        total=simulation.total_steps,
                    )

                    for step in range(simulation.total_steps):
                        step_messages = await simulation.step()
                        messages.extend(step_messages)

                        # Print messages
                        for msg in step_messages:
                            agent = simulation.get_agent(msg.sender_id)
                            sender_name = agent.name if agent else msg.sender_id
                            print_message(sender_name, msg.content, msg.step)

                        progress.update(task, advance=1)

            return messages

        messages = asyncio.run(run_simulation())

        # Output results
        if output_json:
            result = {
                "id": simulation.id,
                "name": simulation.name,
                "status": simulation.status.value,
                "steps": simulation.current_step,
                "total_tokens": simulation.total_tokens,
                "total_cost": simulation.total_cost,
                "agents": [{"id": a.id, "name": a.name} for a in simulation.agents],
                "messages": [m.to_dict() for m in messages],
            }
            print_json(result)
        else:
            console.print()
            print_success(f"Simulation completed!")
            console.print(f"[dim]ID: {simulation.id}[/dim]")
            console.print(f"[dim]Steps: {simulation.current_step}[/dim]")
            console.print(f"[dim]Messages: {len(messages)}[/dim]")
            console.print(f"[dim]Tokens: {simulation.total_tokens:,}[/dim]")
            console.print(f"[dim]Cost: {format_cost(simulation.total_cost)}[/dim]")

    except ConfigurationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except AgentWorldError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)
