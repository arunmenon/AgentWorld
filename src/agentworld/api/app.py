"""FastAPI application for AgentWorld API."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentworld import __version__
from agentworld.persistence.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    yield
    # Shutdown
    pass


def create_app(
    title: str = "AgentWorld API",
    simulation_id: Optional[str] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        title: API title
        simulation_id: Optional simulation ID to focus on

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description="Multi-agent simulation platform API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store simulation_id if provided
    app.state.focused_simulation_id = simulation_id

    # Register routes
    from agentworld.api.routes import (
        simulations,
        agents,
        messages,
        personas,
        health,
        evaluation,
        export,
        apps,
        app_definitions,
        tasks,
        dual_control,
    )

    app.include_router(health.router, tags=["Health"])
    app.include_router(simulations.router, prefix="/api/v1", tags=["Simulations"])
    app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
    app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
    app.include_router(personas.router, prefix="/api/v1", tags=["Personas"])
    app.include_router(evaluation.router, prefix="/api/v1", tags=["Evaluation"])
    app.include_router(export.router, prefix="/api/v1", tags=["Export"])
    app.include_router(apps.router, prefix="/api/v1", tags=["Apps"])
    app.include_router(app_definitions.router, prefix="/api/v1", tags=["App Definitions"])
    app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
    app.include_router(dual_control.router, prefix="/api/v1", tags=["Dual Control Tasks"])

    # Register WebSocket
    from agentworld.api.websocket import register_websocket
    register_websocket(app)

    return app


def run_server(
    app: FastAPI,
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
) -> None:
    """Run the API server.

    Args:
        app: FastAPI application
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    import uvicorn

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
    )


# Module-level app instance for uvicorn CLI
app = create_app()
