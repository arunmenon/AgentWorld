# Feedback: ADR-003: Multi-Provider LLM Architecture

## Findings
### High
- Provider fallback chains are listed without a reproducibility policy (model pinning, deterministic reruns, or recording which provider responded). This conflicts with research reproducibility goals and can make A/B results incomparable. Reference: ADR-003-llm-architecture.md:76.

### Medium
- Cache behavior is underspecified: cache keys, prompt versioning, and parameter inclusion are not defined, so cached responses may be reused incorrectly or across prompt changes. Reference: ADR-003-llm-architecture.md:76.
- Jinja2 prompt templating can introduce prompt injection or unsafe interpolation if agent content is untrusted; require escaping or a safe templating strategy. Reference: ADR-003-llm-architecture.md:50.
- LiteLLM abstracts providers but feature parity (tool calls, JSON mode, streaming) is not addressed; define a capability matrix and required minimal feature set. Reference: ADR-003-llm-architecture.md:40.

### Low
- Provider landscape and pricing are time-sensitive; consider moving to an appendix with a date or removing precise costs. Reference: ADR-003-llm-architecture.md:19.

## Questions
- Will the wrapper expose a stable interface for tool calling and structured outputs, or will those be opt-in per provider?
- How will you record provider/model metadata for each call to support auditability?

## Summary
- The LiteLLM choice is pragmatic, but reproducibility and cache/prompt safety need explicit design.
