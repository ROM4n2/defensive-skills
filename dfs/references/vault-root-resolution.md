# Vault Root Resolution Contract

Every DFS skill that reads or writes knowledge-base paths MUST resolve the Vault root through
this contract. Do not inline a copy of the detection loop, and do not hardcode an absolute path.

## Resolution order (static-first, cheapest first)

| Tier | Source | Cost | When it applies |
|---|---|---|---|
| **1** | `$WIKI_PATH`, then `$OBSIDIAN_VAULT_PATH` | zero tool calls | Environment already exports the Vault root — the normal case |
| **2** | Upward search from `cwd` for `AGENTS.md` or `.obsidian/` | one filesystem walk | Vault is the current project, or a subdirectory of it |
| **3** | Vault-relative functions degrade to `./.agent/` | zero | No Vault present (plain Git repo, CI, first-run user) |

Tier 3 exists so the skills remain usable outside the author's machine — required for
open-source distribution. A skill that cannot degrade MUST fail loudly with an explicit
message naming which tier failed, never silently write to the wrong directory.

## Canonical snippet (reference this, do not copy divergent versions)

```bash
# Tier 1 — prefer the exported environment
VAULT_ROOT="${WIKI_PATH:-${OBSIDIAN_VAULT_PATH:-}}"

# Tier 2 — walk up from cwd looking for a Vault marker
if [ -z "$VAULT_ROOT" ]; then
  d="$PWD"
  while [ "$d" != "/" ]; do
    if [ -f "$d/AGENTS.md" ] || [ -d "$d/.obsidian" ]; then VAULT_ROOT="$d"; break; fi
    d="$(dirname "$d")"
  done
fi

# Tier 3 — degrade, do not fail silently
if [ -z "$VAULT_ROOT" ]; then
  VAULT_ROOT="$PWD/.agent"
  mkdir -p "$VAULT_ROOT"
fi
```

## Rules

1. **MUST** try Tier 1 before Tier 2. The environment variable is authoritative and free.
2. **MUST NOT** hardcode an absolute Vault path in any skill file. The conformance suite
   (Rule 10) rejects any drive-letter literal naming an Obsidian directory.
3. **MUST** write every Vault path as `{vault_root}/<subpath>` so the resolution point stays
   visible and greppable.
4. **MUST** state the Tier 3 degradation behaviour explicitly when the skill writes data.
   Read-only skills may simply report the missing Vault and stop.

## Known Vault subpaths referenced by DFS skills

```
{vault_root}/AGENTS.md                              # canonical rule source
{vault_root}/01-Rules/                              # cross-language engineering rules
{vault_root}/03-Languages/{LANG}/                   # dual-version standards + cheatsheets
{vault_root}/05-Tools/SKILL-REGISTRY.md             # skill registry (L1/L2)
{vault_root}/08-Projects/{project}/01-ADR/          # architecture decision records
{vault_root}/99-Inbox/                              # draft ingestion queue
{vault_root}/scripts/                               # vault-resident tooling
{vault_root}/scripts/tests/                         # conformance + shipped-skill suites
```
