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
     - **Brief carries the delta, never the invariants.** Repository invariants (privacy red lines, format/lint false positives, forbidden commit paths, timeout rules) live in the repo's anchor file — point the child at it and restate only what is specific to this task. Repeating the full invariant set in every brief is pure repeated token cost; the child reads the anchor once and the brief stays small.
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

## [MUST] Isolation & Anti-Degradation Guardrails (HARD GATES)

> **Two axes of isolation** — subagent isolation (which *thread* may edit) **and** VCS isolation (which *branch* the work lands on). Guarding one axis only lets the other leak.

1. **Anti-Degradation Invariant**: Tier 2 and Tier 3 tasks **MUST NOT** be edited in the orchestrator thread without independent reviewer dispatch.
2. **Subagent Orchestration & File-Occupancy Guard**: When dispatching Gear 2 Maker-Checker or Gear 3 Swarm subagents, apply `/dfs-orchestrate` to enforce exclusive per-file partitioning tables, test serialization (preventing DB/file race conditions), adversarial reviewer briefs (`dfs-orchestrate/templates/adversarial-reviewer-brief.md`), and Windows worktree cleanup.
2. **Hard Escalation Trigger**: If a task tagged `[Tier: 1-Light]` touches production source code (any file inside the shipped package / application source tree), core test-gate or CI definition files (linters, quality gates, workflow definitions), or writes out-of-repo files, `/dfs-exec` **MUST automatically escalate it to Tier 2 or Tier 3**.
3. **Physical Receipt Invariant**: Even in Tier 1 Solo Fast-Path, zero code shall be committed without authentic terminal proof (Exit 0 + assertion output).
4. **VCS Isolation Invariant**: **Before Task 1**, `/dfs-exec` **MUST** run `git branch --show-current`. Implementation work MUST NOT be committed on `main`/`master`: create an isolated branch (`git checkout -b <type>/<slug>`) or route the run through `/dfs-pipeline` (isolated worktree). **Only two exceptions** may go straight to the main branch, both requiring explicit user authorization: **release** operations (version bump / tag / release notes) and **bookkeeping** (append-only `WORKMEMORY` events — no code, gate or test changes). The batch landing **MUST** end in a PR, never a direct push. *Why this gate exists*: a 9-commit implementation batch (production source + CI definitions) once shipped straight to `master` because the isolation rule lived **only** in `/dfs-pipeline` — a skill that run never invoked, so nothing on the executed path ever asked the question. **A rule that is not on the executed path does not exist.**

---

## [+] Acceptance Gates (MANDATORY — derived from field failures, not theory)

An exit code 0 proves "nothing crashed", never "the result is right". Four gates exist because
each one caught a real defect that a green suite and a clean exit had already waved through.

1. **Known Defect Classes pre-dispatch check (MUST)** — before dispatching, run the four
   questions from `/dfs-grill` Stage 2.5 against the task: error-classification width,
   cancelled-context teardown, progress semantics (per-run vs absolute), and duplicate
   implementations of one rule. Four consecutive milestones each shipped exactly one real
   defect from these four classes; the questions cost four lines.
2. **Real-data regression gate (Tier 3 MUST)** — for anything touching a database, a generated
   artifact, or a state machine, run the recipes in
   `dfs/references/acceptance-recipes.md`: before/after snapshot + output hash (recipe A),
   kill/resume drill (recipe B), visual self-report for rendered output (recipe C). A Tier 3
   task that never touched real data is not accepted.
3. **Human-artifact safety (MUST)** — when a task produces an artifact a human edits and a
   script reads back (labels, sign-off lists, config the human owns), recipe D applies:
   round-trip self-check at generation, dry-run before any rewrite, append-only by default.
   Silent loss of human input is the worst defect class in this workflow: it produces a
   *plausible wrong conclusion* rather than a visible failure.
4. **Orchestrator re-does one probe (Tier 3 MUST)** — the child's mutation self-report is a
   self-report. Re-execute at least one mutation physically in the parent tree and quote the
   failing assertion verbatim. This is the step that caught a child whose described mutation
   did not match what its code actually did.

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
