# Stored-Data Backfill & Migration Idempotency Invariants (`references/backfill-and-idempotency.md`)

Load this reference during Step 2 (Phase 2 Backfill design) and Step 3 (Verification) whenever a migration backfills historical rows, computes derived projections, or guards idempotent re-runs.

---

## 1. Reconciliation Predicate & Atomic DDL Rules (MUST)

1. **Predicate Direction Must Match Data Monotonicity**:
   - Never gate a migration or backfill skip on `SELECT COUNT(*) > 0` — a partial crash after writing 1 row permanently silences the rest of the backfill.
   - Gate on the **missing-capability predicate** (`WHERE new_col IS NULL` or `watermark < target_id`) so interrupted runs resume to completion.
2. **Single-Transaction Atomic Step**:
   - Schema metadata updates and their corresponding version-table records MUST commit in the same transaction (where the DB engine supports transactional DDL) or use idempotent `IF NOT EXISTS` + capability checks.
3. **Restore-Then-Migrate Compatibility**:
   - Restoring an older backup into a newer binary MUST automatically re-trigger pending migrations and backfills without manual flag resets.

---

## 2. The Six Stored-Data Backfill Invariants (MUST)

Shipping new write-path code does **not** heal historical rows already on disk. Every backfill design MUST obey all six rules:

1. **Read-Time Derivation First**: If a missing field can be deterministically derived from existing columns at read time with negligible cost, prefer a read-time projection over mutating millions of historical rows.
2. **Gate on Capability, Never on a Historical Status Flag**: Trigger backfill whenever the target field is empty (`field IS NULL` / `== ""`) AND the source data required to compute it is present — never on a one-shot boolean `backfill_v1_done` flag.
3. **Additive & Fill-Empty-Only (Idempotent)**: Backfills MUST only populate empty/null fields (`WHERE target_col IS NULL`). Never overwrite non-empty user or production values on re-run.
4. **No Cross-Semantic Source Mixing**: Never copy a similarly named field from a different semantic domain (e.g. substituting `updated_at` when `published_at` is missing, or mixing ratio with share) just to make a column non-null.
5. **Honest `NULL` on Miss**: When historical rows genuinely lack the source inputs needed to derive a field, leave the field `NULL` / empty. Fabricating placeholder values corrupts downstream aggregations.
6. **Checkpoint Accumulator Dimension `>=` Work-Set Dimension**: If an incremental backfill tracks progress with a high-water mark (e.g. `max(row_id)`), any derived summary table grouped by `(row_id, category)` MUST track checkpoints at the full composite key or recompute the affected groups; advancing a scalar cursor before secondary dimensions finish permanently strands historical buckets.

---

## 3. Three-Phase Temporal Regression Suite (MUST)

Every schema migration or backfill test suite MUST verify three temporal states in sequence:
1. **Phase A — Fresh Empty DB**: Schema initializes cleanly and new writes populate all fields.
2. **Phase B — Interrupted / Partial State Re-Run**: Seed legacy rows (some already backfilled, some `NULL`), run the migration/backfill **twice**, and assert:
   - All recoverable `NULL` rows are populated;
   - Already-populated rows are untouched (zero duplicate writes or doubled counters);
   - Unrecoverable rows remain honest `NULL`.
3. **Phase C — Legacy Snapshot Restore**: Load a fixture representing an $N-1$ backup and confirm the startup/migration path heals it to the current contract with zero errors.
