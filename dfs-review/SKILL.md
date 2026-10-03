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

## 🚨 The Adversarial Review Invariant (RFC 2119 MUST)
> **The reviewer reports, the caller fixes. Every finding MUST include a concrete failure scenario with exact `file:line` citations.**
> Anti-Sycophancy: Zero performative praise. The reviewer is an adversarial prosecutor, not a polite assistant.

---

## 🚪 Before you start — is this the right reviewer?

This skill is the **narrow, deep gate**: one adversarial reviewer, one axis, a diff as input, and a verdict allowed to halt the commit.

- Keep it here for a code diff on a **single surface** — one language, one layer, no schema, UI or availability angle.
- Hand off to **`/dfs-team`** when the target spans **two or more** domains (database + performance + availability …), or is not a diff at all (a module, a repo, a design, a plan). A swarm covers the breadth; it produces a report, not a halt.
- Hand off to **`/dfs-grill`** while a design is still being shaped.

Two reviewers on one single-surface diff is waste; one reviewer on a six-domain change is a blind spot.

---

## The 4-Step Review Procedure

```
  [Step 1: Capture & Chunk Git Diff]
                 │
                 ▼
  [Step 2: Retrieve Language Standards (get_rule_snippet)]
                 │
                 ▼
  [Step 3: Dispatch Isolated Reviewer (templates/code-reviewer-prompt.md)]
                 │
                 ▼
  [Step 4: Report Binary Verdict (RED CARD vs CLEAN PASS)]
```

### Step 1 — Capture Git Diff
1. **Extract Diff**:
   - Run `git diff --cached` (or `git diff`, or specific commit range `main...HEAD`).
   - If diff exceeds 15,000 characters, chunk file-by-file via `git diff --name-only` and review incrementally to prevent context degradation.
2. **Checkable Completion Criterion**:
   - Complete diff captured and verified non-empty before invoking standards or subagent.

### Step 2 — Retrieve Applicable Language Standards
1. **Pull Authoritative RFC 2119 Rubric**:
   - The 7-language RFC 2119 rules live in the Vault. Retrieve the current version so review never drifts out of date:
     - `get_rule_snippet(rule, section)`: pull the specific section for each language the diff touches.
     - `list_standards()`: enumerate available language standards when diff spans unfamiliar files.
   - Pass retrieved rule text to the reviewer subagent as the authoritative rubric. Never restate rules from memory.
2. **Checkable Completion Criterion**:
   - Standard snippets retrieved for every touched file extension and passed to the reviewer scaffold.

### Step 3 — Dispatch Independent Reviewer Subagent
1. **Maker-Checker Isolation**:
   - Load the reviewer scaffold from `templates/code-reviewer-prompt.md` via `read_file(path='templates/code-reviewer-prompt.md')`.
   - Dispatch one isolated subagent (`delegate_task` is the portable path; runtime variants in `dfs/references/subagent-dispatch.md`).
   - Reviewer runs strictly read-only (zero source code edits).
   - Reviewer evaluates code strictly against Red Card blockers (RFC 2119 MUST violations) and Yellow Card polish items.
2. **Checkable Completion Criterion**:
   - Subagent output returned containing structured verdict (`RED CARD` or `CLEAN PASS`) with zero performative compliments.

### Step 4 — Report Verdict & Remedy
1. **Process Verdict**:
   - **If Verdict is REJECTED (RED CARD)**: Present findings with exact line numbers, failure scenarios, and minimal fixes. Halt git commit/push until resolved.
   - **If Verdict is APPROVED WITH NOTES / CLEAN PASS**: Present verification proof and proceed to commit.
2. **Checkable Completion Criterion**:
   - Binary decision reached: either a blocking defect list with `file:line` is presented, or explicit merge approval is given.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Looks good to me! Clean and concise code."* | **Sycophantic Blindness**: performative praise masking subtle concurrency or logic bugs. | Ban performative praise. The reviewer acts as an adversarial prosecutor focused solely on defect discovery. |
| *"This could potentially be improved theoretically."* | **Vague Review Bloat**: non-actionable academic feedback that slows down delivery. | Every finding MUST cite exact `file:line` and describe a concrete, falsifiable failure scenario. |
| *"The reviewer subagent fixed the bug directly in the repo."* | **Maker-Checker Boundary Violation**: executing and reviewing in the same context creates blind spots. | Reviewer is strictly read-only. Caller fixes, reviewer only reports. |
| *"Feeding a 20,000-line massive diff in a single prompt."* | **Attention Degradation**: critical boundary errors buried in the middle of long diffs are missed. | If diff > 15,000 characters, partition by file or module and review in chunks. |
