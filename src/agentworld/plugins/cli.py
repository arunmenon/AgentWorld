"""CLI commands for plugin management per ADR-014."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentworld.plugins.registry import PluginRegistry, registry

console = Console()
plugin_app = typer.Typer(name="plugins", help="Manage AgentWorld plugins")


@plugin_app.command("list")
def list_plugins(
    group: Optional[str] = typer.Option(
        None,
        "--group",
        "-g",
        help="Filter by plugin group (topologies, scenarios, validators, extractors, tools, llm_providers, output_formats)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info"),
) -> None:
    """List all installed plugins."""
    registry.discover()

    if group:
        if group not in PluginRegistry.ENTRY_POINT_GROUPS:
            console.print(f"[red]Unknown plugin group: {group}[/red]")
            console.print(f"Available groups: {', '.join(PluginRegistry.ENTRY_POINT_GROUPS.keys())}")
            raise typer.Exit(1)
        groups = [group]
    else:
        groups = list(PluginRegistry.ENTRY_POINT_GROUPS.keys())

    total_plugins = 0

    for g in groups:
        plugins = registry.get_all(g)
        if plugins:
            table = Table(title=f"[bold]{g}[/bold]")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")

            if verbose:
                table.add_column("Parameters", style="dim")

            for name, plugin in plugins.items():
                desc = getattr(plugin, "description", "No description")

                if verbose and hasattr(plugin, "get_parameters"):
                    params = plugin.get_parameters()
                    param_str = ", ".join(p.name for p in params) if params else "-"
                    table.add_row(name, desc, param_str)
                else:
                    table.add_row(name, desc)

                total_plugins += 1

            console.print(table)
            console.print()

    if total_plugins == 0:
        console.print("[dim]No plugins installed[/dim]")
    else:
        console.print(f"[dim]Total: {total_plugins} plugins[/dim]")

    # Show load errors if any
    errors = registry.get_load_errors()
    if errors:
        console.print(f"\n[yellow]Warning: {len(errors)} plugin(s) failed to load[/yellow]")
        if verbose:
            for group_name, ep_name, error in errors:
                console.print(f"  [red]{group_name}/{ep_name}: {error}[/red]")


@plugin_app.command("info")
def plugin_info(
    group: str = typer.Argument(..., help="Plugin group"),
    name: str = typer.Argument(..., help="Plugin name"),
) -> None:
    """Show detailed plugin information."""
    plugin = registry.get(group, name)

    if not plugin:
        console.print(f"[red]Plugin not found: {group}/{name}[/red]")
        raise typer.Exit(1)

    # Basic info
    console.print(Panel(f"[bold]{plugin.name}[/bold]", subtitle=group))
    console.print(f"[bold]Description:[/bold] {getattr(plugin, 'description', 'No description')}")

    # Parameters
    if hasattr(plugin, "get_parameters"):
        params = plugin.get_parameters()
        if params:
            console.print("\n[bold]Parameters:[/bold]")
            for param in params:
                required = "[red](required)[/red]" if param.required else "[dim](optional)[/dim]"
                default = f" [dim]default={param.default}[/dim]" if param.default is not None else ""

                console.print(f"  • [cyan]{param.name}[/cyan] [{param.type}] {required}{default}")
                console.print(f"    {param.description}")

                if param.min_value is not None or param.max_value is not None:
                    range_str = []
                    if param.min_value is not None:
                        range_str.append(f"min={param.min_value}")
                    if param.max_value is not None:
                        range_str.append(f"max={param.max_value}")
                    console.print(f"    [dim]Range: {', '.join(range_str)}[/dim]")

                if param.choices:
                    console.print(f"    [dim]Choices: {param.choices}[/dim]")

    # Schema (for tools)
    if hasattr(plugin, "get_schema"):
        schema = plugin.get_schema()
        if schema:
            console.print("\n[bold]Schema:[/bold]")
            import json
            console.print(f"[dim]{json.dumps(schema, indent=2)}[/dim]")

    # Config schema (for scenarios)
    if hasattr(plugin, "get_config_schema"):
        config_schema = plugin.get_config_schema()
        if config_schema:
            console.print("\n[bold]Config Schema:[/bold]")
            import json
            console.print(f"[dim]{json.dumps(config_schema, indent=2)}[/dim]")

    # Models (for LLM providers)
    if hasattr(plugin, "get_models"):
        models = plugin.get_models()
        if models:
            console.print("\n[bold]Available Models:[/bold]")
            for model in models:
                console.print(f"  • {model}")


@plugin_app.command("groups")
def list_groups() -> None:
    """List available plugin groups."""
    console.print("[bold]Plugin Groups:[/bold]\n")

    group_descriptions = {
        "topologies": "Network topology implementations (e.g., mesh, hub-spoke, lattice)",
        "scenarios": "Simulation scenarios (e.g., focus group, debate, data generation)",
        "validators": "Response validation plugins (e.g., persona adherence, consistency)",
        "extractors": "Data extraction plugins (e.g., sentiment, themes, quotes)",
        "tools": "Agent tools (e.g., calculator, search, file operations)",
        "llm_providers": "Custom LLM providers beyond LiteLLM defaults",
        "output_formats": "Export formats (e.g., Parquet, Arrow)",
    }

    table = Table()
    table.add_column("Group", style="cyan")
    table.add_column("Entry Point", style="dim")
    table.add_column("Description", style="green")

    for group, entry_point in PluginRegistry.ENTRY_POINT_GROUPS.items():
        desc = group_descriptions.get(group, "")
        table.add_row(group, entry_point, desc)

    console.print(table)


@plugin_app.command("reload")
def reload_plugins() -> None:
    """Reload all plugins."""
    console.print("Reloading plugins...")
    registry.reload()

    # Count loaded plugins
    total = sum(len(registry.list(g)) for g in PluginRegistry.ENTRY_POINT_GROUPS)
    console.print(f"[green]Loaded {total} plugins[/green]")

    errors = registry.get_load_errors()
    if errors:
        console.print(f"[yellow]{len(errors)} plugin(s) failed to load[/yellow]")


@plugin_app.command("validate")
def validate_plugin(
    package: str = typer.Argument(..., help="Plugin package name to validate"),
) -> None:
    """Validate a plugin package."""
    console.print(f"Validating plugin package: {package}")

    try:
        import importlib

        module = importlib.import_module(package)
        console.print(f"[green]Package '{package}' can be imported[/green]")

        # Check for common plugin attributes
        checks = []

        if hasattr(module, "name"):
            checks.append(("name property", True))
        else:
            checks.append(("name property", False))

        if hasattr(module, "description"):
            checks.append(("description property", True))
        else:
            checks.append(("description property", False))

        # Display results
        console.print("\n[bold]Validation Results:[/bold]")
        for check, passed in checks:
            status = "[green]✓[/green]" if passed else "[red]✗[/red]"
            console.print(f"  {status} {check}")

    except ImportError as e:
        console.print(f"[red]Failed to import package: {e}[/red]")
        raise typer.Exit(1)
