---
name: dfs-adr
description: Draft and archive numbered Architecture Decision Records.
version: 0.2.0
author: Defensive Skills contributors
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
