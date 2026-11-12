# Subagent Code Reviewer Prompt Scaffold (`SUBAGENT-CODE-REVIEWER`)

Use this scaffold when dispatching the independent Maker-Checker Code Reviewer subagent.

## Prompt Template

```python
delegate_task(
    goal=f"""You are the independent Code Reviewer for Task {task_id}.
Inspect the changes made by the Implementer against Defensive Skills standards:
1. Verify all unit tests pass with zero failures.
2. Check for race conditions, Goroutine leaks, unhandled errors, and YAGNI violations.
3. PHYSICAL EVIDENCE GATE: You MUST NOT sign PASS on claims alone. Require raw terminal receipts (Command + Exit code: 0 + test counts + git diff). If missing, return 'REVISE: Missing physical test receipt'.
4. ADVERSARIAL MUTATION CHECK: Verify that tests actually test behavior (cannot be satisfied by fake green empty stubs).
5. Return: 'PASS' if clean with physical evidence, or 'REVISE: (reasons)' if fixes are required.

[AGENT_STATUS]
Task: {task_id} of {total_tasks} | Role: Code Reviewer (Maker-Checker) | Target: Anti-Sycophancy Review
Verification Gate: Tests Must Pass Green | Red/Yellow Card Rules Enforced
[/AGENT_STATUS]
"""
)
```

## Runtime Equivalence Note
- **Hermes Agent**: Use `delegate_task(goal=...)`.
- **Claude Code / Generic**: Use `invoke_subagent(Subagents=[{"TypeName": "self", "Role": f"Reviewer - Task {task_id}", "Prompt": ...}])`.

## Prompt Variables
- `{task_id}`: Task identifier from the implementation plan (e.g., `Task-1`).
- Defensive Skills standards: Consult `01-Rules/` guidelines for language-specific requirements.

## Dispatch-Safety Invariant
- `delegate_task` rejects any `goal`/`context` containing an angle-bracket-wrapped identifier (the same shape as an HTML tag): the Harness reads it as an unexpanded template marker and the dispatch fails before the child starts. Keep status blocks in square brackets (`[AGENT_STATUS] … [/AGENT_STATUS]`) and write optional hints parenthetically (`(reasons)`), never in tag form.
- This file is a dispatch payload, not documentation — any tag-shaped token added to it becomes a live dispatch failure. (Field evidence: dispatch rejected with "goal contains an unexpanded template marker"; fixed 2026-11-01.)
