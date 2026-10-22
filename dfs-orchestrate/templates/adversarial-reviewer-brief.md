# Adversarial Reviewer Brief (copy and fill)

Use for the independent-review step of maker-checker work. Fill every `{{...}}`; delete the parts that do not apply. The point of the brief is that the reviewer **tries to break the change**, not that it re-runs the builder's commands.

---

Repo: `{{repo}}`. Branch: `{{branch}}` (the current checkout — read from it, do NOT switch branches).

READ-ONLY ROLE: do NOT edit, commit, or push. For mutation checks, use a throwaway file and restore the tree to a clean `git status` before reporting.

HOST DISCIPLINE: use `{{interpreter}}`; run test commands strictly sequentially (concurrent runs share a data dir on this repro and fabricate results in both directions).

UNDER REVIEW: `{{commit_sha}}` — {{one_line_scope}}.

Return exactly one verdict line `PASS` or `REVISE: <reasons>`, then evidence.

## Required checks

**A. Tests, serial.** `{{exact_test_command}}` — report counts and exit code. If a known-flaky test is named in this brief ({{flake_name}}), re-run it alone on failure and say so explicitly rather than treating it as a regression.

**B. Mutation self-proof, redone independently.** {{mutations_to_redo}} — for each: apply it, show the failing assertion text verbatim, restore, prove `git status` is clean.

**C. Adversarial falsification.** {{allowance_or_suppression_to_attack}} — argue from the surrounding *code*, not from the prose reason. State plainly if any entry whitewashes a genuine defect.

**D. Counterexample construction.** Build a case that {{safety_mechanism}} does not catch but a reviewer should. Then judge: is that miss registered as a known limit, or an unacknowledged hole? Paste the mechanism's own stated limit.

**E. The riskiest construct.** {{file:line + why it smells}} — verify it EMPIRICALLY, do not reason from reading. Specifically: {{the exact experiment}}.

**F. Contract monotonicity.** For every changed response/interface: list the shape before vs after and confirm the change is additive only, or state exactly what was removed. Cross-check every consumer (`grep -rn '<field>' {{consumer_dir}}/`) so no caller silently breaks.

**G. Defect sweep.** Races, unhandled error paths, YAGNI. Red Cards (blockers) and Yellow Cards separately.

## Output shape
Verdict line; compact tables with trimmed raw receipts; `Red Cards` and `Yellow Cards` sections; an explicit `Residual unknowns` section (what could not be executed here, and what that means for confidence).

Do not paste whole files.
