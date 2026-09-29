# MCP Contract — `coding-vault-search`

DFS skills talk to the knowledge base through the `coding-vault-search` MCP server. This file is
the single source of truth for which tools exist and what each is for.

A skill declares the tools it may call in its frontmatter:

```yaml
metadata:
  hermes:
    mcp_tools: [search_vault, get_rule_snippet]
```

Conformance Rule 9 rejects any declared name outside the canonical set below. Declaring the
contract is what keeps the skill honest: a tool that disappears from the server breaks the gate
loudly instead of failing silently at runtime.

## Canonical tool set

| Tool | Purpose | Typical caller |
|---|---|---|
| `search_vault` | Keyword retrieval over the Vault (rules, pitfalls, templates) | `dfs-save`, `dfs-debug`, `dfs-onboard` |
| `omni_search` | Escalation-gateway retrieval across all Vault tiers | `dfs-plan`, `dfs-spark`, `dfs-grill` |
| `get_note` | Read one note by relative Vault path | `dfs-onboard`, `dfs-review` |
| `get_rule_snippet` | Pull one section of a rules file (token-cheap JIT slice) | `dfs-review`, `dfs-refactor` |
| `get_code_template` | Extract a pure production code template by name + language | `dfs-plan`, `dfs-tdd` |
| `list_standards` | Enumerate available standards, rules, and interview material | `dfs-onboard`, `dfs-plan` |
| `save_inbox_draft` | Write a draft into `99-Inbox/` (must satisfy the A-MAC gate — see `dfs/references/a-mac-gate.md`) | `dfs-save`, `dfs-debug` |
| `promote_inbox_draft` | Promote an `99-Inbox/` draft into its destination directory | `dfs-inbox-consolidate` |
| `vault_proactive_scan` | Scan a project for unresolved TODOs and debt | `dfs-onboard`, `dfs-research` |

## Rules

1. **MUST** declare in `mcp_tools` every tool the skill actually calls. An undeclared call is a
   contract violation even when the tool exists.
2. **MUST NOT** invent a tool name. If the capability is missing, say so and fall back to
   `read_file` over a resolved `{vault_root}` path instead of guessing a tool name.
3. **MUST** prefer local retrieval over web retrieval. Order of escalation:
   `search_vault` → `omni_search` → `get_note`/`get_rule_snippet` → external web search.
4. **MUST NOT** hardcode rule text that a tool can retrieve. Rules live in the Vault; the skill
   retrieves the current version so it cannot drift out of date.

## Retrieval escalation ladder

```
Question about local conventions?
  ├── Known keyword, narrow scope        → search_vault(query)
  ├── Broad / cross-cutting theme        → omni_search(query, scope='ladder')
  ├── Need one specific rule section     → get_rule_snippet(rule, section)
  ├── Need a whole note verbatim         → get_note(relative_path)
  └── Need a language idiom / template   → get_code_template(name, language)
                │
                └── Nothing in the Vault answers it? → external web search (see dfs-research)
```
