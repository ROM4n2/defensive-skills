# TDD Anti-Patterns: Rationalizations & Their Guards (`references/anti-patterns.md`)

Load this when reviewing a test suite, auditing an agent's self-reported green run, or when a
contributor proposes deleting, skipping, or weakening a test.

Every row is a rationalization observed in practice. The hazard column names what actually breaks; the
guard column is the mechanical check that makes the rationalization impossible rather than discouraged.

---

## 1. The Rationalization Table

| Agent Rationalization (Anti-Pattern) | Real Hazard (DPO Bad Case) | Defensive Guard (MUST) |
|---|---|---|
| *"The test failed, so let me delete or weaken the assert."* | **Malicious Reward Hacking**: masking bugs to simulate 100% pass rates. | NEVER delete or weaken a failing test. Fix production code until the contract passes. |
| *"I'll add `@pytest.mark.skip` or `t.Skip()` to make the suite green."* | **Test Suite Rot**: real regressions pass silently in CI/CD. | Zero tolerance for newly skipped tests. A skipped test is considered a failing test. |
| *"I'll write the implementation first, then write a test to cover it."* | **Fake Green (Tautological Test)**: tests tailored to pass implementation bugs. | Step 2 failure receipt is mandatory before creating production implementation files. |
| *"The implementation looks correct, so I can skip running the test."* | **Premature Completion**: declaring victory without empirical evidence. | Terminal execution receipt with raw exit code 0 is mandatory for completion claims. |
| *"The suite is green, so every test is wired to the code it claims to cover."* | **Unreachable Coverage**: a passing test proves the assertion runs, not that the production path reaches it. | Mutate the *call site* (not the logic) once per critical gate and confirm the suite goes red — see `dfs-gate/references/dead-gate-traps.md` §2. |

---

## 2. Why Each Guard Is Mechanical, Not Advisory

A guard that depends on the reviewer's attention is a guard that fails on the first busy week. Each of
the five above maps to something a script or a receipt can check:

1. **Assert weakening** → the diff shows a removed assertion. Require the pre-change assertion text in
   the PR body; a reviewer diffing `git diff -- '*.py'` for `-assert`/`-expect` catches it in seconds.
2. **Skip markers** → grep the diff for `skip`, `xit`, `t.Skip`, `@Ignore`. Treat a new skip as a
   failing check in CI, not a lint warning.
3. **Implementation-first** → the commit order is the receipt. `git log --oneline -- tests/ src/`
   shows which landed first; a test commit that follows the implementation commit is the tell.
4. **Unverified completion** → the raw exit code and `Ran N tests` line, quoted. "All tests pass"
   without a count is a self-report, not evidence.
5. **Unreachable coverage** → mutation at the call site, applied exactly once
   (`assert raw.count(old) == 1`), with the resulting red output quoted.

---

## 3. Related Traps That Are Not Rationalizations

These are failures of the test itself rather than of the agent's discipline. Full detail lives in
[dead-test-and-quantity-guards.md](dead-test-and-quantity-guards.md):

| Trap | One-line signature |
|---|---|
| Tautological test | Passes before the implementation exists |
| Vacuous fixture | Iterates an empty collection and asserts inside the loop |
| Re-implemented logic | The test copies the production regex/query instead of importing it |
| Presence-only assertion | `assertGreater(size, 4000)` standing in for a value check |
| Constant-false fixture | Hand-typed stub that cannot express the real payload's shape |
| Quantity dimension confusion | `ratio` (1.27) fed to a sink expecting `share` (0..1) |

---

## 4. Applying This During Review

1. Read the test diff **before** the implementation diff. A test that could not have failed tells you
   nothing about the code.
2. For each new test, name the exact production line that would have to change for it to go red. If you
   cannot name one, the test is decorative.
3. For each new gate, apply the fire-ability checklist in
   `dfs-gate/references/dead-gate-traps.md` §5 — a gate is verified by its rejection, not its acceptance.
4. Reject any completion claim that reports a pass without a quoted `Ran N tests` summary or a raw
   exit code.
