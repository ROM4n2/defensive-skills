# scripts/ — shipped engine scripts

Four scripts are shipped here because shipped skills invoke them by path. Everything is standard
library only, and all of them resolve the knowledge root by the same contract the MCP server uses
(`--vault-path` / `--root` → `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → upward marker search).

| Script | Invoked by | What it does |
|---|---|---|
| `vault_exec_state.py` | `dfs-exec`, `dfs-handoff` | Persistent execution ledger (`.vault-exec-ledger.json`) with crash recovery: `init` / `start-task` / `complete-task` / `resume` / `status` / `reset` |
| `vault-inbox-consolidate.py` | `dfs-inbox-consolidate` | Batch-classifies inbox drafts by frontmatter tag and archives them in one transaction (`--dry-run` default, `--execute` / `--apply` to commit) |
| `vault_transaction.py` | imported by the above | Generic multi-file atomic replace + rollback primitive (lock, SHA-256 precondition, journal, backup) — a library, no CLI |
| `routing.example.json` | read by the consolidator | Starter tag → destination routing table. Copy it to `routing.json` and edit |

Run them against a knowledge base:

```bash
python scripts/vault_exec_state.py init --plan-file implementation_plan.md   # writes the ledger in cwd
python scripts/vault-inbox-consolidate.py --vault-path <kb root> --dry-run
python scripts/vault-inbox-consolidate.py --vault-path <kb root> --execute --json
```

`routing.json` is git-ignored. The shipped `routing.example.json` is used when it is absent, so the
consolidator works out of the box — it will route unmatched drafts to `06-Sources/` until you edit
it. Route types: `rule-append` (append to one rules file), `source-article` (one new note in a
directory), `dual` (append to a STANDARDS file and flag its CHEATSHEET as stale), `project` (new
note under a project directory).

## Optional integrations (deliberately NOT shipped)

These are referenced by skills but are **not** in this repo, because each one inspects a knowledge
base's own structure and would be wrong-by-default anywhere else. The conformance gate carries them
in `OPTIONAL_SCRIPT_POINTERS` (explicit and self-invalidating — an entry that stops being referenced
fails Rule 8), so a dangling reference can never hide behind them:

| Reference | Status | What you need instead |
|---|---|---|
| `scripts/vault-healthcheck.py` | not shipped | A repo-wide health/structure check is knowledge-base-specific: write one for your own layout, or drop the step |
| `scripts/vault-inbox-triage.py` | not shipped | Age-based inbox triage; the consolidator's `--dry-run` report covers the common case |
| `scripts/bootstrap.ps1` | not shipped | **Real gap, declared:** `dfs-bootstrap` Phase 3.5 scaffolds `WORKMEMORY/` from that PowerShell script, which is Windows-only and reads a private Vault template tree. The files it produces (the four-piece `WORKMEMORY` set, git hook, anchors) are documented in `dfs-bootstrap/SKILL.md` and can be created by hand until a cross-platform port lands |

## Port divergences from the private vault tree

The private tree is the live source for the author's own knowledge base; this repo is the public
port. Three marks make every divergence greppable — `grep -rn "DFS-PORT\|ponytail:" scripts/ *.md`:

* **`vault-inbox-consolidate.py` (2 marks)** — DFS-PORT 1/2: falls back to `routing.example.json`
  when no local `routing.json` exists (upstream had one hardcoded path). DFS-PORT 2/2: root
  resolution is the shared contract and fails loudly with exit 2 when nothing resolves, instead of
  silently defaulting to `<script>/../..` and reporting "no inbox drafts" for a directory that was
  never a knowledge base.
* **`vault_exec_state.py`, `vault_transaction.py`** — byte-identical to the private originals.
* **`dfs-agent-sdk/references/skill-maintenance.md`** — points at this repo's gate
  (`tests/test_skills_conformance.py`) instead of the private `scripts/tests/` copy.
* **`dfs-bootstrap/SKILL.md`, `dfs-onboard/SKILL.md`** — the vault-side `search-vault.py` CLI is
  replaced by the `search_vault` MCP tool plus the `mcp/README.md` fallback table.

## Tests

```bash
python tests/test_vendored_scripts.py      # ledger lifecycle + transactional archival on a temp root
python tests/test_skills_conformance.py    # 12 rules over all 24 skills, incl. these pointers
```
