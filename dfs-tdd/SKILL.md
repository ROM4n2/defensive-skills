---
name: dfs-tdd
description: Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards.
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tdd, red-green-refactor, mutation-testing, fake-green, testing]
    related_skills: [dfs-plan, dfs-exec, dfs-refactor, dfs-debug]
    mcp_tools: [get_code_template]
---

# DFS-TDD: Contract-Driven Development & Mutation Defense

Execute Test-Driven Development enforcing **The Iron Law**: Zero production code without a failing test, and zero success claims without mutation verification.

## 🚨 The Iron Law of TDD (RFC 2119 MUST)
> **NO production code shall be written before an automated test is written AND verified to fail (RED) for the expected reason.**
> Tests that pass before writing implementation code are invalid (Fake Green).

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

### Step 2: Run Test & Confirm Failure
- Run test command in terminal.
- **Verification Rule**: The failure reason MUST match the missing functionality, NOT a compilation typo or missing import.

### Step 3: Mutation Verification (Anti-Fake Green Defense) (MUST)
- **The Mutation Check**: If the test unexpectedly passes on first run, intentionally mutate the target function to return a zero-value/throw error.
- Verify the test turns RED. If it stays GREEN, the test is not asserting real behavior (Fake Green) and must be rewritten.

### Step 4: Implement Minimal Production Code (GREEN)
- Write the minimal code required to pass the test.
- No premature abstractions or unrequested features (YAGNI).

### Step 5: Refactor with Guard Clauses (REFACTOR)
- Flatten nested `if-else` blocks into top-level Guard Clauses (max 2 levels indentation).
- Ensure all tests remain 100% GREEN throughout refactoring.
- Commit atomically: `git commit -m "feat(<scope>): implement <feature> with TDD"`.
