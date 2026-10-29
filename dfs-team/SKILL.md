---
name: dfs-team
description: Audit code, a design, or a plan with a multi-domain subagent swarm, then collapse the findings into a single consensus report. Use when the target spans two or more specialist domains and needs several independent expert reviews.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags: [multi-agent, team-review, code-review, audit, consensus]
    related_skills: [dfs-review, dfs-grill, dfs-plan]
---
# Multi-Expert Swarm Review & Consensus Synthesis

Orchestrate a full-spectrum domain-specialist subagent swarm to audit a target — code, a design, or a plan — in parallel across **User Experience + Frontend + Database + Performance + Code Quality + Availability**, synthesizing an actionable verdict.

> **Detailed playbook**: this skill's long-form sections were moved to [`references/swarm-synthesis.md`](references/swarm-synthesis.md). Load it when you need the full procedure, the worked example, or the field evidence — the constraints above are self-sufficient without it.

## [MAP] Entry Gate — this skill, or `/dfs-review`?

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

## Phase 1: Swarm Dispatch (Dynamic Seat Pruning & Parallel Fan-out)
Dispatch the relevant specialist seats concurrently with **Strict Dynamic Pruning (硬性席位裁剪)**:
- **Maximum 2~3 Active Seats per Swarm (Anti-429 Rate Limit Guard)**: Never fan out all 6 seats blindly. Scan the target files first and prune irrelevant seats before dispatch:
  * No SQL, migrations, or database schema files in diff -> **SKIP `dba-optimizer`** (zero database surface).
  * No frontend components, DOM, CSS, or client state -> **SKIP `frontend-architect`** (zero UI surface).
  * No hot loops, memory pools, or lock-level concurrency -> **SKIP `perf-profiler`** (zero allocation surface).
  * No user-facing APIs, CLI flags, or UX journey shifts -> **SKIP `product-ux`** (zero product journey surface).
  * No infrastructure, timeouts, retry loops, or network boundaries -> **SKIP `sre-resilience`** (zero resilience surface).
- **Dispatch one subagent per active seat, runtime-neutrally**: `delegate_task` is the portable path; `subagent_type` is the optional Claude Code fallback (see `dfs/references/subagent-dispatch.md`).
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
- Report assembled from `templates/swarm-synthesis-report.md` — the template's required sections and the collapse-before-synthesize rule are in [`references/swarm-synthesis.md`](references/swarm-synthesis.md).

---
