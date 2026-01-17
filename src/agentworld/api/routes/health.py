"""Health check endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter

from agentworld import __version__


router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "api_version": "v1",
        "timestamp": datetime.now(UTC).isoformat(),
    }
