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

## 🚨 The Reproduction-First Invariant (HARD GATE)
> Always complete and verify Step 1 (Evidence & Minimal Reproduction) before attempting any production code change.
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
  [Step 3: Root-Cause Remediation & Mutation Defense]
                               │
                               ▼
  [Step 4: Regression Test & Karpathy Ingestion (/dfs-save)]
```

### Step 1: Evidence & Minimal Reproduction (MUST)
1. **Exact Error Log**: Capture full stack trace and error message.
2. **Minimal Repro Script**: Create a standalone reproduction script in `scratch/repro.<lang>` or write a failing test. Load templates from `templates/repro-scaffold.md` via `read_file(path='templates/repro-scaffold.md')` to scaffold reproductions.
3. **Execute & Confirm Repro**: Run repro script in terminal and confirm it produces the exact reported failure.

### Step 2: Vault Pitfall & Synonym Search
Query Defensive Skills for known gotchas and workarounds:
- Call `search_vault(query="<error_message_or_keyword>")`
- Inspect `01-Rules/ERROR-HANDLING-PATTERNS.md` and `01-Rules/ENVIRONMENT-LOCAL.md`.

### Step 3: Root-Cause Fix & Defense
1. Identify the fundamental flaw (e.g. data race, nil pointer, unhandled encoding, expired context).
2. Implement the fix in production code. *Surgical* is the criterion: the diff touches only the lines the root cause from Step 3 names, and the repro from Step 1 is the thing you re-run to judge it.
3. Run the repro script / failing test and verify it now passes (GREEN).

### Step 4: Regression Lock & Self-Healing Ingestion (MUST)
1. **Promote to Permanent Regression Test**: Move reproduction script into permanent unit test suite under `tests/`.
2. **Automated Self-Healing Loop (A-MAC Gate)**:
   If the bug stems from a non-intuitive root cause (concurrency race condition, unexpected API signature drift, hidden runtime trap, or memory leak):
   - Automatically compose a draft that satisfies the A-MAC gate (`dfs/references/a-mac-gate.md`), appending the Execution Receipt that this step produces.
   - Dispatch `save_inbox_draft(title=..., content=..., tags=...)` or persist directly to `99-Inbox/YYYY-MM-DD-{kebab-topic}.md`.
   - Announce: `✅ Non-intuitive pitfall self-healed: persisted to 99-Inbox/ with regression proof.`

## 🕳️ Anti-patterns

Three ways the 4-step protocol gets silently skipped. Each one actually happened while building this
suite — the receipt is the point, not the slogan.

**1. Fixing from the error message instead of a reproduction.**
"Stack trace says nil map" -> edit the source -> move on. With no reproduction you cannot tell a fix
from a coincidence, and the change ships unverified.
*Receipt:* a batch gate-runner here reported **9/9 suites FAILED** while all 98 test methods were
green — the detector was wrong, not the tree. It had never been calibrated against a run whose result
was already known. Reproduce the failure on a case whose outcome you can predict first.

**2. Swallowing the error and calling it handled.**
`except Exception: continue`, a bare `return None`, or a fallback default turns a real failure into a
quiet success; the worst variant exits **0**.
*Receipt:* a ported tool's root-resolution fallback landed on the checkout's own directory, reported
"inbox does not exist", and **exited 0** — a silent wrong answer. A later `except Exception: continue`
did not hide a defect, but it *moved the attribution* to an unrelated rule. An exception is evidence:
route it into Step 3, do not erase it.

**3. Declaring victory without re-running the original reproduction.**
The fix compiles and a nearby test passes, so you move on — but the exact failing case was never run
again, and no regression test was locked in.
*Receipt:* a shipped template carried a pre-seeded fake history. The tree was "fixed" locally and
every gate was green — yet a fresh clone still broke, because the check ran on the one machine where
the difference was invisible. Re-run the original repro where it failed, then promote it to a
permanent test (Step 4).
