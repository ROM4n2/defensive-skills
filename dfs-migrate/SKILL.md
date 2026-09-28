---
name: dfs-migrate
description: Plan zero-downtime database schema migrations safely. Use when a schema change must ship without taking the service offline.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [database, migration, zero-downtime, ddl, expand-contract, sql]
    related_skills: [dfs-perf, dfs-team, dfs-review]
---

# DFS-MIGRATE: Zero-Downtime Database Schema Migration

Plan and execute production-safe database schema evolutions avoiding metadata locks, replication lag spikes, and service disruptions through the Expand/Contract paradigm.

## 🚨 The Zero-Lock Invariant (HARD GATE)
> Always apply the 5-step Expand/Contract ladder for schema evolutions on production tables.
> Use backward-compatible additions, dual-writes, and decoupled drops to guarantee zero application downtime.

---

## 🛠️ Automated DDL Risk Linter
Before executing any migration SQL, run the static lock-hazard auditor:
```bash
python scripts/ddl_lint.py <path_to_migration.sql> --dialect auto
```
The linter detects table lock hazards (synchronous `NOT NULL` additions, un-aliased renames, non-concurrent index creation) and enforces the Expand/Contract alternatives.

---

## The Migration Design Procedure

### Step 1: Migration Risk Assessment
1. Inspect target table scale:
   ```sql
   SELECT table_rows, data_length, index_length 
   FROM information_schema.tables 
   WHERE table_name = '<target_table>';
   ```
2. Check DDL lock characteristics:
   - MySQL 8.0+: Prefer `ALGORITHM=INSTANT`, fallback to `ALGORITHM=INPLACE, LOCK=NONE`. Reject `LOCK=SHARED` or `LOCK=EXCLUSIVE` on busy tables.
   - PostgreSQL: Use `CREATE INDEX CONCURRENTLY` and `ADD COLUMN ... NULL`.

### Step 2: Formulate Expand/Contract Plan
1. Load `templates/migration-plan-schema.md` via `read_file(path='templates/migration-plan-schema.md')`.
2. Map the change across the 5 phases:
   - **Phase 1 (Expand)**: Add backward-compatible nullable column; deploy dual-writing code.
   - **Phase 2 (Backfill)**: Chunked asynchronous data migration with pacing.
   - **Phase 3 (Read Switch)**: Switch query reads to the new column; verify zero parity errors.
   - **Phase 4 (Write Cutover)**: Decommission legacy column writes.
   - **Phase 5 (Contract)**: Drop deprecated column after canary stabilization.

### Step 3: Backward Compatibility Verification
1. Verify that older running versions of the application binary will NOT crash when connected to the updated schema.
2. Ensure queries use explicit column lists instead of `SELECT *` to prevent wildcard column count mismatch.

### Step 4: Downstream Execution Dispatch
Output the complete migration plan to `docs/migrations/YYYY-MM-DD-<name>.md` and prompt user for DBA review via `/dfs-team`.
