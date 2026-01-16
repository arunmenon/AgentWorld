# Feedback: ADR-004: Trait Vector Persona System

## Findings
### High
- The ADR claims "Same vector = same personality (deterministic)", but without controlling sampling settings and prompts, LLM output will not be deterministic. This undermines reproducibility claims. Reference: ADR-004-trait-vector-persona.md:119.

### Medium
- The mapping from continuous traits to prompt text is coarse (threshold buckets at 0.3/0.7) and will collapse many distinct vectors into identical descriptions. Consider interpolation or weighted phrasing. Reference: ADR-004-trait-vector-persona.md:73.
- Cosine similarity across mixed Big Five and custom traits lacks weighting or normalization for custom dimensions; results could be dominated by arbitrary trait choices. Reference: ADR-004-trait-vector-persona.md:69.
- Custom traits are untyped and unconstrained beyond [0,1]; without schema or units, prompts and evaluation will be inconsistent across scenarios. Reference: ADR-004-trait-vector-persona.md:62.

### Low
- There is no strategy for linking structured fields (occupation, age) to trait vectors, which may limit persona realism. Reference: ADR-004-trait-vector-persona.md:15.

## Questions
- Will traits be sampled from a distribution to create realistic populations, or user-specified only?
- How will prompt text generation be tested for stability across model providers?

## Summary
- The vector approach is solid, but the mapping to prompts and reproducibility guarantees need more rigor.
