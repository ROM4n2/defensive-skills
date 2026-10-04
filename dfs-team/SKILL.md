---
name: dfs-team
description: Audit code, a design, or a plan with a multi-domain subagent swarm, then collapse the findings into a single consensus report. Use when the target spans two or more specialist domains and needs several independent expert reviews.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-agent, team-review, code-review, audit, consensus]
    related_skills: [dfs-review, dfs-grill, dfs-plan]
---

# Multi-Expert Swarm Review & Consensus Synthesis

Orchestrate a full-spectrum domain-specialist subagent swarm to audit a target — code, a design, or a plan — in parallel across **User Experience + Frontend + Database + Performance + Code Quality + Availability**, synthesizing an actionable verdict.

## 🚪 Entry Gate — this skill, or `/dfs-review`?

Both skills audit. They split on **breadth**, and on **what the output is allowed to do**:

| | `/dfs-review` | this skill |
|---|---|---|
| Axes | **one** — code quality and language invariants | **two or more** of the domains tabled below |
| Input | a **diff / pull request** | any target — a diff, a module, a repo, a design, a plan |
| Output | a **gate**: a RED CARD halts the commit | a **report**: P0/P1/P2 plus a consensus action plan, no halt |

- **This skill** — the target plausibly touches **two or more** of the domains below.
- **`/dfs-review`** — a code diff on a single surface: one language, one layer, no schema, UI or
  availability angle. One adversarial reviewer goes deeper on that one axis, for a fraction of the cost.

**A design or a plan is a valid target here.** Seats are picked by what the target contains, so a
design with no code yet runs the seats that do not need code (`product-ux`, `sre-resilience`,
`code-reviewer`) and skips the ones that do (`dba-optimizer`, `perf-profiler`) — record the skips in
the report. `/dfs-grill` remains the better tool while a design is still being *shaped*; this skill
reports on a design that already exists.

A swarm costs one fresh context per seat, plus one independent skeptic read per P0/P1 finding.

**The receipt (MUST).** For every seat you skip, name the **artifact class absent from the target** —
`skipped dba-optimizer: no SQL, migration or data-model file in the diff` — never `not relevant`. A
reason that would be true of every target is not a reason. For the seats you run, name the domain you
judged the target to touch. Both belong in the report header, not in prose.

---

## Phase 1: Swarm Dispatch (Parallel Fan-out)
Dispatch the relevant specialist seats concurrently:
- **Dispatch one subagent per seat, runtime-neutrally**: `delegate_task` is the portable path; `subagent_type` is the optional Claude Code fallback. The runtime variants, the `subagent_type` rule and the **read-scope declaration** each seat owes live in `dfs/references/subagent-dispatch.md`.
- **Batch Parallel Invariant (Hermes MUST)**: In Hermes Agent environments, pass all specialist tasks in a single `delegate_task(tasks=[...])` call rather than serializing dispatches across multiple conversation turns. Parallel execution preserves token budget and accelerates consensus.

| Seat | Subagent Role (`subagent_type`) | Owns (primary claim) | Cross-checks |
|---|---|---|---|
| User Experience & Product | `product-ux` | Real need vs imagined, journey friction, error messaging | — |
| Frontend & State Systems | `frontend-architect` | Render cost, offline/reconnect, **client-state races**, client-side leaks | — |
| Database & Storage | `dba-optimizer` | Index coverage, EXPLAIN, transaction scope, **lock scope**, query cost | — |
| Performance & Concurrency | `perf-profiler` | **memory-level data races**, hot paths, allocation pressure, mutex contention | DB lock contention → `dba-optimizer` |
| Code Quality & Standards | `code-reviewer` | Red/Yellow cards, Ladder of Reuse, YAGNI, dead-green tests, **hardcoded secret** | — |
| SRE & Availability | `sre-resilience` | Timeouts, retries, failure modes, resource bounds | runtime secret exposure → `code-reviewer` |
| Codebase recon (optional) | `codebase-researcher` | Pre-flight inventory when the target scope is unclear | — |
| Code-structure recon (optional) | `codegraph-explorer` | Call chains and impact pre-recon when the target involves "who calls X / what breaks if W changes" | — |

**Checkable Completion Criterion**:
- Active specialist seats dispatched in parallel; receipts collected with line citations and primary domain ownership.

---

## 🚫 Common Rationalizations & Anti-Patterns

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

## Phase 1.5: Adversarial Verification (for P0/P1 findings)

Before synthesis, verify each **P0 and P1** finding. Dispatch an independent skeptic agent via `delegate_task` (or `code-reviewer` seat in Claude Code — its anti-sycophancy protocol is the point) with the prompt: *"Try to refute this finding: <finding + file:line + failure scenario>. Read the actual code. If the scenario cannot actually happen, say why."*

- Refutation fails (the finding survives a genuine read of the code) → label **CONFIRMED**.
- Refutation succeeds or the scenario proves unreachable → label **PLAUSIBLE**, keep it in the report with the label visible — do not silently drop it, and do not let it drive a blocker verdict on its own.
- P2 findings are not adversarially verified; label them UNVERIFIED.

Do not skip this step by trusting seat reports at face value — a single-seat P0 that survives an independent skeptic read is worth five that don't.

---

## Phase 2: Evidence Triangulation & Severity Triage
Classify all discovered findings into strict severity tiers:
- **P0 (Blocker)**: Data corruption, race condition deadlock, secret leak, broken core user flow.
- **P1 (Critical)**: Missing index on hot query, unhandled network timeout, confusing error feedback, Goroutine leak.
- **P2 (Improvement)**: Guard clause flattening, touch target adjustment, minor allocation optimization.

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

## 🧪 Worked example — synthesis excerpt

Target: a diff touching the inbox consolidator. Seats dispatched: `perf-profiler`, `code-reviewer`.
Seats skipped (why): `product-ux`, `frontend-architect` — the diff has no UI or client-state surface.

```
### 🚨 Critical Findings (P0 / P1)
- **[perf-profiler]** [CONFIRMED]: `scripts/vault-inbox-consolidate.py` walks each draft twice
  (`:132` and `:188`), so a large inbox pays 2N file reads per run.
  - *Verification Status*: CONFIRMED via skeptic read — both call sites hit the same directory walk,
    and neither caches the parsed draft.

### ⚠️ Improvements & Suggestions (P2)
- **[code-reviewer]** [UNVERIFIED]: the nested `if` in the archive branch could be flattened with a
  guard clause.
```

A P0 line that failed the skeptic read would stay in the report labelled **PLAUSIBLE** — visible, but
unable to carry the blocker verdict on its own.
