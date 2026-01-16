# UI-ADR-005: CLI Design & Commands

## Status
Accepted

## Dependencies
- **ADR-007**: Visualization Strategy (establishes CLI + Web dual interface)
- **ADR-008**: Persistence & State Management (shared SQLite enables CLI-Web interop)
- **ADR-012**: API & WebSocket Event Schema (CLI uses same backend API)
- **UI-ADR-001**: Design System (color palette applied to Rich output)
- **UI-ADR-002**: Information Architecture (CLI commands mirror web navigation)

## Context

The CLI is the **primary interface for researchers and developers**, providing:

1. **Scriptability**: Batch runs, CI/CD integration, automation
2. **Reproducibility**: Exact command logs for papers and documentation
3. **SSH accessibility**: Remote server access without port forwarding
4. **Speed**: Faster iteration than browser-based workflows
5. **Composition**: Unix pipe integration (`agentworld export | jq | ...`)

### User Personas & CLI Usage

| Persona | Primary CLI Use Cases |
|---------|----------------------|
| **Dr. Maya** (Researcher) | Batch experiment runs, analysis scripts, result export |
| **Jordan** (Developer) | Debugging, config testing, API exploration |
| **Sam** (Data Engineer) | Data generation pipelines, format conversion |
| **Alex** (PM) | Quick status checks, result previews |

### CLI Design Principles

1. **Discoverability**: `--help` at every level, rich examples
2. **Consistency**: Predictable flag patterns across commands
3. **Composability**: JSON output for piping, exit codes for scripting
4. **Interactivity**: Interactive mode for complex configs, non-interactive for automation
5. **Parity**: Every Web UI action has CLI equivalent

## Decision

Implement a comprehensive CLI using **Typer** (for command structure) and **Rich** (for formatted output) with full feature parity to the Web UI.

### 1. Command Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENTWORLD CLI STRUCTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  agentworld                                                         │
│  │                                                                  │
│  ├── run <config.yaml>            Run simulation from config        │
│  │   ├── --steps N                Limit steps (default: from config)│
│  │   ├── --output DIR             Output directory                  │
│  │   ├── --quiet                  Minimal output                    │
│  │   ├── --seed N                 Random seed (reproducibility)     │
│  │   ├── --budget AMOUNT          Cost limit in USD                 │
│  │   ├── --provider NAME          Override LLM provider             │
│  │   └── --watch                  Live output (like tail -f)        │
│  │                                                                  │
│  ├── create                       Create new resources              │
│  │   ├── simulation               Interactive simulation builder    │
│  │   ├── persona                  Interactive persona builder       │
│  │   └── experiment               A/B experiment setup              │
│  │                                                                  │
│  ├── list                         List resources                    │
│  │   ├── simulations              List all simulations              │
│  │   │   ├── --status STATUS      Filter by status                  │
│  │   │   ├── --recent N           Show N most recent                │
│  │   │   └── --format json|table  Output format                     │
│  │   ├── personas                 List saved personas               │
│  │   └── experiments              List experiments                  │
│  │                                                                  │
│  ├── show <id>                    Show resource details             │
│  │   ├── --format json|yaml|rich  Output format                     │
│  │   ├── --include-memory         Include agent memories            │
│  │   ├── --include-reasoning      Include reasoning traces          │
│  │   └── --step N                 Show state at specific step       │
│  │                                                                  │
│  ├── resume <id>                  Resume paused simulation          │
│  │   ├── --from-checkpoint N      Resume from specific checkpoint   │
│  │   └── --steps N                Run N more steps                  │
│  │                                                                  │
│  ├── export <id>                  Export simulation data            │
│  │   ├── --format json|csv|hf     Export format                     │
│  │   ├── --output FILE            Output path                       │
│  │   ├── --include TYPE           messages|memories|metrics|all     │
│  │   └── --anonymize              Remove agent names                │
│  │                                                                  │
│  ├── analyze <id>                 Run analysis on simulation        │
│  │   ├── --extract-opinions       Extract opinions per agent        │
│  │   ├── --extract-themes         Identify recurring themes         │
│  │   ├── --validate               Run persona adherence checks      │
│  │   └── --output FILE            Save analysis results             │
│  │                                                                  │
│  ├── inject <id>                  Inject stimulus (requires paused) │
│  │   ├── --message TEXT           Message content                   │
│  │   ├── --target AGENTS          Target agent IDs (comma-sep)      │
│  │   └── --type TYPE              moderator|event|private           │
│  │                                                                  │
│  ├── serve                        Start web server                  │
│  │   ├── --port N                 Port (default: 8000)              │
│  │   ├── --host ADDR              Host (default: 127.0.0.1)         │
│  │   └── --no-browser             Don't open browser                │
│  │                                                                  │
│  ├── open <id>                    Open simulation in web browser    │
│  │   ├── --panel PANEL            Open specific panel               │
│  │   └── --agent AGENT_ID         Select specific agent             │
│  │                                                                  │
│  ├── config                       Manage configuration              │
│  │   ├── show                     Display current config            │
│  │   ├── set KEY VALUE            Set configuration value           │
│  │   ├── providers                List configured providers         │
│  │   └── providers add NAME       Add new provider                  │
│  │                                                                  │
│  └── version                      Show version info                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Rich Output Formatting

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RICH OUTPUT EXAMPLES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  $ agentworld run focus-group.yaml                                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 🚀 AgentWorld - Focus Group: Product Pricing           v1.0.0│  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │ Simulation ID: focus-group-2024-01-15-abc123                 │  │
│  │ Agents: 6 │ Topology: Hub-Spoke │ Provider: OpenAI GPT-4o    │  │
│  │                                                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ Progress: ████████████████████░░░░░░░░░░░░░░░░░░  45/100 45% │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │ [Step 45]                                                    │  │
│  │ 🟣 Lisa (Engineer): "I think the pricing model needs to      │  │
│  │    account for different user tiers..."                      │  │
│  │                                                              │  │
│  │ 🔵 Bob (Designer): "From a UX perspective, we should         │  │
│  │    consider progressive disclosure..."                       │  │
│  │                                                              │  │
│  │ 💭 Carol is thinking...                                      │  │
│  │                                                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ 💬 Messages: 89 │ 🧠 Reflections: 5 │ 💰 Cost: $3.42         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Press: [Space] Pause │ [→] Step │ [q] Quit │ [i] Inject           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. List Command Output

```
$ agentworld list simulations --recent 5

┌─────────────────────────────────────────────────────────────────────┐
│ ID                          │ Status    │ Steps │ Cost   │ Created │
├─────────────────────────────┼───────────┼───────┼────────┼─────────┤
│ focus-group-2024-01-abc     │ ● Running │ 45    │ $3.42  │ 2m ago  │
│ data-gen-support-xyz        │ ✓ Done    │ 100   │ $8.91  │ 1h ago  │
│ product-test-beta-123       │ ◐ Paused  │ 67    │ $5.23  │ 2h ago  │
│ experiment-pricing-456      │ ✓ Done    │ 200   │ $15.80 │ 1d ago  │
│ focus-group-ux-789          │ ✕ Error   │ 23    │ $2.10  │ 2d ago  │
└─────────────────────────────────────────────────────────────────────┘

Total: 42 simulations │ 12 running │ 25 completed │ 5 paused
```

### 4. Show Command Output

```
$ agentworld show focus-group-2024-01-abc --include-memory

┌─────────────────────────────────────────────────────────────────────┐
│ SIMULATION: focus-group-2024-01-abc                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Name:        Product Pricing Focus Group                            │
│ Status:      ● Running (Step 45/100)                                │
│ Created:     2024-01-15 10:23:45                                    │
│ Topology:    Hub-Spoke (Moderator as hub)                           │
│ Provider:    OpenAI GPT-4o                                          │
│ Seed:        42                                                     │
│                                                                     │
│ AGENTS                                                              │
│ ──────                                                              │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Name     │ Role      │ O    │ C    │ E    │ A    │ N    │ Msgs ││
│ ├──────────┼───────────┼──────┼──────┼──────┼──────┼──────┼──────┤│
│ │ Lisa     │ Engineer  │ 0.85 │ 0.72 │ 0.45 │ 0.68 │ 0.32 │ 15   ││
│ │ Bob      │ Designer  │ 0.78 │ 0.65 │ 0.82 │ 0.75 │ 0.28 │ 18   ││
│ │ Carol    │ Manager   │ 0.52 │ 0.88 │ 0.62 │ 0.71 │ 0.41 │ 12   ││
│ │ Dan      │ Marketer  │ 0.67 │ 0.58 │ 0.91 │ 0.69 │ 0.35 │ 14   ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ MEMORY: Lisa (34 observations, 5 reflections)                       │
│ ──────────────────────────────────────                              │
│ [Reflection] "The team seems to prioritize cost over features       │
│               when evaluating new products."                        │
│               Importance: 9/10 │ 5 min ago                          │
│                                                                     │
│ [Observation] "Bob mentioned budget constraints multiple times"     │
│               Importance: 7/10 │ 8 min ago                          │
│                                                                     │
│ [Observation] "Carol asked about enterprise pricing"                │
│               Importance: 6/10 │ 12 min ago                         │
│                                                                     │
│ ... (31 more, use --verbose for full list)                          │
│                                                                     │
│ METRICS                                                             │
│ ───────                                                             │
│ Messages:    89                                                     │
│ Reflections: 5                                                      │
│ Tokens:      45,230                                                 │
│ Cost:        $3.42                                                  │
│ Duration:    12m 34s                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Use 'agentworld open focus-group-2024-01-abc' to view in browser
```

### 5. Interactive Persona Builder

```
$ agentworld create persona

┌─────────────────────────────────────────────────────────────────────┐
│ 🧑 Interactive Persona Builder                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Let's create a new persona for your simulation.                     │
│                                                                     │
│ Name: Lisa Chen                                                     │
│ Role/Occupation: Software Engineer                                  │
│ Age: 32                                                             │
│                                                                     │
│ Brief description:                                                  │
│ > Tech-savvy professional, skeptical of marketing claims_           │
│                                                                     │
│ BIG FIVE PERSONALITY TRAITS                                         │
│ ──────────────────────────────                                      │
│ Adjust each trait using arrow keys or type a value (0.0-1.0):       │
│                                                                     │
│ Openness (Practical ↔ Creative)                                    │
│ [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░] 0.85                                        │
│                                                                     │
│ Conscientiousness (Flexible ↔ Disciplined)                         │
│ [▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░] 0.72                                        │
│                                                                     │
│ Extraversion (Reserved ↔ Outgoing)                                 │
│ [▓▓▓▓▓▓▓▓▓░░░░░░░░░░░] 0.45                                        │
│                                                                     │
│ Agreeableness (Competitive ↔ Cooperative)                          │
│ [▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░] 0.68                                        │
│                                                                     │
│ Neuroticism (Calm ↔ Anxious)                                       │
│ [▓▓▓▓▓▓░░░░░░░░░░░░░░] 0.32                                        │
│                                                                     │
│ CUSTOM TRAITS (optional)                                            │
│ ─────────────────────────                                           │
│ Add custom trait? (y/N): y                                          │
│ Trait name: tech_savviness                                          │
│ Value (0.0-1.0): 0.90                                               │
│                                                                     │
│ Add another? (y/N): n                                               │
│                                                                     │
│ ──────────────────────────────────────────────────────────────────  │
│ [Enter] Save persona │ [Esc] Cancel │ [?] Help                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6. JSON Output for Scripting

```bash
# Machine-readable output for scripting
$ agentworld list simulations --format json | jq '.[] | select(.status == "completed")'

[
  {
    "id": "data-gen-support-xyz",
    "name": "Customer Support Data Generation",
    "status": "completed",
    "steps": 100,
    "cost": 8.91,
    "created_at": "2024-01-15T09:00:00Z",
    "agents": ["support_agent", "customer_1", "customer_2", "customer_3"]
  },
  ...
]

# Export for HuggingFace datasets
$ agentworld export data-gen-support-xyz --format hf --output ./dataset
Exported 1,234 conversation turns to ./dataset/
Ready for: datasets.load_dataset('./dataset')

# Pipe analysis to file
$ agentworld analyze focus-group-abc --extract-opinions --format json > opinions.json
```

### 7. Exit Codes & Error Handling

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXIT CODES                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Code │ Meaning              │ Example Scenario                     │
│  ─────┼──────────────────────┼─────────────────────────────────────│
│  0    │ Success              │ Simulation completed normally        │
│  1    │ General error        │ Invalid config, missing file         │
│  2    │ Budget exceeded      │ Cost limit reached                   │
│  3    │ Provider error       │ API rate limit, auth failure         │
│  4    │ Timeout              │ Step timeout exceeded                │
│  5    │ User interrupt       │ Ctrl+C pressed                       │
│  6    │ Validation error     │ Persona adherence failed             │
│                                                                     │
│  Usage in scripts:                                                  │
│  ─────────────────                                                  │
│  agentworld run config.yaml --budget 10                             │
│  if [ $? -eq 2 ]; then                                              │
│    echo "Budget exceeded, results may be incomplete"                │
│    agentworld export $SIM_ID --output partial_results.json          │
│  fi                                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8. Environment Variables

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT VARIABLES                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Variable                    │ Description          │ Default       │
│  ────────────────────────────┼──────────────────────┼─────────────│
│  AGENTWORLD_CONFIG_DIR       │ Config directory     │ ~/.agentworld │
│  AGENTWORLD_DB_PATH          │ SQLite database path │ (config dir)  │
│  AGENTWORLD_DEFAULT_PROVIDER │ Default LLM provider │ openai        │
│  AGENTWORLD_BUDGET_LIMIT     │ Default budget limit │ 10.00         │
│  AGENTWORLD_LOG_LEVEL        │ Logging verbosity    │ INFO          │
│  AGENTWORLD_NO_COLOR         │ Disable colors       │ false         │
│  AGENTWORLD_JSON_OUTPUT      │ Always output JSON   │ false         │
│                                                                     │
│  Provider-specific (from ADR-003):                                  │
│  OPENAI_API_KEY              │ OpenAI API key       │ (required)    │
│  ANTHROPIC_API_KEY           │ Anthropic API key    │ (optional)    │
│  OLLAMA_HOST                 │ Ollama server URL    │ localhost:11434│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9. CLI-Web Interoperability (Cross-ref: ADR-008)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLI ↔ WEB INTEROP                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Shared State via SQLite (ADR-008):                                 │
│  ─────────────────────────────────                                  │
│                                                                     │
│  ┌─────────────┐         ┌─────────────┐                           │
│  │   CLI       │         │   Web UI    │                           │
│  │  Process    │◄───────►│   Server    │                           │
│  └──────┬──────┘         └──────┬──────┘                           │
│         │                       │                                   │
│         │    ┌─────────────┐   │                                   │
│         └───►│  SQLite DB  │◄──┘                                   │
│              └─────────────┘                                        │
│                                                                     │
│  Workflow Examples:                                                 │
│  ─────────────────                                                  │
│                                                                     │
│  1. Start in CLI, view in Web:                                      │
│     $ agentworld run config.yaml &                                  │
│     $ agentworld open $SIM_ID    # Opens in browser                 │
│                                                                     │
│  2. Create in Web, run in CLI:                                      │
│     # Create simulation in Web UI                                   │
│     $ agentworld resume web-created-sim-123                         │
│                                                                     │
│  3. Pause in Web, continue in CLI:                                  │
│     # Pause via Web UI pause button                                 │
│     $ agentworld resume sim-123 --steps 50                          │
│                                                                     │
│  4. Batch CLI, analyze in Web:                                      │
│     $ for config in experiments/*.yaml; do                          │
│     $   agentworld run $config --quiet                              │
│     $ done                                                          │
│     # View all results in Web dashboard                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 10. Tab Completion Setup

```bash
# Bash completion (add to ~/.bashrc)
eval "$(_AGENTWORLD_COMPLETE=bash_source agentworld)"

# Zsh completion (add to ~/.zshrc)
eval "$(_AGENTWORLD_COMPLETE=zsh_source agentworld)"

# Fish completion
_AGENTWORLD_COMPLETE=fish_source agentworld | source

# Example completions:
$ agentworld run <TAB>
config.yaml  focus-group.yaml  experiment.yaml

$ agentworld show <TAB>
focus-group-2024-01-abc  data-gen-xyz  experiment-123

$ agentworld list simulations --status <TAB>
running  paused  completed  error

$ agentworld export sim-123 --format <TAB>
json  csv  hf
```

### 11. Help System

```
$ agentworld --help

 Usage: agentworld [OPTIONS] COMMAND [ARGS]...

 AgentWorld - Multi-agent LLM simulation framework

 Build simulated environments with LLM-powered agents for product testing,
 data generation, and social simulation research.

╭─ Commands ──────────────────────────────────────────────────────────────╮
│ run        Run a simulation from configuration file                     │
│ create     Create new simulation, persona, or experiment                │
│ list       List simulations, personas, or experiments                   │
│ show       Show detailed information about a resource                   │
│ resume     Resume a paused simulation                                   │
│ export     Export simulation data to various formats                    │
│ analyze    Run analysis on simulation results                           │
│ inject     Inject stimulus into running/paused simulation               │
│ serve      Start the web server                                         │
│ open       Open simulation in web browser                               │
│ config     View and modify configuration                                │
│ version    Show version information                                     │
╰─────────────────────────────────────────────────────────────────────────╯

╭─ Options ───────────────────────────────────────────────────────────────╮
│ --verbose, -v     Enable verbose output                                 │
│ --quiet, -q       Minimal output (errors only)                          │
│ --json            Output as JSON (for scripting)                        │
│ --no-color        Disable colored output                                │
│ --help            Show this message and exit                            │
╰─────────────────────────────────────────────────────────────────────────╯

 Examples:

   # Quick start with default config
   agentworld run examples/focus-group.yaml

   # Create new persona interactively
   agentworld create persona

   # Export results for analysis
   agentworld export sim-123 --format csv --output results.csv

   # Start web UI
   agentworld serve --port 8080

 Documentation: https://agentworld.dev/docs
 Report issues: https://github.com/agentworld/agentworld/issues
```

## Consequences

### Positive

- **Full feature parity** with Web UI enables flexible workflows
- **Scriptability** supports automation and CI/CD
- **Rich output** provides good UX without browser
- **JSON mode** enables Unix-style composition
- **Interactive builders** lower barrier for complex configs
- **Shared state** enables seamless CLI/Web transitions

### Negative

- **Dual interface maintenance** requires keeping CLI updated with Web
- **Rich formatting** may not render in all terminals
- **Interactive modes** not suitable for pure scripting (need non-interactive flags)

### Implementation Stack

```python
# CLI Framework
typer          # Command structure, argument parsing
rich           # Formatted output, progress bars, tables
click          # Additional CLI utilities (via Typer)

# Interactive
questionary    # Interactive prompts
prompt_toolkit # Advanced input handling

# Output
tabulate       # Table formatting fallback
pyyaml         # YAML parsing/export
```

### Cross-References

| ADR | Relationship |
|-----|--------------|
| **ADR-003** | Provider configuration, API key management |
| **ADR-007** | Establishes CLI as primary interface |
| **ADR-008** | SQLite enables CLI-Web state sharing |
| **ADR-009** | Scenarios can be run via CLI |
| **ADR-010** | Analysis commands use evaluation system |
| **ADR-012** | CLI uses same backend API as Web |
| **UI-ADR-001** | Color palette applied to Rich output |
| **UI-ADR-002** | Command structure mirrors web navigation |
| **UI-ADR-003** | Control commands (run, pause, resume) |
| **UI-ADR-004** | Text-based alternative to visualizations |
