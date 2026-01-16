# Feedback: ADR-002: Agent Scale and Quality Tradeoff

## Findings
### High
- Reproducibility is a stated requirement but the decision does not lock down determinism controls (temperature, seed, model pinning, caching rules). Without these, "reproducible agent behavior" is not achievable. Reference: ADR-002-agent-scale.md:20.

### Medium
- Cost model uses a simplified tokens/step assumption and a single per-token price that does not include memory reflection or evaluation calls, which likely understates costs by multiples. Reference: ADR-002-agent-scale.md:25.
- "Can always reduce persona complexity to scale up" is assumed but the architecture decisions (dual memory, per-agent reflection) may not scale even with simplified personas; consider an explicit "lite agent" mode. Reference: ADR-002-agent-scale.md:35.
- Data generation use cases may need sample sizes larger than 10-50 agents; include a plan for throughput (more runs, cheaper models, or batching). Reference: ADR-002-agent-scale.md:21.

### Low
- Scale tiers are broad and not tied to internal targets (latency per step, tokens per agent). Add measurable constraints to support future review. Reference: ADR-002-agent-scale.md:13.

## Questions
- What determinism strategy will be used to meet the reproducibility requirement?
- What is the target wall-clock time per simulation run?

## Summary
- The small-scale focus fits the use cases, but the reproducibility and cost assumptions need to be operationalized.
