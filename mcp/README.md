# Knowledge-base MCP server

`knowledge_server.py` is a stdio JSON-RPC MCP server implemented with the Python standard library.

## Register

Point `--root` at your Markdown knowledge base.

```jsonc
{
  "mcpServers": {
    "coding-vault-search": {
      "command": "python",
      "args": ["<repo>/mcp/knowledge_server.py", "--root", "<knowledge-root>"]
    }
  }
}
```

Smoke test:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | python mcp/knowledge_server.py --root "<knowledge-root>"
```

The canonical tool set is checked by `tests/test_knowledge_server.py`.

## Root resolution

| Order | Source |
|---|---|
| 1 | `--root <path>` |
| 2 | `$WIKI_PATH`, then `$OBSIDIAN_VAULT_PATH` |
| 3 | Upward search for `AGENTS.md` or `.obsidian/` |
| 4 | Drafts-only mode: `$DFS_INBOX` if set, otherwise `<cwd>/.dfs-inbox` |

Rules:

- An invalid explicit root exits 2; it does not become a drop box.
- Retrieval tools refuse when no knowledge base is configured. They do not report a false “no matches”.
- `save_inbox_draft` writes to the drop box and reports its absolute path.

Optional `knowledge.json` overrides directory names. Unknown keys are rejected.

## File-level equivalents

MCP is optional. Use these operations instead when it is unavailable.

| Tool | File-level operation |
|---|---|
| `search_vault` | Search keywords under `{vault_root}` |
| `omni_search` | Search locally, then upstream docs, then the web |
| `get_note` | Read `{vault_root}/<relative-path>` |
| `get_rule_snippet` | Read only the required section of a rules file |
| `get_code_template` | Read the requested template |
| `list_standards` | Find `*-STANDARDS.md` and `*-CHEATSHEET.md` |
| `save_inbox_draft` | Write the draft with required frontmatter to the configured inbox |
| `promote_inbox_draft` | Write the destination, verify it, then remove the original |
| `vault_proactive_scan` | Search for `TODO`, `FIXME`, `HACK`, and `WORKAROUND` |

Do not invent replacement tool names. Apply the A-MAC admission rules when writing drafts yourself.

## Current limits

- Retrieval uses weighted keyword, tag, and heading scoring, not BM25 or a graph.
- `vault_proactive_scan` is a regex scanner, not an AST analyzer.
- The server is not required for local file access or draft-only operation.

## Test

```bash
python tests/test_knowledge_server.py
```
