---
name: dfs-exec
description: Execute TDD plans via adaptive gear-shifting (Tier 1 Solo-Light, Tier 2 Maker-Checker, Tier 3 Critical-Swarm). Use when an implementation plan exists and the user asks to execute or implement it.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags: [execution, subagents, adaptive-gear, maker-checker, tdd, orchestrator]
    related_skills: [dfs-plan, dfs-tdd, dfs-review, dfs-team]
---
# DFS-EXEC: Adaptive Gear-Shifting Execution Engine

Execute implementation plans (`implementation_plan.md` or `.vault-exec-ledger.json`) by dynamically matching defense rigor to task fragility across **Three Adaptive Gears (自适应三挡变速箱)**.

> **Detailed playbook**: this skill's long-form sections were moved to [`references/gear-playbook.md`](references/gear-playbook.md). Load it when you need the full procedure, the worked example, or the field evidence — the constraints above are self-sufficient without it.

## [NOTE] The Three-Gear Execution Model (Adaptive Tiering)

Read the `[Tier]` tag from the task header in `implementation_plan.md`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Task Header Inspection                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   [Tier: 1-Light]          [Tier: 2-Standard]        [Tier: 3-Critical]
   [NOTE] GEAR 1: Solo-Light     [NOTE] GEAR 2: Maker-Checker  [NOTE] GEAR 3: Critical-Swarm
  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
  │ • Single agent/inline │ │ • Implementer (TDD)   │ │ • Mandatory HITL gate │
  │ • Physical receipt req│ │ • Reviewer subagent   │ │ • Multi-expert review │
  │ • Skip Reviewer agent │ │ • Strict Maker-Checker│ │ • Mutation check probe│
  │ • Batch commit allowed│ │ • Atomic git commit   │ │ • Dual-signed commit  │
  └───────────────────────┘ └───────────────────────┘ └───────────────────────┘
```

---

## [MUST] Isolation & Anti-Degradation Guardrails (HARD GATES)

> **Two axes of isolation** — subagent isolation (which *thread* may edit) **and** VCS isolation (which *branch* the work lands on). Guarding one axis only lets the other leak.

1. **Anti-Degradation Invariant**: Tier 2 and Tier 3 tasks **MUST NOT** be edited in the orchestrator thread without independent reviewer dispatch.
2. **Subagent Orchestration & File-Occupancy Guard**: When dispatching Gear 2 Maker-Checker or Gear 3 Swarm subagents, apply `/dfs-orchestrate` to enforce exclusive per-file partitioning tables, test serialization (preventing DB/file race conditions), adversarial reviewer briefs (`dfs-orchestrate/templates/adversarial-reviewer-brief.md`), and Windows worktree cleanup.
   - Builder brief: `templates/tdd-builder-prompt.md`; reviewer brief: `templates/reviewer-prompt.md`. Load the one matching the gear you are in — the full dispatch text for each gear is in [`references/gear-playbook.md`](references/gear-playbook.md).
2. **Hard Escalation Trigger**: If a task tagged `[Tier: 1-Light]` touches production source code (any file inside the shipped package / application source tree), core test-gate or CI definition files (linters, quality gates, workflow definitions), or writes out-of-repo files, `/dfs-exec` **MUST automatically escalate it to Tier 2 or Tier 3**.
3. **Physical Receipt Invariant**: Even in Tier 1 Solo Fast-Path, zero code shall be committed without authentic terminal proof (Exit 0 + assertion output).
4. **VCS Isolation Invariant**: **Before Task 1**, `/dfs-exec` **MUST** run `git branch --show-current`. Implementation work MUST NOT be committed on `main`/`master`: create an isolated branch (`git checkout -b <type>/<slug>`) or route the run through `/dfs-pipeline` (isolated worktree). **Only two exceptions** may go straight to the main branch, both requiring explicit user authorization: **release** operations (version bump / tag / release notes) and **bookkeeping** (append-only `WORKMEMORY` events — no code, gate or test changes). The batch landing **MUST** end in a PR, never a direct push. *Why this gate exists*: a 9-commit implementation batch (production source + CI definitions) once shipped straight to `master` because the isolation rule lived **only** in `/dfs-pipeline` — a skill that run never invoked, so nothing on the executed path ever asked the question. **A rule that is not on the executed path does not exist.**

> **Acceptance gates (MANDATORY)**: every gear must produce a physical receipt — exit code, assertion
> output, and a before/after snapshot with output hash for the artifact it touched
> (`dfs/references/acceptance-recipes.md` holds recipe A and the rest). The per-gear gate list
> derived from field failures is in [`references/gear-playbook.md`](references/gear-playbook.md).

---

## State Ledger CLI Integration
- Initialize Ledger: `python scripts/vault_exec_state.py init --plan-file implementation_plan.md`
- Start Task: `python scripts/vault_exec_state.py start-task --task-id Task-1`
- Complete Task: `python scripts/vault_exec_state.py complete-task --task-id Task-1 --commit <hash> --reviewer <PASS|SELF-VERIFIED>`
- Resume from Breakpoint: `python scripts/vault_exec_state.py resume`
- Inspect Pipeline Status: `python scripts/vault_exec_state.py status`

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Tier 2 logic task is small, so I will run it in Gear 1 solo mode."* | **Bypassing Maker-Checker**: Logic bugs slip past without adversarial audit. | Core logic tasks MUST run in Gear 2 with independent Reviewer subagent. |
| *"Tier 1 task does not need verification receipts because it is just docs."* | **Broken Links & Stale Dates**: Unverified edits fail repository pre-commit quality gates. | Gear 1 tasks MUST execute checkable commands (grep / strict check) before commit. |
| *"Reviewer found an issue in Tier 2, orchestrator will patch it directly."* | **Boundary Violation**: Violates maker-checker context isolation. | Re-dispatch defect list to implementer subagent; re-verify with reviewer. |
| *"Tests are green and the command exited 0, so the task is accepted."* | **Green-Suite Blindness**: an exit code proves nothing crashed; it never proves the result is right. Blank charts, doubled counters, a refused slot reported as success, and silently dropped human labels all passed a green suite first. | Run the Acceptance Gates above: known-defect-class questions, real-data snapshot / kill-resume / visual recipes, human-artifact safety, and one physically re-done probe. |
| *"The child described its mutation verification, that counts as evidence."* | **Self-Report Laundering**: the description is the child's claim about its own work. | Re-execute one mutation in the parent tree and quote the failing assertion verbatim before signing off. |

---

## Checkable Completion Criterion
- **Gear 1 (Solo-Light)**: command exit code 0 + authentic terminal output receipt.
- **Gear 2 (Maker-Checker)**: independent reviewer subagent emits `APPROVED / CLEAN PASS` + git diff matches task boundary.
- **Gear 3 (Critical-Swarm)**: HITL human sign-off + dual-signed commit + all applicable acceptance gates verified.
