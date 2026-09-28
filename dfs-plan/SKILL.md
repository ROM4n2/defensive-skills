---
name: dfs-plan
description: Draft bite-sized TDD implementation plans from specs. Use when the user asks for an implementation plan, or before writing code for a multi-step feature.
version: 0.2.0
license: MIT
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

## 🧪 Worked example — one task with its exact interface contract

Input spec: *"Add a ledger resume command to the execution engine."* -> `implementation_plan.md` excerpt:

```
## 🎯 Active Frontier (Unblocked Tasks)

### Task 2: Ledger resume loader [Mode: AFK] [Role: TDD Builder]

**Files:**
- Modify: `scripts/vault_exec_state.py`
- Test: `tests/test_vendored_scripts.py`

**Interfaces:**
- Consumes: `json.loads(ledger_path.read_text())`
- Produces: `def resume(ledger_path: Path) -> list[str]`

**Subagent Prompt Scaffold (for /dfs-exec):**
> "Implement Task 2: Ledger resume loader. Steps: write a failing test in
> `tests/test_vendored_scripts.py` (RED); run `python tests/test_vendored_scripts.py` and verify it
> fails; add `resume()` (GREEN); return a receipt with the raw exit code."

**Step Breakdown:**
- [ ] Step 1: Write the failing test (RED)
- [ ] Step 2: Run it and verify it fails with the expected message
- [ ] Step 3: Implement the minimal production code (GREEN)
```

The `Produces:` line is the falsifiable part — `/dfs-exec` must hit that exact signature, or the plan
and the code have silently diverged.
