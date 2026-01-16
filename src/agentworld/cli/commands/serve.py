"""Serve command - start a web server for simulation visualization."""

from typing import Optional

import typer

from agentworld.cli.output import console, print_error, print_success, print_info


def serve(
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to run server on",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind to",
    ),
    simulation_id: Optional[str] = typer.Option(
        None,
        "--simulation",
        "-s",
        help="Simulation ID to focus on",
    ),
    open_browser: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open browser automatically",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode",
    ),
) -> None:
    """Start a web server for simulation visualization.

    Provides a web interface to view simulations, agent interactions,
    and real-time updates.
    """
    try:
        from agentworld.web.server import create_app, run_server
    except ImportError:
        # Fallback to simple server
        print_info("Web module not available. Starting minimal server...")
        _start_minimal_server(host, port, simulation_id, open_browser)
        return

    print_info(f"Starting AgentWorld server on http://{host}:{port}")

    if simulation_id:
        print_info(f"Focused on simulation: {simulation_id}")

    if open_browser:
        import webbrowser
        webbrowser.open(f"http://{host}:{port}")

    app = create_app(simulation_id=simulation_id)
    run_server(app, host=host, port=port, debug=debug)


def _start_minimal_server(
    host: str,
    port: int,
    simulation_id: Optional[str],
    open_browser: bool,
) -> None:
    """Start a minimal HTTP server for basic API access."""
    import json
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from agentworld.persistence.database import init_db
    from agentworld.persistence.repository import Repository

    init_db()
    repo = Repository()

    class AgentWorldHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "/index.html":
                self._serve_index()
            elif self.path == "/api/simulations":
                self._serve_simulations()
            elif self.path.startswith("/api/simulation/"):
                sim_id = self.path.split("/")[-1]
                self._serve_simulation(sim_id)
            else:
                self.send_error(404)

        def _serve_index(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            html = """<!DOCTYPE html>
<html>
<head>
    <title>AgentWorld</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .sim { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .sim:hover { background: #f5f5f5; }
        .status { padding: 3px 8px; border-radius: 4px; font-size: 12px; }
        .completed { background: #d4edda; color: #155724; }
        .running { background: #cce5ff; color: #004085; }
        .pending { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <h1>🌐 AgentWorld</h1>
    <p>Multi-agent simulation framework</p>
    <div id="simulations">Loading...</div>
    <script>
        fetch('/api/simulations')
            .then(r => r.json())
            .then(data => {
                const div = document.getElementById('simulations');
                if (data.length === 0) {
                    div.innerHTML = '<p>No simulations found. Create one with <code>agentworld create</code></p>';
                    return;
                }
                div.innerHTML = data.map(s => `
                    <div class="sim">
                        <strong>${s.name}</strong>
                        <span class="status ${s.status}">${s.status}</span>
                        <br><small>ID: ${s.id} | Steps: ${s.current_step}/${s.total_steps}</small>
                    </div>
                `).join('');
            });
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())

        def _serve_simulations(self):
            sims = repo.list_simulations()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(sims).encode())

        def _serve_simulation(self, sim_id: str):
            sim = repo.get_simulation(sim_id)
            if not sim:
                self.send_error(404)
                return

            agents = repo.get_agents_for_simulation(sim_id)
            messages = repo.get_messages_for_simulation(sim_id)

            result = {
                "simulation": sim,
                "agents": agents,
                "messages": messages,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result, default=str).encode())

        def log_message(self, format, *args):
            # Suppress default logging
            pass

    server = HTTPServer((host, port), AgentWorldHandler)
    print_success(f"Server running at http://{host}:{port}")

    if open_browser:
        import webbrowser
        webbrowser.open(f"http://{host}:{port}")

    console.print("[dim]Press Ctrl+C to stop[/dim]")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print_info("\nServer stopped")
        server.shutdown()
