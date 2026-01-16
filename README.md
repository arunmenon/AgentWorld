# AgentWorld

A multi-agent simulation framework for product testing and data generation.

## Installation

```bash
pip install agentworld
```

## Quick Start

```bash
# Run a simulation
agentworld run examples/two_agents.yaml

# List simulations
agentworld list

# Inspect a simulation
agentworld inspect <simulation-id>
```

## Configuration

Create a YAML configuration file:

```yaml
name: "My Simulation"
initial_prompt: "Discuss the future of technology"
steps: 5
model: "openai/gpt-4o-mini"

agents:
  - name: Alice
    traits:
      openness: 0.9
      conscientiousness: 0.5
      extraversion: 0.7
      agreeableness: 0.6
      neuroticism: 0.3
    background: "A creative thinker"

  - name: Bob
    traits:
      openness: 0.3
      conscientiousness: 0.9
      extraversion: 0.4
      agreeableness: 0.5
      neuroticism: 0.2
    background: "A pragmatic engineer"
```

## License

MIT
