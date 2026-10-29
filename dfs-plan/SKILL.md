---
name: dfs-plan
description: Draft bite-sized TDD implementation plans from specs. Use when the user asks for an implementation plan, or before writing code for a multi-step feature.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags: [planning, tdd, architecture, implementation-plan, task-breakdown]
    related_skills: [dfs-exec, dfs-tdd, dfs-spark, dfs-grill, dfs-orchestrate]
    mcp_tools: [omni_search, get_code_template]
---
# DFS-Anchored Implementation Planning

Produce structured, deterministic implementation plans where every task includes an actionable **Subagent Prompt Scaffold** ready for direct consumption by `/dfs-exec`.

> **Detailed playbook**: this skill's long-form sections were moved to [`references/plan-example.md`](references/plan-example.md). Load it when you need the full procedure, the worked example, or the field evidence — the constraints above are self-sufficient without it.

## [MUST] The Plan-Before-Code Invariant (RFC 2119 MUST)
> **NO multi-step implementation shall begin without an approved `implementation_plan.md` adhering strictly to `templates/plan-schema.md`.**
> Never speculate on downstream unknown components — unknowns MUST be quarantined in Fog of War until upstream tasks graduate them.

---

## [NOTE] This skill, or `/dfs-spark` / `/dfs-exec`?

| | this skill | `/dfs-spark` | `/dfs-exec` |
|---|---|---|---|
| The ask | **plan** — convert spec into discrete TDD tasks | **shape** — turn fuzzy ideas into a design spec | **execute** — run tasks via isolated subagents |
| Output | an `implementation_plan.md` | a design specification | committed code and test receipts |
| Feeds | `/dfs-exec` | `/dfs-plan` | `/dfs-review` / `/dfs-save` |

---

## The 3-Phase Planning Protocol

```
  [Phase 1: Context & Omni-Search Ingestion]
                      │
                      ▼
  [Phase 2: Plan Schema Formulation & Task Scaffolding]
                      │
                      ▼
  [Phase 3: Downstream Dispatch & Ledger Handshake]
```

### Phase 1: Context & Omni-Search Ingestion
1. **Query Knowledge & Architecture Constraints**:
   - Query `omni_search(query, scope='ladder')` to extract architecture invariants.
   - Query `get_code_template` via `coding-vault-search` MCP to retrieve pure language production code idioms.
2. **Inspect Physical Codebase Paths**:
   - Verify existing files, line counts, and import topologies using `read_file` and `search_files`.
   - Never hypothesize signatures for existing code: trace every symbol to its physical definition.
3. **Checkable Completion Criterion**:
   - Architecture constraints extracted and physical target files verified to exist or explicitly marked as new.

### Phase 2: Plan Document Structure (Required Schema)
1. **Enforce Schema Conformity**:
   - Every generated `implementation_plan.md` MUST follow the schema defined in `templates/plan-schema.md`.
   - Load the full template specification via `read_file(path='templates/plan-schema.md')`.
2. **Mandatory Sections in `implementation_plan.md`**:
   - **Plan Header**: Goal, Tech Stack, Spec/ADR Reference, and Global Constraints.
   - **Repo Invariants Pointer**: the path of the repository's invariants/anchor file that every subagent brief will cite instead of restating rules. If none exists, create it as part of Task 0 (`/dfs-onboard` Phase 3 produces it) — a plan whose briefs must each restate the invariants pays that cost on every dispatch.
   - **Task Specification**: Target files (Create/Modify/Test) and Interface boundaries (`Consumes:` / `Produces:`).
   - **Mode Tagging**: Every task MUST be tagged either `[Mode: AFK]` (autonomous) or `[Mode: HITL]` (human checkpoint).
   - **Subagent Prompt Scaffold**: Self-contained dispatch prompt ready for `/dfs-exec` or subagent delegation.
   - **File-Occupancy Partitioning**: For multi-subagent tasks, consult `/dfs-orchestrate` to assign an exclusive per-file table (preventing concurrent merge collisions) before dispatch.
   - **TDD Step Breakdown**: Checkbox list covering Red -> Verify Red -> Green -> Verify Green -> Refactor -> Commit.
   - **Deferred Gap Register**: one row per gap the plan knowingly leaves open, with the columns `gap | why deferred | trigger that forces revisiting | owner`. A row that says only "TODO" is not a register entry — the trigger column is the load-bearing one: a gap deferred without a named trigger gets deferred twice more and is eventually forced open by an unrelated task at the worst moment.
   - **Deviation Table (post-execution, filled before merge)**: `plan text | what was actually built | why`. Three columns, no exceptions: a task whose implementation deviated from its plan without this table does not merge.
3. **Checkable Completion Criterion**:
   - `implementation_plan.md` exists, adheres to `templates/plan-schema.md`, has zero `TODO`/`TBD` in active tasks, and every active task specifies `Produces:` interface signatures.
   - Deferred Gap Register present with a non-empty trigger column for every row.

### Phase 3: Downstream Dispatch & Ledger Handshake
1. **Pre-Dispatch Verification**:
   - The file exists on disk.
   - Every active task carries its Files, its Interfaces, and its Subagent Prompt Scaffold.
   - Every task left in **Fog of War** explicitly names the unknown blocking it.
2. **Ledger Integration**:
   - Initialize ledger: `python scripts/vault_exec_state.py init --plan-file implementation_plan.md`.
3. **Relay to Downstream Skills**:
   - Prompt user: `Plan generated with subagent prompt scaffolds. Initialize ledger and execute with /dfs-exec?`
4. **Checkable Completion Criterion**:
   - Ledger initialization returns exit code 0 (`.vault-exec-ledger.json` created) or plan confirmed ready for dispatch.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I can plan all 5 subsystems at once even though subsystem 2 depends on an unbuilt engine."* | **Speculative Hallucination**: cascading API drifts when upstream assumptions change. | Quarantine unverified dependencies in `## [NOTE] Fog of War`. Break monolithic specs into sub-plans. |
| *"I don't need to read existing code before drafting task files."* | **Phantom Symbol Coupling**: calling non-existent functions or wrong package paths. | Ground all existing paths and interfaces with `read_file` or `search_files` during Phase 1. |
| *"The task description is clear enough; I don't need the prompt scaffold."* | **Subagent Context Amnesia**: isolated subagents lack instructions and fail to execute. | Every task MUST carry a self-contained Subagent Prompt Scaffold. |
| *"I'll group several unrelated edits into Task 1 to save time."* | **Unverifiable Mega-Diffs**: breaking TDD atomicity and impossible maker-checker audit. | Enforce bite-sized task granularity (one discrete 2~5 minute action per task). |

---
