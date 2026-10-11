---
name: dfs-save
description: Harvest non-obvious engineering solutions into 99-Inbox drafts. Use when a debugging session or task just produced a reusable insight worth saving.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags:
      - knowledge-harvesting
      - inbox
      - a-mac
      - karpathy-mode
      - learnings
    related_skills:
      - dfs-inbox-consolidate
      - dfs-handoff
    mcp_tools:
      - search_vault
      - save_inbox_draft
---

# DFS-SAVE: Karpathy-Mode Knowledge Harvester & Ingestion Gate

Harvest non-obvious engineering solutions, environment gotchas, and architectural patterns discovered during coding sessions into `99-Inbox/` with **pre-save deduplication check** and **A-MAC quality validation**.

## 🚨 The A-MAC Ingestion Invariant (RFC 2119 MUST)
> **NO draft shall be persisted to `99-Inbox/` without passing the pre-save similarity check and the A-MAC Quality Gate.**
> Trivial one-off fixes (e.g. typos, single-line syntax fixes) fail A-MAC and MUST NOT be saved.

---

## 🚪 This skill, or `/dfs-inbox-consolidate` / `/dfs-handoff`?

| | this skill | `/dfs-inbox-consolidate` | `/dfs-handoff` |
|---|---|---|---|
| The ask | **harvest** — capture a single discovered insight | **consolidate** — batch-classify inbox drafts into Vault | **handoff** — wrap up active session state |
| Output | a new `99-Inbox/` draft note | filed notes in `01-Rules/`, `03-Languages/`, etc. | a continuation card |
| Feeds | `99-Inbox/` | knowledge vault destinations | next session |

---

## The 3-Step Harvesting Workflow

```
  [Step 1: Novelty Check & Similarity Search (search_vault)]
                               │
                               ▼
  [Step 2: A-MAC Quality Gate & Structured Draft Composition]
                               │
                               ▼
  [Step 3: Call MCP Tool & Persist Physical Receipt]
```

### Step 1: Novelty & Similarity Check
1. **Pre-Save Deduplication Check**:
   - Query `search_vault(query="<topic_keywords>")` before composing a draft.
   - If an existing note addresses the identical problem with >70% similarity, propose appending to or updating the existing note instead of creating a duplicate draft.
2. **Checkable Completion Criterion**:
   - `search_vault` has executed and returned results; similarity is verified <70%, or explicit user agreement to update existing note is recorded.

### Step 2: Compose Draft File
1. **A-MAC Quality Gate Evaluation**:
   - The field schema lives in `dfs/references/a-mac-gate.md`. Reject trivial one-off bug fixes.
   - Load the draft structure specification via `read_file(path='templates/draft-template.md')`.
2. **Required Document Structure**:
   - **Frontmatter**: Valid YAML with `created: YYYY-MM-DD`, `type: source-notes`, `status: draft`, `tags: [...]`, and `source: "..."`.
   - **1. 现象与成因分析 (Symptom & Root Cause)**: Deceptive symptoms, broken state, and true root cause.
   - **2. 终极解决方案 (Permanent Solution & Code)**: Minimal, clean, reproducible code fix.
   - **3. 防御性工程规范 (Defensive Rule)**: Universal rule to prevent recurrence in other projects.
   - **4. 确定性评估信号 (Deterministic Evaluation Signals)**: Tool results count, error receipts, and environment state checks.
3. **Checkable Completion Criterion**:
   - Draft content adheres to `templates/draft-template.md`, includes all 4 mandatory sections, and has zero unpopulated placeholders.

### Step 3: Call MCP Tool & Persist Physical Receipt
1. **Persist Draft**:
   - Call `save_inbox_draft(title=..., content=..., tags=...)` to write to `99-Inbox/` (or `.dfs-inbox/` fallback).
2. **Verify Receipt**:
   - Verify the MCP response returns a successful path confirmation.
   - Announce to user: `✅ Knowledge harvested and persisted to 99-Inbox/ (passed A-MAC gate).`
3. **Checkable Completion Criterion**:
   - MCP call returns success with absolute path printed in terminal output.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Fixed a typo in line 12, let me create an inbox draft."* | **Inbox Noise Pollution**: diluting vault value with trivial churn. | Reject trivial fixes at the A-MAC gate; only harvest non-obvious, reusable learnings. |
| *"I already know this is a novel solution, so I can skip search_vault."* | **Fragmented Duplication**: duplicate notes drift out of sync across the vault. | Mandatory pre-save `search_vault` execution before drafting. |
| *"I'll write free-form text without YAML frontmatter."* | **Ingestion Failure**: `dfs-inbox-consolidate` fails to parse or route unstructured notes. | Frontmatter MUST include `created`, `type: source-notes`, `status: draft`, and taxonomy `tags`. |
| *"I'll invent new ad-hoc tags."* | **Taxonomy Drift**: orphaned tags that match no consolidation routing rules. | Align tags with existing vault taxonomy (`category/*`, `topic/*`, `tool/*`). |
