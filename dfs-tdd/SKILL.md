---
name: dfs-tdd
description: Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards. Use when implementing a feature test-first, or when a green test suite is suspect.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tdd, red-green-refactor, mutation-testing, fake-green, testing]
    related_skills: [dfs-plan, dfs-exec, dfs-refactor, dfs-debug]
    mcp_tools: [get_code_template]
---

# DFS-TDD: Contract-Driven Development & Mutation Defense

Execute Test-Driven Development enforcing **The Iron Law**: Zero production code without a failing test, zero success claims without mutation verification, and zero tolerance for Reward Hacking.

## 🚨 The Iron Law of TDD (RFC 2119 MUST)
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
  ★ [Step 3: Mutation Verification (Anti-Fake Green)] ★
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

### Step 3: Mutation Verification (Anti-Fake Green Defense) (MUST)
- **The Mutation Check**: If the test unexpectedly passes on first run, intentionally mutate the target function to return a zero-value or throw an error.
- Verify the test turns RED. If it stays GREEN, the test is not asserting real behavior (Fake Green) and must be rewritten.
- **Checkable Completion Criterion**: Mutation produces a verified RED failure, and code is reverted to its original clean state.

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

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard (DPO Bad Case) | Defensive Guard (MUST) |
|---|---|---|
| *"The test failed, so let me delete or weaken the assert."* | **Malicious Reward Hacking**: masking bugs to simulate 100% pass rates. | NEVER delete or weaken a failing test. Fix production code until the contract passes. |
| *"I'll add `@pytest.mark.skip` or `t.Skip()` to make the suite green."* | **Test Suite Rot**: real regressions pass silently in CI/CD. | Zero tolerance for newly skipped tests. A skipped test is considered a failing test. |
| *"I'll write the implementation first, then write a test to cover it."* | **Fake Green (Tautological Test)**: tests tailored to pass implementation bugs. | Step 2 failure receipt is mandatory before creating production implementation files. |
| *"The implementation looks correct, so I can skip running the test."* | **Premature Completion**: declaring victory without empirical evidence. | Terminal execution receipt with raw exit code 0 is mandatory for completion claims. |
