---
name: dfs-review
description: Review a code diff against 7-language RFC 2119 DFS rules. Use when the user asks for a code review, or before merging a change.
license: MIT
metadata:
  version: 0.4.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - code-review
    - rfc-2119
    - red-card
    - standards
    - gatekeeper
    - subagents
    related_skills:
    - dfs-team
    - dfs-refactor
    - dfs-exec
    - dfs-verify
    mcp_tools:
    - get_rule_snippet
    - list_standards
---


# DFS-Review: Adversarial Red/Yellow Card Code Review

Conduct thorough, unsparing code review on a git diff or pull request against Defensive Skills standards, The Ladder of Reuse, and language invariants by dispatching an independent, fresh-context reviewer subagent.

## [MUST] The Adversarial Review Invariant (RFC 2119 MUST)
> **The reviewer reports, the caller fixes. Every finding MUST include a concrete failure scenario with exact `file:line` citations.**
> Anti-Sycophancy: Zero performative praise. The reviewer is an adversarial prosecutor, not a polite assistant.

---

## Before you start — is this the right reviewer?
- Code diff on a **single surface**: stay here (one adversarial reviewer, halt authority).
- Multi-domain change (≥2 surfaces) or whole repo: hand off to **`/dfs-team`** (breadth report, not halt).
- Shaping a design before code: hand off to **`/dfs-grill`**.

---

## The 4-Step Review Procedure

`Step 1: Capture Diff` -> `Step 2: Standards` -> `Step 3: Dispatch Reviewer` -> `Step 4: Report Verdict`

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

### Step 3 — Adaptive Review Dispatch (阈值自适应审查)
0. **Attach Test-Evidence Manifest (MUST)**: Hand the reviewer `test name -> what it asserts` plus builder mutation self-proofs with quoted assertions. Mandate: **do not re-derive what manifest already proves**; focus on areas tests cannot reach.
1. **Diff Scope Inspection & Adaptive Dispatch**:
   - **Lightweight Diff (Diff ≤ 20 lines & Docs/Metadata/Constants only)**:
     Orchestrator performs inline self-review against the Red Card rubric directly in-thread, outputting a concise verdict. Eliminates subagent cold-start latency and avoids 429 rate limits for trivial mechanical edits.
   - **Production Logic Diff (Diff > 20 lines or touches business/algorithmic code)**:
     **MANDATORY**: Dispatch independent, context-isolated subagent (`delegate_task` is the portable path; runtime variants in `dfs/references/subagent-dispatch.md`) using `templates/code-reviewer-prompt.md`.
     Reviewer runs strictly read-only (zero source code edits) and evaluates code strictly against Red Card blockers (RFC 2119 MUST violations) and Yellow Card polish items.
2. **Reviewer's mandated focus** (what the manifest cannot cover):
   - **Untested invariants**: error-classification width, cancelled-context teardown, progress semantics, duplicate implementations of one rule (the four classes in `/dfs-grill` Stage 2.5).
   - **Contract breaks**: public signatures, test baselines, packaging/embed guards.
   - **Red Card #10 & Quantity Boundaries**: Check for ratio-into-share/percent traps, bounded sinks lacking clamping, and vacuous/dead tests per [dfs-tdd/references/dead-test-and-quantity-guards.md](dfs-tdd/references/dead-test-and-quantity-guards.md).
   - **Scope creep**: anything in the diff the task did not ask for.
   - **Residual unknowns**: an explicit list of conclusions the reviewer could *not* physically verify on this host. A silent report is treated as full verification and is the one thing a reviewer must never do.
3. **Checkable Completion Criterion**:
   - Structured verdict (`RED CARD` or `CLEAN PASS`) returned with zero performative compliments.
   - Manifest attached, scope limit stated, residual-unknowns list present.

### Step 4 — Report Verdict & Remedy
1. **Process Verdict**:
   - **If Verdict is REJECTED (RED CARD)**: Present findings with `file:line`, concrete failure scenario, and minimal fix. Halt git commit/push until resolved.
   - **If Verdict is APPROVED WITH NOTES / CLEAN PASS**: Present verification proof and proceed to commit.
   - **Disputed Findings**: If a reported defect is disputed or suspected hallucination, invoke `/dfs-verify` for condition checks rather than arguing in prompt prose.
2. **Checkable Completion Criterion**:
   - Binary decision reached: either a blocking defect list with `file:line` is presented, or explicit merge approval is given.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Looks good to me! Clean and concise code."* | **Sycophantic Blindness**: performative praise masking subtle concurrency or logic bugs. | Ban performative praise. The reviewer acts as an adversarial prosecutor focused solely on defect discovery. |
| *"This could potentially be improved theoretically."* | **Vague Review Bloat**: non-actionable academic feedback that slows down delivery. | Every finding MUST cite exact `file:line` and describe a concrete, falsifiable failure scenario. |
| *"The reviewer subagent fixed the bug directly in the repo."* | **Maker-Checker Boundary Violation**: executing and reviewing in the same context creates blind spots. | Reviewer is strictly read-only. Caller fixes, reviewer only reports. |
| *"Feeding a 20,000-line massive diff in a single prompt."* | **Attention Degradation**: critical boundary errors buried in the middle of long diffs are missed. | If diff > 15,000 characters, partition by file or module and review in chunks. |
| *"The builder already ran these tests, so I will re-run them and re-derive the same conclusions."* | **Duplicate Derivation Burn**: a full dispatch spent reproducing evidence that was handed over, while the untested invariants go unexamined. | Consume the Test-Evidence Manifest as given; spend the dispatch on what tests cannot reach (the four defect classes, contract breaks, scope creep, residual unknowns). |
