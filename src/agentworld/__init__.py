"""AgentWorld - A multi-agent simulation framework."""

__version__ = "0.1.0"

from agentworld.core.models import Message, SimulationConfig, SimulationStatus
from agentworld.personas.traits import TraitVector
from agentworld.agents.agent import Agent
from agentworld.simulation.runner import Simulation

__all__ = [
    "Agent",
    "Message",
    "Simulation",
    "SimulationConfig",
    "SimulationStatus",
    "TraitVector",
    "__version__",
]
