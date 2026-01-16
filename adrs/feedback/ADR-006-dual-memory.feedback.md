# Feedback: ADR-006: Dual Memory Architecture

## Findings
### High
- The retrieval formula is inconsistent: the context section defines alpha=recency, beta=importance, gamma=relevance, but the architecture diagram swaps weights and values. This creates ambiguity in core behavior. References: ADR-006-dual-memory.md:21, ADR-006-dual-memory.md:76.
- Memory fields defined here (`location`, `questions_addressed`) are not persisted in ADR-008, which means data loss on checkpoint/restore. References: ADR-006-dual-memory.md:141, ADR-006-dual-memory.md:152, ADR-008-persistence.md:65.

### Medium
- Embedding model and vector dimension are not specified; mixing embeddings across providers will make similarity invalid. Store embedding model metadata per memory. Reference: ADR-006-dual-memory.md:139.
- Reflection trigger threshold (150) and reflection importance (8.0) are fixed without calibration guidance; these should be configurable and validated in experiments. Reference: ADR-006-dual-memory.md:87.
- Importance scoring requires an LLM call per observation; consider heuristics or batching to manage cost. Reference: ADR-006-dual-memory.md:165.

### Low
- No retention or pruning policy is defined for long-running simulations, risking unbounded growth. Reference: ADR-006-dual-memory.md:170.

## Questions
- Which embedding model is the default, and how is it selected for multi-provider runs?
- How will memory schema changes be versioned across checkpoints?

## Summary
- The architecture aligns with Generative Agents, but the retrieval weights and persistence schema need alignment.
