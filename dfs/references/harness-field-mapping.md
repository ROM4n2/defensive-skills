# Harness field mapping — what actually honors what

The DFS suite was authored on **Hermes Agent**. Two of its frontmatter keys do something in one
harness and nothing in another, and one key is **not a harness feature at all** — it is this
suite's own declaration. Guessing here is how a safety intent silently disappears, so every claim
below is tied to a source you can re-run.

**2026-10 Agent Skills migration:** every vendor extension moved UNDER the spec's `metadata`
extension slot (string values), and all lists use block YAML, so the official `skills-ref
validate` reports 24/24 passing. Two real consequences, documented in the rows below: Hermes no
longer reads a platform filter, and Claude Code no longer sees a hard invocation switch.

**Rule: never assume a key is honored. Look it up. If a harness ignores the key, use the lever
named in its row — the safety property must be enforced somewhere.**

## 1. Portable core — every skill carries it, everyone survives it

Present on all 24 skills; each harness either reads it or ignores it without harm.

| Key | Hermes | Claude Code | Codex CLI / Cursor |
|---|---|---|---|
| `name` | read; must match the directory name | required | no skills subsystem — see §3 |
| `description` | read; drives skill selection | required ("only description is recommended so Claude knows when to use the skill") | — |
| `license` | not read by the loader; the skill spec's own optional field | unknown field → ignored | — |
| `metadata.version` | not read — informational only, parked in the spec's extension slot (the spec's own example puts version there) | ignored | — |
| `metadata.platforms` | **inert since the migration** — Hermes read the old top-level `platforms` and hid a skill on a platform it did not list; the metadata string is not read. All 24 skills list linux/macos/windows, so there is no behavior change today | ignored | — |
| `metadata.hermes.tags` | search/display metadata | ignored | — |
| `metadata.hermes.related_skills` | read (source); checked by Conformance Rule 7 | ignored | — |

## 2. Per-skill extensions — behavior differs, so read the row

Set per skill, not everywhere. `metadata.disable-model-invocation` and
`metadata.hermes.mcp_tools` are the two whose presence changes behavior or a contract, so check
those first.

| Key | Used by | Hermes | Claude Code | Lever when the harness ignores it |
|---|---|---|---|---|
| `metadata.disable-model-invocation: "true"` (7 skills: router `dfs`, `dfs-bootstrap`, `dfs-handoff`, `dfs-inbox-consolidate`, `dfs-incident`, `dfs-interview`, `dfs-pipeline`) | keep a side-effecting or router skill from being auto-selected | **not implemented** — see the evidence in §4 | **inert here as well** — Claude Code honored only the old TOP-LEVEL key; values under `metadata` are ignored, so there is no hard switch any more | the file-top banner (§2.1) is now the enforcement on every harness; Claude Code hard lever: set the skill to `"user-invocable-only"` in `skillOverrides`; Hermes: a permission rule or a line in your project rules file |
| `metadata.hermes.mcp_tools` (9 skills) | **DFS-internal contract**: declares which MCP tools a skill may call, checked by Conformance Rules 9 and 11, and read by an agent to choose the file-level fallback | **no harness support — 0 references in the Hermes source** | ignored | nothing to map: this key is the suite talking to its own gate and to the agent. It is not a switch any runtime flips |
| `metadata.hermes.requires_tools` / `metadata.hermes.fallback_for_tools` (+ `*_toolsets`) | would be the Hermes-native way to make a skill appear only when a tool exists | read (source) | ignored | not used by DFS today; if a skill ever *needs* a toolset to work, this is the documented mechanism, and ignoring it costs nothing |
| `metadata.author` (1 skill: `dfs-handoff`) | provenance only — a credit line, not a behavior switch | **not read by the loader** | ignored | nothing to map: attribution, not a capability. `.gitattributes`/LICENSE carry the same claim for the whole tree |

**The one that matters:** seven skills carry a flag no runtime enforces any more. Nothing breaks
when they are invoked — but nothing in the runtime prevents auto-selection. Two of the seven
(`dfs-bootstrap`, `dfs-inbox-consolidate`) write into a repository or move notes, which is exactly
why the rule exists. §2.1 closes this by stating the rule in the file.

### 2.1 The gap, and how it was closed

The intent used to live in a top-level key honored by one harness; when the key moved under
`metadata` for Agent Skills conformance (2026-10), it became inert everywhere. So the rule is
stated in the file itself — the missing line was added to all seven — at the top of each file,
where an agent that reads only the first screen still sees it:

```bash
grep -l 'Invocation . explicit only' dfs*/SKILL.md      # -> 7 files, one per skill in §2
```

The banner's opening sentence — `**Invocation — explicit only.**` — is identical in all seven,
which is what makes it greppable and gateable, and it names the flag so a reader knows why it is
there. The grep above prints the live wording; this doc deliberately does not keep a second copy
of it, because a quoted banner is a second place to edit every time the banner changes.

`tests/test_harness_field_mapping.py::test_06` checks this in the direction that matters: if the
doc claims the banner is applied, every one of the seven files must actually contain it. If you
delete a banner, the gate goes red rather than the doc quietly becoming a lie.

Two harness-side levers remain available and are not mutually exclusive with the banner:

1. **Claude Code**: set the skill to `"user-invocable-only"` in `skillOverrides`.
2. **Hermes**: a permission rule or a line in your project rules file.

## 3. Harnesses with no skills subsystem

Codex CLI and Cursor consume project instruction files, not skill directories:

* **Codex CLI** — `AGENTS.md` at the project root (the same marker DFS already uses to resolve a
  knowledge root, which is why the two compose cleanly). Copy the SKILL.md bodies you want as
  sections, or let the agent read `dfs/<name>/SKILL.md` directly.
* **Cursor** — `.cursor/rules/*.mdc` with its own frontmatter (`description`, `globs`,
  `alwaysApply`); SKILL.md frontmatter is inert there.

In both cases the **body** is the product: the procedure, the checks, and the file-level fallback
table in `mcp/README.md` are harness-neutral. Frontmatter is a Hermes/Claude Code packaging detail.

**Not verified from source here:** cursor.com and agents.md were unreachable from the network
this document was last checked on (TLS handshake failure), so the two rows above come from the
published conventions rather than a fetched spec. Re-fetch before quoting them as normative.

## 4. How to check this yourself

```bash
# Open-standard conformance (official reference validator; all 24 must pass):
skills-ref validate dfs-save        # -> "Valid skill: dfs-save"; repeat per skill
for d in dfs*/; do skills-ref validate "$d"; done

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
# Agent Skills open standard: the six allowed top-level fields and the metadata extension slot
curl -sL https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx
```

Python gates in this repo that depend on these facts:
`tests/test_harness_field_mapping.py` (every frontmatter key in the tree must appear here, and the
portable-core list must match reality).
