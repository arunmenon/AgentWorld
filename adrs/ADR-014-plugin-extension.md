# ADR-014: Plugin and Extension Model

## Status
Accepted

## Dependencies
- **[ADR-004](./ADR-004-trait-vector-persona.md)**: Custom traits as extension point
- **[ADR-005](./ADR-005-network-topology.md)**: Custom topologies
- **[ADR-009](./ADR-009-use-case-scenarios.md)**: Custom scenarios
- **[ADR-010](./ADR-010-evaluation-metrics.md)**: Custom validators/extractors

## Context

**Extensibility Requirements:**

AgentWorld needs extension points for:
- Custom network topologies beyond built-in types
- New scenario types (beyond product testing/data generation)
- Custom evaluation validators and extractors
- Additional LLM providers not in LiteLLM
- Domain-specific agent behaviors and tools

**Design Principles:**
1. **Discoverable**: Plugins auto-discovered without code changes
2. **Isolated**: Plugin failures don't crash core system
3. **Typed**: Strong typing for plugin interfaces
4. **Documented**: Clear contracts for plugin developers

**Extension Points Identified:**

| Extension Point | Use Case |
|-----------------|----------|
| Topology | New network structures (e.g., Erdős–Rényi, lattice) |
| Scenario | Domain-specific simulations (e.g., healthcare, education) |
| Validator | Custom quality checks |
| Extractor | Domain-specific data extraction |
| AgentTool | Tools agents can use (e.g., calculator, search) |
| LLMProvider | Custom model integrations |
| OutputFormat | Export formats (e.g., JSONL, Parquet) |

## Decision

Implement **entry-point based plugin system** using Python's `importlib.metadata` with Protocol-based interfaces.

### Plugin Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Plugin System                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Plugin Registry                           │   │
│  │                                                              │   │
│  │  Discovers plugins via entry points:                         │   │
│  │  - agentworld.topologies                                     │   │
│  │  - agentworld.scenarios                                      │   │
│  │  - agentworld.validators                                     │   │
│  │  - agentworld.extractors                                     │   │
│  │  - agentworld.tools                                          │   │
│  │  - agentworld.llm_providers                                  │   │
│  │  - agentworld.output_formats                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐         │
│  │  Built-in   │      │  Community  │      │   Custom    │         │
│  │  Plugins    │      │  Plugins    │      │   Plugins   │         │
│  │             │      │             │      │             │         │
│  │ MeshTopology│      │ LatticeTop  │      │ MyTopology  │         │
│  │ HubSpoke... │      │ ...         │      │ ...         │         │
│  └─────────────┘      └─────────────┘      └─────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Plugin Protocols (Interfaces)

```python
from typing import Protocol, runtime_checkable, TypeVar, Generic
from abc import abstractmethod

@runtime_checkable
class TopologyPlugin(Protocol):
    """Protocol for topology plugins."""

    @property
    def name(self) -> str:
        """Unique topology name (e.g., 'lattice', 'erdos_renyi')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    def build(self, agent_ids: List[str], **kwargs) -> nx.Graph:
        """Build the topology graph."""
        ...

    def get_parameters(self) -> List[ParameterSpec]:
        """Describe configurable parameters."""
        ...

@runtime_checkable
class ScenarioPlugin(Protocol):
    """Protocol for scenario plugins."""

    @property
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        ...

    async def setup(self, world: World, config: dict) -> None:
        """Configure world and agents for this scenario."""
        ...

    async def run(self, world: World) -> ScenarioResult:
        """Execute the scenario."""
        ...

    def get_config_schema(self) -> dict:
        """JSON Schema for scenario configuration."""
        ...

@runtime_checkable
class ValidatorPlugin(Protocol):
    """Protocol for validator plugins."""

    @property
    def name(self) -> str:
        ...

    async def validate(
        self,
        agent: Agent,
        response: str,
        context: ValidationContext
    ) -> ValidationResult:
        """Validate agent response."""
        ...

@runtime_checkable
class ExtractorPlugin(Protocol):
    """Protocol for extractor plugins."""

    @property
    def name(self) -> str:
        ...

    async def extract(
        self,
        messages: List[Message],
        config: dict
    ) -> dict:
        """Extract structured data from messages."""
        ...

@runtime_checkable
class AgentToolPlugin(Protocol):
    """Protocol for tools agents can use."""

    @property
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        """Description for agent's tool selection."""
        ...

    def get_schema(self) -> dict:
        """JSON Schema for tool parameters."""
        ...

    async def execute(self, **params) -> str:
        """Execute the tool and return result."""
        ...

@dataclass
class ParameterSpec:
    """Specification for a plugin parameter."""
    name: str
    type: str  # "int", "float", "str", "bool"
    description: str
    required: bool = True
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[List[Any]] = None
```

### Plugin Discovery and Registry

```python
from importlib.metadata import entry_points
import importlib

class PluginRegistry:
    """Central registry for all plugins."""

    ENTRY_POINT_GROUPS = {
        "topologies": "agentworld.topologies",
        "scenarios": "agentworld.scenarios",
        "validators": "agentworld.validators",
        "extractors": "agentworld.extractors",
        "tools": "agentworld.tools",
        "llm_providers": "agentworld.llm_providers",
        "output_formats": "agentworld.output_formats",
    }

    def __init__(self):
        self._plugins: Dict[str, Dict[str, Any]] = {
            group: {} for group in self.ENTRY_POINT_GROUPS
        }
        self._loaded = False

    def discover(self) -> None:
        """Discover all installed plugins."""
        if self._loaded:
            return

        for group_name, entry_point_name in self.ENTRY_POINT_GROUPS.items():
            eps = entry_points(group=entry_point_name)

            for ep in eps:
                try:
                    plugin_class = ep.load()
                    plugin = plugin_class()

                    # Validate plugin implements protocol
                    if self._validate_plugin(group_name, plugin):
                        self._plugins[group_name][plugin.name] = plugin
                        logger.info(f"Loaded plugin: {group_name}/{plugin.name}")
                    else:
                        logger.warning(
                            f"Plugin {ep.name} does not implement required protocol"
                        )

                except Exception as e:
                    logger.error(f"Failed to load plugin {ep.name}: {e}")

        self._loaded = True

    def _validate_plugin(self, group: str, plugin: Any) -> bool:
        """Validate plugin implements correct protocol."""
        protocols = {
            "topologies": TopologyPlugin,
            "scenarios": ScenarioPlugin,
            "validators": ValidatorPlugin,
            "extractors": ExtractorPlugin,
            "tools": AgentToolPlugin,
        }
        protocol = protocols.get(group)
        return protocol is None or isinstance(plugin, protocol)

    def get(self, group: str, name: str) -> Optional[Any]:
        """Get a specific plugin by group and name."""
        self.discover()
        return self._plugins.get(group, {}).get(name)

    def list(self, group: str) -> List[str]:
        """List all plugins in a group."""
        self.discover()
        return list(self._plugins.get(group, {}).keys())

    def get_all(self, group: str) -> Dict[str, Any]:
        """Get all plugins in a group."""
        self.discover()
        return self._plugins.get(group, {}).copy()

# Global registry instance
registry = PluginRegistry()
```

### Creating a Plugin Package

**Example: Custom Lattice Topology Plugin**

```
agentworld-lattice-topology/
├── pyproject.toml
├── src/
│   └── agentworld_lattice/
│       ├── __init__.py
│       └── topology.py
└── tests/
    └── test_lattice.py
```

**pyproject.toml:**
```toml
[project]
name = "agentworld-lattice-topology"
version = "1.0.0"
description = "Lattice topology plugin for AgentWorld"
dependencies = ["agentworld>=1.0.0", "networkx>=3.0"]

[project.entry-points."agentworld.topologies"]
lattice = "agentworld_lattice:LatticeTopology"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

**src/agentworld_lattice/topology.py:**
```python
import networkx as nx
from agentworld.plugins import TopologyPlugin, ParameterSpec

class LatticeTopology:
    """2D lattice/grid topology plugin."""

    @property
    def name(self) -> str:
        return "lattice"

    @property
    def description(self) -> str:
        return "2D grid topology where agents connect to 4 neighbors"

    def get_parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="rows",
                type="int",
                description="Number of rows in the grid",
                required=False,
                default=None,  # Auto-calculated from agent count
                min_value=1
            ),
            ParameterSpec(
                name="cols",
                type="int",
                description="Number of columns in the grid",
                required=False,
                default=None,
                min_value=1
            ),
            ParameterSpec(
                name="periodic",
                type="bool",
                description="Wrap edges to form a torus",
                required=False,
                default=False
            ),
        ]

    def build(self, agent_ids: List[str], **kwargs) -> nx.Graph:
        n = len(agent_ids)
        rows = kwargs.get("rows")
        cols = kwargs.get("cols")
        periodic = kwargs.get("periodic", False)

        # Auto-calculate dimensions if not provided
        if rows is None or cols is None:
            rows = int(n ** 0.5)
            cols = (n + rows - 1) // rows

        if rows * cols < n:
            raise ValueError(f"Grid {rows}x{cols} too small for {n} agents")

        # Create grid graph
        G = nx.grid_2d_graph(rows, cols, periodic=periodic)

        # Relabel nodes with agent IDs
        mapping = {(r, c): agent_ids[r * cols + c]
                   for r in range(rows) for c in range(cols)
                   if r * cols + c < n}
        G = nx.relabel_nodes(G, mapping)

        # Remove extra nodes if grid > agent count
        extra_nodes = [node for node in G.nodes() if isinstance(node, tuple)]
        G.remove_nodes_from(extra_nodes)

        return G
```

### Using Plugins in Configuration

```yaml
# config/simulation.yaml
simulation:
  name: "Lattice Network Study"

  topology:
    type: lattice  # Plugin name
    params:
      rows: 5
      cols: 5
      periodic: true

  scenario:
    type: information_spread  # Custom scenario plugin
    params:
      seed_agents: 2
      message: "Breaking news: ..."

  evaluation:
    validators:
      - name: persona_adherence  # Built-in
      - name: domain_accuracy    # Plugin
        params:
          domain: "finance"
          strictness: 0.8

    extractors:
      - name: sentiment          # Built-in
      - name: financial_entities # Plugin
```

### Plugin Sandboxing and Error Handling

```python
import asyncio
from contextlib import asynccontextmanager

class PluginSandbox:
    """Execute plugin code with isolation and error handling."""

    def __init__(self, timeout: float = 30.0, max_memory_mb: int = 512):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    @asynccontextmanager
    async def execute(self, plugin_name: str):
        """Context manager for sandboxed plugin execution."""
        try:
            yield
        except asyncio.TimeoutError:
            logger.error(f"Plugin {plugin_name} timed out after {self.timeout}s")
            raise PluginTimeoutError(plugin_name, self.timeout)
        except MemoryError:
            logger.error(f"Plugin {plugin_name} exceeded memory limit")
            raise PluginMemoryError(plugin_name, self.max_memory_mb)
        except Exception as e:
            logger.error(f"Plugin {plugin_name} failed: {e}")
            raise PluginExecutionError(plugin_name, e)

    async def run_with_timeout(self, coro, plugin_name: str):
        """Run coroutine with timeout."""
        async with self.execute(plugin_name):
            return await asyncio.wait_for(coro, timeout=self.timeout)

# Usage
sandbox = PluginSandbox(timeout=30.0)

async def run_validator(validator: ValidatorPlugin, agent, response, context):
    return await sandbox.run_with_timeout(
        validator.validate(agent, response, context),
        plugin_name=validator.name
    )
```

### Built-in Plugin Hooks

```python
class PluginHooks:
    """Lifecycle hooks for plugins."""

    @staticmethod
    def on_simulation_start(simulation: Simulation) -> None:
        """Called when simulation starts."""
        for plugin in registry.get_all("tools").values():
            if hasattr(plugin, "on_simulation_start"):
                plugin.on_simulation_start(simulation)

    @staticmethod
    def on_step_complete(step: int, world: World) -> None:
        """Called after each step completes."""
        for plugin in registry.get_all("validators").values():
            if hasattr(plugin, "on_step_complete"):
                plugin.on_step_complete(step, world)

    @staticmethod
    def on_simulation_end(simulation: Simulation, result: SimulationResult) -> None:
        """Called when simulation ends."""
        for plugin in registry.get_all("extractors").values():
            if hasattr(plugin, "on_simulation_end"):
                plugin.on_simulation_end(simulation, result)

# Integration in simulation engine (ADR-011)
class SimulationEngine:
    async def run(self, steps: int) -> SimulationResult:
        PluginHooks.on_simulation_start(self.simulation)

        for _ in range(steps):
            step_result = await self.step()
            PluginHooks.on_step_complete(self._step_number, self.world)

        result = SimulationResult(...)
        PluginHooks.on_simulation_end(self.simulation, result)
        return result
```

### Agent Tools Plugin Example

```python
class CalculatorTool:
    """Tool allowing agents to perform calculations."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform mathematical calculations. Input: mathematical expression."

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                }
            },
            "required": ["expression"]
        }

    async def execute(self, expression: str) -> str:
        """Safely evaluate mathematical expression."""
        try:
            # Safe evaluation with limited operations
            allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {e}"

# Usage in agent prompt
def build_tool_prompt(agent: Agent) -> str:
    tools = registry.get_all("tools")
    tool_descriptions = "\n".join([
        f"- {t.name}: {t.description}"
        for t in tools.values()
    ])
    return f"""
You have access to the following tools:
{tool_descriptions}

To use a tool, respond with:
TOOL: <tool_name>
INPUT: <tool_input>
"""
```

### CLI for Plugin Management

```python
import typer

plugin_app = typer.Typer(name="plugins", help="Manage AgentWorld plugins")

@plugin_app.command("list")
def list_plugins(group: str = typer.Option(None, help="Filter by plugin group")):
    """List all installed plugins."""
    registry.discover()

    if group:
        groups = [group]
    else:
        groups = list(PluginRegistry.ENTRY_POINT_GROUPS.keys())

    for g in groups:
        plugins = registry.get_all(g)
        if plugins:
            typer.echo(f"\n{g}:")
            for name, plugin in plugins.items():
                desc = getattr(plugin, "description", "No description")
                typer.echo(f"  - {name}: {desc}")

@plugin_app.command("info")
def plugin_info(group: str, name: str):
    """Show detailed plugin information."""
    plugin = registry.get(group, name)
    if not plugin:
        typer.echo(f"Plugin not found: {group}/{name}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Name: {plugin.name}")
    typer.echo(f"Description: {plugin.description}")

    if hasattr(plugin, "get_parameters"):
        typer.echo("\nParameters:")
        for param in plugin.get_parameters():
            required = "(required)" if param.required else "(optional)"
            typer.echo(f"  - {param.name} [{param.type}] {required}: {param.description}")

@plugin_app.command("validate")
def validate_plugin(package: str):
    """Validate a plugin package before installation."""
    # TODO: Implement validation logic
    pass
```

## Consequences

**Positive:**
- Clean extension points for all major features
- Auto-discovery eliminates manual registration
- Protocol-based typing catches errors early
- Plugin isolation prevents system crashes
- Enables community ecosystem

**Negative:**
- Entry point mechanism has discovery overhead
- Protocol validation at runtime vs compile time
- Plugin version compatibility management
- Documentation burden for plugin developers

**Tradeoffs:**
- Flexibility vs complexity
- Runtime discovery vs explicit registration
- Full isolation vs performance

## Related ADRs
- [ADR-004](./ADR-004-trait-vector-persona.md): Custom traits
- [ADR-005](./ADR-005-network-topology.md): Topology plugins
- [ADR-009](./ADR-009-use-case-scenarios.md): Scenario plugins
- [ADR-010](./ADR-010-evaluation-metrics.md): Validator/extractor plugins
