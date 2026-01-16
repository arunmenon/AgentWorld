# Feedback: ADR-009: Use Case Scenarios

## Findings
### High
- `HubSpokeTopology` is built with `hub_id="moderator"`, but `moderator` is not created as an agent; this will fail or produce a hub that is not an actual actor. References: ADR-009-use-case-scenarios.md:81, ADR-009-use-case-scenarios.md:84.
- `inject_stimulus` sends directly to all agents, bypassing topology rules and always using source "moderator"; this conflicts with ADR-005's communication constraints. Reference: ADR-009-use-case-scenarios.md:54.

### Medium
- `_extract_responses` is referenced but not defined, so the scenario output path is unclear. Reference: ADR-009-use-case-scenarios.md:106.
- `create_subworld` is used without definition; unclear whether it shares state or memory with the main world, which affects data leakage. Reference: ADR-009-use-case-scenarios.md:155.
- YAML config structure does not map cleanly to `ProductTestConfig` fields (product.description vs product_description), so configuration parsing is underspecified. References: ADR-009-use-case-scenarios.md:73, ADR-009-use-case-scenarios.md:254.
- Data generation loops do not include diversity or stopping criteria, which can yield repetitive or degenerate outputs. Reference: ADR-009-use-case-scenarios.md:196.

### Low
- No data quality or safety filtering is described for generated datasets. Reference: ADR-009-use-case-scenarios.md:23.

## Questions
- Is "moderator" a real agent with its own persona, or a system role?
- How will scenarios surface structured outputs for downstream evaluation (ties to ADR-010)?

## Summary
- Scenario coverage is strong, but topology enforcement and configuration mapping need tightening.
