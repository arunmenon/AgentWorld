"""Create command - create new simulations interactively."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Prompt, Confirm

from agentworld.cli.output import console, print_error, print_success, print_info
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository
from agentworld.core.models import SimulationConfig, AgentConfig


def create(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Simulation name",
    ),
    from_file: Optional[Path] = typer.Option(
        None,
        "--from-file",
        "-f",
        help="Load configuration from YAML/JSON file",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Use a predefined template: debate, focus_group, interview",
    ),
    agents: int = typer.Option(
        2,
        "--agents",
        "-a",
        help="Number of agents to create",
    ),
    steps: int = typer.Option(
        10,
        "--steps",
        "-s",
        help="Number of simulation steps",
    ),
    model: str = typer.Option(
        "openai/gpt-4o-mini",
        "--model",
        "-m",
        help="LLM model to use",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode with prompts",
    ),
) -> None:
    """Create a new simulation.

    Supports interactive mode, templates, or configuration files.
    """
    init_db()
    repo = Repository()

    # Load from file if provided
    if from_file:
        if not from_file.exists():
            print_error(f"File not found: {from_file}")
            raise typer.Exit(1)

        content = from_file.read_text()
        if from_file.suffix in (".yaml", ".yml"):
            try:
                import yaml
                config_data = yaml.safe_load(content)
            except ImportError:
                print_error("PyYAML not installed. Use JSON format or install pyyaml.")
                raise typer.Exit(1)
        else:
            config_data = json.loads(content)

        config = SimulationConfig.from_dict(config_data)
        print_success(f"Loaded configuration from {from_file}")

    # Use template if provided
    elif template:
        config = _create_from_template(template, name or f"{template}_sim", agents, steps, model)
        if not config:
            raise typer.Exit(1)

    # Interactive mode
    elif interactive:
        config = _interactive_create()
        if not config:
            raise typer.Exit(1)

    # Default creation
    else:
        if not name:
            name = Prompt.ask("Simulation name", default="my_simulation")

        initial_prompt = Prompt.ask(
            "Initial prompt/topic",
            default="Discuss the future of artificial intelligence"
        )

        # Create default agents
        agent_configs = []
        for i in range(agents):
            agent_configs.append(AgentConfig(
                name=f"Agent_{i + 1}",
                traits={
                    "openness": 0.5 + (i * 0.1),
                    "conscientiousness": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.3,
                },
                background=f"You are agent {i + 1} in this simulation.",
            ))

        config = SimulationConfig(
            name=name,
            agents=agent_configs,
            steps=steps,
            initial_prompt=initial_prompt,
            model=model,
        )

    # Save simulation config
    from agentworld.simulation.runner import Simulation

    sim = Simulation.from_config(config)
    sim._save_state()

    print_success(f"Created simulation: {sim.name}")
    print_info(f"ID: {sim.id}")
    print_info(f"Agents: {len(sim.agents)}")
    print_info(f"Steps: {sim.total_steps}")
    console.print(f"\n[dim]Run with: agentworld run {sim.id}[/dim]")


def _create_from_template(
    template: str,
    name: str,
    num_agents: int,
    steps: int,
    model: str,
) -> Optional[SimulationConfig]:
    """Create configuration from template."""
    templates = {
        "debate": {
            "initial_prompt": "Debate the pros and cons of remote work vs office work.",
            "agents": [
                {"name": "Advocate_For", "traits": {"openness": 0.8, "extraversion": 0.7}},
                {"name": "Advocate_Against", "traits": {"openness": 0.6, "conscientiousness": 0.8}},
            ],
        },
        "focus_group": {
            "initial_prompt": "Discuss your experience with our product and suggest improvements.",
            "agents": [
                {"name": "Enthusiast", "traits": {"openness": 0.9, "extraversion": 0.8}},
                {"name": "Skeptic", "traits": {"openness": 0.4, "conscientiousness": 0.7}},
                {"name": "Pragmatist", "traits": {"openness": 0.6, "agreeableness": 0.6}},
            ],
        },
        "interview": {
            "initial_prompt": "Conduct a job interview for a software engineering position.",
            "agents": [
                {"name": "Interviewer", "traits": {"conscientiousness": 0.9, "extraversion": 0.6}},
                {"name": "Candidate", "traits": {"openness": 0.7, "neuroticism": 0.4}},
            ],
        },
    }

    if template not in templates:
        print_error(f"Unknown template: {template}")
        print_info(f"Available templates: {', '.join(templates.keys())}")
        return None

    tpl = templates[template]
    agent_configs = [
        AgentConfig(
            name=a["name"],
            traits=a["traits"],
            background=f"You are {a['name']} in this {template} scenario.",
        )
        for a in tpl["agents"]
    ]

    return SimulationConfig(
        name=name,
        agents=agent_configs,
        steps=steps,
        initial_prompt=tpl["initial_prompt"],
        model=model,
    )


def _interactive_create() -> Optional[SimulationConfig]:
    """Interactive simulation creation."""
    console.print("[bold]Interactive Simulation Creator[/bold]\n")

    name = Prompt.ask("Simulation name")
    initial_prompt = Prompt.ask("Topic or initial prompt")
    num_agents = int(Prompt.ask("Number of agents", default="2"))
    steps = int(Prompt.ask("Number of steps", default="10"))
    model = Prompt.ask("LLM model", default="openai/gpt-4o-mini")

    agent_configs = []
    for i in range(num_agents):
        console.print(f"\n[bold]Agent {i + 1}[/bold]")
        agent_name = Prompt.ask("Name", default=f"Agent_{i + 1}")
        background = Prompt.ask("Background", default="")

        # Simple trait collection
        openness = float(Prompt.ask("Openness (0-1)", default="0.5"))
        extraversion = float(Prompt.ask("Extraversion (0-1)", default="0.5"))

        agent_configs.append(AgentConfig(
            name=agent_name,
            traits={
                "openness": openness,
                "conscientiousness": 0.5,
                "extraversion": extraversion,
                "agreeableness": 0.5,
                "neuroticism": 0.3,
            },
            background=background,
        ))

    if not Confirm.ask("\nCreate this simulation?"):
        return None

    return SimulationConfig(
        name=name,
        agents=agent_configs,
        steps=steps,
        initial_prompt=initial_prompt,
        model=model,
    )
