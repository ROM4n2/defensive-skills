"""Hook installation and — the part that used to be missing — hook activation.

`core.hooksPath` is local config: it does not travel with a clone. The old code only set it when it
had written the hook that run, so a teammate's first `git clone && bootstrap` printed two `[OK]` lines
and left every gate disconnected. Activation is now its own step, run every time.

Activation is also the one place that can silently disable someone else's gate: a repo may point
`core.hooksPath` at its own directory (DeLector points at `.git/local-hooks`, which chains a
machine-local fingerprint gate). Overwriting that is allowed only with an explicit flag, and the
previous value is recorded in git config so it can be restored.
"""
from __future__ import annotations

import os
import pathlib

from . import gitops
from .constants import (
    HOOK_VERSION,
    HOOK_VERSION_MARKER,
    OVERLAY_HOOK_DIR,
    TEMPLATES,
)
from .fsio import keep_backup
from .report import say

# Directories the shipped hook already chains to, so repointing away from them disables nothing.
CHAINED_DIRS = (".githooks", ".git/hooks")


def installed_version(hook: pathlib.Path) -> str | None:
    """Read the DFS version marker from an installed hook, or None when it is project-owned."""
    if not hook.is_file():
        return None
    for line in hook.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(HOOK_VERSION_MARKER):
            return line.split(HOOK_VERSION_MARKER, 1)[1].strip()
    return None


def version_key(value: str) -> tuple[int, ...] | None:
    """"5" -> (5,), "5.2" -> (5, 2); None when the marker is not numeric."""
    parts = value.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def hook_path(target: pathlib.Path, *, overlay: bool) -> pathlib.Path:
    return target / (OVERLAY_HOOK_DIR / "pre-commit" if overlay else pathlib.Path(".githooks") / "pre-commit")


def _write_hook(hook: pathlib.Path, body: bytes, dry_run: bool, *, keep: bool) -> bool:
    backup = hook.with_suffix(".dfsbak")
    planned = f"would write {hook.name} ({len(body)} bytes, LF, no BOM)"
    if keep:
        planned += f", previous kept as {backup.name}"
    if dry_run:
        say("DRY", planned)
        return False
    hook.parent.mkdir(parents=True, exist_ok=True)
    if keep and hook.exists():
        keep_backup(hook)
    hook.write_bytes(body)
    os.chmod(hook, 0o755)
    return True


def _activate(
    target: pathlib.Path,
    dry_run: bool,
    *,
    overlay: bool,
    wrote_hook: bool,
    take_hooks_path: bool,
) -> None:
    wanted = (OVERLAY_HOOK_DIR if overlay else pathlib.Path(".githooks")).as_posix()
    current = gitops.hooks_path(target)
    if current == wanted:
        say("OK", f"core.hooksPath already {wanted}")
        return
    if current is None:
        say("DRY" if dry_run else "GIT", f"core.hooksPath: (unset) -> {wanted}")
        if not dry_run:
            gitops.set_hooks_path(target, wanted, previous=None)
        return
    if not wrote_hook:
        say("OK", f"core.hooksPath stays {current} — your own hook chain keeps running")
        return
    # The shipped hook chains to $DFS_UPSTREAM_HOOKS, .githooks/ and .git/hooks/, so repointing away
    # from one of those keeps the upstream gate alive. Anything else (a repo's own hooks directory)
    # would simply stop running, so that switch needs the explicit flag.
    if current not in CHAINED_DIRS and not take_hooks_path:
        say("WARN", f"core.hooksPath points at {current}; not overwriting it: hooks there would stop running")
        say("NEXT", "re-run with --take-hooks-path to switch (the old value is saved in "
                    "dfs.bootstrap.hooksPathBackup)")
        return
    say("DRY" if dry_run else "GIT", f"core.hooksPath: {current} -> {wanted}")
    if current in CHAINED_DIRS:
        say("OK", f"{current}/pre-commit keeps running through the hook's upstream chain")
    else:
        say("WARN", f"hooks under {current} are no longer run by git; restore with "
                    f"`git config core.hooksPath {current}`")
    if not dry_run:
        gitops.set_hooks_path(target, wanted, previous=current)


def _record_exec_bit(target: pathlib.Path, hook: pathlib.Path, dry_run: bool) -> None:
    """Make the 0755 mode survive the index — Windows cannot record it from the working tree."""
    rel = hook.relative_to(target).as_posix()
    if dry_run:
        say("DRY", f"would ensure {rel} is 100755 in the index")
        return
    mode = gitops.index_mode(target, rel)
    if mode is None:
        say("NEXT", f"`git add --chmod=+x {rel}` before committing; Windows records 100644, and "
                    f"POSIX clones then ignore the hook")
        return
    if mode == "100755":
        say("OK", f"{rel} index mode 100755")
        return
    new_mode = gitops.record_exec_bit(target, rel)
    say("GIT", f"{rel} index mode {mode} -> {new_mode} (a 100644 hook is ignored on POSIX clones)")


def _install_or_upgrade(
    target: pathlib.Path, hook: pathlib.Path, body: bytes, dry_run: bool
) -> bool:
    """Install when absent, upgrade when older, leave alone when current, newer, or project-owned."""
    label = hook.relative_to(target).as_posix()
    if not hook.exists():
        wrote = _write_hook(hook, body, dry_run, keep=False)
        if not dry_run:
            say("OK", f"installed {label} (LF, no BOM)")
        return wrote
    installed = installed_version(hook)
    if installed is None:
        say("OK", f"existing {label} preserved (project-owned, no DFS version marker)")
        say("NEXT", "run `python scripts/bootstrap.py --doctor --target <repo>` to see which "
                    "capabilities it actually has; `--emit-checks` adds our gates without replacing it")
        return False
    key, wanted_key = version_key(installed), version_key(HOOK_VERSION)
    if key is not None and wanted_key is not None and key > wanted_key:
        say("OK", f"existing {label} is newer (v{installed} > v{HOOK_VERSION}) — left as is")
        return False
    if key is not None and wanted_key is not None and key == wanted_key:
        say("OK", f"existing {label} already at version {HOOK_VERSION}")
        return False
    wrote = _write_hook(hook, body, dry_run, keep=True)
    if not dry_run:
        say("OK", f"upgraded hook v{installed} -> v{HOOK_VERSION} (previous kept as "
                  f"{hook.with_suffix('.dfsbak').name})")
    return wrote


def install_hook(
    target: pathlib.Path,
    dry_run: bool,
    *,
    force: bool = False,
    overlay: bool = False,
    take_hooks_path: bool = False,
) -> None:
    template = TEMPLATES / "githooks-pre-commit.sh"
    if not template.is_file():
        say("ERR", f"hook template missing: {template}")
        raise SystemExit(2)
    hook = hook_path(target, overlay=overlay)
    if hook.exists() and force:
        wrote = _write_hook(hook, body=template.read_bytes(), dry_run=dry_run, keep=True)
        if not dry_run:
            say("OK", f"hook force-installed (previous kept as {hook.with_suffix('.dfsbak').name})")
    else:
        wrote = _install_or_upgrade(target, hook, template.read_bytes(), dry_run)

    _activate(
        target, dry_run, overlay=overlay, wrote_hook=wrote,
        take_hooks_path=take_hooks_path,
    )
    if not overlay:
        _record_exec_bit(target, hook, dry_run)
