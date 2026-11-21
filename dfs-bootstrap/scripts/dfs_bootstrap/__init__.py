"""Implementation package for the dfs-bootstrap CLI.

`scripts/bootstrap.py` stays a thin entrypoint so the mutation harness, the tests and the docs keep
one stable path to run; everything with behavior lives here, grouped by concern:

    constants   literals both the writers and doctor agree on
    report      the [OK]/[DRY]/[WARN] vocabulary (and the dry-run honesty rules)
    fsio        atomic writes — a half-written hook or gate must be impossible
    gitops      the handful of git queries and config writes we rely on
    hook        hook install + core.hooksPath activation
    gates       the two stdlib gates and their version drift
    anchors     AGENTS.md / CLAUDE.md / the private overlay anchor
    workmemory  the five-piece shared working memory
    doctor      read-only capability report (mode aware, exit codes 0/1/2)
    cli         argument parsing and the phase order
"""
