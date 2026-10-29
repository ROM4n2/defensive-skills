# The Three Gate Proofs, Anti-Dilution Adjudication & Headless Traps (`references/anti-dilution-and-three-proofs.md`)

Load this reference when verifying a new gate (Step 3), adjudicating an initial scan that tripped the anti-dilution stop (Step 4), or building visual/DOM/CI gates.

---

## 1. The Three Mandatory Proofs of a Gate (MUST)

A gate that exits 0 on a clean tree has proven nothing. Every mechanical gate MUST ship with three physical proofs recorded in its PR/commit receipt:

1. **Proof 1 — Liveness Proof (It Actually Ran on the Target Surface)**:
   - Show the execution log proving the gate ran on the intended trigger event and scanned a non-zero target set (e.g. `Scanned 42 files`). A CI job whose path filter never matches, or a scanner whose glob matched `0 files` and exited `0`, is a dead gate.
2. **Proof 2 — Discriminative Proof (Mutation Self-Proof)**:
   - Inject one realistic instance of the defect shape into a throwaway fixture or target file, run the gate, and record the `exit 1` output naming `file:line`. Revert and record `exit 0`.
3. **Proof 3 — Cost Proof (Bounded Execution Budget)**:
   - Measure and record wall-clock duration (`time <gate-cmd>`). Pre-commit gates MUST finish in single-digit seconds (avoiding full-repo subprocess spawns per file); heavy full-matrix scans belong in pre-push or CI. A gate that is too slow gets bypassed with `--no-verify`.

---

## 2. Headless Browser & Async Rendering Fake-Proof Trap (MUST)

Never use `chromium --headless --screenshot --virtual-time-budget=N` as a visual or rendering gate:
- `--virtual-time-budget` fast-forwards timers synthetically before async fonts, WebGL/Canvas charts, or layout passes actually paint, producing **all-white screenshots** (false red) or capturing stale pre-hydration DOM (false green).
- **Mandatory Guard**: Visual and DOM gates MUST drive the page via CDP/Playwright over real wall-clock readiness: wait for an explicit application readiness attribute (`document.body.dataset.ready === "1"`) AND assert non-zero rendered pixel/bounding-box counts (`getImageData` non-transparent pixels `> 0` or `getBoundingClientRect().width > 0`) before capturing evidence.

---

## 3. Step 4 Full Playbook — Adjudicating an Anti-Dilution Stop

When the first scan returns a large hit list, adjudicate in this exact order — never by bulk-suppressing first:

1. **Bifurcate every hit into genuine incident vs legitimate site**: Ask *if this fails, does the caller still receive a success-shaped result?* A swallowed best-effort cleanup is legitimate; a swallowed failure whose absence changes what the caller believes happened is an incident.
2. **Justify any narrowing by mechanism, and register the limit it introduces**: Name the structural difference between kept and dropped forms (never the hit count), record the excluded defect class in the gate's own header comment, and **re-run the mutation self-proof** afterwards.
3. **Fix the incidents; do not suppress them**: Make the failure observable so the body no longer matches the criterion. A fix that makes an existing exemption obsolete MUST delete that exemption in the same commit.
4. **A genuine incident that falls out of scope due to narrowing MUST still be fixed**: Narrowing a criterion is not licence to ignore a known bug.
5. **Report the exact arithmetic**: `original = narrowed-away N + fixed M + suppressed K`, with all three terms enumerated.
6. **A cluster sharing one legitimate mechanism indicts the CRITERION, not the codebase**: Teach the gate the repo's convention (e.g. a loading order or call wrapper) rather than adding per-site suppressions.
7. **The refined criterion MUST NOT clear the motivating finding**: Lock a unit sample built from the original incident's exact shape that MUST still fail. For export-surface (`__all__` / barrel) rules, protect only symbols the module defines as its own member, never bare foreign re-exports.
8. **Transitional suppressions for unowned files require an owner + plan entry**: Label the suppression reason explicitly as a genuine defect and register it in the owning workstream's backlog.

---

## 4. Extended Gate Pitfalls

- **Security-gate config failing OPEN**: Linter/scanner YAML loaders routinely ignore misspelled keys and run 0 rules (`exit 0`). Verify every config key against schema/source and test with one intentional violation.
- **String-matching a symptom instead of AST/mechanism**: A gate matching a literal variable name or comment (`"ev.max_turns"`) is satisfied by a code comment or defeated by aliasing. Parse the AST or match the structural call site, and strip comments before matching.
