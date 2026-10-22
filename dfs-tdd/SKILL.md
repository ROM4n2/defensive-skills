---
name: dfs-tdd
description: Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards. Use when implementing a feature test-first, or when a green test suite is suspect.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags: [tdd, red-green-refactor, mutation-testing, fake-green, testing]
    related_skills: [dfs-plan, dfs-exec, dfs-refactor, dfs-debug]
    mcp_tools: [get_code_template]
---
# DFS-TDD: Contract-Driven Development & Mutation Defense

Execute Test-Driven Development enforcing **The Iron Law**: Zero production code without a failing test, zero success claims without mutation verification, and zero tolerance for Reward Hacking.

## [MUST] The Iron Law of TDD (RFC 2119 MUST)
> **NO production code shall be written before an automated test is written AND verified to fail (RED) for the expected reason.**
> Tests that pass before writing implementation code are invalid (Fake Green).
> Deleting failing tests, weakening assertions, or skipping tests to simulate a green result is strictly forbidden (Reward Hacking).

---

## The 5-Step Industrial TDD Lifecycle

```
       [Step 1: Write Unit Test (RED)]
                     │
                     ▼
       [Step 2: Verify Test Fails with Expected Error]
                     │
                     ▼
  [NOTE] [Step 3: Mutation Verification (Anti-Fake Green)] [NOTE]
    (Mutate logic -> Assert test fails -> Revert)
                     │
                     ▼
       [Step 4: Write Minimal Production Code (GREEN)]
                     │
                     ▼
       [Step 5: Refactor & Flatten with Guard Clauses]
```

### Step 1: Write the Failing Test (RED)
- Write concise, behavior-driven unit tests asserting one specific contract.
- Use Defensive Skills pure test templates (`get_code_template("test-suite", lang="...")`).
- **Checkable Completion Criterion**: The test file exists and asserts the unbuilt behavior.

### Step 2: Run Test & Confirm Failure
- Run the test command in the terminal.
- **Verification Rule**: The failure reason MUST match the missing functionality, NOT a compilation typo or missing import.
- **Checkable Completion Criterion**: Terminal output records non-zero exit code (`exit != 0`) with the expected assertion failure message.

### Step 3: Mutation Verification (Anti-Fake Green Defense) (Targeted MUST)
- **Applicability Scope (When to Mutate)**:
  1. **Mandatory Case**: The test unexpectedly passes on first run (Step 2 passed without code — obvious Fake Green / Tautological Test).
  2. **High-Risk Invariant Case**: Cryptographic logic, concurrent lock handoffs, and security gatekeeper rules.
  3. **The Four Mandatory Classes (field-derived — mutate these even when the logic looks trivial)**:
     - **Corruption/duplication guards** — anything whose job is to stop a value being written twice (idempotency keys, accumulate-vs-replace, dedupe predicates). A guard that silently stops guarding doubles data.
     - **State transitions** — every legal/illegal edge of a state machine. Remove the `WHERE status IN (...)` guard and confirm the illegal-transition test goes red.
     - **Error classification** — any branch that maps an exception to a retryable vs permanent outcome. Break the mapping and confirm the test that pins it fails.
     - **Human-input parsing boundaries** — any regex/parser that reads back an artifact a human edited. Loosen the pattern by one character and confirm the "malformed row is rejected" test fails; this is the class that silently ate three human judgements and produced a plausible wrong conclusion.
  4. **Exempt Case**: Standard linear functions, simple DTO mappers, or obvious bugfixes that already failed Step 2 with the exact expected error message. Do not perform ritualistic mutation for trivial logic.
- **The Mutation Check**: Intentionally mutate the target function to return a zero-value or throw an error.
- Verify the test turns RED. If it stays GREEN, the test is not asserting real behavior (Fake Green) and must be rewritten.
- **Evidence Rule (MUST)**: quote the failing assertion **verbatim** in the report — `file:line: expected X, got Y`. "The test went red" is a self-report; the assertion text is evidence.
- **Tier 3 Addition (MUST)**: the orchestrator physically re-executes at least one mutation in the parent tree. A child's description of its own mutation has been observed to disagree with what its code actually did.
- **Checkable Completion Criterion**: Mutation produces a verified RED failure with a quoted assertion, and code is reverted to its original clean state.

### Step 4: Implement Minimal Production Code (GREEN)
- Write the minimal code required to pass the test.
- Reject premature abstractions or unrequested features (YAGNI).
- **Checkable Completion Criterion**: Terminal output records exit code 0 (`exit 0`), 100% test pass count, and zero skipped tests.

### Step 5: Refactor with Guard Clauses (REFACTOR)
- Flatten nested `if-else` blocks into top-level Guard Clauses (max 2 levels indentation).
- Ensure all tests remain 100% GREEN throughout refactoring.
- Commit atomically: `git commit -m "feat(<scope>): implement <feature> with TDD"`.
- **Checkable Completion Criterion**: All tests pass (`exit 0`), code conforms to guard clause standards, and an atomic git commit hash is produced.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard (DPO Bad Case) | Defensive Guard (MUST) |
|---|---|---|
| *"The test failed, so let me delete or weaken the assert."* | **Malicious Reward Hacking**: masking bugs to simulate 100% pass rates. | NEVER delete or weaken a failing test. Fix production code until the contract passes. |
| *"I'll add `@pytest.mark.skip` or `t.Skip()` to make the suite green."* | **Test Suite Rot**: real regressions pass silently in CI/CD. | Zero tolerance for newly skipped tests. A skipped test is considered a failing test. |
| *"I'll write the implementation first, then write a test to cover it."* | **Fake Green (Tautological Test)**: tests tailored to pass implementation bugs. | Step 2 failure receipt is mandatory before creating production implementation files. |
| *"The implementation looks correct, so I can skip running the test."* | **Premature Completion**: declaring victory without empirical evidence. | Terminal execution receipt with raw exit code 0 is mandatory for completion claims. |
