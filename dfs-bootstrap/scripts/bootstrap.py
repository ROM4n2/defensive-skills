#!/usr/bin/env python3
"""DFS bootstrap — idempotent repo scaffolding. UTF-8, no BOM, LF.

This file is the entrypoint only; behavior lives in the ``dfs_bootstrap`` package next to it:

    constants   literals the writers and doctor agree on
    report      the [OK]/[DRY]/[WARN] vocabulary — a tag must describe what actually happened
    fsio        atomic writes (temp file + os.replace, retried on Windows file locks)
    gitops      the git queries we rely on: toplevel, is_tracked, hooksPath, index mode
    hook        hook install + core.hooksPath activation (activation runs every time, not only
                when this run wrote the hook — the config does not travel with a clone)
    gates       the two stdlib gates, whole-file version markers, 0-byte repair
    anchors     AGENTS.md (single source of truth), CLAUDE.md (2-line pointer), overlay layer
    workmemory  5-piece shared working memory, completed per file
    doctor      read-only capability report: mode aware, exit 0 clean / 1 gaps / 2 cannot run
    cli         argument parsing, the repository-root guard, and the phase order

Two modes. `owner` (default) writes artifacts to the working tree as tracked files. `overlay` targets
someone else's upstream: the same artifacts are written but excluded locally (`.git/info/exclude`, LF
pins in `.git/info/attributes`, hook in `.git/dfs-hooks`), so no tracked file changes and a pull
request contains only real work. Mode semantics: `references/overlay-mode.md`.

Anchors use `$WIKI_PATH`, never an absolute root: a literal path fails the repo's own `[ABS_PATH]`
gate and is wrong on any other machine. A missing template exits 2 rather than warning — a scaffold
that silently skips files is the failure class this suite exists to prevent.

Usage:
    python bootstrap.py [--target DIR] [--vault-root PATH] [--dry-run] [--mode owner|overlay]
                        [--legacy-aliases] [--no-gates] [--force-hook] [--take-hooks-path]
                        [--doctor] [--doctor-mode auto|owner|overlay] [--verify]
                        [--emit-checks] [--emit-ci github]
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dfs_bootstrap.anchors import (  # noqa: E402,F401
    has_rule_anchor,
    rule_anchor_text,
    workmemory_anchor_text,
)
from dfs_bootstrap.cli import (  # noqa: E402,F401
    ensure_git_repository,
    environment_baseline,
    main,
    resolve_vault_root,
)
from dfs_bootstrap.constants import (  # noqa: E402,F401
    GATE_VERSION,
    HOOK_VERSION,
    POINTER_BODY,
    REQUIRED_IGNORES,
)

if __name__ == "__main__":
    raise SystemExit(main())
