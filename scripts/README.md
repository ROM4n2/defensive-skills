# scripts/ — shipped engine scripts

Four scripts are shipped here because shipped skills invoke them by path. Everything is standard
library only, and all of them resolve the knowledge root by the same contract the MCP server uses
(`--vault-path` / `--root` → `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → upward marker search).

The fifth shipped program lives with its skill instead: **`dfs-bootstrap/scripts/bootstrap.py`** —
the cross-platform workspace bootstrap (`.gitignore` guards, secret-scanning hook, rule anchors,
`WORKMEMORY/` scaffold). It reads the templates next to it, so it stays inside the skill directory.
`tests/test_bootstrap_script.py` drives it against a temp repo.

| Script | Invoked by | What it does |
|---|---|---|
| `vault_exec_state.py` | `dfs-exec`, `dfs-handoff` | Persistent execution ledger (`.vault-exec-ledger.json`) with crash recovery: `init` / `start-task` / `complete-task` / `resume` / `status` / `reset` |
| `vault-inbox-consolidate.py` | `dfs-inbox-consolidate` | Batch-classifies inbox drafts by frontmatter tag and archives them in one transaction (`--dry-run` default, `--execute` / `--apply` to commit, `--inbox <dir>` to read a queue from anywhere) |
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

### `--inbox`: consuming a queue that is not `<root>/99-Inbox`

A drop box (see `mcp/README.md` § Root resolution) lives outside the knowledge base, so `--inbox`
has to work from anywhere — including with no root at all:

```bash
# no knowledge base yet: list what is waiting, file nothing
python scripts/vault-inbox-consolidate.py --inbox .dfs-inbox

# later, with a root: file the same drafts, and remove the originals from the drop box
python scripts/vault-inbox-consolidate.py --inbox .dfs-inbox --vault-path <kb root> --execute
```

Three rules make that safe rather than convenient:

* **Listing needs no root; filing does.** `--execute` without a resolvable root exits 2 — archiving
  means "write a destination + delete the original", and neither end may be guessed.
* **A named root is never second-guessed.** If `$WIKI_PATH`/`--vault-path` resolve to nothing, the
  tool says so and exits 2. It does not silently fall back to a drop box the way the server does.
* **The transaction's path bound is extended explicitly, not dismantled.** `stage_deletion` refuses
  any path outside `vault_root` — except a root the *caller* declared via `VaultTransaction(...,
  extra_roots=[...])`, which the consolidator passes only for the `--inbox` directory. Writes still
  never leave the root. `tests/test_vendored_scripts.py::TestDeletionBounds` pins all three
  behaviors, including the refusal, so the bound cannot be quietly relaxed.

## Optional integrations (deliberately NOT shipped)

These are referenced by skills but are **not** in this repo, because each one inspects a knowledge
base's own structure and would be wrong-by-default anywhere else. The conformance gate carries them
in `OPTIONAL_SCRIPT_POINTERS` (explicit and self-invalidating — an entry that stops being referenced
fails Rule 8), so a dangling reference can never hide behind them:

| Reference | Status | What you need instead |
|---|---|---|
| `scripts/vault-healthcheck.py` | not shipped | A repo-wide health/structure check is knowledge-base-specific: write one for your own layout, or drop the step |
| `scripts/vault-inbox-triage.py` | not shipped | Age-based inbox triage; the consolidator's `--dry-run` report covers the common case |

The Windows-only PowerShell bootstrap that used to be a declared gap here is **no longer a gap**:
`dfs-bootstrap` ships a cross-platform port (`dfs-bootstrap/scripts/bootstrap.py`) and no longer
references anything outside the repo, so its entry was removed from `OPTIONAL_SCRIPT_POINTERS`
rather than kept as a permanent exemption. That removal is what the stale-exemption check is for —
leaving it behind would have turned a real fix into a silent mute.

## Port divergences from the private vault tree

The private tree is the live source for the author's own knowledge base; this repo is the public
port. Three marks make every divergence greppable — `grep -rn "DFS-PORT\|ponytail:" scripts/ *.md`:

* **`vault-inbox-consolidate.py` (2 marks)** — DFS-PORT 1/2: falls back to `routing.example.json`
  when no local `routing.json` exists (upstream had one hardcoded path). DFS-PORT 2/2: root
  resolution is the shared contract and fails loudly with exit 2 when nothing resolves, instead of
  silently defaulting to `<script>/../..` and reporting "no inbox drafts" for a directory that was
  never a knowledge base.
* **`vault_exec_state.py`, `vault_transaction.py`** — content-identical to the private originals.
  The repository stores LF for `*.py` (see `.gitattributes`), so a byte-level comparison against a
  CRLF working copy differs by line endings only; verify with
  `git show HEAD:scripts/<file> | tr -d '\r' | sha256sum`.
* **`dfs-bootstrap/SKILL.md`, `dfs-onboard/SKILL.md`** — the vault-side `search-vault.py` CLI is
  replaced by the `search_vault` MCP tool plus the `mcp/README.md` fallback table; both files also
  drop a hardcoded projects-root assumption (`D:\Code\{project}`) for a neutral placeholder.
  `dfs-bootstrap` additionally gains `scripts/bootstrap.py` + `templates/workmemory/`, which the
  private tree does not have (it still runs the PowerShell original).
* **`vault_transaction.py` gains `extra_roots`** — a caller-declared exception to the deletion bound,
  needed so `--inbox <dir outside the root>` can remove the draft it just filed. Default behavior is
  unchanged (no extra roots → the same refusal), and writes are never allowed outside the root.

## Tests

```bash
python tests/test_vendored_scripts.py      # ledger + transaction + archival + deletion bounds (17)
python tests/test_bootstrap_script.py      # bootstrap.py against a temp repo: idempotency, no clobber
python tests/test_skills_conformance.py    # 12 rules over all 23 skills, incl. these pointers
```
