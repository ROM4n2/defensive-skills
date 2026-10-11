# Implementation Plan Schema

Every generated `implementation_plan.md` MUST adhere strictly to the following structure:

```markdown
# [Feature Name] Implementation Plan

> **Goal**: [One sentence describing what this builds]
> **Tech Stack**: [Go 1.24+ / C++20 / Python 3.11 / C11]
> **Spec Reference**: [Link to Design Spec or ADR]
> **Global Constraints**: [Version floors, no-leak regex, UTF-8 stdout, guard clauses]

---

## 🏛️ Decisions So Far
<!-- Closed decisions and resolved architectural questions; low-res index -->
- [ADR-0001](link): Adopted Go 1.24+ worker pool over unbounded goroutines.

---

## 🎯 Active Frontier (Unblocked Tasks)

### Task 1: [Component Name] [Tier: 1-Light | 2-Standard | 3-Critical] [Mode: AFK | HITL] [Role: ...]
*(Tier: 1-Light = Solo Fast-Path + physical receipt, no Reviewer subagent | 2-Standard = Full TDD Builder + Reviewer Maker-Checker | 3-Critical = Swarm / HITL gate)*
*(Mode: AFK = Fully autonomous execution | Mode: HITL = Human-in-the-loop approval gate)*

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:120-150`
- Test: `tests/test_exact_feature.py`

**Interfaces:**
- Consumes: `func ExistingHelper(ctx context.Context) (Data, error)`
- Produces: `func NewService(cfg Config) (*Service, error)`

**Injected Instincts (Compile-Time Rule Injection):**
- [ ] `[Instinct: Concurrency]`: Pass `context.Context` down call chains; verify zero Goroutine leaks with `-race`.
- [ ] `[Instinct: Zero-Lock DDL]`: (If touching SQL) Follow Expand/Contract ladder; run `scripts/ddl_lint.py`.
- [ ] `[Instinct: Supply-Chain]`: (If touching manifests) Run package vulnerability audit.

**Subagent Prompt Scaffold (for /dfs-exec):**
> "Implement Task 1: {task_title}.
> Mode: AFK | Role: TDD Builder
> Goal: {task_goal}.
> Target Files: Create `{path_1}`, Test `{test_path}`.
> Injected Instincts: {injected_instincts}
> TDD Steps:
> 1. Write failing test `{test_path}` (RED).
> 2. Run `{test_cmd}` and verify failure.
> 3. Implement minimal code in `{path_1}` (GREEN).
> 4. Flatten with Guard Clauses (max 2 levels).
> Return: Summary with MANDATORY Physical Execution Receipt (exit code + stdout snippet)."

**Step Breakdown:**
- [ ] **Step 1: Write the failing test (RED)**
- [ ] **Step 2: Run test and verify it fails with expected message**
- [ ] **Step 3: Implement minimal production code (GREEN)**
- [ ] **Step 4: Run tests and verify all green**
- [ ] **Step 5: Refactor & Flatten with guard clauses (REFACTOR)**
- [ ] **Step 6: Physical Evidence Gate**: Capture raw terminal execution receipt (Command + Exit code: 0 + test pass count + git diff)
- [ ] **Step 7: Git atomic commit**

---

## 🌫️ Fog of War (Not Yet Specified)
<!-- Tasks that depend on open unknowns or upstream outcomes; FORBIDDEN from premature speculative breakdown -->
- **[Unknown 1]**: Caching tier strategy (Pending benchmarking results from Task 2).
- **[Unknown 2]**: Distributed coordinator topology (Pending ADR-0002 decision).

---

## 🚫 Out of Scope
<!-- Explicitly ruled out boundaries for this effort; never graduates into tasks -->
- Multi-region cross-datacenter consensus replication.
- Web UI dashboard (pure CLI backend engine scope).
```

## Schema Invariants & Rules
1. **Discrete Task Granularity**: Each task represents one bite-sized action executable within 2~5 minutes.
2. **Adaptive Tiering Tagging (MUST)**: Every task MUST be tagged with its defense tier:
   - `[Tier: 1-Light]`: Pure docs, YAML metadata, constants, config tweaks, running existing scripts. Uses Solo Fast-Path (single agent or inline execution with physical binary verification receipt like grep/exit 0, skips Reviewer subagent).
   - `[Tier: 2-Standard]`: Standard feature dev, bugfix, logic refactoring requiring tests. Uses full TDD Red-Green-Refactor + Maker-Checker isolated Reviewer subagent.
   - `[Tier: 3-Critical]`: Schema migrations, multi-repo writes, core security/gate changes. Mandatory HITL checkpoint + multi-perspective review.
3. **Batching Syntax for Tier 1**: Consecutive Tier 1 tasks MAY be grouped into a single batch block (e.g. `### Batch 1 [Tier: 1-Light]: Tasks 1-5 [Mode: AFK]`) to execute continuously and commit atomically in one git commit, avoiding fragmented subagent cascades.
4. **Mode Tagging (MUST)**: Every task MUST be tagged either `[Mode: AFK]` (autonomous) or `[Mode: HITL]` (human checkpoint).
5. **Fog of War Invariant**: Never speculative-plan tasks in detail if prerequisite architecture is unknown. Place them in `## Fog of War` until upstream Frontier tasks graduate them.
6. **Physical Evidence Gate**: No task is complete without an authentic terminal receipt containing raw exit code, pass counts, and diff stats. Even Tier 1 tasks require physical binary verification (grep count / exit 0).
