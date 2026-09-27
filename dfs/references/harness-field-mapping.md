# Harness field mapping — what actually honors what

The DFS suite was authored on **Hermes Agent**. Two of its frontmatter keys do something in one
harness and nothing in another, and one key is **not a harness feature at all** — it is this
suite's own declaration. Guessing here is how a safety intent silently disappears, so every claim
below is tied to a source you can re-run.

**Rule: never assume a key is honored. Look it up. If a harness ignores the key, use the lever
named in its row — the safety property must be enforced somewhere.**

## 1. Portable core — every skill carries it, everyone survives it

Present on all 23 skills; each harness either reads it or ignores it without harm.

| Key | Hermes | Claude Code | Codex CLI / Cursor |
|---|---|---|---|
| `name` | read; must match the directory name | required | no skills subsystem — see §3 |
| `description` | read; drives skill selection | required ("only `description` is recommended so Claude knows when to use the skill") | — |
| `version` | metadata | unknown field → ignored | — |
| `author` | metadata | unknown field → ignored | — |
| `platforms` | read; a skill is hidden on a platform it does not list | unknown field → ignored | — |
| `metadata.hermes.tags` | search/display metadata | ignored | — |
| `metadata.hermes.related_skills` | read (source); checked by Conformance Rule 7 | ignored | — |

## 2. Per-skill extensions — behavior differs, so read the row

| Key | Used by | Hermes | Claude Code | Lever when the harness ignores it |
|---|---|---|---|---|
| `disable-model-invocation: true` (7 skills: router `dfs`, `dfs-bootstrap`, `dfs-handoff`, `dfs-inbox-consolidate`, `dfs-incident`, `dfs-interview`, `dfs-pipeline`) | keep a side-effecting or router skill from being auto-selected | **not implemented** — see the evidence in §4 | honored: "To keep a personal or project skill but stop Claude from invoking it on its own" | Claude Code: set the skill to `"user-invocable-only"` in `skillOverrides`, or say it in prose; any harness: see §2.1 |
| `metadata.hermes.mcp_tools` (9 skills) | **DFS-internal contract**: declares which MCP tools a skill may call, checked by Conformance Rules 9 and 11, and read by an agent to choose the file-level fallback | **no harness support — 0 references in the Hermes source** | ignored | nothing to map: this key is the suite talking to its own gate and to the agent. It is not a switch any runtime flips |
| `metadata.hermes.requires_tools` / `fallback_for_tools` (+ `*_toolsets`) | would be the Hermes-native way to make a skill appear only when a tool exists | read (source) | ignored | not used by DFS today; if a skill ever *needs* a toolset to work, this is the documented mechanism, and ignoring it costs nothing |

**The one that matters:** seven skills rely on a key Hermes does not implement. Nothing breaks —
they still work when invoked — but on Hermes the *prevention* is missing, so auto-selection is
possible. Two of the seven (`dfs-bootstrap`, `dfs-inbox-consolidate`) write into a repository or
move notes, which is exactly why the rule exists.

### 2.1 The gap, stated plainly

**The intent lives only in the key.** Checked, not assumed:

```bash
grep -inE "explicitly invoked|explicit invocation|only when .*explicit" dfs*/SKILL.md   # -> no hits
```

So on a harness that ignores `disable-model-invocation`, nothing at all stops the router or the
repo-bootstrapper from being auto-selected. Three ways to close it, in ascending order of effort:

1. **Do nothing** — acceptable if you only ever run Claude Code, where the key is honored.
2. **Harness-side**: use that harness's own mechanism (Claude Code: `skillOverrides`;
   Hermes: a permission rule or a line in your project rules file).
3. **Portable**: add one line to each of the seven bodies —
   *"Run only on explicit request; this skill must not be auto-selected."* — after which the
   protection travels with the file. This is the only fix that works on a harness that has no
   override mechanism, and it is deliberately **not done yet**: it edits seven production skills,
   so it is a decision, not a cleanup.

## 3. Harnesses with no skills subsystem

Codex CLI and Cursor consume project instruction files, not skill directories:

* **Codex CLI** — `AGENTS.md` at the project root (the same marker DFS already uses to resolve a
  knowledge root, which is why the two compose cleanly). Copy the SKILL.md bodies you want as
  sections, or let the agent read `dfs/<name>/SKILL.md` directly.
* **Cursor** — `.cursor/rules/*.mdc` with its own frontmatter (`description`, `globs`,
  `alwaysApply`); SKILL.md frontmatter is inert there.

In both cases the **body** is the product: the procedure, the checks, and the file-level fallback
table in `mcp/README.md` are harness-neutral. Frontmatter is a Hermes/Claude Code packaging detail.

**Not verified from source here:** cursor.com and agents.md were unreachable from the network this
document was last checked on (TLS handshake failure), so the two rows above come from the published
conventions rather than a fetched spec. Re-fetch before quoting them as normative.

## 4. How to check this yourself

```bash
HERMES_SRC="$LOCALAPPDATA/hermes/hermes-agent"     # git-installed Hermes source; adjust if yours differs

# Hermes: what the loader reads (source, not docs)
grep -rn 'frontmatter\.get("' "$HERMES_SRC/tools/skills_tool.py" "$HERMES_SRC/agent/skill_utils.py"

# Hermes: is disable-model-invocation a Hermes feature at all?
grep -rl "disable-model-invocation" "$HERMES_SRC"    # -> one hit: a test asserting an IMPORTED
                                                     #    Claude Code skill mentions it
# Hermes: is mcp_tools a Hermes feature?
grep -rl "mcp_tools" "$HERMES_SRC"                   # -> no hits

# Claude Code: the fields, their exact-match rule, and the unknown-field behavior
curl -sL https://docs.claude.com/en/docs/claude-code/skills
```

Python gates in this repo that depend on these facts:
`tests/test_harness_field_mapping.py` (every frontmatter key in the tree must appear here, and the
portable-core list must match reality).
