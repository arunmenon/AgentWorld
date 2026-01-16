"""Configuration loading and parsing."""

from pathlib import Path
from typing import Any

import yaml

from agentworld.core.models import SimulationConfig, AgentConfig
from agentworld.core.exceptions import ConfigurationError


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed configuration dictionary

    Raises:
        ConfigurationError: If file cannot be loaded or parsed
    """
    path = Path(path)

    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {path}: {e}")

    if not isinstance(data, dict):
        raise ConfigurationError(f"Configuration must be a dictionary, got {type(data).__name__}")

    return data


def parse_simulation_config(data: dict[str, Any]) -> SimulationConfig:
    """Parse a simulation configuration from dictionary.

    Args:
        data: Configuration dictionary

    Returns:
        SimulationConfig instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate required fields
    if "name" not in data:
        raise ConfigurationError("Configuration must have a 'name' field")

    if "agents" not in data or not data["agents"]:
        raise ConfigurationError("Configuration must have at least one agent")

    # Parse agents
    agents = []
    for i, agent_data in enumerate(data["agents"]):
        if isinstance(agent_data, str):
            # Simple agent definition (just a name)
            agents.append(AgentConfig(name=agent_data))
        elif isinstance(agent_data, dict):
            if "name" not in agent_data:
                raise ConfigurationError(f"Agent {i} must have a 'name' field")
            agents.append(AgentConfig.from_dict(agent_data))
        else:
            raise ConfigurationError(f"Invalid agent definition at index {i}")

    return SimulationConfig(
        name=data["name"],
        agents=agents,
        steps=data.get("steps", 10),
        initial_prompt=data.get("initial_prompt", ""),
        model=data.get("model", "openai/gpt-4o-mini"),
        seed=data.get("seed"),
        temperature=data.get("temperature", 0.7),
    )


def load_simulation_config(path: str | Path) -> SimulationConfig:
    """Load and parse a simulation configuration file.

    Args:
        path: Path to YAML configuration file

    Returns:
        SimulationConfig instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    data = load_yaml_config(path)
    return parse_simulation_config(data)
