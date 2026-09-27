# Research Brief Schema

The deliverable of `dfs-research`. Every section is mandatory; write `None found` rather than
deleting a section.

```markdown
---
created: YYYY-MM-DD
type: source-notes
status: draft
tags: [research/<topic>, evidence/<tier-mix>]
source: external-research
question: "<one falsifiable sentence>"
---

# {Title}

## 1. Question & Scope
- **Question**: {restated as one falsifiable sentence}
- **In scope**: {what was searched}
- **Out of scope**: {what was deliberately excluded}
- **Version pin**: {vendor/product version or access date}

## 2. Answer
{Direct answer in 1-3 sentences. If it cannot be answered, say so plainly.}

## 3. Claims & Evidence

| # | Claim | Tier | Locator | Version/Date |
|---|---|---|---|---|
| 1 | {claim} | A / B / C | {URL, file:line, or note path} | {pin} |
| 2 | {claim} | UNVERIFIED | {blocker description} | — |

## 4. Conflicts & Gaps
- **Conflicts**: {source A says X, source B says Y — both reported, neither silently chosen}
- **Gaps**: {what could not be retrieved and why}

## 5. Internal Cross-Reference
- Vault notes consulted: `{note paths}`
- Overlap verdict: {new topic / extends existing note `<path>` / duplicate}

## 6. Distilled Rule (optional)
{If the finding generalises beyond this question, state the one-line defensive rule it implies.
Otherwise write "Not applicable".}

## 7. Deterministic Evaluation Signals
- Retrieval calls made: {internal N / external M}
- Claims by tier: A={a} B={b} C={c} UNVERIFIED={u}
- Blockers encountered: {list or None}
```
