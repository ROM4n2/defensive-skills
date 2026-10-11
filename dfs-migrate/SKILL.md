---
name: dfs-migrate
description: Plan zero-downtime database schema migrations safely. Use when a schema change must ship without taking the service offline.
license: MIT
metadata:
  version: 0.2.0
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

## 🚨 The Zero-Lock Invariant (RFC 2119 MUST)
> **Always apply the 5-step Expand/Contract ladder for schema evolutions on production tables.**
> Use backward-compatible additions, dual-writes, and decoupled drops to guarantee zero application downtime.
> Running destructive or lock-holding DDL (`ALTER TABLE ... DROP COLUMN`, synchronous `ADD COLUMN NOT NULL`) on active tables is strictly prohibited.

---

## The 4-Stage Migration Lifecycle

```
  [Stage 1: Migration Risk Assessment & Table Scale Profiling]
                               │
                               ▼
  [Stage 2: Formulate Expand/Contract Plan (5 Phases)]
                               │
                               ▼
  [Stage 3: Backward Compatibility & Wildcard Verification]
                               │
                               ▼
  [Stage 4: Automated DDL Risk Lint & Execution Artifact Dispatch]
```

## 🛠️ Automated DDL Risk Linter
Before executing any migration SQL, run the static lock-hazard auditor:
```bash
python scripts/ddl_lint.py <path_to_migration.sql> --dialect auto
```
The linter detects table lock hazards (synchronous `NOT NULL` additions, un-aliased renames, non-concurrent index creation) and enforces the Expand/Contract alternatives.

---

## The Migration Design Procedure

### Step 1: Migration Risk Assessment
1. **Scale & Lock Inspection**: Inspect target table scale:
   ```sql
   SELECT table_rows, data_length, index_length 
   FROM information_schema.tables 
   WHERE table_name = '<target_table>';
   ```
2. **DDL Lock Characteristics**:
   - MySQL 8.0+: Prefer `ALGORITHM=INSTANT`, fallback to `ALGORITHM=INPLACE, LOCK=NONE`. Reject `LOCK=SHARED` or `LOCK=EXCLUSIVE` on busy tables.
   - PostgreSQL: Use `CREATE INDEX CONCURRENTLY` and `ADD COLUMN ... NULL`.
3. **Checkable Completion Criterion**:
   - Table scale documented; target lock algorithm identified; zero exclusive locks verified.

### Step 2: Formulate Expand/Contract Plan
1. Load `templates/migration-plan-schema.md` via `read_file(path='templates/migration-plan-schema.md')`.
2. Map the change across the 5 phases:
   - **Phase 1 (Expand)**: Add backward-compatible nullable column; deploy dual-writing code.
   - **Phase 2 (Backfill)**: Chunked asynchronous data migration with pacing.
   - **Phase 3 (Read Switch)**: Switch query reads to the new column; verify zero parity errors.
   - **Phase 4 (Write Cutover)**: Decommission legacy column writes.
   - **Phase 5 (Contract)**: Drop deprecated column after canary stabilization.
3. **Checkable Completion Criterion**:
   - All 5 phases populated with explicit SQL statements, backfill chunk size, and verification queries.

### Step 3: Backward Compatibility Verification
1. Verify that older running versions of the application binary will NOT crash when connected to the updated schema.
2. Ensure queries use explicit column lists instead of `SELECT *` to prevent wildcard column count mismatch.
3. **Checkable Completion Criterion**:
   - Codebase checked for wildcard `SELECT *` queries targeting the altered table; verified zero crashes under version $N-1$ binary.

### Step 4: Downstream Execution Dispatch & Lint Verification
1. Run static DDL auditor: `python scripts/ddl_lint.py <path_to_migration.sql> --dialect auto`. Ensure exit code 0.
2. Output the complete migration plan to `docs/migrations/YYYY-MM-DD-<name>.md` and prompt user for DBA review via `/dfs-team`.
3. **Checkable Completion Criterion**:
   - `ddl_lint.py` returns exit code 0; migration document written to `docs/migrations/` with rollback SQL steps included.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"The table is small in dev, so I'll execute `ALTER TABLE ... ADD COLUMN NOT NULL DEFAULT x` directly."* | **Metadata Lock Outages**: In production with concurrent queries, synchronous NOT NULL locks all table reads/writes. | Enforce Phase 1 Expand: add nullable column first, backfill asynchronously, then contract. |
| *"Renaming this column is clean and refactors technical debt in one migration."* | **Immediate Production Outage**: In-flight queries using the old column fail immediately during deployment. | Never rename columns in-place. Add new column, dual-write, backfill, switch reads, drop old. |
| *"We can backfill all 10 million rows in a single UPDATE statement during low traffic."* | **Replication Lag & Lock Escalation**: Monolithic updates bloat undo logs, hold row locks, and break read replicas. | Backfill MUST be chunked (e.g. 1000 rows/batch) with explicit pacing sleep intervals. |
| *"A rollback plan isn't necessary because adding a nullable column can't break anything."* | **Irreversible State Drift**: If downstream application code errors on the new column, recovery stalls without down SQL. | Every migration step MUST include deterministic rollback SQL in the plan card. |
