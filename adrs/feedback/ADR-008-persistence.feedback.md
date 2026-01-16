# Feedback: ADR-008: Persistence and State Management

## Findings
### High
- The schema does not include `location` or `questions_addressed` from ADR-006, so memory data would be lost on persistence and restore. References: ADR-008-persistence.md:65, ADR-006-dual-memory.md:141.
- Checkpoint `world_state` is stored as JSON but no serialization format is defined for complex objects (embeddings, graphs). This risks broken pause/resume. Reference: ADR-008-persistence.md:99.

### Medium
- SQLite `JSON` columns are listed, but SQLite treats JSON as TEXT unless JSON1 is available; this affects querying and migrations. Reference: ADR-008-persistence.md:45.
- Embedding BLOB storage has no dtype or model metadata; future reads may be incompatible. Reference: ADR-008-persistence.md:71.
- Foreign keys lack `ON DELETE` policies, risking orphaned rows when simulations are deleted. Reference: ADR-008-persistence.md:56.

### Low
- `updated_at` is defined but not maintained; add triggers or update logic. Reference: ADR-008-persistence.md:48.

## Questions
- What is the canonical serialization format for `world_state` (JSON, msgpack, protobuf)?
- Is JSON1 extension required, and will it be enforced in setup?

## Summary
- SQLite is a good fit, but schema parity with memory types and checkpoint serialization need to be nailed down.
