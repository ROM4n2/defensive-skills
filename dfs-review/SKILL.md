---
name: dfs-review
description: "Review code diffs against 7-language RFC 2119 DFS rules."
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, rfc-2119, red-card, standards, gatekeeper, subagents]
    related_skills: [dfs-team, dfs-refactor, dfs-exec]
    mcp_tools: [get_rule_snippet, list_standards]
---

# DFS-Review: Adversarial Red/Yellow Card Code Review

Conduct thorough, unsparing code review on a git diff or pull request against Defensive Skills standards, The Ladder of Reuse, and language invariants by dispatching an independent, fresh-context reviewer subagent.

**Core Invariant:** The reviewer reports, the caller fixes. Every finding must have a concrete failure scenario. Anti-sycophancy: zero performative praise.

---

## The 3-Step Review Procedure

### Step 1 — Capture Git Diff
Run the inspection using terminal:
```bash
git diff --cached
```
If cached diff is empty, run `git diff`. If specific commit ranges or files are targeted (e.g. `main...HEAD`), review those directly.
If the diff exceeds 15,000 characters, review file-by-file via `git diff --name-only` and `git diff HEAD -- <file>`.

### Step 2 — Retrieve Applicable Language Standards
The 7-language RFC 2119 rules live in the Vault, not in this skill. Retrieve the current version so
the review cannot drift out of date:
- `get_rule_snippet(rule, section)` — pull the specific section for each language the diff touches.
- `list_standards()` — enumerate available language standards when the diff spans unfamiliar files.
Pass the retrieved rule text to the reviewer subagent as the authoritative rubric. Do not restate
the rules from memory.

### Step 3 — Dispatch Independent Reviewer Subagent
Load the reviewer scaffold from `templates/code-reviewer-prompt.md` via `read_file(path='templates/code-reviewer-prompt.md')`.
Dispatch an isolated subagent via `delegate_task` (Hermes) or `invoke_subagent` (Claude Code / generic):
- Provide ONLY the diff content and the Red/Yellow card protocol;
- Reviewer runs with read-only permissions (zero source code edits);
- Reviewer evaluates code strictly against Red Card blockers and Yellow Card polish items.

### Step 4 — Report Verdict & Remedy
- **If Verdict is REJECTED (RED CARD):** Present findings with exact line numbers, failure scenarios, and minimal fixes. Halt git commit/push until resolved.
- **If Verdict is APPROVED WITH NOTES / CLEAN PASS:** Present verification proof and proceed to commit.
