# Module Splitting, Seam Safety Net & Quantitative Delta Schema (`references/split-and-seam-safety.md`)

Load this reference when splitting a large source or test file across modules, relocating functions, or formatting the final Quantitative Delta Report.

---

## 1. Seam-First Split Protocol (Modernize Probes Before Moving Code) (MUST)

When splitting a monolith or large file into multiple modules, **the order of operations is load-bearing**:

1. **Audit Test Coupling First**: Before moving a single line of production code, inspect all tests covering the target file. Identify tests that pin *internal mechanics* (reading source files as text with `indexOf`/`regex`, importing private helpers directly from the old file path, or asserting internal call counts).
2. **Modernize to Public Contract Probes First (Commit 1)**: Rewrite internal-coupled assertions into behavioral probes against the **public entrypoint / interface** while the production code is still in its original file. Verify the modernized probes pass **and** fail under a deliberate production mutation.
3. **Relocate Production Code Second (Commit 2)**: Move the code only after the contract probes are green and location-independent. Never rewrite tests and move production code in the same commit — if a test breaks, you lose the ability to tell whether the move broke behavior or the test edit broke the probe.

---

## 2. Post-Move Monkeypatch / Mock Reachability Guard (MUST)

Relocating a function from module `A` to module `B` while re-exporting it in `A` (`from B import helper`) silently breaks tests that patch `A.helper` when callers inside `B` now invoke `B.helper` directly:
- The test suite stays **100% green** (if the mock was guarding a failure branch or fallback), or hits the real dependency without interception.
- **Mandatory Rule**: After any cross-module move, grep all `patch(` / `monkeypatch.setattr(` targets for moved symbols. Update patch targets to the **module where the symbol is looked up at call time** (`B.helper`), and run **one mutation probe** (force `B.helper` to raise or return a sentinel) to prove the mock actually intercepts execution.

---

## 3. Test-Monolith Split Triple Conservation (MUST)

When splitting a large test file (`test_monolith.py`) into focused test modules by surface:
1. **Capture Pre-Split Baseline**: Record exact counts before editing:
   - Total collected test items (`pytest --collect-only -q` / `go test -list .`)
   - Exact set of test node IDs (normalized without file prefix)
   - Total `assert` / assertion helper occurrences across the split files
2. **Enforce Triple Conservation (`Delta == 0`)**: After splitting and deleting the original monolith, the union of the new test files MUST preserve **100% of test functions, 100% of parameterized test IDs, and 100% of assertions**. Zero tests may be dropped, skipped, or silently weakened during relocation.

---

## 4. Output Schema: Quantitative Delta Report

Every refactoring deliverable MUST conclude with this quantitative comparison:

```markdown
# [NOTE] Code Refactoring Summary: [Target Module]

### [NOTE] Complexity & Quantitative Delta
- **Max Indentation Depth**: `4 levels` -> `2 levels` (Guard Clauses)
- **Lines of Code (LOC)**: `340` -> `195` ([-] 42.6% reduction)
- **Deletions**: <what was deleted and why>
- **Stdlib Replacements**: <custom X -> stdlib Y>
- **Seam & Conservation Proof** (if splitting files): <test count N -> N, patch reachability verified>
- **Test Integrity**: [PASS] All N tests passing (Green-to-Green preserved)

### [NOTE] Key Transformation Diff
```diff
- if user != nil {
-     if user.IsActive {
-         return doWork(user)
-     }
- }
- return ErrUnauthorized
+ if user == nil || !user.IsActive {
+     return ErrUnauthorized
+ }
+ return doWork(user)
```
```
