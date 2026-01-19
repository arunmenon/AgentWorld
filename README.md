# AgentWorld

A multi-agent simulation framework for AI agent testing and synthetic training data generation.

## Overview

AgentWorld enables you to:
- **Test AI Agents**: Benchmark external agents against realistic simulated personas
- **Generate Training Data**: Create high-quality synthetic datasets in multiple formats
- **Run Social Simulations**: Model multi-agent conversations with diverse personalities

## Features

### Core Simulation
- **Persona-driven agents** with Big Five personality traits (OCEAN model)
- **Flexible topology** - mesh, hub-spoke, ring, or custom networks
- **Memory system** - observations, reflections, and retrieval
- **Checkpoint/restore** - save and resume simulation state
- **Step-by-step control** - pause, resume, inject stimuli

### Agent Testing
- **External agent injection** - replace any simulated agent with your HTTP endpoint
- **Circuit breaker protection** - automatic failover and retry logic
- **Privacy tiers** - control what persona data is shared externally
- **Performance metrics** - latency percentiles, error rates, circuit state

### Training Data Export
- **JSONL** - Raw message format
- **OpenAI** - Fine-tuning format for GPT models
- **Anthropic** - Claude fine-tuning format
- **ShareGPT** - Open-source model training (Vicuna, etc.)
- **Alpaca** - Instruction tuning format
- **DPO** - Preference pairs for RLHF (requires evaluation scores)

### Evaluation Framework
- **Heuristic evaluators** - length check, keyword filter
- **LLM-based evaluators** - persona adherence, coherence, relevance, consistency
- **Provenance tracking** - judge model, prompt hash, cost, latency
- **Score filtering** - filter exports by quality threshold

### Interfaces
- **CLI** - Full command-line interface
- **REST API** - FastAPI with OpenAPI docs
- **WebSocket** - Real-time simulation events
- **Web UI** - React dashboard with live visualization

---

## Installation

```bash
# Clone the repository
git clone https://github.com/arunmenon/AgentWorld.git
cd AgentWorld

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)
```

---

## Quick Start

### 1. Run a Simulation

```bash
# Run from YAML config
python -m agentworld run examples/two_agents.yaml

# List all simulations
python -m agentworld list

# Inspect a simulation
python -m agentworld inspect <simulation-id>

# Step through simulation
python -m agentworld step <simulation-id> --count=5
```

### 2. Start the Web UI

```bash
# Start API server (terminal 1)
python -m agentworld serve

# Start web UI (terminal 2)
cd web && npm install && npm run dev
```

Then open http://localhost:5173

### 3. Export Training Data

```bash
# Export as OpenAI fine-tuning format
python -m agentworld export <simulation-id> --format=openai --output=data.jsonl

# Available formats: jsonl, openai, anthropic, sharegpt, alpaca, dpo
```

---

## Configuration

### Simulation YAML

```yaml
name: "Team Discussion"
initial_prompt: "Discuss the future of AI"
steps: 10
model: "openai/gpt-4o-mini"

agents:
  - name: Alice
    traits:
      openness: 0.9
      conscientiousness: 0.5
      extraversion: 0.7
      agreeableness: 0.6
      neuroticism: 0.3
    background: "AI researcher passionate about ethics"

  - name: Bob
    traits:
      openness: 0.4
      conscientiousness: 0.9
      extraversion: 0.5
      agreeableness: 0.7
      neuroticism: 0.2
    background: "Software engineer focused on practical applications"

topology:
  type: mesh  # or: hub_spoke, ring, fully_connected

memory:
  enabled: true
  max_observations: 100
  reflection_threshold: 5
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
ANTHROPIC_API_KEY=sk-ant-...
AGENTWORLD_DB_PATH=./agentworld.db
AGENTWORLD_LOG_LEVEL=INFO
```

---

## CLI Reference

```bash
# Simulation Management
agentworld run <config.yaml>      # Create and run simulation
agentworld list [--json]          # List all simulations
agentworld inspect <id>           # Show simulation details
agentworld show <id>              # Detailed view with messages
agentworld step <id> [--count=N]  # Advance simulation steps
agentworld inject <id> "message"  # Inject stimulus

# Checkpoints
agentworld checkpoint save <id>   # Save checkpoint
agentworld checkpoint list <id>   # List checkpoints
agentworld checkpoint restore <checkpoint-id>

# Personas
agentworld persona list           # List persona library
agentworld persona show <id>      # Show persona details
agentworld persona search <query> # Search personas
agentworld persona collection list

# Export
agentworld export <id> --format=openai --output=data.jsonl

# Plugins
agentworld plugins list           # List installed plugins
agentworld plugins groups         # Show plugin categories

# Server
agentworld serve [--port=8000]    # Start API server
```

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/simulations` | List simulations |
| POST | `/api/v1/simulations` | Create simulation |
| GET | `/api/v1/simulations/{id}` | Get simulation |
| DELETE | `/api/v1/simulations/{id}` | Delete simulation |
| POST | `/api/v1/simulations/{id}/start` | Start simulation |
| POST | `/api/v1/simulations/{id}/pause` | Pause simulation |
| POST | `/api/v1/simulations/{id}/step` | Step simulation |
| POST | `/api/v1/simulations/{id}/inject` | Inject message |
| GET | `/api/v1/simulations/{id}/agents` | List agents |
| GET | `/api/v1/simulations/{id}/messages` | List messages |

### Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/simulations/{id}/export/formats` | List available formats |
| GET | `/api/v1/simulations/{id}/export?format=jsonl` | Export as JSONL |
| GET | `/api/v1/simulations/{id}/export?format=openai` | Export as OpenAI |
| GET | `/api/v1/simulations/{id}/export?format=anthropic` | Export as Anthropic |
| GET | `/api/v1/simulations/{id}/export?format=sharegpt` | Export as ShareGPT |
| GET | `/api/v1/simulations/{id}/export?format=alpaca` | Export as Alpaca |
| GET | `/api/v1/simulations/{id}/export?format=dpo` | Export as DPO pairs |

### Evaluation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/simulations/{id}/evaluate` | Run evaluators |
| GET | `/api/v1/simulations/{id}/evaluations` | Get evaluations |
| GET | `/api/v1/simulations/{id}/evaluations/summary` | Get summary |

### Agent Injection Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/simulations/{id}/inject-agent` | Inject external agent |
| GET | `/api/v1/simulations/{id}/injected-agents` | List injected agents |
| DELETE | `/api/v1/simulations/{id}/inject-agent/{agent_id}` | Remove agent |

### WebSocket

```javascript
// Connect to simulation events
const ws = new WebSocket('ws://localhost:8000/ws/simulations/{id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Event types: connected, step.started, step.completed, message.created
  console.log(data.type, data);
};
```

---

## Agent Injection

Test your external AI agent against simulated personas:

```bash
# Inject an external agent
curl -X POST http://localhost:8000/api/v1/simulations/{id}/inject-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "alice-agent-id",
    "endpoint_url": "https://your-agent.com/respond",
    "timeout_seconds": 30,
    "privacy_tier": "basic"
  }'
```

Your endpoint receives:
```json
{
  "schema_version": "1.0",
  "request_id": "uuid",
  "agent_id": "string",
  "persona_ref": { "persona_id": "...", "persona_hash": "..." },
  "conversation_context": { "last_k_turns": [...] },
  "current_stimulus": "Hello, how are you?"
}
```

Your endpoint returns:
```json
{
  "response_text": "I'm doing well, thanks for asking!",
  "confidence": 0.95
}
```

---

## Evaluation

Run quality evaluations on simulation messages:

```bash
# Run heuristic evaluators
curl -X POST http://localhost:8000/api/v1/simulations/{id}/evaluate \
  -H "Content-Type: application/json" \
  -d '{"evaluator_names": ["length_check", "keyword_filter"]}'

# Run LLM-based evaluators
curl -X POST http://localhost:8000/api/v1/simulations/{id}/evaluate \
  -H "Content-Type: application/json" \
  -d '{"evaluator_names": ["persona_adherence", "coherence", "relevance"]}'

# Get evaluation summary
curl http://localhost:8000/api/v1/simulations/{id}/evaluations/summary
```

Available evaluators:
- `length_check` - Message length validation
- `keyword_filter` - Prohibited content detection
- `persona_adherence` - Does response match persona traits?
- `coherence` - Is the response logically consistent?
- `relevance` - Is the response on-topic?
- `consistency` - Does it match previous statements?

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI (React)                        │
│         Dashboard │ Simulations │ Personas │ Settings        │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   REST API (FastAPI)   │
                    │   WebSocket Events     │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                    Core Services                            │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Simulation │   Export    │  Evaluation │ Agent Injection │
│   Runner    │   Service   │  Framework  │    Provider     │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                    Infrastructure                           │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Agents    │   Memory    │  Topology   │   Persistence   │
│  (LiteLLM)  │   System    │   Network   │   (SQLAlchemy)  │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

See [Architecture Decision Records](./adrs/) for detailed design documentation.

---

## Development

### Running Tests

```bash
# Python tests
python -m pytest tests/ -v

# Frontend tests
cd web && npm test
```

### Project Structure

```
AgentWorld/
├── src/agentworld/
│   ├── agents/          # Agent implementations
│   ├── api/             # FastAPI routes & schemas
│   ├── cli/             # CLI commands
│   ├── core/            # Core models
│   ├── evaluation/      # Evaluator framework
│   ├── llm/             # LLM provider (LiteLLM)
│   ├── memory/          # Memory system
│   ├── persistence/     # Database models & repository
│   ├── scenarios/       # Scenario types
│   ├── services/        # Export service
│   ├── simulation/      # Runner, control, checkpoint
│   └── topology/        # Network topologies
├── web/                 # React frontend
├── tests/               # Test suites
├── adrs/                # Architecture Decision Records
└── examples/            # Example configurations
```

---

## License

MIT

---

## Links

- [GitHub Repository](https://github.com/arunmenon/AgentWorld)
- [Architecture Decision Records](./adrs/)
- [API Documentation](http://localhost:8000/docs) (when server running)
