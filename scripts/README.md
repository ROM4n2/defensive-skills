# Shipped scripts

All shipped scripts use the Python standard library.

## Ledger CLI

The ledger has one home: [`dfs-exec/scripts/vault_exec_state.py`](../dfs-exec/scripts/vault_exec_state.py).

| Caller | Working directory | Command |
|---|---|---|
| `dfs-exec` | `dfs-exec/` | `python scripts/vault_exec_state.py <command>` |
| `dfs-plan` | `dfs-plan/` | `python ../dfs-exec/scripts/vault_exec_state.py <command>` |
| `dfs-handoff` | `dfs-handoff/` | `python ../dfs-exec/scripts/vault_exec_state.py resume` |

Commands: `init`, `start-task`, `complete-task`, `resume`, `status`, and `reset`. The ledger file is `.vault-exec-ledger.json` in the selected workdir.

Read-only status check:

```bash
python dfs-exec/scripts/vault_exec_state.py --workdir <workdir> status --json
```

## Inbox archival

| Path | Purpose |
|---|---|
| `scripts/vault-inbox-consolidate.py` | Classify and archive drafts transactionally |
| `scripts/vault_transaction.py` | Atomic replace, rollback, journal, and backup support |
| `scripts/routing.example.json` | Example tag-to-destination routing table |

```bash
python scripts/vault-inbox-consolidate.py --vault-path <knowledge-root> --dry-run
python scripts/vault-inbox-consolidate.py --vault-path <knowledge-root> --execute --json
```

Use `--inbox <dir>` for a queue outside the knowledge base. Listing works without a root; `--execute` requires one. A failed or skipped draft is not deleted, and same-run destination collisions are refused.

Copy `routing.example.json` to `routing.json` to customize routing. `routing.json` is git-ignored.

## Bootstrap

[`dfs-bootstrap/scripts/bootstrap.py`](../dfs-bootstrap/scripts/bootstrap.py) reads templates from its own Skill directory.

Behavior:

- Run `git init` when `.git` is missing and confirm the initial branch. Initialization failure stops the run.
- Install `.githooks/pre-commit` and set `core.hooksPath`; existing hooks are preserved.
- Write `.gitignore`, anchors, and the five WORKMEMORY files without overwriting existing work.
- Support `--dry-run`; missing templates exit 2.

## Deliberately unshipped

| Item | Reason |
|---|---|
| `scripts/vault-healthcheck.py` | Depends on one knowledge base's layout |
| `scripts/vault-inbox-triage.py` | Depends on one knowledge base's inbox policy |
| `scripts/sync-workmemory-template.py` | Synchronizes a private vault layout; bundled templates are the public source |

## Tests

```bash
python tests/test_vendored_scripts.py
python tests/test_bootstrap_script.py
python tests/test_skills_conformance.py
```
