# Zero-Cost Probe Recipes

Load when a claim needs physical evidence and the cheapest reliable path is a throwaway harness rather than the full suite. Every recipe is read-only against the repo, needs no paid API calls, and leaves no artifact behind.

---

## 1. Throwaway in-package behavior probe

Proves what a function actually does when a doc comment, design note, or prep material says otherwise.

1. Place `zz_probe_<topic>_test.go` inside the package under test, **in-package** (package name matching the code, not `_test`) so unexported symbols are reachable.
2. Write one `TestProbe_<Claim>` that builds the minimal input distinguishing claimed from actual behavior, and `t.Logf` the observable. The log line is the evidence; an assertion may stay advisory.
3. Run narrow, not the whole suite: `go test ./<pkg> -run TestProbe_<Claim> -v -count=1`, prefixing `GOWORK=off` when a workspace file would redirect the module.
4. Delete it in the same call chain — run, then `rm -f <path>` — and confirm the working tree is clean before reporting.

**Why deletion is mandatory**: a probe that outlives its question becomes a false regression signal and a maintenance liability on a shard nobody re-ran. The probe answers one claim, then leaves.

Python equivalent: a `tmp_probe_<topic>.py` run with the project interpreter, same run-then-delete discipline.

## 2. Query-plan probe for declared capacity

Tests "supports N queued" / "handles M concurrent claims" without starting the service.

1. Read the exact SQL the hot path issues, and the DDL that creates the table.
2. Build a throwaway DB in the scratch dir: replicate the DDL, seed N rows in the state the claim describes (e.g. all rows in the queue state).
3. `EXPLAIN QUERY PLAN` the exact statement from step 1.

Reading the result:

- `SEARCH <table> USING INDEX ...` — the claim has an index behind it.
- `SCAN <table>` — every assertion about that path costs a full scan at the stated N.

Then grep the DDL for `CREATE INDEX` on the state column. The missing index is the root cause; the plan row is the proof. Both belong in the verdict.

## 3. Observability-surface probe

Verifies "we expose metric X / trace Y" claims.

- Grep the **exposition function** (the one that renders the output format) and every call site that increments or records the value.
- A metric absent from the exposition function is not exposed; a metric with no increment site is decoration.
- Keep the two modes apart: *computable* (a `PendingCount()`-style getter exists and is called internally) versus *exposed* (the value appears in rendered output). Deriving an observability claim from the existence of a getter is the common error.

**Why**: route tables and design docs list intentions; the exposition function lists reality.

## 4. Absence probe

- Prove a missing capability with a re-runnable negative search: `grep -rn '<symbol>' --include='*.go' .` returning zero hits, or a directory listing showing no such file.
- Put the exact command in the verdict so a later reviewer re-runs it instead of trusting prose.

## 5. Gate-enforcement probe (declared gate vs enforced gate)

Tests "our architecture/quality gate protects this repo" claims. A gate that exists but nothing invokes is a gate that only fires when someone remembers to type the command.

1. Locate the gate artifact: a test-based architecture guard, a pre-commit hook, a lint config.
2. Locate what invokes it: CI workflow directory, hook-install script plus the git config key that points at it (`git config --get core.hooksPath`), a documented make target.
3. If the only invocation path is "a human runs the test suite locally", the gate is advisory. That is a finding, not a pass — the gate's value is its enforcement, and the enforcement is what an outsider checks first (a CI badge is visible on the repo page; a local convention is not).

**Why**: the gap is invisible from inside the repo because the gate goes green whenever you do run it. Verify the invocation path, not the gate's own correctness.

---

## Probe discipline

- **One probe, one claim.** A probe that could explain two findings has isolated neither.
- **Report the raw observable** — the log line, the plan row, the zero-hit grep — not a paraphrase of it.
- **Zero cost means zero paid calls and zero production writes.** If a probe would need either, downgrade the claim to unbacked rather than running it.
- **Probe the code, not the documentation about the code.** When the two disagree, the probe decides and the documentation is the defect to report.
- **Never resolve a contradiction by re-reading the prose.** The pull to "read it once more and it'll make sense" is the failure mode these recipes exist to replace.
