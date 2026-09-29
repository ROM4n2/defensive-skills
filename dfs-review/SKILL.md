---
name: dfs-review
description: Review a code diff against 7-language RFC 2119 DFS rules. Use when the user asks for a code review, or before merging a change.
version: 0.2.0
license: MIT
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

## 🚪 Before you start — is this the right reviewer?

This skill is the **narrow, deep gate**: one adversarial reviewer, one axis, a diff as input, and a
verdict allowed to halt the commit.

- Keep it here for a code diff on a **single surface** — one language, one layer, no schema, UI or
  availability angle.
- Hand off to **`/dfs-team`** when the target spans **two or more** domains (database + performance +
  availability …), or is not a diff at all (a module, a repo, a design, a plan). A swarm covers the
  breadth; it produces a report, not a halt.
- Hand off to **`/dfs-grill`** while a design is still being shaped.

Two reviewers on one single-surface diff is waste; one reviewer on a six-domain change is a blind spot.

---

## The 4-Step Review Procedure

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
Dispatch one isolated subagent (`delegate_task` is the portable path; runtime variants in `dfs/references/subagent-dispatch.md`):
- Provide ONLY the diff content and the Red/Yellow card protocol;
- Reviewer runs with read-only permissions (zero source code edits);
- Reviewer evaluates code strictly against Red Card blockers and Yellow Card polish items.

### Step 4 — Report Verdict & Remedy
- **If Verdict is REJECTED (RED CARD):** Present findings with exact line numbers, failure scenarios, and minimal fixes. Halt git commit/push until resolved.
- **If Verdict is APPROVED WITH NOTES / CLEAN PASS:** Present verification proof and proceed to commit.
