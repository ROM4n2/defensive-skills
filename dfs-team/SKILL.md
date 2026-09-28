---
name: dfs-team
description: Orchestrate multi-expert subagent reviews into a consensus. Use when a design or plan needs several independent expert reviews and a merged verdict.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-agent, team-review, code-review, audit, consensus]
    related_skills: [dfs-review, dfs-grill, dfs-plan]
---

# Multi-Expert Swarm Review & Consensus Synthesis

Orchestrate a full-spectrum domain-specialist subagent swarm to audit code in parallel across **User Experience + Architecture + Database + Performance + Security**, synthesizing an actionable verdict.

## Phase 1: Swarm Dispatch (Parallel Fan-out)
Dispatch the relevant specialist seats concurrently:
- **Runtime-neutral dispatch**: In Hermes or standard multi-agent environments, dispatch subagents using `delegate_task` with targeted role goals, scope, and instructions corresponding to the seat.
- **Claude Code fallback**: In Claude Code environments, dispatch subagent seats (`~/.claude/agents/` as optional Claude-specific fallback) using the `subagent_type` values below.

| Seat | Subagent Role (`subagent_type`) | Covers |
|---|---|---|
| User Experience & Product | `product-ux` | Real need vs imagined, journey friction, error messaging |
| Frontend & State Systems | `frontend-architect` | Async races, offline/reconnect, render cost, leaks |
| Database & Storage | `dba-optimizer` | Index coverage, EXPLAIN, locks, transaction scope |
| Performance & Concurrency | `perf-profiler` | Data races, hot paths, allocation pressure, contention |
| Code Quality & Standards | `code-reviewer` | Red/Yellow cards, Ladder of Reuse, YAGNI, dead-green tests |
| SRE & Availability | `sre-resilience` | Timeouts, retries, failure modes, resource bounds, secrets |
| Codebase recon (optional) | `codebase-researcher` | Pre-flight inventory when the target scope is unclear |
| Code-structure recon (optional) | `codegraph-explorer` | Call chains and impact pre-recon when the target involves "who calls X / what breaks if W changes" |

**Pick seats by what the target actually contains.** A pure-frontend diff does not need `dba-optimizer`; a SQL migration does not need `product-ux`. Dispatching all seats at every target burns tokens and produces filler findings — state which seats you skipped and why (template field, not prose).

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
