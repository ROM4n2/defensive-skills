---
name: dfs-spark
description: Generate a design specification from a fuzzy need through Dual-Lens dialogue, at a size the idea earns. Use when the user has an idea with no design yet and wants it shaped into a spec, a short design note, or a feasibility answer.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - brainstorming
    - idea-sizing
    - design-spec
    - dual-lens
    - product-ux
    related_skills:
    - dfs-plan
    - dfs-grill
    - dfs-adr
    - dfs-exec
    mcp_tools:
    - omni_search
---


# DFS-SPARK: Idea Sizing & Exploratory Design

Turn vague ideas, open-ended feature thoughts, or fuzzy developer needs into structured, knowledge-grounded design specifications through collaborative dialogue across **Dual Lenses: User Problem Validation + Technical Architecture**.

## The Spec-First Invariant (RFC 2119 MUST)
> Do NOT invoke implementation skills, write code, or scaffold repositories until presenting the spec and obtaining human partner approval.

---

## This skill, or /dfs-grill?
- No design yet: start here to **generate** a spec, note, or feasibility spike.
- Proposal exists and needs edges interrogated/forced to a choice: hand off to **`/dfs-grill`** (ADR output).

---

## The 5-Phase Idea Sizing State Machine

`Phase 1: Classification` -> `Phase 2: Grounding` -> `Phase 3: Socratic Dialogue` -> `Phase 4: Spec Generation` -> `Phase 5: Handoff Gate`

---

## Phase 1: Intent Scoping & Three-Path Classification
Classify the task upfront and announce it:
- **Spike**: Present probe plan in 2-3 sentences, get nod, investigate, report recommendation (no spec doc).
- **Bounded**: Clarify questions, present 2-3 paragraph design in chat, get approval, proceed without plan doc.
- **Architectural**: Full process (Phase 2 to Phase 5). Done when classification confirmed by user.

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
- **Agent & Harness Architecture Guardrails (when designing AI agents/RAG/tools)**: Enforce the 11-system empirical baselines — native concurrency loop over black-box agent frameworks, deterministic AST/ripgrep over source-code vector RAG, bit-perfect prefix caching, and deferred loading (`tool_search`) above 15 tools. Load [references/agent-harness-and-sizing-examples.md](references/agent-harness-and-sizing-examples.md) §1.
- **Checkable Completion Criterion**:
  - Trade-off matrix rendered comparing A/B/C across complexity, operational cost, and YAGNI risk; user selection recorded.

---

## Phase 4: Spec Generation & Self-Review
On approval of the approach:
1. Generate `docs/specs/YYYY-MM-DD-<topic>-design.md` following schema in `templates/spec-template.md` (`Problem Statement`, `User Journey`, `Architecture`, `Edge Cases`, `Test Strategy`).
2. Self-Review: Check for zero `TODO`/`TBD` placeholders, contradictions, or scope creep. Done when all 5 schema sections populated.

---

## Phase 5: Handoff Gate (Relay to /dfs-plan)
Prompt user:
`Design spec ready and approved. Ready to generate implementation plan via /dfs-plan?`
Auto-relay to `/dfs-plan` upon confirmation.
- **Checkable Completion Criterion**:
  - Human partner explicit approval received; target plan file path confirmed for `/dfs-plan`.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"The idea is obvious, so I'll jump straight to scaffolding code."* | **Speculative Architecture & Rework**: Coding without an agreed design wastes time on misaligned assumptions. | Stop at Phase 1/4. Never write production code until spec receives human approval. |
| *"I'll add flexible abstractions now in case we need Kafka or GraphQL later."* | **Premature Complexity (YAGNI Violation)**: Over-engineered designs introduce maintenance burden for unused features. | Propose Minimalist Option A first; enforce Ladder of Reuse against stdlib. |
| *"The user asked a simple probe question, so I'll write a full 200-line spec."* | **Process Bureaucracy**: Over-processing small spikes stalls exploration velocity. | Honor the Three-Path Classification: Spikes need 2-3 sentence probe plans, not spec docs. |
| *"I left some edge cases as TBD in the spec to figure out during coding."* | **Fog of War Trap**: Unresolved architectural questions explode into blocking bugs during execution. | Spec MUST contain zero TODO/TBD markers; resolve or explicitly scope out before handoff. |

## Worked Example
For worked classification and sizing examples (Spike vs Bounded vs Architectural storage layer), load [references/agent-harness-and-sizing-examples.md](references/agent-harness-and-sizing-examples.md) §2.
