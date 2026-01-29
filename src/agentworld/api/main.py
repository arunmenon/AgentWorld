"""Main entry point for the AgentWorld API.

This module creates the FastAPI application instance for use with uvicorn.
"""

from agentworld.api.app import create_app

# Create the application instance
app = create_app()
