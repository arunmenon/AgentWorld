"""Config command - manage AgentWorld configuration."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table
from rich.panel import Panel

from agentworld.cli.output import console, print_error, print_success, print_info


# Default config location
CONFIG_DIR = Path.home() / ".agentworld"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "default_model": "openai/gpt-4o-mini",
    "default_steps": 10,
    "default_agents": 2,
    "database_path": str(CONFIG_DIR / "agentworld.db"),
    "log_level": "INFO",
    "auto_checkpoint": True,
    "checkpoint_interval": 5,
    "max_concurrent_llm_calls": 10,
    "api_keys": {},
}


def config(
    action: str = typer.Argument(
        "show",
        help="Action: show, set, get, reset, path",
    ),
    key: Optional[str] = typer.Argument(
        None,
        help="Configuration key",
    ),
    value: Optional[str] = typer.Argument(
        None,
        help="Configuration value",
    ),
) -> None:
    """Manage AgentWorld configuration.

    Actions:
    - show: Display all configuration
    - get <key>: Get a specific value
    - set <key> <value>: Set a configuration value
    - reset: Reset to defaults
    - path: Show config file path
    """
    if action == "show":
        _show_config()
    elif action == "get":
        if not key:
            print_error("Key required for 'get' action")
            raise typer.Exit(1)
        _get_config(key)
    elif action == "set":
        if not key or value is None:
            print_error("Key and value required for 'set' action")
            raise typer.Exit(1)
        _set_config(key, value)
    elif action == "reset":
        _reset_config()
    elif action == "path":
        _show_path()
    else:
        print_error(f"Unknown action: {action}")
        print_info("Available actions: show, get, set, reset, path")
        raise typer.Exit(1)


def _ensure_config_dir() -> None:
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict:
    """Load configuration from file."""
    _ensure_config_dir()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
            # Merge with defaults for any missing keys
            return {**DEFAULT_CONFIG, **config}
        except json.JSONDecodeError:
            print_info("Config file corrupted, using defaults")
            return DEFAULT_CONFIG.copy()

    return DEFAULT_CONFIG.copy()


def _save_config(config: dict) -> None:
    """Save configuration to file."""
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def _show_config() -> None:
    """Display all configuration."""
    config = _load_config()

    console.print(Panel("[bold]AgentWorld Configuration[/bold]"))

    table = Table()
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Type", style="dim")

    for key, value in sorted(config.items()):
        if key == "api_keys":
            # Don't show API keys in full
            value_str = f"{{...}} ({len(value)} keys)"
        else:
            value_str = str(value)

        table.add_row(key, value_str, type(value).__name__)

    console.print(table)
    console.print(f"\n[dim]Config file: {CONFIG_FILE}[/dim]")


def _get_config(key: str) -> None:
    """Get a specific configuration value."""
    config = _load_config()

    if key not in config:
        print_error(f"Unknown configuration key: {key}")
        print_info(f"Available keys: {', '.join(config.keys())}")
        raise typer.Exit(1)

    value = config[key]

    if key == "api_keys":
        # Show API keys partially
        if value:
            for k, v in value.items():
                masked = v[:8] + "..." if len(v) > 8 else "***"
                console.print(f"  {k}: {masked}")
        else:
            console.print("  (none set)")
    else:
        console.print(f"{key}: {value}")


def _set_config(key: str, value: str) -> None:
    """Set a configuration value."""
    config = _load_config()

    # Handle special keys
    if key == "api_keys":
        print_error("Use 'agentworld config set api_keys.PROVIDER KEY' format")
        print_info("Example: agentworld config set api_keys.openai sk-xxx")
        raise typer.Exit(1)

    if key.startswith("api_keys."):
        # Setting an API key
        provider = key.split(".", 1)[1]
        if "api_keys" not in config:
            config["api_keys"] = {}
        config["api_keys"][provider] = value
        _save_config(config)
        print_success(f"Set API key for {provider}")
        return

    if key not in DEFAULT_CONFIG:
        print_error(f"Unknown configuration key: {key}")
        print_info(f"Available keys: {', '.join(DEFAULT_CONFIG.keys())}")
        raise typer.Exit(1)

    # Type conversion based on default value type
    default_value = DEFAULT_CONFIG[key]
    try:
        if isinstance(default_value, bool):
            value = value.lower() in ("true", "1", "yes", "on")
        elif isinstance(default_value, int):
            value = int(value)
        elif isinstance(default_value, float):
            value = float(value)
        # str stays as str, dict/list need special handling
    except ValueError as e:
        print_error(f"Invalid value type: {e}")
        raise typer.Exit(1)

    config[key] = value
    _save_config(config)
    print_success(f"Set {key} = {value}")


def _reset_config() -> None:
    """Reset configuration to defaults."""
    from rich.prompt import Confirm

    if not Confirm.ask("Reset all configuration to defaults?"):
        print_info("Cancelled")
        return

    _save_config(DEFAULT_CONFIG.copy())
    print_success("Configuration reset to defaults")


def _show_path() -> None:
    """Show configuration file path."""
    console.print(f"Config directory: {CONFIG_DIR}")
    console.print(f"Config file: {CONFIG_FILE}")
    console.print(f"Exists: {CONFIG_FILE.exists()}")


# Additional subcommands for specific configurations
config_app = typer.Typer(help="Configuration management")


@config_app.command("list")
def config_list() -> None:
    """List all configuration."""
    _show_config()


@config_app.command("get")
def config_get(key: str) -> None:
    """Get a configuration value."""
    _get_config(key)


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    _set_config(key, value)


@config_app.command("reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    _reset_config()


@config_app.command("path")
def config_path() -> None:
    """Show config file path."""
    _show_path()
