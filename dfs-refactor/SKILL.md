---
name: dfs-refactor
description: Execute senior-level refactoring with guard-clause flattening. Use when the user asks to clean up, simplify, or restructure existing code.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - refactoring
    - guard-clauses
    - complexity-reduction
    - code-quality
    - yagni
    related_skills:
    - dfs-tdd
    - dfs-review
    - dfs-perf
---


# DFS-REFACTOR: Senior Complexity Reduction & Flattening

Execute senior-level code refactoring focusing on complexity reduction, Guard Clause flattening, stdlib consolidation, and dead code elimination while maintaining 100% Green test coverage.

## The Behavior Preservation Invariant (RFC 2119 MUST)
> DO NOT touch production code until the full test suite is verified GREEN. Stop immediately if test count changes.

---

## The 5-Step Refactoring Lifecycle

`Step 0: Baseline` -> `Step 1: Deletion` -> `Step 2: Flatten` -> `Step 3: Deepen` -> `Step 4: Verify`

### Step 0: Establish Green Baseline (MUST)
1. Run full test suite before any edit. Record exact passing count $N$.
2. **Seam-First Split Precheck (when splitting files/modules)**: If tests pin internal layout, modernize to public contract probes in a separate commit *before* moving code — load [references/split-and-seam-safety.md](references/split-and-seam-safety.md) §1.
3. Preserved invariant: if tests fail/missing, stop and invoke `/dfs-debug` or `/dfs-tdd`. Done when 100% green with count $N$.

### Step 1: The Deletion Test — Remove Before Reshaping
Before reshaping, ask: **can I delete it entirely?**
- Delete single-implementation interfaces, speculative forwarding wrappers, unreachable dead code, and duplicate helpers.
- The best refactoring is deletion. Done when unneeded code removed and test suite re-run with exact $N$ passes.

### Step 2: Flatten & Consolidate
Apply in order:
1. **Guard Clause Flattening**: Max 2 levels of indentation. Return early on preconditions and null checks. Happy path reads straight down.
2. **Ladder of Reuse**: Level 0 (YAGNI delete) -> Level 1 (Stdlib built-ins) -> Level 2 (Existing deps) -> Level 3 (Minimal implementation).
3. **Extract Cohesive Helpers**: Break functions > 40 lines into focused single-purpose pure helpers. Done when max depth <= 2 and $N$ passes.

### Step 3: Deepen Modules
A deep module has a minimal public interface and high-cohesion internals:
- Reduce public surface; move caller sequencing and orchestration logic inward.
- **Cohesive File Splitting & Test Triple Conservation**: When splitting files, preserve package boundaries and enforce 100% conservation of test count, test IDs, and assertions per [references/split-and-seam-safety.md](references/split-and-seam-safety.md) §3.
- Done when public surface is minimized, misuse is caught by types/tests, and all $N$ tests pass.

### Step 4: Verify Green + Atomic Commit (MUST)
1. Re-verify full test suite passes with exact same count $N$. Revert atomic edit if broken.
2. **Post-Move Mock Reachability (MUST)**: If symbols moved across modules, verify `patch` targets point to call-time lookup module and prove interception with 1 mutation ([references/split-and-seam-safety.md](references/split-and-seam-safety.md) §2).
3. Commit atomically per refactoring concern (`flatten`, `delete`, `stdlib`, `deepen`). Leave campsite cleaner than found.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"There are no tests, but I'll refactor carefully using clean patterns."* | **Undetected Regressions**: restructuring untested code introduces subtle behavioral breakages. | MUST verify a passing test baseline before refactoring. If missing, invoke `/dfs-tdd` first. |
| *"While cleaning up this function, I also added a helpful new option."* | **Conflated Diff Blast Radius**: mixing refactoring with behavior changes ruins git bisect and auditability. | Refactoring commits MUST contain ZERO behavioral or feature additions. |
| *"A test failed after flattening, so I updated the assertion to match."* | **Reward Hacking & Test Corruption**: silently changing expected outcomes masks genuine regressions. | NEVER modify existing test assertions during refactoring unless signature changes were pre-approved. |
| *"I'll batch all cleanups across 10 files into one final commit."* | **Unreviewable Mega-Diffs**: inability to isolate which transformation caused a failure if rolled back. | Commit atomically per refactoring concern (delete, flatten, stdlib, deepen). |

---

## Output Schema: Quantitative Delta Report

Every refactoring deliverable MUST conclude with the Quantitative Delta Report (complexity delta, LOC reduction, deletions, and Green-to-Green preservation) per [references/split-and-seam-safety.md](references/split-and-seam-safety.md) §4.
