"""Open command - open simulation data in external applications."""

import json
import tempfile
from pathlib import Path
from typing import Optional
import webbrowser

import typer

from agentworld.cli.output import console, print_error, print_success, print_info
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


def open_simulation(
    simulation_id: str = typer.Argument(..., help="Simulation ID to open"),
    app: str = typer.Option(
        "browser",
        "--app",
        "-a",
        help="Application: browser, vscode, json, csv",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (for json/csv)",
    ),
) -> None:
    """Open simulation data in external applications.

    Supports opening in browser, VS Code, or exporting to files.
    """
    init_db()
    repo = Repository()

    # Get simulation
    sim = repo.get_simulation(simulation_id)
    if not sim:
        print_error(f"Simulation not found: {simulation_id}")
        raise typer.Exit(1)

    agents = repo.get_agents_for_simulation(simulation_id)
    messages = repo.get_messages_for_simulation(simulation_id)

    data = {
        "simulation": sim,
        "agents": agents,
        "messages": messages,
    }

    if app == "browser":
        _open_in_browser(simulation_id, data)
    elif app == "vscode":
        _open_in_vscode(simulation_id, data, output)
    elif app == "json":
        _export_json(simulation_id, data, output)
    elif app == "csv":
        _export_csv(simulation_id, messages, output)
    else:
        print_error(f"Unknown app: {app}")
        print_info("Supported: browser, vscode, json, csv")
        raise typer.Exit(1)


def _open_in_browser(simulation_id: str, data: dict) -> None:
    """Open simulation visualization in browser."""
    # Create a temporary HTML file with visualization
    html_content = _generate_html_visualization(data)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        prefix=f"agentworld_{simulation_id}_",
    ) as f:
        f.write(html_content)
        temp_path = f.name

    print_info(f"Opening in browser: {temp_path}")
    webbrowser.open(f"file://{temp_path}")
    print_success("Opened simulation in browser")


def _generate_html_visualization(data: dict) -> str:
    """Generate HTML visualization for simulation."""
    sim = data["simulation"]
    agents = data["agents"]
    messages = data["messages"]

    agents_html = "\n".join(
        f'<div class="agent"><strong>{a.get("name", "Unknown")}</strong> ({a.get("id", "")[:8]})</div>'
        for a in agents
    )

    messages_html = "\n".join(
        f'''<div class="message">
            <span class="step">Step {m.get("step", 0)}</span>
            <span class="sender">{m.get("sender_id", "")[:8]}</span>
            <div class="content">{m.get("content", "")[:500]}</div>
        </div>'''
        for m in messages
    )

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{sim.get("name", "Simulation")} - AgentWorld</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: system-ui; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .status {{ padding: 5px 10px; border-radius: 4px; font-size: 14px; }}
        .completed {{ background: #d4edda; color: #155724; }}
        .running {{ background: #cce5ff; color: #004085; }}
        .pending {{ background: #fff3cd; color: #856404; }}
        .grid {{ display: grid; grid-template-columns: 250px 1fr; gap: 20px; }}
        .sidebar {{ background: white; padding: 20px; border-radius: 8px; height: fit-content; }}
        .main {{ background: white; padding: 20px; border-radius: 8px; }}
        .agent {{ padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 4px; }}
        .message {{ padding: 15px; margin: 10px 0; border-left: 3px solid #007bff; background: #f8f9fa; }}
        .step {{ background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
        .sender {{ font-weight: bold; margin-left: 10px; }}
        .content {{ margin-top: 10px; white-space: pre-wrap; }}
        .stats {{ display: flex; gap: 20px; margin-top: 10px; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .stat-label {{ font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 {sim.get("name", "Simulation")}</h1>
            <span class="status {sim.get("status", "pending")}">{sim.get("status", "unknown")}</span>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{sim.get("current_step", 0)}/{sim.get("total_steps", 0)}</div>
                    <div class="stat-label">Steps</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(agents)}</div>
                    <div class="stat-label">Agents</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(messages)}</div>
                    <div class="stat-label">Messages</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${sim.get("total_cost", 0):.4f}</div>
                    <div class="stat-label">Cost</div>
                </div>
            </div>
        </div>
        <div class="grid">
            <div class="sidebar">
                <h3>Agents</h3>
                {agents_html}
            </div>
            <div class="main">
                <h3>Conversation</h3>
                {messages_html if messages_html else "<p>No messages yet</p>"}
            </div>
        </div>
    </div>
</body>
</html>"""


def _open_in_vscode(simulation_id: str, data: dict, output: Optional[Path]) -> None:
    """Open simulation data in VS Code."""
    import subprocess

    # Determine output path
    if output:
        file_path = output
    else:
        file_path = Path(tempfile.gettempdir()) / f"agentworld_{simulation_id}.json"

    # Write JSON
    file_path.write_text(json.dumps(data, indent=2, default=str))

    # Try to open in VS Code
    try:
        subprocess.run(["code", str(file_path)], check=True)
        print_success(f"Opened in VS Code: {file_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Could not open VS Code. Is it installed?")
        print_info(f"Data saved to: {file_path}")


def _export_json(simulation_id: str, data: dict, output: Optional[Path]) -> None:
    """Export simulation data as JSON."""
    if output:
        file_path = output
    else:
        file_path = Path(f"{simulation_id}.json")

    file_path.write_text(json.dumps(data, indent=2, default=str))
    print_success(f"Exported JSON: {file_path}")


def _export_csv(simulation_id: str, messages: list, output: Optional[Path]) -> None:
    """Export messages as CSV."""
    import csv

    if output:
        file_path = output
    else:
        file_path = Path(f"{simulation_id}_messages.csv")

    with open(file_path, "w", newline="") as f:
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

    print_success(f"Exported CSV: {file_path}")
