# Feedback: ADR-010: Evaluation and Metrics System

## Findings
### High
- `on_memory_added` increments `observations_per_agent` for all memory types, including reflections, which will skew metrics and break memory health reporting. Reference: ADR-010-evaluation-metrics.md:112.
- `run_ab_test` mutates `scenario.config` in place and reuses the same scenario across runs, risking cross-variant contamination and invalid comparisons. Reference: ADR-010-evaluation-metrics.md:276.

### Medium
- Network metrics assume connected graphs; for disconnected topologies, `avg_path_length` is undefined and is silently skipped. Define a strategy (largest component or per-component). Reference: ADR-010-evaluation-metrics.md:126.
- The LLM interface here uses `llm.complete`, which does not match the `litellm.acompletion` example in ADR-003; define a stable wrapper API to avoid inconsistent implementations. Reference: ADR-010-evaluation-metrics.md:167.
- LLM-based extractors return JSON but error handling and validation are not described; parsing failures will corrupt metrics. Reference: ADR-010-evaluation-metrics.md:219.

### Low
- `check_coherence` is a stub; either define or remove. Reference: ADR-010-evaluation-metrics.md:195.
- Validation thresholds for `passed` are not specified. Reference: ADR-010-evaluation-metrics.md:199.

## Questions
- Will evaluation use a separate model from the simulation model to reduce bias?
- How will you sample or budget validation calls to control cost?

## Summary
- The evaluation system is comprehensive, but it needs safeguards to avoid invalid metrics and cross-run contamination.
