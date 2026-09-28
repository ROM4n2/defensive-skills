---
name: dfs-adr
description: Draft and archive numbered Architecture Decision Records. Use when the user makes an architecture decision or asks to record one.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [adr, architecture, decision-record, madr, documentation]
    related_skills: [dfs-grill, dfs-spark, dfs-plan, dfs-save]
---

# DFS-ADR: Architecture Decision Record Generator

Lock in key architectural decisions into permanent history in `08-Projects/{project}/01-ADR/` or `01-Rules/` using the MADR (Markdown Architecture Decision Record) specification.

## Core Invariants (MUST)
1. **Auto-Incrementing Numbering**: Scan existing ADRs in `08-Projects/{project}/01-ADR/` and assign the next sequential number (e.g. `0001`, `0002`, `0003`).
2. **Binary Decision Inquest**: An ADR MUST only be recorded when the decision is **hard to reverse, surprising without context, or involves genuine trade-offs**.
3. **Structured Schema**: MUST strictly follow the 5 core sections: Context, Decision Drivers, Considered Options (Pros/Cons), Decision Outcome, and Consequences.

---

## The 3-Phase ADR Workflow

### Phase 1: Numbering & Path Resolution
1. Target Directory: `08-Projects/{project_name}/01-ADR/` (create if missing).
2. Count existing `[0-9]{4}-*.md` files to determine next index `NNNN`.
3. Generate filename: `NNNN-{kebab-case-title}.md` (e.g. `0004-sqlite-wal-concurrency.md`).

### Phase 2: MADR Template Composition
Load and fill the standardized MADR template from `templates/adr-template.md` via `read_file(path='templates/adr-template.md')`.

The ADR document structure comprises 5 core sections:
1. **Context and Problem Statement**: Engineering context, forces at play, and why a decision is necessary.
2. **Decision Drivers**: Key architectural forces and priorities shaping the choice.
3. **Considered Options**: Evaluated alternatives with structured pros and cons.
4. **Decision Outcome**: Selected option with first-principles rationale justifying the trade-off.
5. **Consequences and Trade-offs**: Positive outcomes, negative trade-offs, and compliance guardrails.

### Phase 3: Dual-Track Archiving
- Call `save_inbox_draft` MCP to create an entry in `99-Inbox/`, or directly write to `08-Projects/{project}/01-ADR/`.
- Update the project's `README.md` or `AGENT-CONTEXT.md` with the new ADR reference.

## 🧪 Worked example — ADR-0004

Input: *"We are moving SQLite to WAL mode. Record the decision."*
Output file: `08-Projects/dfs/01-ADR/0004-sqlite-wal-concurrency.md`

```
---
title: "ADR-0004: SQLite WAL Mode for Concurrent Readers"
created: 2026-09-28
type: project
status: stable
---

# ADR-0004: SQLite WAL Mode for Concurrent Readers

## 1. Context and Problem Statement
Worker goroutines read while a single writer commits; `journal_mode=DELETE` serialized the whole
database and produced `SQLITE_BUSY` under load.

## 2. Decision Drivers
- Maximize read throughput under concurrent workers
- Zero external daemon dependencies for embedded desktop use

## 3. Considered Options
- **Option 1: WAL mode** — pros: concurrent readers, one writer; cons: extra `-wal`/`-shm` files
- **Option 2: single serialized connection** — pros: no new files; cons: throughput collapses

## 4. Decision Outcome
Chosen **Option 1**, because WAL decouples readers from the writer without adding a daemon.

## 5. Consequences and Trade-offs
- Positive: readers stop blocking; `SQLITE_BUSY` disappears under the measured load
- Negative: `-wal`/`-shm` must ship beside the DB; mitigated by a checkpoint on close
- Guardrail: `PRAGMA journal_mode` is asserted in `tests/test_vendored_scripts.py`
```

The number `0004` came from counting the existing `[0-9]{4}-*.md` files in that directory, not from
memory.
