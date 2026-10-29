# dfs-plan — extended playbook (tier 3)

Loaded on demand by `dfs-plan/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

## [NOTE] Worked Example — One Task With Its Exact Interface Contract

Input spec: *"Add a ledger resume command to the execution engine."* -> `implementation_plan.md` excerpt:

```markdown

## [NOTE] Active Frontier (Unblocked Tasks)

### Task 2: Ledger resume loader [Mode: AFK] [Role: TDD Builder]

**Files:**
- Modify: `scripts/vault_exec_state.py`
- Test: `tests/test_vendored_scripts.py`

**Interfaces:**
- Consumes: `json.loads(ledger_path.read_text())`
- Produces: `def resume(ledger_path: Path) -> list[str]`

**Subagent Prompt Scaffold (for /dfs-exec):**
> "Implement Task 2: Ledger resume loader. Steps: write a failing test in
> `tests/test_vendored_scripts.py` (RED); run `python tests/test_vendored_scripts.py` and verify it
> fails; add `resume()` (GREEN); return a receipt with the raw exit code."

**Step Breakdown:**
- [ ] Step 1: Write the failing test (RED)
- [ ] Step 2: Run it and verify it fails with the expected message
- [ ] Step 3: Implement the minimal production code (GREEN)
```

The `Produces:` line is the falsifiable part — `/dfs-exec` must hit that exact signature, or the plan
and the code have silently diverged.
