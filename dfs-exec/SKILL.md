---
name: dfs-exec
description: Execute TDD plans via isolated subagents with maker-checker. Use when an implementation plan exists and the user asks to execute or implement it.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [execution, subagents, maker-checker, tdd, orchestrator]
    related_skills: [dfs-plan, dfs-tdd, dfs-review]
---

# DFS-EXEC: Multi-Subagent Deterministic Execution Engine

Execute implementation plans (`implementation_plan.md` or `.vault-exec-ledger.json`) by dispatching fresh, context-isolated subagents for each task.

## 🚨 The Subagent Isolation Invariant (RFC 2119 MUST)
> **The Orchestrator main thread focuses strictly on State Tracking, Task Dispatching, Maker-Checker Review Oversight, and Git Commits.**
> When any production source code edit is needed, dispatch a fresh, context-isolated subagent via `delegate_task` instead of editing code in the orchestrator thread.

---

## The 3-Stage Task Execution State Machine

For each Task in the implementation plan, follow this strict loop:

```
           ┌──────────────────────────────────────────────┐
           │ Task Initialized (Status: IN_PROGRESS)      │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
      [Step 1: Dispatch Implementer Subagent (TDD Builder)]
      delegate_task(
        goal="<Self-contained prompt scaffold from dfs-plan>"
      )
                                  │
                                  ▼ (Implementer returns code & test evidence)
      [Step 2: Dispatch Reviewer Subagent (Maker-Checker)]
      delegate_task(
        goal="Review Task N against 01-Rules/ and verify all tests pass..."
      )
                                  │
                                  ▼ (Reviewer returns PASS / REVISE)
      [Step 3: Atomic Git Commit & Ledger Update]
      - git commit -m "feat(<scope>): complete Task N"
      - python scripts/vault_exec_state.py complete-task --task-id <id> --reviewer PASS
```

> **Runtime Neutrality Note:** In Hermes Agent environments, subagents are dispatched via `delegate_task(goal=...)`. In Claude Code or other multi-agent runtimes, use the equivalent `invoke_subagent` syntax. Both provide full context isolation.

---

### Step 1: Dispatch Implementer Subagent (TDD Builder)
1. **Context-Isolated Implementation**:
   - Dispatch `delegate_task(goal=...)` with the self-contained prompt scaffold generated during `/dfs-plan`.
   - Implementer loads `templates/tdd-builder-prompt.md` via `read_file(path='templates/tdd-builder-prompt.md')`.
   - Implementer executes strict RED-GREEN-REFACTOR TDD cycle, producing git diff and test receipts.
2. **Checkable Completion Criterion**:
   - Implementer subagent completes with exit receipts showing test suite green and non-empty diff for the targeted task scope.

### Step 2: Dispatch Reviewer Subagent (Maker-Checker)
1. **Adversarial Read-Only Audit**:
   - Dispatch `delegate_task(goal=...)` with `templates/reviewer-prompt.md` loaded via `read_file(path='templates/reviewer-prompt.md')`.
   - Reviewer audits diff against Defensive Skills rules with zero production code edits.
   - Reviewer issues binary verdict: `PASS` (Clean) or `REVISE` (blocking defects with `file:line` citations).
2. **Checkable Completion Criterion**:
   - Reviewer subagent returns unambiguous `PASS` verdict, or `REVISE` defect list with specific line citations requiring re-dispatch.

### Step 3: Atomic Git Commit & State Ledger Update
1. **Commit & Ledger Persistence**:
   - Commit changes atomically: `git commit -m "feat(<scope>): complete Task N"`.
   - Update ledger: `python scripts/vault_exec_state.py complete-task --task-id <id> --reviewer PASS`.
   - Verify ledger status before advancing to Task N+1.
2. **Checkable Completion Criterion**:
   - Git commit SHA verified on current branch; `vault_exec_state.py` reports task status `COMPLETED`.

---

## Standard Subagent Dispatch Scaffolds

Load dispatch templates via `read_file` prior to triggering subagents:

- **Trailing State Bar Injection (MUST)**:
  Always append a read-only `<agent_status>` block at the tail of the dispatched prompt to anchor task focus without invalidating prefix KV caches.
- **Implementer Scaffold (`SUBAGENT-TDD-BUILDER`)**:
  Defined in `templates/tdd-builder-prompt.md`. Load via `read_file(path='templates/tdd-builder-prompt.md')`. Enforces strict RED-GREEN-REFACTOR TDD cycle.
- **Reviewer Scaffold (`SUBAGENT-CODE-REVIEWER`)**:
  Defined in `templates/reviewer-prompt.md`. Load via `read_file(path='templates/reviewer-prompt.md')`. Enforces Maker-Checker independent verification against Defensive Skills standards.

---

## State Ledger CLI Integration
- Initialize Ledger: `python scripts/vault_exec_state.py init --plan-file implementation_plan.md`
- Start Task: `python scripts/vault_exec_state.py start-task --task-id Task-1`
- Complete Task: `python scripts/vault_exec_state.py complete-task --task-id Task-1 --commit <hash> --reviewer PASS`
- Resume from Breakpoint: `python scripts/vault_exec_state.py resume`
- Inspect Pipeline Status: `python scripts/vault_exec_state.py status`

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"This task is simple, so I'll edit code directly in the orchestrator thread."* | **Context Bloat & Maker-Checker Collapse**: orchestrator context drowns in diffs; skips independent review. | Orchestrator NEVER writes production code directly. Dispatch subagents for all edits. |
| *"The implementer self-reported tests pass, so I can skip the reviewer subagent."* | **Hallucination Cascades**: accepting unverified claims allows broken code into commits. | Maker-Checker is mandatory: reviewer subagent MUST inspect diff before commit. |
| *"Task hit a minor blocker, so I'll skip it and proceed to the next task."* | **Broken Dependency Chain**: partial implementations cause compounding failures downstream. | Stop loop on task failure. Iterate with implementer or escalate to user; never skip. |
| *"Reviewer found an issue, so the orchestrator will quickly patch it inline."* | **Boundary Violation**: bypasses maker-checker isolation and introduces unreviewed changes. | Send review defects back to implementer subagent to fix; re-verify with reviewer. |
