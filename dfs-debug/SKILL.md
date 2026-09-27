---
name: dfs-debug
description: Execute 4-step systematic root-cause debugging with repro.
version: 0.2.0
author: Defensive Skills contributors
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
2. Implement surgical fix in production code.
3. Run the repro script / failing test and verify it now passes (GREEN).

### Step 4: Regression Lock & Self-Healing Ingestion (MUST)
1. **Promote to Permanent Regression Test**: Move reproduction script into permanent unit test suite under `tests/`.
2. **Automated Self-Healing Loop (A-MAC Gate)**:
   If the bug stems from a non-intuitive root cause (concurrency race condition, unexpected API signature drift, hidden runtime trap, or memory leak):
   - Automatically compose an A-MAC draft formatted with Symptom, Root Cause, Solution, Defensive Rule, and Execution Receipt.
   - Dispatch `save_inbox_draft(title=..., content=..., tags=...)` or persist directly to `99-Inbox/YYYY-MM-DD-{kebab-topic}.md`.
   - Announce: `✅ Non-intuitive pitfall self-healed: persisted to 99-Inbox/ with regression proof.`
