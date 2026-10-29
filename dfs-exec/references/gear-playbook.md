# dfs-exec — extended playbook (tier 3)

Loaded on demand by `dfs-exec/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

## Gear 1: Solo-Light (极速自证档)
- **Applicable Tasks**: `[Tier: 1-Light]` — Documentation, YAML frontmatter, constants, config updates, running existing build/export scripts.
- **Workflow**:
  1. **Execution**: Orchestrator executes directly in-thread (for scripts/docs) or dispatches a single lightweight subagent.
  2. **Physical Evidence Gate (MANDATORY)**: Must capture unambiguous binary evidence (`exit code 0`, `grep` assertion count, lint clean). Qualitative claims ("I verified it") are strictly rejected.
  3. **Skip Reviewer Subagent**: No independent Reviewer subagent is dispatched. Saves token cold-start overhead and eliminates 429 rate limits.
  4. **Batch Commit Support**: Consecutive Tier 1 tasks in a `### Batch N [Tier: 1-Light]` group accumulate diffs, run overall repository quality gate, and commit as a single batch commit (`chore(<scope>): complete Batch N (Tasks X-Y)`).

---

## Gear 2: Maker-Checker (标准工业档)
- **Applicable Tasks**: `[Tier: 2-Standard]` — Production logic implementation, algorithmic changes, bugfixes with unit tests, refactoring.
- **Workflow (The Strict 3-Stage Loop)**:
  1. **Step 1: Dispatch Implementer Subagent (TDD Builder)**
     - Dispatches fresh context-isolated subagent with `templates/tdd-builder-prompt.md`.
     - **Brief carries the delta, never the invariants.** Repository invariants (privacy red lines, format/lint false positives, forbidden commit paths, timeout rules) live in the repo's anchor file — point the child at it and restate only what is specific to this task. Repeating the full invariant set in every brief is pure repeated token cost; the child reads the anchor once and the brief stays small.
     - Executes strict RED-GREEN-REFACTOR TDD cycle.
  2. **Step 2: Dispatch Reviewer Subagent (Code Reviewer)**
     - Dispatches independent read-only reviewer subagent with `templates/reviewer-prompt.md`.
     - Reviewer checks diff against RFC 2119 standards and returns binary verdict: `PASS` or `REVISE`.
  3. **Step 3: Atomic Git Commit & State Ledger Update**
     - `git commit -m "feat(<scope>): complete Task N"`.
     - `python scripts/vault_exec_state.py complete-task --task-id <id> --reviewer PASS`.

---

## Gear 3: Critical-Swarm (顶格会诊档)
- **Applicable Tasks**: `[Tier: 3-Critical]` — Multi-repository batch writes, schema migrations, core gate logic modifications, security/credential boundary shifts.
- **Workflow**:
  1. **HITL Authorization Gate**: Present change impact, target repository list, and irreversible risks to user. Await explicit user confirmation before touching files.
  2. **Dual-Agent Adversarial Execution**: Implementer subagent + Reviewer subagent with mandatory mutation testing probe.
  3. **Verification & Ledger Sign-off**: Multi-repo atomic commits, state verification across all boundaries.

---

## [+] Acceptance Gates (MANDATORY — derived from field failures, not theory)

An exit code 0 proves "nothing crashed", never "the result is right". Four gates exist because
each one caught a real defect that a green suite and a clean exit had already waved through.

1. **Known Defect Classes pre-dispatch check (MUST)** — before dispatching, run the four
   questions from `/dfs-grill` Stage 2.5 against the task: error-classification width,
   cancelled-context teardown, progress semantics (per-run vs absolute), and duplicate
   implementations of one rule. Four consecutive milestones each shipped exactly one real
   defect from these four classes; the questions cost four lines.
2. **Real-data regression gate (Tier 3 MUST)** — for anything touching a database, a generated
   artifact, or a state machine, run the recipes in
   `dfs/references/acceptance-recipes.md`: before/after snapshot + output hash (recipe A),
   kill/resume drill (recipe B), visual self-report for rendered output (recipe C). A Tier 3
   task that never touched real data is not accepted.
3. **Human-artifact safety (MUST)** — when a task produces an artifact a human edits and a
   script reads back (labels, sign-off lists, config the human owns), recipe D applies:
   round-trip self-check at generation, dry-run before any rewrite, append-only by default.
   Silent loss of human input is the worst defect class in this workflow: it produces a
   *plausible wrong conclusion* rather than a visible failure.
4. **Orchestrator re-does one probe (Tier 3 MUST)** — the child's mutation self-report is a
   self-report. Re-execute at least one mutation physically in the parent tree and quote the
   failing assertion verbatim. This is the step that caught a child whose described mutation
   did not match what its code actually did.

---
