"""List command for viewing simulations."""

from typing import Optional

import typer

from agentworld.cli.output import print_simulation_table, print_json, print_error
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.core.models import SimulationStatus


def list_simulations(
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (pending, running, completed, failed)",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Maximum number of simulations to show",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """List all simulations.

    Example:
        agentworld list
        agentworld list --status completed
        agentworld list --json
    """
    try:
        # Initialize database
        init_db()

        # Get repository
        repo = Repository()

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = SimulationStatus(status.lower())
            except ValueError:
                print_error(f"Invalid status: {status}")
                print_error(f"Valid values: {', '.join(s.value for s in SimulationStatus)}")
                raise typer.Exit(1)

        # Get simulations
        simulations = repo.list_simulations(status=status_filter, limit=limit)

        # Output
        if output_json:
            print_json(simulations)
        else:
            print_simulation_table(simulations)

        repo.close()

    except Exception as e:
        print_error(f"Failed to list simulations: {e}")
        raise typer.Exit(1)
