---
name: dfs-plan
description: Draft bite-sized TDD implementation plans from specs.
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, tdd, architecture, implementation-plan, task-breakdown]
    related_skills: [dfs-exec, dfs-tdd, dfs-spark, dfs-grill]
    mcp_tools: [omni_search, get_code_template]
---

# DFS-Anchored Implementation Planning

Produce structured, deterministic implementation plans where every task includes an actionable **Subagent Prompt Scaffold** ready for direct consumption by `/dfs-exec`.

## Core Planning Invariants (MUST)
1. **Scope Check**: If spec covers multiple independent subsystems, break into sub-plans.
2. **File Structure & Clear Boundaries**: Map out created/modified files, line ranges, and interface signatures (`Consumes:` / `Produces:`).
3. **Bite-Sized Task Granularity**: Every step is one discrete action (2~5 minutes).
4. **TDD Baked into Every Task**: Red -> Verify Red -> Green -> Verify Green -> Commit.
5. **Subagent Prompt Scaffold per Task**: Every task MUST include an explicit prompt block for `/dfs-exec` dispatch.

---

## Phase 1: Context & Omni-Search Ingestion
1. Query `omni_search(query, scope='ladder')` to extract architecture constraints.
2. Query `get_code_template` via `coding-vault-search` MCP to extract pure Go/C++/C/Python production code snippets.

---

## Phase 2: Plan Document Structure (Required Schema)

Every generated `implementation_plan.md` MUST follow the schema defined in `templates/plan-schema.md`.
Load the full template specification via `read_file(path='templates/plan-schema.md')` when drafting plans.

Key required sections in `implementation_plan.md`:
- **Plan Header**: Goal, Tech Stack, Spec/ADR Reference, and Global Constraints.
- **Task Specification**: Target files (Create/Modify/Test) and Interface boundaries (`Consumes:` / `Produces:`).
- **Subagent Prompt Scaffold**: Self-contained dispatch prompt ready for `/dfs-exec` or subagent delegation.
- **TDD Step Breakdown**: Checkbox list covering Red -> Verify Red -> Green -> Verify Green -> Refactor -> Commit.

---

## Phase 3: Downstream Dispatch
Prompt user: `Plan generated with subagent prompt scaffolds. Initialize ledger and execute with /dfs-exec?`
