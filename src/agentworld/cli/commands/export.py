"""Export command - export simulation data to various formats."""

import json
import csv
from pathlib import Path
from typing import Optional

import typer

from agentworld.cli.output import console, print_error, print_success, print_info
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


def export(
    simulation_id: str = typer.Argument(..., help="Simulation ID to export"),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout for json)",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format: json, csv, hf (HuggingFace)",
    ),
    include: str = typer.Option(
        "messages",
        "--include",
        "-i",
        help="What to include: messages, memories, metrics, all",
    ),
    anonymize: bool = typer.Option(
        False,
        "--anonymize",
        help="Remove agent names (use Agent_1, Agent_2, etc.)",
    ),
) -> None:
    """Export simulation data to various formats.

    Supports JSON for general use, CSV for spreadsheets, and
    HuggingFace format for ML training.
    """
    init_db()
    repo = Repository()

    # Get simulation
    sim = repo.get_simulation(simulation_id)
    if not sim:
        print_error(f"Simulation not found: {simulation_id}")
        raise typer.Exit(1)

    # Get agents
    agents = repo.get_agents_for_simulation(simulation_id)
    agent_map = {a["id"]: a for a in agents}

    # Create anonymization mapping if needed
    anon_map = {}
    if anonymize:
        for i, agent in enumerate(agents, 1):
            anon_map[agent["id"]] = f"Agent_{i}"
            anon_map[agent.get("name", "")] = f"Agent_{i}"

    # Gather data based on include option
    data = {
        "simulation_id": simulation_id,
        "simulation_name": sim.get("name", ""),
        "status": sim.get("status", ""),
        "total_steps": sim.get("total_steps", 0),
        "current_step": sim.get("current_step", 0),
    }

    # Always include agent info
    if anonymize:
        data["agents"] = [
            {"id": anon_map.get(a["id"], a["id"]), "name": anon_map.get(a["name"], a["name"])}
            for a in agents
        ]
    else:
        data["agents"] = agents

    # Include messages
    if include in ("messages", "all"):
        messages = repo.get_messages_for_simulation(simulation_id)
        if anonymize:
            for msg in messages:
                msg["sender_id"] = anon_map.get(msg["sender_id"], msg["sender_id"])
                if msg.get("receiver_id"):
                    msg["receiver_id"] = anon_map.get(msg["receiver_id"], msg["receiver_id"])
        data["messages"] = messages

    # Include memories
    if include in ("memories", "all"):
        memories = []
        for agent in agents:
            agent_memories = repo.get_memories_for_agent(agent["id"])
            for mem in agent_memories:
                if anonymize:
                    mem["agent_id"] = anon_map.get(mem["agent_id"], mem["agent_id"])
                memories.append(mem)
        data["memories"] = memories

    # Include metrics
    if include in ("metrics", "all"):
        data["metrics"] = {
            "total_tokens": sim.get("total_tokens", 0),
            "total_cost": sim.get("total_cost", 0.0),
            "message_count": len(data.get("messages", [])),
        }

    # Export based on format
    if format == "json":
        output_str = json.dumps(data, indent=2, default=str)
        if output:
            output.write_text(output_str)
            print_success(f"Exported to {output}")
        else:
            console.print(output_str)

    elif format == "csv":
        if not output:
            print_error("CSV format requires --output file")
            raise typer.Exit(1)

        messages = data.get("messages", [])
        if not messages:
            print_error("No messages to export")
            raise typer.Exit(1)

        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["step", "sender_id", "receiver_id", "content", "timestamp"]
            )
            writer.writeheader()
            for msg in messages:
                writer.writerow({
                    "step": msg.get("step", 0),
                    "sender_id": msg.get("sender_id", ""),
                    "receiver_id": msg.get("receiver_id", ""),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", ""),
                })
        print_success(f"Exported {len(messages)} messages to {output}")

    elif format == "hf":
        if not output:
            output = Path(f"./{simulation_id}_dataset")

        output.mkdir(parents=True, exist_ok=True)

        # Create HuggingFace dataset format
        messages = data.get("messages", [])

        # Create conversations format
        conversations = []
        current_conv = []

        for msg in messages:
            sender = agent_map.get(msg.get("sender_id", ""), {}).get("name", msg.get("sender_id", ""))
            if anonymize:
                sender = anon_map.get(sender, sender)

            current_conv.append({
                "role": sender,
                "content": msg.get("content", ""),
            })

        if current_conv:
            conversations.append({"messages": current_conv})

        # Write dataset files
        data_file = output / "data.jsonl"
        with open(data_file, "w") as f:
            for conv in conversations:
                f.write(json.dumps(conv) + "\n")

        # Write dataset card
        readme = output / "README.md"
        readme.write_text(f"""---
dataset_info:
  features:
  - name: messages
    sequence:
      struct:
      - name: role
        dtype: string
      - name: content
        dtype: string
  num_rows: {len(conversations)}
---

# {sim.get('name', 'AgentWorld Simulation')} Dataset

Generated by AgentWorld from simulation {simulation_id}.

## Usage

```python
from datasets import load_dataset
dataset = load_dataset('{output}')
```
""")

        print_success(f"Exported HuggingFace dataset to {output}/")
        print_info(f"Contains {len(conversations)} conversations, {len(messages)} turns")
        console.print(f"\n[dim]Load with: datasets.load_dataset('{output}')[/dim]")

    else:
        print_error(f"Unknown format: {format}")
        raise typer.Exit(1)
