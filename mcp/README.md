# Knowledge-base MCP server

`knowledge_server.py` is a **stdio JSON-RPC MCP server, standard library only**. It gives the DFS
skills their knowledge layer: retrieval, note reads, rule slicing, code templates, draft capture,
draft promotion, and project debt scanning.

The nine tool names are a **contract**, not an implementation detail. Skills declare the tools they
may call in `metadata.hermes.mcp_tools`, and Conformance Rule 9 rejects any name outside the
canonical set. The server's `tools/list` is asserted equal to that set by
`tests/test_knowledge_server.py`, so the two cannot drift apart unnoticed.

## Register it

Point `--root` at **your** markdown knowledge base. The same server serves any directory tree of
markdown notes; nothing here is tied to a particular vault.

```jsonc
// Claude Code (settings) / Codex / Cursor (mcp.json) — shape varies slightly per harness
{
  "mcpServers": {
    "coding-vault-search": {
      "command": "python",
      "args": ["<repo>/mcp/knowledge_server.py", "--root", "<your knowledge root>"]
    }
  }
}
```

Smoke test without a harness:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | python mcp/knowledge_server.py --root "<your knowledge root>"
```

## Root resolution

Same contract as the skills use (`dfs/references/vault-root-resolution.md`):

1. `--root <path>`
2. `$WIKI_PATH`, then `$OBSIDIAN_VAULT_PATH`
3. Upward search from the current directory for `AGENTS.md` or `.obsidian/`
4. **Drafts-only mode** — the server still starts, and `save_inbox_draft` writes to a local drop
   box (`$DFS_INBOX`, else `<cwd>/.dfs-inbox`), which is created on first use with a `README.md`
   that explains itself. Every retrieval tool refuses with a message naming the missing root.

Two rules keep step 4 from turning into the silent wrong answer that the private original's
hardcoded absolute fallback was:

* **A root you named is never second-guessed.** `--root /typo` exits 2; it does not quietly become
  a drop box. Same for a found root whose `knowledge.json` is broken — that is a config error.
* **Retrieval refuses instead of answering "nothing found."** A drop box is not a knowledge base,
  and "no matches" must never look the same as "no knowledge base wired up."

The drop box is deliberately *not* a directory like `docs/` — that name belongs to a real project
already, and agent drafts landing in someone's documentation tree are indistinguishable from
content afterwards.

## Layout (not assumed)

Defaults match the layout the DFS skills were written against. Override any of it with an optional
`knowledge.json` at the knowledge root — unknown keys are rejected rather than ignored:

```json
{
  "content_dirs": ["notes", "rules", "inbox"],
  "rules_dir": "rules",
  "languages_dir": "standards",
  "career_dir": "career",
  "inbox_dir": "inbox",
  "code_template_dir": "templates/code",
  "prompts_dir": "tools/subagents"
}
```

```bash
python tests/test_knowledge_server.py        # 22 end-to-end tests, temp knowledge root
```

## When the MCP server is unavailable

The server is an accelerator, not a precondition. Every capability has a file-level equivalent —
skills MUST degrade to these rather than invent a tool name (contract rule 2) or abandon the
knowledge step. Resolve `{vault_root}` first, then:

| Tool | File-level fallback |
|---|---|
| `search_vault` | `search_files` (ripgrep) for the keywords across `{vault_root}` |
| `omni_search` | the same search; on a miss, escalate per the ladder (local code → upstream docs → web) |
| `get_note` | `read_file` on `{vault_root}/<rel_path>` |
| `get_rule_snippet` | `read_file` the rules file, then use only the matching `##` section — never paste the whole file |
| `get_code_template` | `read_file` the template file under the templates dir |
| `list_standards` | `search_files` for `*-STANDARDS.md` / `*-CHEATSHEET.md` under the languages dir |
| `save_inbox_draft` | `write_file` to `{vault_root}/<inbox_dir>/YYYY-MM-DD-<slug>.md` with the frontmatter documented below — or, with no root at all, to `$DFS_INBOX` / `.dfs-inbox/` in the working directory, and then **say the absolute path in your output** |
| `promote_inbox_draft` | `read_file` the draft, `write_file` it to the destination with `status: stable`, then delete the draft |
| `vault_proactive_scan` | `search_files` for `TODO|FIXME|HACK|WORKAROUND` across the project |

The **A-MAC admission gate is normative, not server-enforced**: without the server the agent applies
it itself. Reject a draft whose title is shorter than 4 characters, whose body is shorter than 30
characters, or which is a throwaway scratch record — the gate exists to stop noise from entering
the knowledge base, and it does not stop being true just because a tool is missing.

**Whatever the path, say where the draft went.** The whole point of the drop box is that a draft
written with no configuration is still findable later; a draft announced as "saved" without a path
is one the user will never see again.

## Deliberate ceilings

Documented in the module docstring, repeated here so they are not mistaken for parity:

* `search_vault` is a weighted keyword/tag/heading scorer, not the private original's BM25 + graph
  retriever. Fine at note scale; swap in a real ranker past ~10k notes.
* `omni_search`'s L0 rung names your harness's own code search instead of probing for a specific
  external binary, so it stays harness-agnostic.
* `vault_proactive_scan` is a regex debt scanner, not an AST analyser with ROI scoring.
