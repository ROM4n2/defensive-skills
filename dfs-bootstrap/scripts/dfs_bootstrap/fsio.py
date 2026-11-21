"""Atomic writes. A truncated hook or gate is the failure class this module exists to remove.

The old gate upgrade did ``dest.replace(.dfsbak)`` and then truncated the destination in place: a
kill, a full disk, or Defender holding the handle left a 0-byte ``check_repo_hygiene.py`` behind, and
that file was then permanently classified as "project-owned — preserved" (no version marker), so the
tool could never repair it. Every write here goes to a sibling temp file and is swapped in with
``os.replace``; a lock on Windows is retried a few times instead of exploding.
"""
from __future__ import annotations

import os
import pathlib
import tempfile
import time

from .report import say

_RETRIES = 3
_RETRY_SLEEP = 0.2


def _atomic_replace(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    tmp = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        last: OSError | None = None
        for attempt in range(_RETRIES):
            try:
                os.replace(tmp, path)
                return
            except OSError as exc:  # Windows: a scanner or the indexer can hold the target briefly
                last = exc
                time.sleep(_RETRY_SLEEP * (attempt + 1))
        raise last if last is not None else OSError(f"could not replace {path}")
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def write_text(path: pathlib.Path, text: str, dry_run: bool, *, planned: str | None = None) -> bool:
    """UTF-8, no BOM, LF. Returns True when the file was written."""
    if dry_run:
        say("DRY", planned or f"would write {path}")
        return False
    _atomic_replace(path, text.encode("utf-8"))
    return True


def append_text(path: pathlib.Path, text: str, dry_run: bool, *, planned: str | None = None) -> bool:
    """Append without losing what is already there (read, concatenate, atomic replace)."""
    if dry_run:
        say("DRY", planned or f"would append {len(text)} bytes to {path}")
        return False
    existing = path.read_bytes() if path.exists() else b""
    _atomic_replace(path, existing + text.encode("utf-8"))
    return True


def write_bytes(path: pathlib.Path, body: bytes, dry_run: bool, *, planned: str | None = None) -> bool:
    if dry_run:
        say("DRY", planned or f"would write {path} ({len(body)} bytes)")
        return False
    _atomic_replace(path, body)
    return True


def keep_backup(path: pathlib.Path) -> pathlib.Path:
    """Copy the current bytes to `<name>.dfsbak` before an upgrade overwrites them."""
    backup = path.with_suffix(path.suffix + ".dfsbak")
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(path.read_bytes())
    return backup
