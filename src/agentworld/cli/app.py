"""Main CLI application."""

import typer
from typing import Optional

from agentworld import __version__


app = typer.Typer(
    name="agentworld",
    help="AgentWorld - Multi-agent simulation framework",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"agentworld {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """AgentWorld - Multi-agent simulation framework."""
    pass


# Import and register commands
from agentworld.cli.commands import run, list_cmd, inspect, step, inject, checkpoint
from agentworld.cli.commands import show, resume, export as export_cmd
from agentworld.cli.commands import create, analyze, serve, open as open_cmd, config
from agentworld.cli.commands import persona
from agentworld.plugins.cli import plugin_app


app.command(name="run")(run.run)
app.command(name="list")(list_cmd.list_simulations)
app.command(name="inspect")(inspect.inspect)
app.command(name="show")(show.show)
app.command(name="resume")(resume.resume)
app.command(name="export")(export_cmd.export)
app.command(name="step")(step.step)
app.command(name="inject")(inject.inject)
app.command(name="create")(create.create)
app.command(name="analyze")(analyze.analyze)
app.command(name="serve")(serve.serve)
app.command(name="open")(open_cmd.open_simulation)
app.command(name="config")(config.config)
app.add_typer(checkpoint.checkpoint_app, name="checkpoint")
app.add_typer(config.config_app, name="cfg")
app.add_typer(plugin_app, name="plugins")
app.add_typer(persona.persona_app, name="persona")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
