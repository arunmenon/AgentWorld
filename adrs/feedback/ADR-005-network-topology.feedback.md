# Feedback: ADR-005: Network Topology Architecture

## Findings
### High
- `get_metrics` calls `nx.average_shortest_path_length` and `nx.diameter` without guarding against disconnected graphs, which will raise and break simulations for some topologies. Reference: ADR-005-network-topology.md:104.
- The Hub-Spoke design references a `hub_id`, but `nx.star_graph` creates numeric nodes; without explicit remapping, the hub may not match the intended agent ID. This can invalidate moderator routing. Reference: ADR-005-network-topology.md:132.

### Medium
- The abstraction locks to undirected graphs (`nx.Graph`), which prevents representing asymmetric communication or influence; clarify if a `DiGraph` is needed. Reference: ADR-005-network-topology.md:56.
- `SmallWorldTopology.build` does not validate `k` or `p` (for example, `k` must be even and less than n), which can throw at runtime. Reference: ADR-005-network-topology.md:116.
- `can_communicate` only checks direct edges; it is unclear whether multi-hop routing is permitted or how messages traverse the topology. Reference: ADR-005-network-topology.md:100.

### Low
- `add_edge` includes a `weight` parameter but weight is not used elsewhere; clarify whether weighted routing is in scope. Reference: ADR-005-network-topology.md:59.

## Questions
- Should topologies support directed edges for influence or authority flows?
- What is the expected behavior when the graph is disconnected?

## Summary
- The NetworkX abstraction is appropriate, but hub mapping and metric computation need hardening.
