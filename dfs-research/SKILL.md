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

**Core invariant (Anti-Fabrication):** every claim in the output carries a source tier and a
resolvable locator, or it is explicitly marked `UNVERIFIED`. When a fact cannot be retrieved,
write `UNVERIFIED` and say so — never fill the gap with a plausible guess.

**Scope detection:** resolve `{vault_root}` per `dfs/references/vault-root-resolution.md` before
touching any Vault path.

---

## Phase 0 — Frame the Question (HITL)

Restate the request as one falsifiable sentence and name what would count as an answer.
Ask the human to confirm scope when the answer changes which sources count (internal only vs
external, one vendor vs comparative, version-pinned vs latest). Otherwise proceed.

Tag the run:
- `[HITL]` — the scope decision or a paywalled/ambiguous source needs a human.
- `[AFK]` — a bounded retrieval loop that runs unattended.

## Phase 1 — Internal First (MCP)

Retrieve from the Vault before spending a single web request. Escalation ladder
(see `dfs/references/mcp-contract.md`):

```
search_vault(query)                      → narrow, known keyword
omni_search(query, scope='ladder')       → broad or cross-cutting theme
get_note(relative_path)                  → one note verbatim
get_rule_snippet(rule, section)          → one rule section, token-cheap
```

Stop as soon as the Vault answers the question. Record which notes answered it — those become
`INTERNAL` citations and they outrank every external source.

## Phase 2 — External Retrieval

Only reach outside for what the Vault could not answer. Prefer in this order:

1. **Primary artifacts** — official documentation, source code, language specs, RFCs.
2. **Authoritative discussion** — maintainer write-ups, release notes, accepted proposals.
3. **Community material** — forums, blog posts, issue threads.

Fetch with the runtime's web tool. When a page is blocked, paywalled, or bot-walled, apply the
`blocked-page-recovery` skill rather than reporting failure — and if it still fails, mark the
claim `UNVERIFIED` with the blocker described.

Pin the version or date for every external claim. An unpinned claim about a moving target is a
future bug.

## Phase 3 — Grade Evidence

Assign every claim exactly one tier:

| Tier | Meaning | Requirement |
|---|---|---|
| `A` | Primary artifact | Direct quote or code excerpt + locator |
| `B` | Authoritative secondary | Named author/organisation + locator |
| `C` | Community material | Locator + explicit note that it is unverified by the vendor |
| `UNVERIFIED` | Not retrieved | State the blocker; never present it as fact |

Cross-check: when two sources conflict, report both and mark the conflict. Do not silently pick
the one that reads better.

## Phase 4 — Sink into the Vault

Compose the finding with `templates/research-brief.md`, then hand it to the ingestion path:

- `search_vault(query=<topic>)` first — if a note already covers it, propose an update instead
  of creating a duplicate.
- `save_inbox_draft(title=..., content=..., tags=...)` to land it in `{vault_root}/99-Inbox/`.
- Promotion to a permanent directory is `dfs-inbox-consolidate`'s job, not this skill's.

Report back with: the question, the tier breakdown, the count of claims per tier, and any
`UNVERIFIED` items listed explicitly.

## Instincts (compile-time)

- `[Instinct: Anti-Fabrication]` — a claim without a locator is `UNVERIFIED`, not a finding.
- `[Instinct: Internal-First]` — every external request must be preceded by a Vault query.
- `[Instinct: Version-Pin]` — an unpinned claim about a moving target MUST be pinned or dropped.
