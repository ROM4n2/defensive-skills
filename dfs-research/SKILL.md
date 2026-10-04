---
name: dfs-research
description: Research external sources and sink findings into the Vault. Use when the user asks to investigate a topic and record what was learned.
version: 0.1.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, retrieval, web-search, evidence-grading, citation]
    related_skills: [dfs-inbox-consolidate, dfs-spark, dfs-grill]
    mcp_tools: [search_vault, omni_search, get_note, get_rule_snippet, save_inbox_draft]
---

# DFS-Research: Evidence-Graded External Retrieval

Turn an open question into a graded, cited knowledge artifact, then sink it into the Vault.

## 🚨 The Anti-Fabrication Invariant (RFC 2119 MUST)
> **Every claim in the research deliverable MUST carry a verifiable source tier (A/B/C) and a resolvable locator (URL, file:line, or RFC citation), or it is explicitly marked `UNVERIFIED`.**
> When a fact cannot be retrieved, write `UNVERIFIED` and describe the blocker — NEVER fill the gap with plausible-looking hallucinated claims.

**Scope detection:** resolve `{vault_root}` per `dfs/references/vault-root-resolution.md` before touching any Vault path.

---

## The 5-Phase Evidence-Graded Research Loop

```
  [Phase 0: Frame Question & Falsifiable Criterion (HITL/AFK)]
                                │
                                ▼
  [Phase 1: Internal First — Vault Escalation Ladder]
                                │
                                ▼
  [Phase 2: External Retrieval & Blocked Page Recovery]
                                │
                                ▼
  [Phase 3: Evidence Grading (Tier A/B/C/UNVERIFIED)]
                                │
                                ▼
  [Phase 4: Sink to Vault (A-MAC Gate -> 99-Inbox/)]
```

### Phase 0 — Frame the Question (HITL)
Restate the request as one falsifiable sentence and name what would count as an answer.
Ask the human to confirm scope when the answer changes which sources count (internal only vs external, one vendor vs comparative, version-pinned vs latest). Otherwise proceed.
Tag the run:
- `[HITL]` — the scope decision or a paywalled/ambiguous source needs a human.
- `[AFK]` — a bounded retrieval loop that runs unattended.
- **Checkable Completion Criterion**:
  - Scope articulated as a single falsifiable sentence; execution mode tagged (`[HITL]` or `[AFK]`).

### Phase 1 — Internal First (MCP)
Retrieve from the Vault before spending a single web request. Escalation ladder (see `dfs/references/mcp-contract.md`):
```
search_vault(query)                      → narrow, known keyword
omni_search(query, scope='ladder')       → broad or cross-cutting theme
get_note(relative_path)                  → one note verbatim
get_rule_snippet(rule, section)          → one rule section, token-cheap
```
Stop as soon as the Vault answers the question. Record which notes answered it — those become `INTERNAL` citations and outrank external sources.
- **Checkable Completion Criterion**:
  - MCP query executed; local matches cited, or absence explicitly logged before escalating to web.

### Phase 2 — External Retrieval
Only reach outside for what the Vault could not answer. Prefer in this order:
1. **Primary artifacts** — official documentation, source code, language specs, RFCs.
2. **Authoritative discussion** — maintainer write-ups, release notes, accepted proposals.
3. **Community material** — forums, blog posts, issue threads.
Fetch with the runtime's web tool. Pin the version or date for every external claim.
- **Checkable Completion Criterion**:
  - External fetches recorded with exact URLs and version/date stamps.

### Phase 3 — Grade Evidence
Assign every claim exactly one tier:
| Tier | Meaning | Requirement |
|---|---|---|
| `A` | Primary artifact | Direct quote or code excerpt + locator |
| `B` | Authoritative secondary | Named author/organisation + locator |
| `C` | Community material | Locator + explicit note that it is unverified by the vendor |
| `UNVERIFIED` | Not retrieved | State the blocker; never present it as fact |
Cross-check: when two sources conflict, report both and mark the conflict.
- **Checkable Completion Criterion**:
  - Claims cataloged into Tier A/B/C; zero unverified claims presented as verified facts.

### Phase 4 — Sink into the Vault
Compose the finding with `templates/research-brief.md`, then hand it to the ingestion path:
- `search_vault(query=<topic>)` first — if a note already covers it, propose an update instead of creating a duplicate.
- `save_inbox_draft(title=..., content=..., tags=...)` to land it in `{vault_root}/99-Inbox/`.
- **Checkable Completion Criterion**:
  - Research brief generated; `save_inbox_draft` returns draft path in `99-Inbox/` passing A-MAC gate.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I already know this library's API from memory, so I don't need to search."* | **Knowledge Cutoff & API Drift**: LLMs misremember deprecated methods and subtle parameter changes. | Always verify API claims against current primary docs (Tier A) or local rules before asserting. |
| *"A blog post described this workaround, so I will present it as best practice."* | **Cargo Cult Solutions**: Unofficial community blog posts often contain anti-patterns or insecure hacks. | Label community posts as Tier C; prioritize official docs and language RFCs (Tier A/B). |
| *"Web search returned nothing useful, so I will synthesize a plausible hypothesis."* | **Hallucination Contamination**: Fabricating answers poisons downstream design decisions. | If unretrieved, mark explicitly as `UNVERIFIED` with blocker explanation. Never synthesize. |
| *"This topic is broad, so I will write a 1,000-line omnibus overview."* | **Context Bloat & Signal Loss**: Massive unstructured text dumps overwhelm human partner attention. | Synthesize into structured Research Brief schema with tier breakdown and actionable conclusions. |

## Instincts (compile-time)

- `[Instinct: Anti-Fabrication]` — a claim without a locator is `UNVERIFIED`, not a finding.
- `[Instinct: Internal-First]` — every external request must be preceded by a Vault query.
- `[Instinct: Version-Pin]` — an unpinned claim about a moving target MUST be pinned or dropped.
