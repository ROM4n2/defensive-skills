---
name: dfs-bootstrap
description: "Use when bootstrapping a repo with security hooks."
license: MIT
disable-model-invocation: true
metadata:
  version: 0.5.0
  platforms: linux, macos, windows
  hermes:
    tags: [bootstrap, git-hooks, security, pre-commit, repo-init]
    related_skills: [dfs-onboard, dfs-save, dfs-pipeline, dfs-gate]
---
# DFS-BOOTSTRAP: Repository Security & Knowledge Anchoring

> **Invocation — explicit only.** This skill carries top-level `disable-model-invocation: true`,
> which prevents automatic model selection while preserving explicit `/dfs-bootstrap` invocation in
> Antigravity and Claude Code. Wait until the user asks for it, or until an already-running DFS skill
> routes here. Harnesses that ignore the field still enforce this banner — see
> `dfs/references/harness-field-mapping.md`.

Initialize any repository with a zero-leak secret hook, two mechanical gates, and a single-source-of-truth
rules anchor. The full procedure, worked example, and field evidence live in
[`references/bootstrap-phases.md`](references/bootstrap-phases.md); load it for any Phase below.

## Two Modes (MUST — choose before running)

| Mode | When | What git sees |
|---|---|---|
| `--mode owner` (default) | You own the repository | Artifacts tracked; `.gitignore` / `.gitattributes` appended to |
| `--mode overlay` | Secondary development on **someone else's upstream** | Nothing tracked: exclusions in `.git/info/exclude`, LF pins in `.git/info/attributes`, hook in `.git/dfs-hooks` |

Choosing wrong is a leak: owner mode on a fork puts `AGENTS.md` / `WORKMEMORY/` in your PR; overlay on
your own repo leaves the apparatus untracked and unshared. Overlay guarantees and the "upstream already
owns `AGENTS.md`/a hook" case: [`references/overlay-mode.md`](references/overlay-mode.md).

## The 5-Phase Protocol (constraints only — details in tier 3)

- **Phase 0 — Git init (MUST)**: `git init` if `.git` missing; confirm repo + branch before any write;
  require non-empty `user.name`/`user.email` before Phase 4 commits (set by the user, never silently).
- **Phase 1 — Hook, ignores & EOL pins (MUST)**: cover sensitive patterns **plus agent scratch** (`.worktrees/`,
  `.vault-exec-ledger.json`). Install the hook LF/no-BOM **and pin endings in `.gitattributes` in the same
  step** — on Windows `core.autocrlf=true` otherwise re-materialises CRLF and git cannot spawn the hook.
  `core.hooksPath` activation runs **every** run (local config does not survive a clone); repointing it
  needs `--take-hooks-path`. Index the 0755 explicitly (`core.filemode=false`). Full mechanism:
  `references/bootstrap-phases.md` Phase 1.
- **Phase 1b — Repository gates (SHOULD, default on)**: two stdlib gates land in `scripts/` (`--no-gates`
  skips). A project-owned copy (no marker) is never overwritten; a DFS-marked older copy auto-upgrades.
  Thresholds, pragmas, opt-ins: [`references/gate-reference.md`](references/gate-reference.md).
- **Phase 2 — Rules anchor (MUST)**: `AGENTS.md` is the single source of truth; `CLAUDE.md` is exactly the
  2-line `@AGENTS.md` pointer (a custom copy is backed up as `CLAUDE.md.dfsbak`). Scaffold the 5-piece
  `WORKMEMORY/` (INDEX / INDEX-topics / PROJECT_OVERVIEW / PROTOCOL / work.log); `INDEX.md` is the HOT
  layer, topics go to `INDEX-topics.md` (WARM). Fill the overview from the real codebase.
- **Phase 3 — Local-only gate (default on)**: `templates/local-gates/fingerprint-gate.sh` installs into
  `$GIT_DIR/local-gates/` — **never into the tracked tree**. It keeps this machine's identifiers out of a
  public remote; a tracked copy would carry the identifiers it hides. Patterns are absolute paths
  carrying identity (real username dirs, private vault paths). Do NOT list generic tool dir names
  (`\.codebuddy/`, `\.trae-cn/`) — they carry no identity and flag legitimate "ignore this dir" comments.
  Details: `references/gate-reference.md` §7.
- **Phase 4 — Binary verification (HARD GATE)**: green `bash .githooks/pre-commit` on a clean tree only proves
  no crash. Six probes: clean passes; synthetic secret `[LINE]`; sensitive filename `[NAME]`; CRLF under
  `.githooks/` `[EOL]`; host path / conflict marker `[ABS_PATH]`/`[CONFLICT]` through the hook; HEAD unchanged
  after every abort. Assemble probe content at runtime; target a sibling under `.githooks/`, never the running
  hook. Commands: `references/bootstrap-phases.md` Phase 4.

## Checkable Completion Criterion
- Hook installed LF, **100755 in the index**, carrying the current `# dfs-bootstrap-hook-version:` marker.
- `core.hooksPath` set (verified each run); `.gitattributes` (or `.git/info/attributes`) pins `.githooks/**`
  and `WORKMEMORY/**` to LF.
- `AGENTS.md` holds the rules anchor; `CLAUDE.md` is exactly the 2-line pointer.
- `--target` was the repository **root** — a subdirectory is refused with exit 2.
- All six probes exit 1 with their own tag; `git rev-parse HEAD` unchanged.
- Overlay mode only: `git status --porcelain`, `git diff`, `git diff --cached` all empty.

## Running the tests (blocks, not everything)
```bash
python -B tests/blocks.py --list        # root hook doctor report repair bootstrap overlay gates ...
python -B tests/blocks.py doctor        # only the block you touched
python -B tests/blocks.py all           # before shipping
python -B tests/mutation_check_structure.py   # proves the tests can fail (~2 min)
```
`tests/harness.py` builds a real git repo per test and runs the real CLI; nothing is mocked.

## [ANTI] Common Rationalizations
Eight canonical rationalizations (skipping the hook, CRLF without pins, live secret probes, rule
duplication, expanded anchors, stale hooks, fork pollution, silent bloat) and their mechanical guards
live in [references/anti-patterns.md](references/anti-patterns.md).

**Non-negotiable**: a bootstrap that cannot prove its gate blocks something, and cannot prove it left the
tracked tree untouched, has been verified only by execution — not by evidence.
