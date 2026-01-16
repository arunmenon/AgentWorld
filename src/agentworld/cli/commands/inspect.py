"""Inspect command for viewing simulation details."""

from typing import Optional

import typer

from agentworld.cli.output import (
    console,
    print_simulation_detail,
    print_json,
    print_error,
)
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


def inspect(
    simulation_id: str = typer.Argument(
        ...,
        help="Simulation ID to inspect",
    ),
    messages: bool = typer.Option(
        False,
        "--messages",
        "-m",
        help="Show only messages",
    ),
    agents: bool = typer.Option(
        False,
        "--agents",
        "-a",
        help="Show only agents",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """Inspect a simulation's details.

    Example:
        agentworld inspect abc123
        agentworld inspect abc123 --messages
        agentworld inspect abc123 --json
    """
    try:
        # Initialize database
        init_db()

        # Get repository
        repo = Repository()

        # Get simulation
        simulation = repo.get_simulation(simulation_id)
        if simulation is None:
            print_error(f"Simulation not found: {simulation_id}")
            raise typer.Exit(1)

        # Get related data
        sim_agents = repo.get_agents_for_simulation(simulation_id)
        sim_messages = repo.get_messages_for_simulation(simulation_id)

        # Output based on flags
        if output_json:
            if messages:
                print_json(sim_messages)
            elif agents:
                print_json(sim_agents)
            else:
                result = {
                    **simulation,
                    "agents": sim_agents,
                    "messages": sim_messages,
                }
                print_json(result)
        else:
            if messages:
                # Show only messages
                if not sim_messages:
                    console.print("[dim]No messages found.[/dim]")
                else:
                    for msg in sim_messages:
                        sender_id = msg.get("sender_id", "unknown")
                        sender_name = sender_id
                        for agent in sim_agents:
                            if agent.get("id") == sender_id:
                                sender_name = agent.get("name", sender_id)
                                break

                        step = msg.get("step", 0)
                        content = msg.get("content", "")
                        console.print(f"[dim]Step {step}[/dim] [cyan]{sender_name}:[/cyan] {content}")
            elif agents:
                # Show only agents
                if not sim_agents:
                    console.print("[dim]No agents found.[/dim]")
                else:
                    for agent in sim_agents:
                        console.print(f"[cyan]{agent.get('name')}[/cyan] ({agent.get('id')})")
                        traits = agent.get("traits", {})
                        if traits:
                            for trait, value in traits.items():
                                console.print(f"  [dim]{trait}:[/dim] {value:.2f}")
            else:
                # Show full details
                print_simulation_detail(simulation, sim_agents, sim_messages)

        repo.close()

    except Exception as e:
        print_error(f"Failed to inspect simulation: {e}")
        raise typer.Exit(1)
