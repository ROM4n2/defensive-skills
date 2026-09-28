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

## 🚨 The Subagent Isolation Invariant (HARD GATE)
> Always enforce subagent isolation: The Orchestrator main thread focuses strictly on **State Tracking (Ledger), Task Dispatching, Maker-Checker Review Oversight, and Git Commits**.
> When any production source code edit is needed, dispatch a fresh, context-isolated subagent via `delegate_task` (or runtime equivalent) instead of making direct edits in the orchestrator thread.

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
