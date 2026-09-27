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
5. Output final summary with test execution evidence.

<agent_status>
Task: {task_id} of {total_tasks} | Role: TDD Builder | Status: IN_PROGRESS
Completed: {completed_tasks} | Pending: {pending_tasks}
Invariants: Strict RED-GREEN-REFACTOR | Zero Mock on Real Paths
</agent_status>
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
