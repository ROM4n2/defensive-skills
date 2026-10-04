---
name: dfs-spark
description: Generate a design specification from a fuzzy need through Dual-Lens dialogue, at a size the idea earns. Use when the user has an idea with no design yet and wants it shaped into a spec, a short design note, or a feasibility answer.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [brainstorming, idea-sizing, design-spec, dual-lens, product-ux]
    related_skills: [dfs-plan, dfs-grill, dfs-adr, dfs-exec]
    mcp_tools: [omni_search]
---

# DFS-SPARK: Idea Sizing & Exploratory Design

Turn vague ideas, open-ended feature thoughts, or fuzzy developer needs into structured, knowledge-grounded design specifications through collaborative dialogue across **Dual Lenses: User Problem Validation + Technical Architecture**.

## 🚨 The Spec-First Invariant (RFC 2119 MUST)
> **Do NOT invoke any implementation skill, write production code, or scaffold repositories until presenting the design spec and obtaining explicit human partner approval.**
> Jumping into coding from fuzzy requirements without a sized specification violates the Fog of War staged development principle.

---

## 🚪 This skill, or `/dfs-grill`?

Both start from something vague. They split on **what you are being asked to do**:

| | this skill | `/dfs-grill` |
|---|---|---|
| The ask | **generate** — there is no design yet | **interrogate** — a proposal exists and its edges are unclear |
| Output | a **spec**, sized to the idea (or a feasibility answer / a short design note) | an **ADR**: every undecided point forced to a choice |
| Feeds | `/dfs-plan` | the decision record |

A design already written, and you want it attacked? That is `/dfs-grill`. Nothing designed yet? Start
here, and let Phase 1 decide how much process the idea has earned.

---

## The 5-Phase Idea Sizing State Machine

```
  [Phase 1: Intent Scoping & Three-Path Classification (Spike/Bounded/Arch)]
                               │
                               ▼
  [Phase 2: Vault & Codebase Knowledge Grounding (L1 -> L0)]
                               │
                               ▼
  [Phase 3: Socratic Dialogue & Dual-Lens Trade-Off Matrix (UX vs Tech)]
                               │
                               ▼
  [Phase 4: Spec Generation & Self-Review (Zero TBD Check)]
                               │
                               ▼
  [Phase 5: Handoff Gate (Relay to /dfs-plan)]
```

---

## Phase 1: Intent Scoping & Three-Path Classification
Classify the task upfront and announce it:
- **Spike** (Feasibility question): "Can we / what is the cost / quick probe". Present probe plan in 2-3 sentences, get nod, investigate, report recommendation. No spec doc.
- **Bounded** (Scoped tweak to existing code): Clarify questions, present 2-3 paragraph design in chat, get explicit approval, then proceed without plan doc.
- **Architectural** (New feature / subsystem / restructuring): Full process (Phase 2 to Phase 5).
- **Checkable Completion Criterion**:
  - Classification announced with justification; user confirms scope before proceeding.

---

## Phase 2: Vault & Codebase Knowledge Grounding
1. Query `omni_search(query, scope='ladder')` to check if similar problems were already solved in `08-Projects/` or `01-Rules/`.
2. Inspect codebase dependencies and standard library capabilities to ground ideation in reality.
3. **Checkable Completion Criterion**:
   - `omni_search` executed or codebase dependencies checked; prior art or existing patterns cited.

---

## Phase 3: Socratic Dialogue & Dual-Lens Trade-Off Matrix

### Step 0: User Value & Journey Validation (`SUBAGENT-PRODUCT-UX` Lens)
Before discussing technical implementation, validate:
1. **Real Problem vs Imaginary Need**: Who is the target user? In what exact scenario will they use this? What is the cost of doing nothing?
2. **Core User Journey**: What are the minimal steps (<= 3 steps) to reach value (Time-to-Value)? Where are potential friction points?

### Step 1: Technical & Architectural Trade-offs
Propose **2 to 3 distinct approaches** with explicit trade-offs:
- **Option A (Minimalist)**: Lowest complexity, zero-dependency, standard library first.
- **Option B (Domain-Native)**: Deep integration with existing project engines.
- **Option C (Extensible)**: Pluggable architecture for future multi-tenant growth.
- **Checkable Completion Criterion**:
  - Trade-off matrix rendered comparing A/B/C across complexity, operational cost, and YAGNI risk; user selection recorded.

---

## Phase 4: Spec Generation & Self-Review
On user approval of the approach:
1. Generate design document: `docs/specs/YYYY-MM-DD-<topic>-design.md` (or `08-Projects/{project}/`).
2. Load and follow the design specification schema defined in `templates/spec-template.md` via `read_file(path='templates/spec-template.md')`.
3. **Required Schema**:
   - `1. Problem Statement & User Value` (Why build this, target scenario)
   - `2. User Journey & Core Flow` (Step-by-step user interaction & feedback)
   - `3. Architecture & Data Models` (Components, types, persistence)
   - `4. Edge Cases & Resilience` (Network drops, race conditions, error boundaries)
   - `5. Test Strategy` (Unit tests, integration scenarios)
4. Spec Self-Review: Check for zero "TODO/TBD" placeholders, contradictions, or scope creep.
5. **Checkable Completion Criterion**:
   - Design spec written to disk; zero `TODO`/`TBD` occurrences; all 5 schema sections populated.

---

## Phase 5: Handoff Gate (Relay to /dfs-plan)
Prompt user:
`Design spec ready and approved. Ready to generate implementation plan via /dfs-plan?`
Auto-relay to `/dfs-plan` upon confirmation.
- **Checkable Completion Criterion**:
  - Human partner explicit approval received; target plan file path confirmed for `/dfs-plan`.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"The idea is obvious, so I'll jump straight to scaffolding code."* | **Speculative Architecture & Rework**: Coding without an agreed design wastes time on misaligned assumptions. | Stop at Phase 1/4. Never write production code until spec receives human approval. |
| *"I'll add flexible abstractions now in case we need Kafka or GraphQL later."* | **Premature Complexity (YAGNI Violation)**: Over-engineered designs introduce maintenance burden for unused features. | Propose Minimalist Option A first; enforce Ladder of Reuse against stdlib. |
| *"The user asked a simple probe question, so I'll write a full 200-line spec."* | **Process Bureaucracy**: Over-processing small spikes stalls exploration velocity. | Honor the Three-Path Classification: Spikes need 2-3 sentence probe plans, not spec docs. |
| *"I left some edge cases as TBD in the spec to figure out during coding."* | **Fog of War Trap**: Unresolved architectural questions explode into blocking bugs during execution. | Spec MUST contain zero TODO/TBD markers; resolve or explicitly scope out before handoff. |

## 🧪 Worked example — classification decides the process

Input A: *"Can we cut cold-start below 200 ms?"* -> Phase 1 classifies this a **Spike** (a
feasibility / cost question): present a 2-3 sentence probe plan, get a nod, investigate, report — no
spec document.

Input B: *"We want a pluggable storage layer."* -> **Architectural**: full Phase 2-5. Phase 3, Step 1
trade-off matrix:

| Option | Complexity | Startup cost | Verdict |
|---|---|---|---|
| A. Minimalist: stdlib `dbm` only | lowest | none | rejected — no query support |
| B. Domain-Native: reuse the existing SQLite engine | medium | reuses the existing open path | **chosen** |
| C. Extensible: pluggable driver registry | highest | none | rejected — YAGNI at one backend |

Chosen **B**: the repo already opens SQLite, and a driver registry would have exactly one member.

Its mirrored output — the approved spec head — is:

```
# Design Specification: Pluggable Storage Layer

**Date**: 2026-09-28
**Status**: APPROVED
**Target Path**: `docs/specs/2026-09-28-storage-layer-design.md`

## 1. Problem Statement & User Value
- Why build this: one backend today, a second is planned for next quarter.
- Target Scenario & Persona: the platform engineer wiring storage per environment.
- Cost of Doing Nothing: each environment keeps a bespoke, untested adapter.

## 2. User Journey & Core Flow
1. Set `storage.driver` -> the loader resolves the backend
2. Write a record -> the configured driver persists it
3. Read it back through the same interface -> value achieved
```
