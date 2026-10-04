---
name: dfs-debug
description: Execute 4-step systematic root-cause debugging with a reproduction. Use when the user reports a bug, a failing test, or says something is broken.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, root-cause, reproduction, systematic-debugging, troubleshooting]
    related_skills: [dfs-tdd, dfs-save, systematic-debugging]
    mcp_tools: [search_vault, save_inbox_draft]
---

# DFS-DEBUG: 4-Step Systematic Root-Cause Debugging

Resolve bugs, race conditions, memory leaks, and runtime panics with zero guesswork using the 4-step root-cause protocol.

## 🚨 The Reproduction-First Invariant (RFC 2119 MUST)
> **NO production code changes shall be attempted until Step 1 (Evidence & Minimal Reproduction) produces a verified red failure.**
> Reproduce the exact failure mode deterministically in an isolated test or repro script to eliminate guesswork before editing source files.

---

## The 4-Step Root-Cause Protocol

```
  [Step 1: Evidence Capture & Minimal Repro (scratch/repro.*)]
                               │
                               ▼
  [Step 2: Vault Pitfall & Intent Mapping (search_vault)]
                               │
                               ▼
  [Step 3: Root-Cause Remediation & Surgical Fix]
                               │
                               ▼
  [Step 4: Regression Lock & Self-Healing Ingestion (/dfs-save)]
```

### Step 1: Evidence & Minimal Reproduction (MUST)
1. **Exact Error Log**: Capture full stack trace, error message, and environment context.
2. **Minimal Repro Script**: Create a standalone reproduction script in `scratch/repro.<lang>` or write a failing test. Load templates from `templates/repro-scaffold.md` via `read_file(path='templates/repro-scaffold.md')` to scaffold reproductions.
3. **Execute & Confirm Red Repro**: Run repro script in terminal and verify it fails with the exact reported error (non-zero exit code or specific exception).
4. **Checkable Completion Criterion**:
   - Repro script or failing test executed in terminal; physical output exhibits the exact reported error and non-zero exit code.

### Step 2: Vault Pitfall & Synonym Search
1. **Query Prior Art**: Query Defensive Skills knowledge base for known gotchas and workarounds:
   - Call `search_vault(query="<error_message_or_keyword>")`
   - Inspect `01-Rules/ERROR-HANDLING-PATTERNS.md` and `01-Rules/ENVIRONMENT-LOCAL.md`.
2. **Checkable Completion Criterion**:
   - `search_vault` executed; relevant patterns retrieved or confirmed as a novel incident.

### Step 3: Root-Cause Remediation & Surgical Fix
1. **Identify Root Cause**: Identify the fundamental flaw (e.g. data race, nil pointer, unhandled encoding, expired context, resource leak).
2. **Surgical Fix**: Implement the fix in production code. *Surgical* is the criterion: the diff touches only the lines the root cause identifies.
3. **Verify Green Repro**: Re-run the repro script or failing test from Step 1 and verify it now passes (exit code 0).
4. **Checkable Completion Criterion**:
   - Repro script or failing test from Step 1 re-run and returns exit code 0; surrounding regression test suite remains 100% green.

### Step 4: Regression Lock & Self-Healing Ingestion (MUST)
1. **Promote to Permanent Regression Test**: Move reproduction script into permanent unit test suite under `tests/`.
2. **Automated Self-Healing Loop (A-MAC Gate)**:
   If the bug stems from a non-intuitive root cause (concurrency race condition, unexpected API signature drift, hidden runtime trap, or memory leak):
   - Automatically compose a draft that satisfies the A-MAC gate (`dfs/references/a-mac-gate.md`), appending the Execution Receipt that this step produces.
   - Dispatch `save_inbox_draft(title=..., content=..., tags=...)` or persist directly to `99-Inbox/YYYY-MM-DD-{kebab-topic}.md`.
   - Announce: `✅ Non-intuitive pitfall self-healed: persisted to 99-Inbox/ with regression proof.`
3. **Checkable Completion Criterion**:
   - Regression test permanently committed in test suite; if A-MAC eligible, `save_inbox_draft` returns success receipt with saved note path.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Stack trace says nil map, so I'll edit the code directly without writing a repro script."* | **Coincidental Healing**: cannot distinguish a real fix from an untested coincidence; bugs reappear under edge cases. | Always verify Step 1 red repro before editing production source files. |
| *"I added `except Exception: continue` or a fallback default, so the bug is handled."* | **Silent Error Swallowing**: masking real defects behind exit code 0; turns runtime failures into silent data corruption. | Never swallow exceptions. Fix root cause or propagate typed errors. |
| *"The code compiles and a nearby test passes, so I don't need to re-run the repro."* | **Unverified Fix / False Green**: original failure mode was never tested against the fix. | Re-run the exact failing repro script from Step 1 and verify exit code 0. |
| *"The test was too strict, so I'll relax the assertion or delete the failing test."* | **Reward Hacking**: eroding test suite guarantees to fake completion. | NEVER alter or delete failing tests to fabricate green status; fix production code. |
