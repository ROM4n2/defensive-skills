# Overlay Mode: Private Scaffolding on Someone Else's Upstream (`references/overlay-mode.md`)

Load this when you run `dfs-bootstrap` on a repository you do **not** own — a fork, a vendored
dependency, or an open-source contribution.

The problem it solves: `AGENTS.md`, `CLAUDE.md`, `WORKMEMORY/`, the gates, and the pre-commit hook are
*your* working apparatus. They do not belong in a pull request to upstream, and they must not appear in
`git diff` — otherwise every review starts with a page of files the maintainer has to reject.

---

## 1. What overlay mode does differently

| Artifact | owner mode | overlay mode |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | working tree, tracked | working tree, listed in `.git/info/exclude` |
| `WORKMEMORY/` (5 files) | working tree, tracked | working tree, excluded |
| `check_repo_hygiene.py`, `check_repo_structure.py`（`scripts/` 下） | working tree, tracked | working tree, excluded |
| secret patterns (`.env`, `*.pem`, …) | appended to tracked `.gitignore` | appended to `.git/info/exclude` |
| LF pins | appended to tracked `.gitattributes` | appended to `.git/info/attributes` |
| hook | `.githooks/pre-commit` (tracked) | `.git/dfs-hooks/pre-commit` (inside `.git`) |
| `core.hooksPath` | `.githooks` | `.git/dfs-hooks` |

`core.hooksPath` is a **local** git config value, so pointing it inside `.git` is not a global change
and is invisible to upstream.

---

## 2. Why these three mechanisms and not others

**`.git/info/exclude`** — the only per-repository ignore file that is never committed and never appears
in a diff. It behaves exactly like `.gitignore` for `git status`, `git add`, and
`git ls-files --others --exclude-standard`. Alternative `skip-worktree` / `assume-unchanged` bit
twiddling was rejected: those are fragile across branch switches and silently revert.

**`.git/info/attributes`** — the *highest* precedence attributes source in git. It applies `eol=lf` to
your private files without touching the tracked `.gitattributes`, so a fork's diff stays clean while
the hook still gets LF endings.

**`.git/dfs-hooks/`** — a hook inside `.git` is neither tracked nor diffed, and it survives
`git checkout -- .`, `git reset --hard`, and branch switches (verified). Putting it in `.githooks/`
would create an untracked directory that `git status` reports on every fork.

---

## 3. Measured guarantees

Verified on git 2.53 with a realistic fork (tracked `.gitignore` + `.gitattributes` + source):

| Property | Command | Result |
|---|---|---|
| No tracked change | `git status --porcelain` | empty |
| No unstaged change | `git diff` | empty |
| Nothing staged | `git diff --cached --name-only` | empty |
| `git add -A` stages nothing private | `git diff --cached --name-only` after add | empty |
| Upstream ignore file untouched | byte-compare with `HEAD:.gitignore` | identical |
| Upstream attributes untouched | byte-compare with `HEAD:.gitattributes` | identical |
| Private files survive `checkout -- .` and `reset --hard` | file exists | yes |
| A real upstream commit stays clean | `git status --porcelain` after commit | empty |

The gate self-acceptance rule applies here too: `check_repo_hygiene.py` accepts the LF pins from
**either** `.gitattributes` or `.git/info/attributes`. Accepting only the tracked file made overlay mode
fail its own gate on every commit — the self-rejection trap from
`dfs-gate/references/dead-gate-traps.md` §3.

---

## 4. Usage

```bash
# One-time on a fresh clone, and any time after (idempotent; the hook upgrades via its version marker)
python scripts/bootstrap.py --target . --vault-root "$WIKI_PATH" --mode overlay
```

Bootstrap prints the cleanliness proof at the end:

```
  [OK] upstream tree is clean (git status / diff / staged all empty)
```

If it prints `[WARN] overlay left tracked changes`, something in the repo was already modified before
bootstrap ran — inspect before committing.

---

## 5. When upstream already owns AGENTS.md, CLAUDE.md or a pre-commit hook

This is the case that silently breaks a naive overlay. Both failures below were measured on a real fork
before they were fixed, and both are asserted in `tests/test_overlay.py`.

### 5.1 Tracked rules files are never modified

| Situation | Naive behaviour | What bootstrap does now |
|---|---|---|
| `AGENTS.md` is tracked and has no anchor | appends the anchor → `git status` shows `M AGENTS.md`, the block lands in the next PR | writes `AGENTS.dfs.md` instead; `AGENTS.md` stays byte-identical to `HEAD` |
| `AGENTS.md` is tracked and already has an anchor | idempotent skip | idempotent skip (nothing written at all) |
| `CLAUDE.md` is tracked | may rewrite it into a pointer → destroys upstream content | never touched |
| `WORKMEMORY/` does not exist | scaffolds it | scaffolds it, and `.git/info/exclude` hides it |

`AGENTS.dfs.md` carries both the rules anchor and the WORKMEMORY anchor, so nothing is lost — it is
simply stored where git cannot see it. `_is_tracked()` (a `git ls-files --error-unmatch` probe) is the
single fact that decides whether a path belongs to us or to upstream.

### 5.2 The upstream hook is chained, not replaced

Pointing `core.hooksPath` at `.git/dfs-hooks` **replaces** the repository's hook. On a fork that already
has a pre-commit gate, that silently disables `make test`, lint, license checks — everything — and
commits keep succeeding, so nobody notices.

The installed hook therefore delegates first:

```bash
chain_upstream() {
    local self; self="$(basename "$0")"
    local candidates=()
    [ -n "${DFS_UPSTREAM_HOOKS:-}" ] && candidates+=("$DFS_UPSTREAM_HOOKS/$self")
    candidates+=(".githooks/$self" ".git/hooks/$self")
    for candidate in "${candidates[@]}"; do
        [ -f "$candidate" ] && [ -x "$candidate" ] || continue
        # skip ourselves, then run the upstream hook and propagate its failure
        if ! "$candidate" "$@"; then
            printf '[CHAIN] upstream hook failed: %s\n' "$candidate" >&2
            exit 1
        fi
        printf '[CHAIN] upstream hook passed: %s\n' "$candidate" >&2
        return 0
    done
    return 0
}
```

Properties that matter:

| Property | Why |
|---|---|
| Upstream hook runs **first** | Its failure must abort before our gates spend time scanning |
| Failure propagates as `exit 1` | A swallowed chain failure is worse than no chain |
| Self-recursion is skipped by resolved path | `.git/dfs-hooks/pre-commit` must never chain to itself |
| Absence is silent | A repo with no upstream hook produces no `[CHAIN]` output |
| `DFS_UPSTREAM_HOOKS` overrides the search | Non-standard layouts (husky, lefthook) need one env var, not a code change |

`core.hooksPath` is still set to `.git/dfs-hooks` — that is unavoidable, since git runs exactly one hook
per event. Chaining is what makes the replacement non-destructive.

### 5.3 Verifying on a real fork

```bash
python scripts/bootstrap.py --mode overlay --target . --vault-root "$WIKI_PATH"
git status --porcelain          # must be empty
git diff HEAD -- AGENTS.md      # must be empty
ls AGENTS.dfs.md                # private layer, invisible to git
git commit --allow-empty -m probe   # must print [CHAIN] upstream hook passed
```

---

## 6. What overlay mode deliberately does NOT do

| Not done | Why |
|---|---|
| Add private paths to a *tracked* `.gitignore` | That is the leak this mode exists to prevent. |
| Use `--assume-unchanged` / `--skip-worktree` | They silently revert on branch switch and are not portable. |
| Create `.githooks/` | An untracked directory shows up in `git status` on every fork. |
| Modify a tracked `AGENTS.md` / `CLAUDE.md` | Upstream's content; the private layer goes to `AGENTS.dfs.md`. |
| Silently replace the upstream hook | The installed hook chains to it and propagates its exit code. |
| Block you from committing private files manually | `git add -f AGENTS.md` still works. Overlay prevents *accidents*, not deliberate acts. |

---

## 7. Migrating an existing overlay repo to owner mode

When you later fork the project into your own repository:

1. `git rm --cached` nothing — the private files were never tracked.
2. Delete the local exclusions so they become visible again:
   ```bash
   git config --unset core.hooksPath
   # remove the DFS block from .git/info/exclude and .git/info/attributes
   ```
3. Re-run bootstrap in owner mode: `python scripts/bootstrap.py --mode owner --target .`
   It will append the patterns to the tracked `.gitignore` / `.gitattributes` and install
   `.githooks/pre-commit`.

The reverse migration (owner → overlay) is the same sequence with `--mode overlay`, after removing the
DFS block from the tracked ignore/attributes files.

---

## 8. Known limits

- **Windows + `core.autocrlf=true`**: the private files are pinned via `.git/info/attributes`, but a
  checkout performed *before* bootstrap will already have converted them. Bootstrap writes LF, so a
  fresh run is clean; pre-existing files need one `--mode overlay` re-run.
- **Nested repositories**: `.git/info/*` applies to the containing repository only. A submodule with its
  own `.git` needs its own overlay bootstrap.
- **`git clean -xdf`** removes excluded files, including `WORKMEMORY/`. That is standard git behaviour
  for untracked files and is the one operation that destroys overlay state — keep the vault copy, or
  commit `WORKMEMORY/` in a private branch if the history matters.
