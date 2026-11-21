"""The git facts bootstrap depends on, each in one place.

Two of these are load-bearing beyond convenience:

* :func:`toplevel` — bootstrap must know whether it was pointed at the root of a repository or at a
  subdirectory of one. Treating the latter as "no repository" created a nested repo, wrote anchors
  into the outer repo's tracked files and then reported the outer tree as clean.
* :func:`index_mode` / :func:`record_exec_bit` — on Windows ``core.filemode=false`` makes
  ``os.chmod`` invisible to git, so a committed hook lands as 100644 and every POSIX clone ignores
  it with "hook was ignored because it is not set as executable".
"""
from __future__ import annotations

import pathlib
import subprocess

from .constants import HOOKS_PATH_BACKUP_KEY


def run_git(target: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def toplevel(target: pathlib.Path) -> pathlib.Path | None:
    """The work-tree root containing `target`, or None when it is not inside a repository."""
    proc = run_git(target, "rev-parse", "--show-toplevel")
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return pathlib.Path(proc.stdout.strip()).resolve()
    except OSError:
        return None


def is_tracked(target: pathlib.Path, rel: str) -> bool:
    """True when git already tracks `rel` — i.e. the file belongs to upstream, not to us."""
    return run_git(target, "ls-files", "--error-unmatch", "--", rel).returncode == 0


def hooks_path(target: pathlib.Path) -> str | None:
    proc = run_git(target, "config", "--get", "core.hooksPath")
    value = proc.stdout.strip()
    return value or None


def set_hooks_path(target: pathlib.Path, value: str, *, previous: str | None) -> bool:
    """Point git at `value`, remembering what it used to be so the change is reversible."""
    if previous:
        run_git(target, "config", "--local", HOOKS_PATH_BACKUP_KEY, previous)
    else:
        run_git(target, "config", "--local", "--unset", HOOKS_PATH_BACKUP_KEY)
    return run_git(target, "config", "--local", "core.hooksPath", value).returncode == 0


def index_mode(target: pathlib.Path, rel: str) -> str | None:
    """The mode git recorded for `rel` (``100755`` / ``100644``), or None when untracked."""
    proc = run_git(target, "ls-files", "-s", "--", rel)
    line = proc.stdout.strip().splitlines()
    if not line:
        return None
    return line[0].split(maxsplit=1)[0]


def record_exec_bit(target: pathlib.Path, rel: str) -> str | None:
    """Force 100755 into the index for a tracked file; returns the resulting mode.

    Only meaningful where `core.filemode` is false (Windows): the working-tree chmod is invisible to
    git there, so the mode has to be written to the index explicitly. Staging a mode-only change is
    visible in `git status` — that is the point, it is a real fix that a reviewer can see.
    """
    if index_mode(target, rel) is None:
        return None
    run_git(target, "update-index", "--chmod=+x", "--", rel)
    return index_mode(target, rel)


def cleanliness(target: pathlib.Path) -> tuple[str, str, str]:
    """(status, diff, staged-names) — the overlay contract read back from git, not assumed."""
    return (
        run_git(target, "status", "--porcelain").stdout.strip(),
        run_git(target, "diff").stdout.strip(),
        run_git(target, "diff", "--cached", "--name-only").stdout.strip(),
    )
