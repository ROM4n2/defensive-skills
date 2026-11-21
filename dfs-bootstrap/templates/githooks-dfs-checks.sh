#!/usr/bin/env bash
# dfs-bootstrap reusable gate runner — SOURCE this from a project-owned hook, never install it as a hook.
#
# Usage (in .githooks/pre-commit, AFTER your own checks):
#   ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
#   [ -f "$ROOT/.githooks/dfs-checks.sh" ] && . "$ROOT/.githooks/dfs-checks.sh"
#
# Contract:
# - Adds no EOL/secret checks of its own (your hook owns those) — two GATES only.
# - hygiene: --staged, blocks (seconds). structure: whole graph (~8s on a 500-module repo) — OFF by
#   default; set DFS_STRUCTURE_LOCAL=1 to also run it locally. The authoritative run belongs in CI
#   via `bootstrap.py --emit-ci github`, where nobody waits for it. Do NOT move it into the commit
#   path by default: an 8s pause on every Python commit trains people to use --no-verify.
# - Exit 0 on success; on failure prints the gate's output and returns 1. Your hook must `|| exit 1`.
# - Never touches core.hooksPath or any tracked file. Safe to source repeatedly.

dfs_checks_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

dfs_checks_py=""
for dfs_cand in "$dfs_checks_root"/.venv/Scripts/python.exe "$dfs_checks_root"/.venv/bin/python; do
    if [ -x "$dfs_cand" ]; then dfs_checks_py="$dfs_cand"; break; fi
done
[ -n "$dfs_checks_py" ] || dfs_checks_py="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"

if [ -z "$dfs_checks_py" ]; then
    printf '[dfs-checks] no python interpreter found; gates skipped\n' >&2
    return 0 2>/dev/null || exit 0
fi

if [ -f "$dfs_checks_root/scripts/check_repo_hygiene.py" ]; then
    dfs_hyg_out="$("$dfs_checks_py" -B "$dfs_checks_root/scripts/check_repo_hygiene.py" --staged 2>&1)"
    if [ $? -ne 0 ]; then
        printf '%s\n' "$dfs_hyg_out" >&2
        printf '[dfs-checks] hygiene gate failed\n' >&2
        return 1 2>/dev/null || exit 1
    fi
fi

if [ "${DFS_STRUCTURE_LOCAL:-0}" = "1" ] && \
   [ -f "$dfs_checks_root/scripts/check_repo_structure.py" ] && \
   [ -n "$(git diff --cached --name-only --diff-filter=ACMR -- '*.py')" ]; then
    dfs_struct_out="$("$dfs_checks_py" -B "$dfs_checks_root/scripts/check_repo_structure.py" --all 2>&1)"
    if [ $? -ne 0 ]; then
        printf '%s\n' "$dfs_struct_out" >&2
        printf '[dfs-checks] structure gate failed\n' >&2
        return 1 2>/dev/null || exit 1
    fi
fi

return 0 2>/dev/null || exit 0
