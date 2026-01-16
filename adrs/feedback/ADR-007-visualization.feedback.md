# Feedback: ADR-007: Visualization Strategy

## Findings
### Medium
- The event bus publishes to subscribers sequentially; a slow or failing subscriber can block the simulation and UI updates. Consider fan-out with isolation and backpressure. Reference: ADR-007-visualization.md:100.
- The web UI requirement includes network graphs, but the "simple HTML/JS" stack does not identify a graph rendering approach or performance constraints; risk of under-scoping. Reference: ADR-007-visualization.md:95.

### Low
- No non-interactive CLI mode is specified for CI/logging, so rich live output may be hard to capture. Reference: ADR-007-visualization.md:40.
- Remote web access implies auth and access control; not mentioned. Reference: ADR-007-visualization.md:20.

## Questions
- Is the event system expected to buffer or persist events for late subscribers?
- Will the web UI be read-only or allow control of the simulation?

## Summary
- The dual UI plan is reasonable, but the event pipeline and web rendering scope need more detail.
