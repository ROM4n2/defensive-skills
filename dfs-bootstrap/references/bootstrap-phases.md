# dfs-bootstrap — extended playbook (tier 3)

Loaded on demand by `dfs-bootstrap/SKILL.md`. The skill keeps the constraints and completion criteria;
this file keeps the commands, the pattern lists, and the probe set. Gate thresholds and opt-in checks
live in [`gate-reference.md`](gate-reference.md); overlay mechanics in [`overlay-mode.md`](overlay-mode.md).

---

### Phase 0: Git Initialization (MUST — 此步不得跳过)
1. If `<project-root>` has no `.git`, run `git init`. Confirm with `git rev-parse --is-inside-work-tree` and `git symbolic-ref --short HEAD`; any failure stops the bootstrap before files or hooks are changed.
2. Before Phase 4 commit probes, require `git config --global --get user.name` and `git config --global --get user.email` to be non-empty. If either is missing, stop and ask the user to run `git config --global user.name "<name>"` or `git config --global user.email "<email>"`; never modify global config silently.
3. Enter Phase 1 only after repository confirmation. Dry-run describes `git init`; apply performs it.

### Phase 1: Security Git Hooks, .gitignore & EOL Pins (MUST)
1. Verify `.gitignore` contains all sensitive patterns (list MUST stay in sync with `REQUIRED_IGNORES` in `scripts/bootstrap.py` — it is the single source of truth):
   ```gitignore
   # Secrets & Local Configs
   config.yaml
   config.yml
   config.local.yaml
   .env
   .env.*
   *.env
   *.secret
   *.pem
   *.key
   *.local.json
   credentials.json

   # Agent-runtime scratch (never a deliverable)
   .worktrees/
   .vault-exec-ledger.json
   ```
   `.worktrees/` is a git worktree of the *same* repo (a subagent checkout); committing it doubles the
   tree and confuses every later `git worktree` command. `.vault-exec-ledger.json` is `dfs-exec`'s
   per-run task state, not an artefact.
2. Install `.githooks/pre-commit` from `templates/githooks-pre-commit.sh` with **Unix (LF) line
   endings and no UTF-8 BOM** — a CRLF or BOM shebang stops git from spawning the hook
   (`cannot spawn .githooks/pre-commit`):
   ```bash
   mkdir -p .githooks
   cp templates/githooks-pre-commit.sh .githooks/pre-commit   # first line MUST be exactly: #!/usr/bin/env bash
   chmod +x .githooks/pre-commit
   git config core.hooksPath .githooks
   ```
   For project-specific quality gates beyond base security, author them with `/dfs-gate`.
3. **Pin LF in `.gitattributes` — otherwise the hook re-breaks on fresh checkout.** On Windows
   `core.autocrlf=true` silently rewrites `pre-commit` to CRLF when git materializes it, undoing the
   normalization above:
   ```gitattributes
   .githooks/** text eol=lf
   WORKMEMORY/** text eol=lf   # append-only UTF-8 log; keeps git diffs sane
   *.sh text eol=lf
   ```
   After adding `.gitattributes`, run `git add --renormalize .` so the stored blobs are LF.
4. **The hook enforces four classes**, each with a probe in Phase 4:
   - `[LINE]` / `[NAME]` — content and filename secret rules. Content scanning is one
     `git grep --cached` over the whole index, not one `git show` per file (measured 3.6 s versus
     8.8 s for 300 files).
   - `[EOL]` — a staged file **under `.githooks/`** whose worktree bytes contain CRLF. This is the only
     check that reads the worktree: `text eol=lf` files are normalised by `git add`, so scanning the
     index blob for CRLF would be dead code, but a CRLF script in that directory cannot be executed.
   - `[CHAIN]` — the upstream hook, run first; its failure aborts the commit (see `overlay-mode.md` §5).
   - the two repository gates, launched **concurrently** (see `gate-reference.md`).
5. **Hook version marker.** Line 2 of the template is `# dfs-bootstrap-hook-version: N`.
   `bootstrap.py` reads it to decide whether an installed hook is an older DFS copy (upgrade it, keep
   the previous file as `pre-commit.dfsbak`) or a project-owned gatekeeper (no marker → never touch).
   Bump `N` on any behaviour change; otherwise existing repos keep their stale gate forever.

### Phase 2: Rules Anchor — Single Source of Truth (MUST)

Only `AGENTS.md` carries stable project rules and facts. Temporary status, decisions, lessons, and
handoffs belong in `WORKMEMORY/`; promote them into `AGENTS.md` only when they become durable rules.
`CLAUDE.md` is exactly:

```markdown
@AGENTS.md
<!-- Canonical rules live in AGENTS.md; read ./AGENTS.md directly if your runtime does not expand @imports. -->
```

Claude Code expands `@AGENTS.md` natively; runtimes that do not expand imports read the pointer as a
one-line instruction. Either way the rules exist once.

**Do not generate `.agent-rules.md` / `.cursorrules`.** They were emitted by bootstrap 0.2.x and the
result is measured: across the author's repositories `.cursorrules` was byte-identical to `AGENTS.md`
in 2 repos, identical to `.agent-rules.md` in 4, and genuinely divergent in the rest — i.e. neither a
safe duplicate nor a maintained file. `bootstrap.py` now reports them and writes into them only with
`--legacy-aliases`.

**The anchor names tools, never an external path.** No harness expands a shell variable inside
markdown, and `search_vault` resolves the knowledge base from its own location — so a line like
``$WIKI_PATH/AGENTS.md`` reads as a pointer and behaves as decoration. Write the MCP tool and skill
names an agent can act on and keep every external path out, expanded or not. An absolute root is the
worst case: it trips the `[ABS_PATH]` hygiene rule in the very repo being bootstrapped and is wrong
on any other machine. Bootstrap **fails closed** (exit 2) when `$WIKI_PATH` / `--vault-root` has no
`AGENTS.md`; `--allow-missing-vault-agents` overrides, accepting that the knowledge base is then
unreachable by path.

---

### Phase 4: Full Probe Set (HARD GATE)

Run every probe against a throwaway repo, then restore it. A probe that cannot fail proves nothing —
each line below names the tag the hook must emit.

```bash
# 1. Clean tree must pass (no false positive on repo content)
bash .githooks/pre-commit            # expect exit 0

# 2. Synthetic secret -> [LINE], commit truly aborted
python -c "open('__probe__.txt','w').write('k = sk-' + '0'*32)"
git add __probe__.txt
before=$(git rev-parse HEAD)
git commit -m probe                  # expect exit != 0 and '[LINE]' in the output
[ "$(git rev-parse HEAD)" = "$before" ]   # HEAD unchanged: the commit was aborted, not warned
git reset -q HEAD __probe__.txt && rm -f __probe__.txt

# 3. Sensitive filename -> [NAME]
printf 'x=1' > .env && git add -f .env
git commit -m envprobe               # expect '[NAME]'
git reset -q HEAD .env && rm -f .env

# 4. CRLF under .githooks/ -> [EOL]   (sibling file, never the running hook)
printf '#!/usr/bin/env bash\r\nexit 0\r\n' > .githooks/pre-push
git add .githooks/pre-push
git commit -m eolprobe               # expect '[EOL]'
git reset -q HEAD .githooks/pre-push && rm -f .githooks/pre-push

# 5. Hygiene gate reached THROUGH the hook -> [ABS_PATH]
mkdir -p src && printf 'p = "D:/Code/other/x.py"\n' > src/demo.py   # git:allow-abs-path (intentional probe)
git add src/demo.py
git commit -m abspath                # expect '[ABS_PATH]' on stderr
git reset -q HEAD src/demo.py && rm -rf src

# 7. Checkout durability (Windows, supplementary — NOT probe 6): the pin must survive re-materialisation
rm .githooks/pre-commit && git checkout -- .githooks/pre-commit
file .githooks/pre-commit            # expect plain 'ASCII text', NOT 'with CRLF line terminators'
```

Probe 6 in the skill's completion criterion is **`git rev-parse HEAD` unchanged after every abort**;
this checkout-durability check is an extra Windows-only step, numbered 7 here so the two documents do
not disagree about what probe 6 means. In overlay mode the hook is not at `.githooks/pre-commit` at
all (`.git/dfs-hooks/pre-commit`), so run this one only in owner mode.

Probe 5 catches **unreachable wiring**: without it, the gate's invocation can be deleted from the hook
while every direct-invocation test stays green (`dfs-gate/references/dead-gate-traps.md` §2).

Probe 4 must target a **sibling** file. Overwriting the executing hook makes bash fail with a parse
error (exit 2), which looks like a pass to a careless `if [ $? -ne 0 ]` check but never exercises the gate.

Also verify, without a commit:

- `CLAUDE.md` is exactly the 2-line `@AGENTS.md` pointer — a full rules copy there is a regression.
- `AGENTS.md` carries the anchor header **and at least one MCP tool token**, and contains no host
  path — neither the expanded vault root nor an unexpanded `$WIKI_PATH/...` form.
- In overlay mode: `git status --porcelain`, `git diff`, and `git diff --cached` are all empty.
