---
name: dfs-spark
description: Turn 0-to-1 ideas into specs through Dual-Lens dialogue. Use when the user has a rough idea and wants to shape it into a written spec.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [brainstorming, 0-to-1, design-spec, dual-lens, product-ux]
    related_skills: [dfs-plan, dfs-grill, dfs-adr, dfs-exec]
    mcp_tools: [omni_search]
---

# DFS-SPARK: 0-to-1 Feature Ideation & Exploratory Design

Turn vague ideas, open-ended feature thoughts, or fuzzy developer needs into structured, knowledge-grounded design specifications through collaborative dialogue across **Dual Lenses: User Problem Validation + Technical Architecture**.

## The Iron Gate (HARD GATE)
Do NOT invoke any implementation skill, write production code, or scaffold repositories until presenting the design spec and obtaining explicit human partner approval.

---

## Phase 1: Intent Scoping & Three-Path Classification
Classify the task upfront and announce it:
- **Spike** (Feasibility question): "Can we / what is the cost / quick probe". Present probe plan in 2-3 sentences, get nod, investigate, report recommendation. No spec doc.
- **Bounded** (Scoped tweak to existing code): Clarify questions, present 2-3 paragraph design in chat, get explicit approval, then proceed without plan doc.
- **Architectural** (New feature / subsystem / restructuring): Full process (Phase 2 to Phase 5).

---

## Phase 2: Vault & Codebase Knowledge Grounding
1. Query `omni_search(query, scope='ladder')` to check if similar problems were already solved in `08-Projects/` or `01-Rules/`.
2. Inspect codebase dependencies and standard library capabilities to ground ideation in reality.

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

---

## Phase 5: Handoff Gate (Relay to /dfs-plan)
Prompt user:
`Design spec ready and approved. Ready to generate implementation plan via /dfs-plan?`
Auto-relay to `/dfs-plan` upon confirmation.

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
