---
name: dfs-gate
description: "Use when turning a recurring defect into a mechanical gate."
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - ci
    - gates
    - prevention
    - defensive-engineering
    - static-analysis
    related_skills:
    - dfs-maintain
    - dfs-verify
    - dfs-debug
    - dfs-bootstrap
    - dfs-incident
    - dfs-orchestrate
    mcp_tools: []
---



# DFS-GATE: Make the Rule Fail Loudly, or It Does Not Exist

> **Invariant (MUST)**: a rule that lives only in prose does not exist. A rule on the executed path — a CI job, a pre-commit / pre-push hook, a linter — does exist.

When the same *shape* of defect recurs, fixing the instance is not the fix. The durable fix is a gate that makes the shape fail loudly on every future contributor's path. This skill is how to build one that people keep instead of one they route around.

## The 4-Step Gate Design Procedure

`Step 1: Preconditions` -> `Step 2: Exit Contract` -> `Step 3: Three Proofs` -> `Step 4: Anti-Dilution`

### Step 1 — Establish Design Preconditions
1. **Name the failure shape in one sentence** and cite the concrete incidents sharing it.
2. **Choose enforcement layer deliberately**: pre-commit for fast author feedback; CI for authoritative unbypassable backstop.
3. **Mirror existing repo gate tools**: copy argv conventions and exit-code semantics from sibling gates.

### Step 2 — Exit-Code Contract (MUST)
- `0` = pass; `1` = violation found; `2` = gate could not run (environment unusable). Never collapse `1` and `2`.

### Step 3 — The Three Mandatory Proofs & Trust Rules
Every gate MUST provide the **Three Mandatory Proofs** recorded in its PR/commit receipt per [references/anti-dilution-and-three-proofs.md](references/anti-dilution-and-three-proofs.md) §1:
1. **Proof 1 (Liveness)**: Execution log showing non-zero scanned targets on intended trigger event.
2. **Proof 2 (Discriminative Mutation)**: Deliberate defect injection produces `exit 1` naming `file:line`; revert gives `exit 0`.
3. **Proof 3 (Cost Budget)**: Fast wall-clock duration (single-digit seconds for pre-commit).
- **Core Rules**: Match mechanism over symptom; never land red on day one (suppress legitimate legacy sites with true-to-code reasons); fail loud without `continue-on-error`.

### Step 4 — Adjudicating an Anti-Dilution Stop
If the initial scan returns high hit volume, stop and adjudicate per [references/anti-dilution-and-three-proofs.md](references/anti-dilution-and-three-proofs.md) §3:
1. Bifurcate hits: genuine incident vs legitimate site (ask: *does caller receive false success?*).
2. Justify narrowing by mechanism (never hit count), register limits, and re-run mutation proof.
3. Fix incidents (never bulk-suppress); report exact arithmetic: `original = narrowed N + fixed M + suppressed K`.
4. Refined criterion MUST NOT clear the motivating finding. Transitional suppressions require owner + backlog issue.

## Pitfalls & Anti-Patterns
- **Adversarial Gate Review**: Stress-test gate mechanisms against evasion strategies in [references/adversarial-gate-review.md](references/adversarial-gate-review.md).
- **Headless Browser Fake-Proof**: Never use `--virtual-time-budget` for visual/DOM gates; wait for explicit `dataset.ready` and assert non-zero pixel/bounding-box counts ([references/anti-dilution-and-three-proofs.md](references/anti-dilution-and-three-proofs.md) §2).
- **Fail Open Security Config**: Linters ignoring misspelled keys exit 0. Verify every key against schema and test intentional violations ([references/anti-dilution-and-three-proofs.md](references/anti-dilution-and-three-proofs.md) §4).
- **Regex Export/Route Bypass**: Line-anchored regexes (`^export`) miss aliases (`export { a as b }`) and indented exports. Query runtime authorities (AST / `__all__` / dynamic import) instead ([references/anti-dilution-and-three-proofs.md](references/anti-dilution-and-three-proofs.md) §5).
- **Silent Mutation Mis-match**: Unasserted mutation replacement on CRLF/drifted lines misses silently. Assert `count == 1` before checking gate failure ([references/anti-dilution-and-three-proofs.md](references/anti-dilution-and-three-proofs.md) §6).
- **Symptom Gating**: String matching without AST or mechanism is defeated by aliasing or code comments.
- **Prose Substitution**: Text documentation in 01-Rules is ignored without automated execution. Convert recurring defects into mechanical gates.

## Checkable Completion Criterion
- Gate committed to `.githooks/` or CI configuration.
- Three proofs verified (liveness log, mutation quote, runtime budget).
- **Meta-test verified (MUST)**: the gate script is shipped together with at least one negative
  fixture it rejects, with the rejection line quoted verbatim. A gate whose only evidence is
  "it returns 0 on the good input" is unverified — it cannot distinguish "correct" from
  "checked nothing". See `dfs-gate/references/` for the fixture pattern and
  `dfs-tdd/references/dead-test-and-quantity-guards.md` §4.
