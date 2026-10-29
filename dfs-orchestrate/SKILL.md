---
name: dfs-orchestrate
description: Dispatch and verify subagents with file-occupancy guards. Use when several subagents must work in one repo without colliding, or a batch needs a granularity call.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  author: Haoyu, Hermes Agent
  hermes:
    tags:
    - delegation
    - subagents
    - verification
    - multi-agent
    - orchestration
    related_skills:
    - dfs-exec
    - dfs-pipeline
    - dfs-maintain
    - dfs-gate
    - dfs-verify
    - dfs-plan
    mcp_tools: []
---

# DFS-ORCHESTRATE: Multi-Agent Dispatch, Verify, Merge

> **Invariant (MUST)**: A child's report is a **self-report, not evidence**. Nothing a subagent asserts about its own work counts until the orchestrator reproduces the claim in the parent tree.

## When to use
- Dispatching subagents to implement, review, or verify work across parallel streams in one repo.
- Acting on completion reports: merging child branches, triaging findings, enforcing maker-checker separation.

---

## The Loop

### 1. Partition by FILE before dispatch
- **Exclusive ownership per file**: Measure spread, assign exclusive file ownership in plan/handoff, and serialize same-file workstreams (see `dfs-maintain`).
- **Contract amendments**: Re-check file allocation immediately whenever follow-up scope touches new files.

### 2. Brief construction
- **Dual-Layer Dispatch Routing & Fresh-Context Follow-Up (MUST)**: Route work by task shape (in-thread vs fresh subagent vs persistent CLI worker). Never resurrect a bloated 50K-token worker session for a small follow-up fix; dispatch a fresh small-context subagent with exact `file:line` delta. Load [references/brief-and-pitfalls-playbook.md](references/brief-and-pitfalls-playbook.md) §1.
- **Reference repo invariants**: Restate only the delta; cite repository anchor files to avoid repeating full invariants.
- **Pass actionable evidence**: Cite exact `file:line` quotes, never subjective conclusions.
- **Prescribe receipt & blast-radius gate list**: Command + exit code + counts + diff stat; grep callers across test tree for changed symbols.
- **Relocation & multi-batch split rules**: Enforce frozen surface (zero assertion changes) and require residual inventory handbacks. Load [references/brief-and-pitfalls-playbook.md](references/brief-and-pitfalls-playbook.md) §2.
- **Batching & escalation**: Size dispatches by domain; escalate lightweight tasks to maker-checker if they touch production code.

### 3. Serialize unshareable resources
- **One test process at a time**: Serial test execution prevents false greens and baseline contamination on shared DB/cache/ports.

### 4. Verify before merge
- **Parent tree reproduction**: Re-run affected test suites serially from parent tree sizing by blast radius, not diff size.
- **Cross-check receipts & batch ordering**: Verify counts match; ensure restructuring preserved earlier fixes without silent drops.

### 5. Review adversarially or not at all
- **Adversarial brief**: Require reviewers to falsify assumptions, rerun mutations verbatim, and test riskiest hops (load `templates/adversarial-reviewer-brief.md`).

### 6. Merge, then clean
- **Inner-first & exact-ID cleanup**: Prune target worktrees by exact ID (`rm -rf .worktrees/subagent-<id>`), never blanket wildcards.

---

## Acting on what a child reports
- **Reproduce before registering**: Unreproduced findings stay observations, not backlog items.
- **Premise corrections**: Adopt child contradictions when verified by checkable code artifacts (`file:line` / AST / failing test).
- **Invalidate on write warnings**: Re-derive figures in parent tree if child run reported write-channel failures.

## Pitfalls
- **Parent workspace misrouting (`GOWORK=off`)**: Isolate toolchains so subagent worktrees never compile parent roots.
- **No empty turns**: Always emit a status line on dispatch, and complete the full merge-and-prune cascade in the same turn upon a PASS verdict.
- **Wildcard worktree deletion**: Never run `rm -rf .worktrees/*` while sibling subagents are alive.
- **Hoisting forced copies**: Hoist cross-boundary helper copies before subsequent batches land to prevent multi-copy drift.
For full routing, relocation rules, and worktree pitfall catalog, load [references/brief-and-pitfalls-playbook.md](references/brief-and-pitfalls-playbook.md) §3.

## Checkable Completion Criterion
- Subagent branch merged only after serial verification suite passes in parent tree.
- All child worktrees pruned cleanly with zero residual locks (`git worktree list` shows only primary branches).

---

## Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"The subagent reported tests passed, so I can trust it."* | **Unverified Self-Reporting**: Subagents may hallucinate green runs or omit tests. | Orchestrator MUST independently run the physical test suite and verify diffs. |
| *"Two subagents modifying the same file can resolve git conflicts later."* | **Concurrent Mutation Conflict**: Parallel edits overwrite work and trigger merge conflicts. | Enforce File-Occupancy Tables: exactly one subagent is granted write ownership per file. |
| *"Running tests in parallel across all subagents speeds up the build."* | **Environment Contention**: Parallel suites collide on DB, sockets, and cache states. | Execute verification test suites serially; never run contending suites concurrently. |
