---
name: dfs-save
description: "Harvest non-obvious engineering solutions to 99-Inbox."
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [knowledge-harvesting, inbox, a-mac, karpathy-mode, learnings]
    related_skills: [dfs-inbox-consolidate, dfs-handoff]
    mcp_tools: [search_vault, save_inbox_draft]
---

# DFS-SAVE: Karpathy-Mode Knowledge Harvester & Ingestion Gate

Harvest non-obvious engineering solutions, environment gotchas, and architectural patterns discovered during coding sessions into `99-Inbox/` with **pre-save deduplication check**.

## The Ingestion Invariants (MUST)
1. **Novelty Check (Pre-Save Deduplication)**: Query `search_vault(query="<topic>")` before saving. If a note with >70% similarity exists, propose updating the existing note instead of creating a duplicate draft.
2. **Quality Gate (A-MAC)**: Reject trivial one-off bug fixes ("fixed typo in line 12"). MUST record: Symptom, Root Cause, Solution, and Defensive Rule.
3. **Structured YAML**: MUST include valid YAML frontmatter with `created`, `type: source-notes`, `status: draft`, `tags`, and `source`.

---

## The 3-Step Harvesting Workflow

### Step 1: Novelty & Similarity Check
```python
# Check existing knowledge
search_results = search_vault(topic_keywords)
# If identical problem already documented: Propose edit to existing note
```

### Step 2: Compose Draft File
Draft path: `{vault_root}/99-Inbox/YYYY-MM-DD-{kebab-topic}.md` (resolve `{vault_root}` per `dfs/references/vault-root-resolution.md`)

Load the draft structure specification via `read_file(path='templates/draft-template.md')` when drafting inbox notes.

Key required sections in `draft-template.md`:
- **Frontmatter**: Valid YAML with `created`, `type: source-notes`, `status: draft`, `tags`, and `source`.
- **1. 现象与成因分析 (Symptom & Root Cause)**: Misleading symptoms, broken state, and root cause.
- **2. 终极解决方案 (Permanent Solution & Code)**: Clean, reproducible code fix.
- **3. 防御性工程规范 (Defensive Rule)**: Universal rule to prevent recurrence in other projects.
- **4. 确定性评估信号 (Deterministic Evaluation Signals)**: Tool results count, error receipts, and environment state check.

### Step 3: Call MCP Tool
Call `save_inbox_draft(title=..., content=..., tags=...)` to write to `99-Inbox/`.
Announce to user: `✅ Knowledge harvested and persisted to 99-Inbox/ (passed A-MAC gate).`
