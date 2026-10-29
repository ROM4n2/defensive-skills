---
name: dfs-migrate
description: Plan zero-downtime database schema migrations safely. Use when a schema change must ship without taking the service offline.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - database
    - migration
    - zero-downtime
    - ddl
    - expand-contract
    - sql
    related_skills:
    - dfs-perf
    - dfs-team
    - dfs-review
---


# DFS-MIGRATE: Zero-Downtime Database Schema Migration

Plan and execute production-safe database schema evolutions avoiding metadata locks, replication lag spikes, and service disruptions through the Expand/Contract paradigm.

## [MUST] The Zero-Lock Invariant (RFC 2119 MUST)
> **Always apply the 5-step Expand/Contract ladder for schema evolutions on production tables.**
> Use backward-compatible additions, dual-writes, and decoupled drops to guarantee zero application downtime.
> Running destructive or lock-holding DDL (`ALTER TABLE ... DROP COLUMN`, synchronous `ADD COLUMN NOT NULL`) on active tables is strictly prohibited.

---

## The 4-Stage Migration Lifecycle

`Stage 1: Risk Assessment` -> `Stage 2: Expand/Contract Plan` -> `Stage 3: Backward Compatibility` -> `Stage 4: Execution & Lint`

## Automated DDL Risk Linter
Before executing any migration SQL, run the static lock-hazard auditor:
```bash
python scripts/ddl_lint.py <path_to_migration.sql> --dialect auto
```
Detects lock hazards (synchronous `NOT NULL`, un-aliased renames, non-concurrent indexes) and enforces Expand/Contract.

---

## The Migration Design Procedure

### Step 1: Migration Risk Assessment
1. **Scale & Lock Inspection**: Query table scale (`table_rows`, `data_length`, `index_length`) from `information_schema.tables WHERE table_name = '<target_table>'`.
2. **DDL Lock Characteristics**:
   - MySQL 8.0+: Prefer `ALGORITHM=INSTANT`, fallback to `ALGORITHM=INPLACE, LOCK=NONE`. Reject `LOCK=SHARED` or `LOCK=EXCLUSIVE` on busy tables.
   - PostgreSQL: Use `CREATE INDEX CONCURRENTLY` and `ADD COLUMN ... NULL`.
3. **Checkable Completion Criterion**:
   - Table scale documented; target lock algorithm identified; zero exclusive locks verified.

### Step 2: Formulate Expand/Contract Plan
1. Load `templates/migration-plan-schema.md` via `read_file(path='templates/migration-plan-schema.md')`.
2. Map the change across the 5 phases:
   - **Phase 1 (Expand)**: Add backward-compatible nullable column; deploy dual-writing code.
   - **Phase 2 (Backfill)**: Chunked asynchronous data migration with pacing (obey the Six Stored-Data Backfill Invariants & Monotonic Capability Predicate in [references/backfill-and-idempotency.md](references/backfill-and-idempotency.md) §1–§2 — gate on target IS NULL, never on COUNT(*) > 0 or a one-shot flag).
   - **Phase 3 (Read Switch)**: Switch query reads to the new column; verify zero parity errors.
   - **Phase 4 (Write Cutover)**: Decommission legacy column writes.
   - **Phase 5 (Contract)**: Drop deprecated column after canary stabilization.
3. **Checkable Completion Criterion**:
   - All 5 phases populated with explicit SQL statements, backfill chunk size, and verification queries.

### Step 3: Backward Compatibility Verification
1. Verify that older running versions of the application binary will NOT crash when connected to the updated schema.
2. Ensure queries use explicit column lists instead of `SELECT *` to prevent wildcard column count mismatch.
3. **Three-Phase Temporal Regression**: Verify Fresh DB -> Partial/Interrupted Re-run (idempotent, honest NULL) -> Legacy Restore per [references/backfill-and-idempotency.md](references/backfill-and-idempotency.md) §3.
4. **Checkable Completion Criterion**:
   - Codebase checked for wildcard `SELECT *` queries targeting the altered table; verified zero crashes under version $N-1$ binary; three-phase temporal regression verified.

### Step 4: Downstream Execution Dispatch & Lint Verification
1. Run static DDL auditor: `python scripts/ddl_lint.py <path_to_migration.sql> --dialect auto`. Ensure exit code 0.
2. Output the complete migration plan to `docs/migrations/YYYY-MM-DD-<name>.md` and prompt user for DBA review via `/dfs-team`.
3. **Checkable Completion Criterion**:
   - `ddl_lint.py` returns exit code 0; migration document written to `docs/migrations/` with rollback SQL steps included.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Table is small in dev; I'll ADD COLUMN NOT NULL directly."* | **Metadata Lock Outages** | Enforce Phase 1 Expand: nullable first, backfill async, contract later. |
| *"Renaming this column in-place refactors technical debt."* | **Immediate Outage** | Never rename columns in-place. Add new, dual-write, backfill, cutover, drop old. |
| *"Backfill all 10M rows in a single UPDATE in off-peak."* | **Replication Lag & Locks** | Backfill MUST be chunked (e.g. 1000 rows/batch) with explicit sleep pacing. |
| *"Rollback plan unnecessary for adding a nullable column."* | **Irreversible State Drift** | Every migration step MUST include deterministic rollback SQL in plan card. |
