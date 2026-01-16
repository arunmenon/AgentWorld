"""Inject command for adding stimuli to simulations."""

from typing import Optional
import typer
from rich.console import Console

from agentworld.cli.output import print_error, print_success, print_info


console = Console()


def inject(
    simulation_id: str = typer.Argument(..., help="Simulation ID"),
    message: str = typer.Argument(..., help="Message to inject"),
    target: Optional[str] = typer.Option(
        None, "--target", "-t", help="Target agent ID (omit for broadcast)"
    ),
    source: str = typer.Option(
        "system", "--source", "-s", help="Source of the message"
    ),
    stimulus_type: str = typer.Option(
        "announcement", "--type", help="Stimulus type (announcement, question, prompt)"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Inject a stimulus into a running simulation.

    Stimuli can be announcements, questions, or prompts that are
    delivered to agents during the next step.
    """
    from agentworld.persistence.repository import Repository
    from agentworld.persistence.database import init_db
    from agentworld.scenarios.stimulus import Stimulus, StimulusType
    from agentworld.core.models import SimulationStatus
    import json

    try:
        init_db()
        repo = Repository()

        # Validate simulation exists
        sim_data = repo.get_simulation(simulation_id)
        if sim_data is None:
            print_error(f"Simulation '{simulation_id}' not found")
            raise typer.Exit(1)

        # Validate stimulus type
        valid_types = ["announcement", "question", "prompt", "topic_change", "instruction"]
        if stimulus_type not in valid_types:
            print_error(f"Invalid stimulus type. Valid types: {', '.join(valid_types)}")
            raise typer.Exit(1)

        # Create stimulus
        try:
            stype = StimulusType(stimulus_type)
        except ValueError:
            stype = StimulusType.ANNOUNCEMENT

        target_agents = [target] if target else None
        stimulus = Stimulus(
            content=message,
            stimulus_type=stype,
            target_agents=target_agents,
            source=source,
        )

        if json_output:
            result = {
                "status": "queued",
                "stimulus": stimulus.to_dict(),
                "simulation_id": simulation_id,
                "note": "Stimulus will be delivered on next step execution",
            }
            console.print_json(data=result)
        else:
            print_success(f"Stimulus queued for simulation '{simulation_id}'")
            print_info(f"  Type: {stimulus_type}")
            print_info(f"  Source: {source}")
            print_info(f"  Target: {target or 'all agents (broadcast)'}")
            print_info(f"  Content: {message[:100]}{'...' if len(message) > 100 else ''}")
            print_info("\nNote: The stimulus will be delivered on the next step execution")

    except Exception as e:
        print_error(f"Error: {e}")
        raise typer.Exit(1)
