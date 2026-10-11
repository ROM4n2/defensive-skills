---
license: MIT
name: dfs-exec
description: Execute TDD plans via adaptive gear-shifting (Tier 1 Solo-Light, Tier 2 Maker-Checker, Tier 3 Critical-Swarm). Use when an implementation plan exists and the user asks to execute or implement it.
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags: [execution, subagents, adaptive-gear, maker-checker, tdd, orchestrator]
    related_skills: [dfs-plan, dfs-tdd, dfs-review, dfs-team]
---

# DFS-EXEC: Adaptive Gear-Shifting Execution Engine

Execute implementation plans (`implementation_plan.md` or `.vault-exec-ledger.json`) by dynamically matching defense rigor to task fragility across **Three Adaptive Gears (自适应三挡变速箱)**.

## ⚙️ The Three-Gear Execution Model (Adaptive Tiering)

Read the `[Tier]` tag from the task header in `implementation_plan.md`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Task Header Inspection                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   [Tier: 1-Light]          [Tier: 2-Standard]        [Tier: 3-Critical]
   ⚙️ GEAR 1: Solo-Light     ⚙️ GEAR 2: Maker-Checker  ⚙️ GEAR 3: Critical-Swarm
  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
  │ • Single agent/inline │ │ • Implementer (TDD)   │ │ • Mandatory HITL gate │
  │ • Physical receipt req│ │ • Reviewer subagent   │ │ • Multi-expert review │
  │ • Skip Reviewer agent │ │ • Strict Maker-Checker│ │ • Mutation check probe│
  │ • Batch commit allowed│ │ • Atomic git commit   │ │ • Dual-signed commit  │
  └───────────────────────┘ └───────────────────────┘ └───────────────────────┘
```

---

## Gear 1: Solo-Light (极速自证档)
- **Applicable Tasks**: `[Tier: 1-Light]` — Documentation, YAML frontmatter, constants, config updates, running existing build/export scripts.
- **Workflow**:
  1. **Execution**: Orchestrator executes directly in-thread (for scripts/docs) or dispatches a single lightweight subagent.
  2. **Physical Evidence Gate (MANDATORY)**: Must capture unambiguous binary evidence (`exit code 0`, `grep` assertion count, lint clean). Qualitative claims ("I verified it") are strictly rejected.
  3. **Skip Reviewer Subagent**: No independent Reviewer subagent is dispatched. Saves token cold-start overhead and eliminates 429 rate limits.
  4. **Batch Commit Support**: Consecutive Tier 1 tasks in a `### Batch N [Tier: 1-Light]` group accumulate diffs, run overall repository quality gate, and commit as a single batch commit (`chore(<scope>): complete Batch N (Tasks X-Y)`).

---

## Gear 2: Maker-Checker (标准工业档)
- **Applicable Tasks**: `[Tier: 2-Standard]` — Production logic implementation, algorithmic changes, bugfixes with unit tests, refactoring.
- **Workflow (The Strict 3-Stage Loop)**:
  1. **Step 1: Dispatch Implementer Subagent (TDD Builder)**
     - Dispatches fresh context-isolated subagent with `templates/tdd-builder-prompt.md`.
     - Executes strict RED-GREEN-REFACTOR TDD cycle.
  2. **Step 2: Dispatch Reviewer Subagent (Code Reviewer)**
     - Dispatches independent read-only reviewer subagent with `templates/reviewer-prompt.md`.
     - Reviewer checks diff against RFC 2119 standards and returns binary verdict: `PASS` or `REVISE`.
  3. **Step 3: Atomic Git Commit & State Ledger Update**
     - `git commit -m "feat(<scope>): complete Task N"`.
     - `python scripts/vault_exec_state.py complete-task --task-id <id> --reviewer PASS`.

---

## Gear 3: Critical-Swarm (顶格会诊档)
- **Applicable Tasks**: `[Tier: 3-Critical]` — Multi-repository batch writes, schema migrations, core gate logic modifications, security/credential boundary shifts.
- **Workflow**:
  1. **HITL Authorization Gate**: Present change impact, target repository list, and irreversible risks to user. Await explicit user confirmation before touching files.
  2. **Dual-Agent Adversarial Execution**: Implementer subagent + Reviewer subagent with mandatory mutation testing probe.
  3. **Verification & Ledger Sign-off**: Multi-repo atomic commits, state verification across all boundaries.

---

## 🚨 Subagent Isolation & Anti-Degradation Guardrails (HARD GATES)

1. **Anti-Degradation Invariant**: Tier 2 and Tier 3 tasks **MUST NOT** be edited in the orchestrator thread without independent reviewer dispatch.
2. **Hard Escalation Trigger**: If a task tagged `[Tier: 1-Light]` touches production business logic, core test gate files (e.g. `vault-healthcheck.py`), or writes out-of-repo files, `/dfs-exec` **MUST automatically escalate it to Tier 2 or Tier 3**.
3. **Physical Receipt Invariant**: Even in Tier 1 Solo Fast-Path, zero code shall be committed without authentic terminal proof (Exit 0 + assertion output).

---

## State Ledger CLI Integration
- Initialize Ledger: `python scripts/vault_exec_state.py init --plan-file implementation_plan.md`
- Start Task: `python scripts/vault_exec_state.py start-task --task-id Task-1`
- Complete Task: `python scripts/vault_exec_state.py complete-task --task-id Task-1 --commit <hash> --reviewer <PASS|SELF-VERIFIED>`
- Resume from Breakpoint: `python scripts/vault_exec_state.py resume`
- Inspect Pipeline Status: `python scripts/vault_exec_state.py status`

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Tier 2 logic task is small, so I will run it in Gear 1 solo mode."* | **Bypassing Maker-Checker**: Logic bugs slip past without adversarial audit. | Core logic tasks MUST run in Gear 2 with independent Reviewer subagent. |
| *"Tier 1 task does not need verification receipts because it is just docs."* | **Broken Links & Stale Dates**: Unverified edits fail repository pre-commit quality gates. | Gear 1 tasks MUST execute checkable commands (grep / strict check) before commit. |
| *"Reviewer found an issue in Tier 2, orchestrator will patch it directly."* | **Boundary Violation**: Violates maker-checker context isolation. | Re-dispatch defect list to implementer subagent; re-verify with reviewer. |
