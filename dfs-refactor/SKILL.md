---
name: dfs-refactor
description: Execute senior-level refactoring with guard-clause flattening. Use when the user asks to clean up, simplify, or restructure existing code.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [refactoring, guard-clauses, complexity-reduction, code-quality, yagni]
    related_skills: [dfs-tdd, dfs-review, dfs-perf]
---

# DFS-REFACTOR: Senior Complexity Reduction & Flattening

Execute senior-level code refactoring focusing on complexity reduction, Guard Clause flattening, stdlib consolidation, and dead code elimination while maintaining 100% Green test coverage.

## 🚨 The Iron Rule (HARD GATE)
> **DO NOT touch any production code until the full test suite is verified GREEN.**
> Refactoring = changing internal structure without changing external behavior. If you cannot run the test suite, you are not refactoring — you are guessing.

---

## The 5-Step Refactoring Lifecycle

```
  [Step 0: Establish Green Baseline]
                     │
                     ▼
  [Step 1: The Deletion Test — remove before reshaping]
                     │
                     ▼
  [Step 2: Flatten & Consolidate (Guard Clauses + Stdlib)]
                     │
                     ▼
  [Step 3: Deepen Modules (minimal interface, high-cohesion internals)]
                     │
                     ▼
  [Step 4: Verify Green + Atomic Commit]
```

### Step 0: Establish Green Baseline (MUST)
Run the full test suite **before any edit**. Record the passing count. This is your invariant — every subsequent step must preserve it. If tests are already failing, stop and call `/dfs-debug` first.

### Step 1: The Deletion Test — Remove Before Reshaping
Before refactoring code into a "better shape", ask: **can I delete it entirely?**

- **Single-implementation interface**: an interface/ABC/protocol with exactly one concrete type → delete the interface, inline the implementation.
- **Speculative wrapper**: a class/function that adds no logic, just forwards arguments → delete it, call the underlying directly.
- **Dead code**: unreachable branches, unused imports, commented-out blocks → delete without ceremony.
- **Duplicate helper**: same logic in two places → keep the better one, delete the other.

The best refactoring is deletion. Every line you delete is a line that can never have a bug.

### Step 2: Flatten & Consolidate
Apply these in order:

1. **Guard Clause Flattening**: Maximum 2 levels of indentation. Return early on preconditions, validation errors, and nil/null checks. The happy path reads straight down the left margin.
2. **The Ladder of Reuse (all levels)**:
   - Level 0 (YAGNI): Does this abstraction serve a real caller today, or an imagined future one? If imagined → delete (Step 1).
   - Level 1 (Stdlib): Replace custom wheels with standard library built-ins (`functools.lru_cache`, `sync.OnceValue`, `itertools`, `context`, `http`).
   - Level 2 (Existing deps): Can an already-imported library do this? If yes → delete the custom code.
   - Level 3 (Minimal effective implementation): If you must write it, write the smallest version that passes the tests.
3. **Extract cohesive helpers**: Break functions > 40 lines into focused pure helpers. Each helper does one thing and returns one thing.

### Step 3: Deepen Modules
A **shallow module** has a complex interface but weak implementation (many public methods, thin bodies). A **deep module** has a minimal interface and high-cohesion internals.

- Reduce the public surface: can callers reach the same outcome with fewer exposed functions/methods?
- Move orchestration logic inward: if the caller must call A then B then C in order, that sequence belongs inside the module.
- **Done when** you can name, for each public function, the misuse a caller could still make — and a type error or a test catches every one of them. An uncaught misuse means the interface is still too wide.

### Step 4: Verify Green + Atomic Commit (MUST)
1. Run the full test suite. **Exact same passing count as Step 0.** If any test broke, revert the last atomic edit and re-examine.
2. Commit per refactoring type, not per file:
   ```
   refactor(<scope>): flatten guard clauses in <module>
   refactor(<scope>): delete single-impl interface <Name>
   refactor(<scope>): replace custom <X> with stdlib <Y>
   ```
3. **营地法则 (Campsite Rule)**: Leave the code cleaner than you found it. If you touched a function and noticed unrelated mess, note it — but do not fix it in this commit. Separate commits for separate concerns.

---

## Output Schema: Quantitative Delta Report

Every refactoring deliverable MUST provide a quantitative comparison:

```markdown
# 🧹 Code Refactoring Summary: [Target Module]

### 📊 Complexity & Quantitative Delta
- **Max Indentation Depth**: `4 levels` ➔ `2 levels` (Guard Clauses)
- **Lines of Code (LOC)**: `340` ➔ `195` (🔻 42.6% reduction)
- **Deletions**: <what was deleted and why>
- **Stdlib Replacements**: <custom X → stdlib Y>
- **Test Integrity**: ✅ All 48 tests passing (Green-to-Green preserved)

### 🔍 Key Transformation Diff
```diff
- if user != nil {
-     if user.IsActive {
-         if user.HasPermission("admin") {
-             return doAdminWork(user)
-         }
-     }
- }
- return ErrUnauthorized
+
+ if user == nil || !user.IsActive || !user.HasPermission("admin") {
+     return ErrUnauthorized
+ }
+ return doAdminWork(user)
```
```
