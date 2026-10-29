# Agent Harness Architecture Guardrails & Worked Sizing Examples (`references/agent-harness-and-sizing-examples.md`)

Load this reference during Phase 3 Step 1 (when designing AI agent, RAG, or tool-calling architectures) and for worked examples of the Three-Path Classification (Spike vs Bounded vs Architectural).

---

## 1. Industrial Coding-Agent & Harness Guardrails (11-System Empirical Baseline) (MUST)

When shaping a spec for an AI agent, runtime harness, or retrieval system, enforce these four empirical baselines (derived from a 4M-LOC source audit across 11 production coding agents):

1. **Absence 1 — Zero Black-Box Agent Frameworks in Production Loops**:
   - Reject LangChain, LangGraph, CrewAI, and AutoGen for core execution loops. They obscure token budgets, break prompt caching, and make multi-turn state deadlocks un-debuggable.
   - **Mandate**: Build on native language concurrency (`asyncio` / `Promise` / Go `goroutine` + `context.WithCancelCause`) with a flat **Middleware Pipeline** once `>= 3` orthogonal turn controls (token cap, cost circuit-breaker, read-only guard) exist.
2. **Absence 2 — Zero Vector RAG Over Rapidly Mutating Source Code**:
   - Production coding agents use **0% vector embeddings** for source-code navigation because code has exact AST/symbol structure and mutates every minute (causing immediate index staleness).
   - **Mandate**: For source code, use deterministic lexical/structural tools (`ripgrep`, `glob`, `tree-sitter` AST, hierarchical `AGENTS.md`). Reserve FTS5 + vector hybrid retrieval strictly for static/semi-static documentation or knowledge corpora.
3. **Bit-Perfect Prefix Normalization (KV Cache Economics)**:
   - Deterministically sort tool schemas and freeze static system-prompt prefixes across turns. Never inject per-turn timestamps, random UUIDs, or mutating memory blobs into the system prefix.
4. **ACPI Poka-yoke & Deferred Tool Discovery (`> 15` Tools)**:
   - When total tools exceed **15**, mandate on-demand deferred loading (`tool_search`) so tool schemas do not consume >40% of the context window.
   - Split mutually exclusive tool parameters into separate single-purpose tools, constrain finite strings to closed `enum`s, and return structured error JSON carrying `suggested_action`.

---

## 2. Worked Example — Classification Decides the Process

**Input A**: *"Can we cut cold-start below 200 ms?"* -> Phase 1 classifies this a **Spike** (a feasibility / cost question): present a 2–3 sentence probe plan, get a nod, investigate, report — no spec document.

**Input B**: *"We want a pluggable storage layer."* -> **Architectural**: full Phase 2–5. Phase 3 Step 1 trade-off matrix:

| Option | Complexity | Startup cost | Verdict |
|---|---|---|---|
| A. Minimalist: stdlib `dbm` only | lowest | none | rejected — no query support |
| B. Domain-Native: reuse the existing SQLite engine | medium | reuses existing open path | **chosen** |
| C. Extensible: pluggable driver registry | highest | none | rejected — YAGNI at one backend |

Chosen **B**: the repo already opens SQLite, and a driver registry would have exactly one member.

Mirrored output — the approved spec head:
```markdown
# Design Specification: Pluggable Storage Layer

**Date**: 2026-09-28 | **Status**: APPROVED | **Target Path**: `docs/specs/2026-09-28-storage-layer-design.md`

## 1. Problem Statement & User Value
- Why build this: one backend today, a second is planned for next quarter.
- Target Scenario & Persona: the platform engineer wiring storage per environment.
- Cost of Doing Nothing: each environment keeps a bespoke, untested adapter.

## 2. User Journey & Core Flow
1. Set `storage.driver` -> the loader resolves the backend
2. Write a record -> the configured driver persists it
3. Read it back through the same interface -> value achieved
```
