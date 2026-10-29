# dfs-team — extended playbook (tier 3)

Loaded on demand by `dfs-team/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

## Phase 1.5: Adversarial Verification (for P0/P1 findings)

Before synthesis, verify each **P0 and P1** finding. Dispatch an independent skeptic agent via `delegate_task` (or `code-reviewer` seat in Claude Code — its anti-sycophancy protocol is the point) with the prompt: *"Try to refute this finding: <finding + file:line + failure scenario>. Read the actual code. If the scenario cannot actually happen, say why."*

- Refutation fails (the finding survives a genuine read of the code) → label **CONFIRMED**.
- Refutation succeeds or the scenario proves unreachable → label **PLAUSIBLE**, keep it in the report with the label visible — do not silently drop it, and do not let it drive a blocker verdict on its own.
- P2 findings are not adversarially verified; label them UNVERIFIED.
- **Unverified Claim Resolution**: For any findings marked UNVERIFIED (or disputed PLAUSIBLE claims) that must be acted upon before implementation, route to `/dfs-verify` to obtain physical negative-search proof and verify condition guards before filing remediation tasks.

Do not skip this step by trusting seat reports at face value — a single-seat P0 that survives an independent skeptic read is worth five that don't.

---

## Phase 2: Evidence Triangulation & Severity Triage
Classify all discovered findings into strict severity tiers:
- **P0 (Blocker)**: Data corruption, race condition deadlock, secret leak, broken core user flow.
- **P1 (Critical)**: Missing index on hot query, unhandled network timeout, confusing error feedback, Goroutine leak.
- **P2 (Improvement)**: Guard clause flattening, touch target adjustment, minor allocation optimization.

---

## [NOTE] Worked example — synthesis excerpt

Target: a diff touching the inbox consolidator. Seats dispatched: `perf-profiler`, `code-reviewer`.
Seats skipped (why): `product-ux`, `frontend-architect` — the diff has no UI or client-state surface.

```
### [NOTE] Critical Findings (P0 / P1)
- **[perf-profiler]** [CONFIRMED]: `scripts/vault-inbox-consolidate.py` walks each draft twice
  (`:132` and `:188`), so a large inbox pays 2N file reads per run.
  - *Verification Status*: CONFIRMED via skeptic read — both call sites hit the same directory walk,
    and neither caches the parsed draft.

### [NOTE] Improvements & Suggestions (P2)
- **[code-reviewer]** [UNVERIFIED]: the nested `if` in the archive branch could be flattened with a
  guard clause.
```

A P0 line that failed the skeptic read would stay in the report labelled **PLAUSIBLE** — visible, but
unable to carry the blocker verdict on its own.
## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"All seats are important, so I will dispatch all 6 specialists on a 10-line helper diff."* | **Token Waste & Fluff Inflation**: Forcing irrevelant reviewers produces fabricated nitpicks. | Pick seats strictly based on artifact classes present in target. Explicitly justify skips. |
| *"Seat reported a P0 issue, so I will print it as confirmed without verification."* | **False-Positive Panics**: Subagents frequently hallucinate severity or overlook call-site guards. | Mandatory Phase 1.5 Adversarial Skeptic Read for all P0/P1 findings before synthesis. |
| *"I'll list findings from every seat individually to show how thorough the audit was."* | **Synthesis Failure & Inflated Count**: Printing duplicate findings uncollapsed distorts priorities. | Strict Collapse Rule: Report findings count MUST be strictly less than raw seat count. |
| *"The consensus report is done, so the audit finishes without actionable remediation."* | **Passive Documentation**: Audit reports without sequenced patches leave debt unaddressed. | Mandatory Action Plan: Every synthesis MUST output ordered, concrete remediation steps. |

**`subagent_type` names the base agent only** — this seat's job is its Owns column. See `dfs/references/subagent-dispatch.md`.

**Pick seats by what the target actually contains.** A pure-frontend diff does not need `dba-optimizer`; a SQL migration does not need `product-ux`. Dispatching all seats at every target burns tokens and produces filler findings. Record the roster
and the per-skip evidence in the report header; the required format is in the Entry Gate above.

**One concept, one owner.** A cross-check seat may still report, but its finding is the secondary
reading, and the collapse rule folds it into the owner's line. Note that two of the four apparent
overlaps were never one concept: **races split by kind** — client-state races belong to
`frontend-architect`, memory-level data races to `perf-profiler` — and a *lock* means "transaction
scope too wide" to `dba-optimizer` while it means "measured contention" to `perf-profiler`. Only the
second pair is a genuine shared concept, and it now has a declared owner.

A seat reporting **outside** its Owns column is a signal: the target contains something the roster has
no owner for. Say so, instead of letting the nearest seat absorb it.

If the target scope is vague, run `codebase-researcher` first. If the target involves call-chain or impact questions, run `codegraph-explorer` first (in parallel with `codebase-researcher` when both apply), then fan out the specialists against what the recon found.

---

## Phase 3: Unified Synthesis Report
Load and follow the Executive Expert Panel Synthesis Card template from `templates/swarm-synthesis-report.md` via `read_file(path='templates/swarm-synthesis-report.md')`.

### Collapse before you synthesize (MUST)

The seat table overlaps by construction. One missing index is at once an index-coverage finding
(`dba-optimizer`), a hot-path finding (`perf-profiler`), and a timeout risk (`sre-resilience`).
Printed raw, that reads like a more thorough report while being one defect said three times and
weighted three times.

- **One underlying defect → one finding.** When several seats report the same defect, merge them into
  a single line naming **every** proposing seat, and keep the **highest** severity proposed.
- Keep the most concrete failure scenario and drop the paraphrases of it.
- **Checkable:** the report's finding count must be **strictly less than** the sum of the seats'
  finding counts. Both numbers are recorded in the report header. Equal numbers mean no collapse
  happened — what follows is a concatenation, not a synthesis, and its verdict is not yet trustworthy.

Key reporting rules:
- **Dispatched vs Skipped**: Explicitly record which seats ran and which seats were skipped and why.
- **Verification Badges**: Every P0/P1 finding line MUST carry its **CONFIRMED / PLAUSIBLE** label from Phase 1.5. A P0 verdict MUST NOT rest on a PLAUSIBLE finding alone.
- **Reuse Ladder Invariant**: Every finding proposing new code or a dependency MUST include a Reuse Ladder check against stdlib and existing modules.
- **Actionable Patches**: Synthesize concrete, ordered remediation steps into the consensus action plan.
