# dfs-grill — extended playbook (tier 3)

Loaded on demand by `dfs-grill/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

### Stage 1: Dual-Lens Background Inquest (Parallel Fan-out)
When the proposal is complex enough that background research pays for itself, dispatch the relevant seats concurrently across specialists.
- **Dispatch one subagent per lens, runtime-neutrally**: `delegate_task` is the portable path; `subagent_type` is the optional Claude Code fallback. The variants and the `subagent_type` rule live in `dfs/references/subagent-dispatch.md`.

| Lens | Subagent Role (`subagent_type`) | Grills on |
|---|---|---|
| Product & UX | `product-ux` | Real pain vs imagined need, journey friction, mental model, human-readable failure |
| Frontend & State | `frontend-architect` | State machine consistency, async races, offline/reconnect, render cost |
| Backend & Concurrency | `code-reviewer` | Thread/goroutine lifecycle, lock scope, transaction boundaries, silent errors |
| Storage & DBA | `dba-optimizer` | Schema shape, index coverage, query cost, lock ordering |
| SRE & Resilience | `sre-resilience` | Downstream timeouts, retries, failure modes, resource bounds |

**`subagent_type` names the base agent only** — this lens's job is its Grills-on column, and `code-reviewer` here runs a concurrency review, not the Red/Yellow protocol. See `dfs/references/subagent-dispatch.md`.

**Only dispatch the lenses the proposal actually touches.** For a small or purely local design decision, skip Stage 1 entirely and go straight to Stage 3 — a five-agent panel on a two-file change is theatre, and the specialists will manufacture findings to justify their seat.
- **Checkable Completion Criterion**:
  - Relevant specialist lenses dispatched; seat findings received or explicit skip justified based on proposal scope.

### Stage 2: Context Ingestion & The Ladder of Reuse
Query `omni_search(proposal, scope='ladder')` to challenge against **The Ladder of Reuse (RFC 2119 MUST)**:
- **Level 0 (YAGNI / User Value)**: Does this feature actually solve a real user problem?
- **Level 1 (Stdlib/Existing Code)**: Does standard library or existing codebase already have a 3-line solution?
- **Level 2 (Existing Dependencies)**: Can existing libraries satisfy this without adding new dependencies?
- **Checkable Completion Criterion**:
  - `omni_search` query executed; Ladder of Reuse evaluation recorded against stdlib and existing modules.

### Stage 2.5: Known Defect Class Interrogation (MUST — 四类已知缺陷)
Before synthesizing frontier questions, run these four against the proposal. They are not
hypothetical: four consecutive milestones each shipped exactly one real defect from one of
these classes, and every one of them had passed a green test suite.

| # | Class | The question to ask | Field evidence |
|---|---|---|---|
| 1 | **Error-classification width** | Which failures in this catch/handler are *permanent* and which are *retryable*? What does the retrying side actually read — a code, or a message nobody prints? | `except Exception -> 503` turned "empty model spec" and "index out of range" into "try again later"; the Go side read only the code, the service logged nothing, so the misconfiguration had **no landing point anywhere on the chain**. |
| 2 | **Cancelled-context teardown** | On the cancel/abort path, which context does the *closing write* use? | Passing an already-cancelled `ctx` to the final status write: `database/sql` checks `ctx.Done()` **before** acquiring a connection, so the UPDATE is never sent. The job stayed `running` forever and the `canceled` branch was dead code. |
| 3 | **Progress semantics** | Is this number "what this run did" or "the absolute state"? Does it still answer the question after a *resume* and after a *no-op run*? | Per-run counters recorded `0/0` for a conversation that was already fully scored, and "24% done" for one that had just finished. Absolute coverage is the only number that answers "how far along?" in both cases. |
| 4 | **One rule, two implementations** | How many places implement this rule? Can they drift, and which one do the tests pin? | A threshold was implemented twice: one side treated the exact boundary as neutral, the other as a verdict — and the mutation test pinned only one of them. The result was a silent polarity inversion waiting for the right input. |

- **Checkable Completion Criterion**: each of the four classes is either answered in the design or explicitly recorded as not applicable with a reason.

### Stage 3: Frontier Round Protocol (Tight Socratic Rounds)
Synthesize the specialists' findings into tight, numbered questions:

```markdown
[?] **Q1 - <Product & User Experience Decision>**: <Socratic question body exposing user journey friction or value assumptions>
  - Option A: [Minimalist/High-Value approach]
  - Option B: [Feature-rich approach]

->️ **Recommended**: Option A — [Concise justification on user value & simplicity]

---

[?] **Q2 - <Technical Architecture Decision>**: <Question about failure recovery, concurrency, or data consistency>

->️ **Recommended**: [Concrete defense strategy]
```

Recompute the frontier on each user reply. Stop when every frontier point carries a chosen option in the draft: a point that still has an open question and no chosen option *is* the frontier, so the cone is closed only when none remain.
- **Checkable Completion Criterion**:
  - Socratic questions formulated with `->️ Recommended` options; user answers received closing the frontier cone.

### Stage 4: Consensus & ADR Archiving
Summarize consensus into a formal **Architecture Decision Record (ADR-000x)**:
- Context, Decision Drivers (both User & Tech), Considered Options, Pros/Cons, Decision Outcome, and Consequences.
- Dual-Track Ingestion Gate:
  - Option 1: Draft in `99-Inbox/`
  - Option 2: Direct promotion to `08-Projects/{project}/01-ADR/` or `01-Rules/`.
- **Checkable Completion Criterion**:
  - ADR document physically written with resolved sequential number; consensus decisions locked.

---
