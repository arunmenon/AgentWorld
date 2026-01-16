#!/usr/bin/env python
"""
scripts/verify_phase2.py

Run this script to verify Phase 2 (Memory & Topology) is complete.
Exit code 0 = all checks pass
Exit code 1 = one or more checks failed
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class PhaseVerifier:
    def __init__(self):
        self.checks = []
        self.failed = False

    def check(self, name: str, condition: bool, error_msg: str = ""):
        self.checks.append((name, condition, error_msg))
        if not condition:
            self.failed = True
            print(f"  ✗ {name}")
            if error_msg:
                print(f"      Error: {error_msg}")
        else:
            print(f"  ✓ {name}")

    def report(self):
        print("\n" + "=" * 60)
        print("PHASE 2 VERIFICATION RESULTS")
        print("=" * 60)

        passed = sum(1 for _, c, _ in self.checks if c)
        total = len(self.checks)
        print(f"\nPassed: {passed}/{total}")

        print("=" * 60)
        if self.failed:
            print("✗ PHASE 2 INCOMPLETE")
            return 1
        else:
            print("✓ PHASE 2 COMPLETE")
            return 0


async def verify_memory_system(v: PhaseVerifier):
    """Verify memory system components."""
    print("\n--- Memory System ---")

    # Test imports
    try:
        from agentworld.memory import (
            Memory, MemoryConfig, Observation, Reflection,
            MemoryRetrieval, ImportanceRater, EmbeddingGenerator
        )
        v.check("Memory imports", True)
    except ImportError as e:
        v.check("Memory imports", False, str(e))
        return

    # Test Observation creation
    try:
        obs = Observation(content="Test observation", source="test")
        v.check("Observation creation", obs.content == "Test observation")
    except Exception as e:
        v.check("Observation creation", False, str(e))

    # Test Memory system
    try:
        config = MemoryConfig()
        memory = Memory(config=config)
        v.check("Memory instantiation", memory is not None)
    except Exception as e:
        v.check("Memory instantiation", False, str(e))

    # Test add_observation
    try:
        obs = await memory.add_observation(
            content="I observed Alice talking to Bob",
            source="Alice"
        )
        v.check("Add observation", obs is not None and obs.id is not None)
    except Exception as e:
        v.check("Add observation", False, str(e))

    # Test observation storage
    try:
        obs_list = memory.observations
        v.check("Observation storage", len(obs_list) >= 1)
    except Exception as e:
        v.check("Observation storage", False, str(e))

    # Test importance rater heuristics
    try:
        rater = ImportanceRater()
        score = rater._rate_heuristic("This is very important information!")
        v.check("Importance rating (heuristic)", 1.0 <= score <= 10.0)
    except Exception as e:
        v.check("Importance rating (heuristic)", False, str(e))

    # Test retrieval config
    try:
        from agentworld.memory.retrieval import RetrievalConfig
        config = RetrievalConfig(alpha=0.5, beta=0.3, gamma=0.2)
        total = config.alpha + config.beta + config.gamma
        v.check("Retrieval config", abs(total - 1.0) < 0.01)
    except Exception as e:
        v.check("Retrieval config", False, str(e))

    # Test reflection config
    try:
        from agentworld.memory.reflection import ReflectionConfig
        config = ReflectionConfig(threshold=100.0, enabled=True)
        v.check("Reflection config", config.threshold == 100.0)
    except Exception as e:
        v.check("Reflection config", False, str(e))


async def verify_topology_system(v: PhaseVerifier):
    """Verify topology system components."""
    print("\n--- Topology System ---")

    # Test imports
    try:
        from agentworld.topology import (
            Topology, TopologyMetrics, RoutingMode,
            MeshTopology, HubSpokeTopology, HierarchicalTopology,
            SmallWorldTopology, ScaleFreeTopology, CustomTopology
        )
        from agentworld.topology.types import create_topology
        v.check("Topology imports", True)
    except ImportError as e:
        v.check("Topology imports", False, str(e))
        return

    agents = ["alice", "bob", "charlie", "diana"]

    # Test Mesh topology
    try:
        mesh = MeshTopology()
        mesh.build(agents)
        metrics = mesh.get_metrics()
        # Mesh should have n*(n-1)/2 edges for undirected
        expected_edges = len(agents) * (len(agents) - 1) // 2
        v.check(
            "Mesh topology",
            metrics.edge_count == expected_edges and mesh.can_communicate("alice", "bob")
        )
    except Exception as e:
        v.check("Mesh topology", False, str(e))

    # Test Hub-Spoke topology
    try:
        hub = HubSpokeTopology()
        hub.build(agents, hub_id="alice")
        # Hub should connect to all others
        neighbors = hub.get_neighbors("alice")
        v.check(
            "Hub-spoke topology",
            len(neighbors) == len(agents) - 1 and hub.hub_id == "alice"
        )
    except Exception as e:
        v.check("Hub-spoke topology", False, str(e))

    # Test Hierarchical topology
    try:
        hier = HierarchicalTopology()
        hier.build(agents, branching_factor=2)
        metrics = hier.get_metrics()
        v.check(
            "Hierarchical topology",
            metrics.node_count >= 1 and metrics.is_connected
        )
    except Exception as e:
        v.check("Hierarchical topology", False, str(e))

    # Test Small-World topology
    try:
        sw = SmallWorldTopology()
        sw.build(agents, k=2, p=0.3)
        metrics = sw.get_metrics()
        v.check(
            "Small-world topology",
            metrics.node_count == len(agents) and metrics.edge_count > 0
        )
    except Exception as e:
        v.check("Small-world topology", False, str(e))

    # Test Scale-Free topology
    try:
        sf = ScaleFreeTopology()
        sf.build(agents, m=1)
        metrics = sf.get_metrics()
        v.check(
            "Scale-free topology",
            metrics.node_count == len(agents) and metrics.is_connected
        )
    except Exception as e:
        v.check("Scale-free topology", False, str(e))

    # Test create_topology factory
    try:
        topology = create_topology("mesh", agents)
        v.check(
            "create_topology factory",
            topology.topology_type == "mesh"
        )
    except Exception as e:
        v.check("create_topology factory", False, str(e))

    # Test topology metrics
    try:
        from agentworld.topology.metrics import TopologyAnalyzer
        analyzer = TopologyAnalyzer(mesh)
        centrality = analyzer.get_centrality()
        v.check(
            "Topology metrics",
            len(centrality.degree) == len(agents)
        )
    except Exception as e:
        v.check("Topology metrics", False, str(e))

    # Test TopologyGraph wrapper
    try:
        from agentworld.topology.graph import TopologyGraph
        graph = TopologyGraph(mesh, RoutingMode.DIRECT_ONLY)
        recipients = graph.get_valid_recipients("alice")
        v.check(
            "TopologyGraph wrapper",
            len(recipients) == len(agents) - 1
        )
    except Exception as e:
        v.check("TopologyGraph wrapper", False, str(e))


async def verify_persistence(v: PhaseVerifier):
    """Verify persistence layer updates."""
    print("\n--- Persistence ---")

    try:
        from agentworld.persistence.models import (
            MemoryModel, TopologyEdgeModel, TopologyConfigModel
        )
        v.check("Persistence model imports", True)
    except ImportError as e:
        v.check("Persistence model imports", False, str(e))
        return

    try:
        from agentworld.persistence.database import init_db, reset_db
        from agentworld.persistence.repository import Repository

        init_db(in_memory=True)
        repo = Repository()
        v.check("Repository with new models", True)
    except Exception as e:
        v.check("Repository with new models", False, str(e))
        return

    # Test saving topology config
    try:
        # First save a simulation
        sim_data = {
            "id": "test123",
            "name": "Test Sim",
            "status": "pending",
        }
        repo.save_simulation(sim_data)

        config_data = {
            "simulation_id": "test123",
            "topology_type": "mesh",
            "directed": False,
            "config": {"test": "value"},
        }
        repo.save_topology_config(config_data)
        v.check("Save topology config", True)
    except Exception as e:
        v.check("Save topology config", False, str(e))

    # Test saving topology edges
    try:
        edges = [
            ("a1", "a2", 1.0),
            ("a2", "a3", 1.0),
            ("a1", "a3", 0.5),
        ]
        count = repo.save_topology_edges("test123", edges)
        v.check("Save topology edges", count == 3)
    except Exception as e:
        v.check("Save topology edges", False, str(e))

    # Test retrieving topology edges
    try:
        edges = repo.get_topology_edges("test123")
        v.check("Retrieve topology edges", len(edges) == 3)
    except Exception as e:
        v.check("Retrieve topology edges", False, str(e))

    # Clean up
    try:
        reset_db()
    except:
        pass


async def verify_integration(v: PhaseVerifier):
    """Verify memory and topology integration with Agent and Simulation."""
    print("\n--- Integration ---")

    try:
        from agentworld.agents.agent import Agent
        from agentworld.personas.traits import TraitVector
        from agentworld.simulation.runner import Simulation

        v.check("Integration imports", True)
    except ImportError as e:
        v.check("Integration imports", False, str(e))
        return

    # Test Agent with memory
    try:
        traits = TraitVector(openness=0.8)
        agent = Agent(name="TestAgent", traits=traits)
        memory = agent.memory
        v.check("Agent memory access", memory is not None)
    except Exception as e:
        v.check("Agent memory access", False, str(e))

    # Test Simulation with topology
    try:
        sim = Simulation(
            name="Test Simulation",
            topology_type="mesh",
        )
        traits = TraitVector()
        sim.add_agent(Agent(name="Alice", traits=traits))
        sim.add_agent(Agent(name="Bob", traits=traits))

        # Access topology (should auto-initialize)
        topology = sim.topology
        v.check(
            "Simulation topology",
            topology is not None and topology.topology_type == "mesh"
        )
    except Exception as e:
        v.check("Simulation topology", False, str(e))

    # Test topology communication check
    try:
        can_comm = sim.can_communicate(
            sim.agents[0].id,
            sim.agents[1].id
        )
        v.check("Topology communication check", can_comm)
    except Exception as e:
        v.check("Topology communication check", False, str(e))


async def main():
    v = PhaseVerifier()

    print("=" * 60)
    print("PHASE 2 VERIFICATION: Memory & Topology")
    print("=" * 60)

    await verify_memory_system(v)
    await verify_topology_system(v)
    await verify_persistence(v)
    await verify_integration(v)

    return v.report()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
