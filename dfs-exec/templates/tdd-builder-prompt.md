# Subagent TDD Builder Prompt Scaffold (`SUBAGENT-TDD-BUILDER`)

Use this scaffold when dispatching the dedicated TDD Builder implementer subagent.

## Prompt Template

```python
delegate_task(
    goal=f"""You are the dedicated TDD Builder for Task {task_id}: {task_name}.
Goal: Implement the required logic strictly following The Iron Law of TDD.

Target Files:
- Create: {target_files}
- Tests: {test_files}

Instructions:
1. Write the failing test first (RED).
2. Run test command: `{test_cmd}` and verify failure.
3. Implement minimal code to pass (GREEN).
4. Refactor with Guard Clauses (max 2 levels indentation).
5. Mutation self-proof for the four mandatory classes — corruption/duplication guards,
   state transitions, error classification, human-input parsing boundaries. Quote the
   failing assertion VERBATIM (`file:line: expected X, got Y`), then revert and prove the
   tree is green again. A prose claim ("the test went red") is not evidence.
   - **If this task emits numbers** (figures, tables, reports, PDFs), add the numeric branch:
     make one number in the single source of truth wrong and prove the emitted artefact goes
     red. Typing the value directly into the plot call and asserting only that a file exists
     is the exact failure mode this branch exists to catch.
6. Declare what you could NOT validate on this host, and anything you found OUTSIDE your
   file ownership. Both are mandatory report fields; silence is read as "nothing to report".

Output final summary with test execution evidence.

[AGENT_STATUS]
Task: {task_id} of {total_tasks} | Role: TDD Builder | Status: IN_PROGRESS
Completed: {completed_tasks} | Pending: {pending_tasks}
Invariants: Strict RED-GREEN-REFACTOR | Zero Mock on Real Paths
Repo invariants: {repo_invariants_path} — read it; do not wait for the rules to be restated.
[/AGENT_STATUS]
"""
)
```

## Runtime Equivalence Note
- **Hermes Agent**: Use `delegate_task(goal=...)`.
- **Claude Code / Generic**: Use `invoke_subagent(Subagents=[{"TypeName": "self", "Role": f"TDD Builder - Task {task_id}", "Prompt": ...}])`.

## Prompt Variables
- `{task_id}`: Task identifier from the implementation plan (e.g., `Task-1`).
- `{task_name}`: Descriptive title of the task.
- `{target_files}`: Paths of files created or modified.
- `{test_files}`: Paths of corresponding test files.
- `{test_cmd}`: Exact terminal command to run the targeted test.
- `{repo_invariants_path}`: Path to the repository's invariants/anchor file the child must read (see `dfs-plan` Phase 2). Leave empty only when the repo genuinely has none.

## Dispatch-Safety Invariant
- `delegate_task` rejects any `goal`/`context` containing an angle-bracket-wrapped identifier (the same shape as an HTML tag): the Harness reads it as an unexpanded template marker and the dispatch fails before the child starts. Keep status blocks in square brackets (`[AGENT_STATUS] … [/AGENT_STATUS]`) and write optional hints parenthetically (`(reasons)`), never in tag form.
- This file is a dispatch payload, not documentation — any tag-shaped token added to it becomes a live dispatch failure. (Field evidence: dispatch rejected with "goal contains an unexpanded template marker"; fixed 2026-11-01.)
