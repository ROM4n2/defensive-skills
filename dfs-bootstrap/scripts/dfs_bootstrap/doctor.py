"""Read-only capability report.

Three defects drove this rewrite:

* the hook was looked for at `.githooks/pre-commit` only. In overlay mode it installs to
  `.git/dfs-hooks/pre-commit`, so doctor reported it missing forever — a closed loop with no green.
* gate version gaps were printed but never reached the exit code, so `doctor || exit 1` in CI passed
  on a stale gate.
* capabilities were `token in text`, so a comment that merely mentions "secret scan" counted as a
  working secret scan. Textual detection is still used (a project hook can be any shape), but it is
  labelled as such, and `--verify` executes the DFS hook against a synthetic secret to prove it blocks.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

from . import gitops
from .constants import GATE_TEMPLATES, GATE_VERSION, OVERLAY_HOOK_DIR
from .gates import installed_version as gate_version
from .hook import hook_path, installed_version, version_key
from .report import say

# label, tokens that indicate the capability is *written into* the hook text
CAPABILITIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("secret scan (.env/key patterns)", ("NAME", "密钥", "secret", "PRIVATE KEY")),
    ("EOL check under .githooks/", ("EOL", "tr -cd '\\r'", "CRLF")),
    ("upstream chain", ("chain_upstream", "upstream hook")),
    ("hygiene gate", ("check_repo_hygiene", "dfs-checks")),
    ("structure gate", ("check_repo_structure", "dfs-checks")),
    ("allow-secret pragma", ("allow-secret",)),
)


def resolve_mode(target: pathlib.Path, mode: str) -> str:
    if mode != "auto":
        return mode
    return "overlay" if (target / OVERLAY_HOOK_DIR / "pre-commit").is_file() else "owner"


def _run_secret_probe(target: pathlib.Path, hook: pathlib.Path) -> tuple[bool, str]:
    """Execute the installed hook in a scratch repo against a synthetic key.

    The probe content is assembled at runtime on purpose: a literal `sk-…` in this file would trip
    the very scanners we ship. Returns (blocked, detail).
    """
    secret = "sk-" + "0" * 32
    with tempfile.TemporaryDirectory() as tmp:
        scratch = pathlib.Path(tmp)
        gitops.run_git(scratch, "init", "-q")
        gitops.run_git(scratch, "config", "user.email", "probe@example.invalid")
        gitops.run_git(scratch, "config", "user.name", "probe")
        dest = scratch / ".githooks" / "pre-commit"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(hook.read_bytes())
        gitops.run_git(scratch, "config", "core.hooksPath", ".githooks")
        (scratch / "leak.txt").write_text(f"token = {secret}\n", encoding="utf-8")
        gitops.run_git(scratch, "add", "-A")
        proc = gitops.run_git(scratch, "commit", "-m", "probe")
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0:
        return False, "the hook let a synthetic secret through"
    if "leak.txt" in output:
        return True, "hook blocked the synthetic secret (it named leak.txt)"
    return False, f"hook exited {proc.returncode} without naming the offending file"


def _report_capabilities(text: str, *, verify: bool, target: pathlib.Path, hook: pathlib.Path) -> int:
    missing = 0
    for label, tokens in CAPABILITIES:
        declared = any(token in text for token in tokens)
        if declared:
            say("OK", f"{label} (declared in hook text)")
        else:
            say("GAP", label)
            missing += 1
    if verify:
        blocked, detail = _run_secret_probe(target, hook)
        say("OK" if blocked else "GAP", f"secret scan probe: {detail}")
        missing += 0 if blocked else 1
    else:
        say("INFO", "capability detection is textual; `--verify` executes the DFS hook's secret probe")
    return missing


def _report_gates(target: pathlib.Path) -> int:
    gaps = 0
    wanted = version_key(GATE_VERSION)
    for _template, dest_rel in GATE_TEMPLATES:
        dest = target / dest_rel
        rel = dest_rel.as_posix()
        if not dest.is_file():
            say("GAP", f"{rel} missing")
            gaps += 1
            continue
        if dest.stat().st_size == 0:
            say("GAP", f"{rel} is 0 bytes (interrupted upgrade), re-run bootstrap")
            gaps += 1
            continue
        gv = gate_version(dest)
        if gv is None:
            say("INFO", f"{rel} has no gate version marker (project-owned, preserved by bootstrap)")
            continue
        key = version_key(gv)
        if key is not None and wanted is not None and key < wanted:
            say("GAP", f"{rel} v{gv} < v{GATE_VERSION}, re-run bootstrap to upgrade")
            gaps += 1
            continue
        say("OK", f"{rel} v{gv}")
    return gaps


def doctor(target: pathlib.Path, *, mode: str = "auto", verify: bool = False) -> int:
    resolved = resolve_mode(target, mode)
    hook = hook_path(target, overlay=resolved == "overlay")
    print(f"DFS doctor -> {target.resolve()}  [mode={resolved}]")
    print("-" * 68)
    if not hook.is_file():
        say("GAP", f"{hook.relative_to(target).as_posix()} missing — run bootstrap to install one")
        return 1
    text = hook.read_text(encoding="utf-8", errors="replace")
    version = installed_version(hook)
    say("OK" if version else "GAP",
        f"hook version marker: v{version}" if version else "no DFS version marker (project-owned)")

    missing = _report_capabilities(text, verify=verify, target=target, hook=hook)
    gates = _report_gates(target)
    path_hint = gitops.hooks_path(target)
    say("INFO", f"core.hooksPath = {path_hint or '(unset: git runs no hook at all)'}")
    if path_hint is None:
        say("GAP", "core.hooksPath is unset: the installed hook is never executed")
        missing += 1
    elif path_hint not in (".githooks", OVERLAY_HOOK_DIR.as_posix()):
        say("WARN", f"core.hooksPath points at {path_hint}; DFS hooks are not the ones running")

    if gates:
        say("NEXT", "re-run `python scripts/bootstrap.py --target <repo>` to upgrade DFS-marked gates")
    if missing:
        say("NEXT", "`--emit-checks` adds our gates to a project-owned hook without replacing it; "
                    "`--force-hook --take-hooks-path` replaces it (your own scans stop running)")
    if sys.stdout.isatty() and not missing and not gates:
        say("DONE", "no gaps")
    return 1 if (missing or gates) else 0
