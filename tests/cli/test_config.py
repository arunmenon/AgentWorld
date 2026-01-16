"""Tests for CLI configuration loading."""

import pytest
import yaml
from pathlib import Path

from agentworld.cli.config import (
    load_yaml_config,
    parse_simulation_config,
    load_simulation_config,
)
from agentworld.core.exceptions import ConfigurationError


@pytest.fixture
def valid_config_file(tmp_path):
    """Create a valid configuration file."""
    config = {
        "name": "Test Simulation",
        "agents": [
            {"name": "Alice", "traits": {"openness": 0.8}},
            {"name": "Bob", "traits": {"extraversion": 0.7}},
        ],
        "steps": 5,
        "initial_prompt": "Discuss AI ethics",
        "model": "gpt-4o-mini",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file


@pytest.fixture
def minimal_config_file(tmp_path):
    """Create a minimal valid configuration file."""
    config = {
        "name": "Minimal Sim",
        "agents": ["Alice", "Bob"],
    }
    config_file = tmp_path / "minimal.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file


class TestLoadYamlConfig:
    """Tests for load_yaml_config function."""

    def test_loads_valid_yaml(self, valid_config_file):
        """Test loading valid YAML file."""
        data = load_yaml_config(valid_config_file)

        assert isinstance(data, dict)
        assert data["name"] == "Test Simulation"
        assert len(data["agents"]) == 2

    def test_raises_on_missing_file(self, tmp_path):
        """Test error on missing file."""
        missing = tmp_path / "missing.yaml"

        with pytest.raises(ConfigurationError) as exc:
            load_yaml_config(missing)
        assert "not found" in str(exc.value)

    def test_raises_on_invalid_yaml(self, tmp_path):
        """Test error on invalid YAML."""
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("{ invalid yaml: [")

        with pytest.raises(ConfigurationError) as exc:
            load_yaml_config(invalid_file)
        assert "Invalid YAML" in str(exc.value)

    def test_raises_on_non_dict(self, tmp_path):
        """Test error when YAML is not a dictionary."""
        list_file = tmp_path / "list.yaml"
        with open(list_file, "w") as f:
            yaml.dump(["item1", "item2"], f)

        with pytest.raises(ConfigurationError) as exc:
            load_yaml_config(list_file)
        assert "dictionary" in str(exc.value)


class TestParseSimulationConfig:
    """Tests for parse_simulation_config function."""

    def test_parses_valid_config(self):
        """Test parsing valid configuration."""
        data = {
            "name": "Test",
            "agents": [
                {"name": "Alice", "traits": {"openness": 0.8}},
                {"name": "Bob"},
            ],
            "steps": 10,
        }
        config = parse_simulation_config(data)

        assert config.name == "Test"
        assert len(config.agents) == 2
        assert config.agents[0].name == "Alice"
        assert config.steps == 10

    def test_parses_simple_agent_names(self):
        """Test parsing simple string agent names."""
        data = {
            "name": "Simple",
            "agents": ["Alice", "Bob", "Charlie"],
        }
        config = parse_simulation_config(data)

        assert len(config.agents) == 3
        assert config.agents[0].name == "Alice"
        assert config.agents[1].name == "Bob"

    def test_raises_on_missing_name(self):
        """Test error on missing name field."""
        data = {
            "agents": [{"name": "Alice"}],
        }

        with pytest.raises(ConfigurationError) as exc:
            parse_simulation_config(data)
        assert "name" in str(exc.value)

    def test_raises_on_missing_agents(self):
        """Test error on missing agents field."""
        data = {
            "name": "No Agents",
        }

        with pytest.raises(ConfigurationError) as exc:
            parse_simulation_config(data)
        assert "agent" in str(exc.value).lower()

    def test_raises_on_empty_agents(self):
        """Test error on empty agents list."""
        data = {
            "name": "Empty Agents",
            "agents": [],
        }

        with pytest.raises(ConfigurationError) as exc:
            parse_simulation_config(data)
        assert "agent" in str(exc.value).lower()

    def test_raises_on_agent_without_name(self):
        """Test error on agent without name."""
        data = {
            "name": "Test",
            "agents": [{"traits": {"openness": 0.5}}],  # No name
        }

        with pytest.raises(ConfigurationError) as exc:
            parse_simulation_config(data)
        assert "name" in str(exc.value)

    def test_default_values(self):
        """Test default values are applied."""
        data = {
            "name": "Defaults",
            "agents": [{"name": "Alice"}],
        }
        config = parse_simulation_config(data)

        assert config.steps == 10
        assert config.model == "openai/gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.seed is None

    def test_custom_values(self):
        """Test custom values override defaults."""
        data = {
            "name": "Custom",
            "agents": [{"name": "Alice"}],
            "steps": 25,
            "model": "gpt-4",
            "temperature": 0.9,
            "seed": 42,
        }
        config = parse_simulation_config(data)

        assert config.steps == 25
        assert config.model == "gpt-4"
        assert config.temperature == 0.9
        assert config.seed == 42


class TestLoadSimulationConfig:
    """Tests for load_simulation_config function."""

    def test_loads_and_parses(self, valid_config_file):
        """Test loading and parsing config file."""
        config = load_simulation_config(valid_config_file)

        assert config.name == "Test Simulation"
        assert len(config.agents) == 2
        assert config.steps == 5

    def test_minimal_config(self, minimal_config_file):
        """Test loading minimal config file."""
        config = load_simulation_config(minimal_config_file)

        assert config.name == "Minimal Sim"
        assert len(config.agents) == 2
        assert config.agents[0].name == "Alice"

    def test_handles_path_string(self, valid_config_file):
        """Test handling string path."""
        config = load_simulation_config(str(valid_config_file))
        assert config.name == "Test Simulation"
