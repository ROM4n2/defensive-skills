"""Ignore / attributes writers: the two tracked files, and their overlay-local counterparts."""
from __future__ import annotations

import pathlib

from .constants import (
    ATTRIBUTES_HEADER,
    EXCLUDE_HEADER,
    GITATTRIBUTES_HEADER,
    GITATTRIBUTES_LINES,
    IGNORE_HEADER,
    OVERLAY_PRIVATE_PATHS,
    REQUIRED_IGNORES,
)
from .fsio import append_text
from .report import say


def _ensure(path: pathlib.Path, wanted: list[str], header: str, dry_run: bool, noun: str) -> list[str]:
    """Append only the missing lines; report the plan in dry-run instead of claiming the result."""
    existing = path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []
    missing = [line for line in wanted if line not in existing]
    if not missing:
        say("OK", f"{path.name} already carries all {len(wanted)} {noun}(s)")
        return []
    prefix = "" if not existing else "\n"
    body = f"{prefix}{header}\n" + "\n".join(missing) + "\n"
    append_text(path, body, dry_run,
                planned=f"would append {len(missing)} {noun}(s) to {path}: {', '.join(missing)}")
    if not dry_run:
        say("OK", f"added {len(missing)} {noun}(s) to {path.name}")
    return missing


def ensure_gitignore(target: pathlib.Path, dry_run: bool) -> list[str]:
    return _ensure(target / ".gitignore", REQUIRED_IGNORES, IGNORE_HEADER, dry_run, "required pattern")


def ensure_gitattributes(target: pathlib.Path, dry_run: bool) -> list[str]:
    """Pin LF for the files whose line endings are load-bearing (hook shebang, work log)."""
    return _ensure(target / ".gitattributes", GITATTRIBUTES_LINES, GITATTRIBUTES_HEADER, dry_run, "LF pin")


def ensure_local_exclude(target: pathlib.Path, dry_run: bool) -> list[str]:
    """Overlay: hide private scaffolding from git without touching the tracked .gitignore."""
    wanted = [*OVERLAY_PRIVATE_PATHS, *REQUIRED_IGNORES]
    return _ensure(target / ".git" / "info" / "exclude", wanted, EXCLUDE_HEADER, dry_run, "private pattern")


def ensure_local_attributes(target: pathlib.Path, dry_run: bool) -> list[str]:
    """Overlay: `$GIT_DIR/info/attributes` outranks every other source, so the pins stay local."""
    return _ensure(target / ".git" / "info" / "attributes", GITATTRIBUTES_LINES, ATTRIBUTES_HEADER,
                   dry_run, "LF pin")
