"""The two stdlib gates and their version drift.

Same contract as the hook (a project-owned copy is never overwritten) with two repairs:

* the marker is read from the whole file, not the first five lines — a gate whose header grows a
  comment used to be reclassified as project-owned and never updated again;
* a 0-byte destination is treated as a damaged DFS file, not as someone's own copy. The old
  replace-then-truncate upgrade could leave exactly that, and "preserved" made it permanent.
"""
from __future__ import annotations

import pathlib

from .constants import (
    GATE_TEMPLATES,
    GATE_VERSION,
    GATE_VERSION_MARKER,
    LOCAL_GATE_DEST,
    LOCAL_GATE_TEMPLATE,
    LOCAL_GATE_VERSION,
    LOCAL_GATE_VERSION_MARKER,
)
from .fsio import keep_backup, write_text
from .report import say
from .hook import version_key


def _version_at(path: pathlib.Path, marker: str) -> str | None:
    """Read a DFS version marker from anywhere in the file, or None when project-owned."""
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(marker):
            return line.split(marker, 1)[1].strip()
    return None


def installed_version(path: pathlib.Path) -> str | None:
    """Read the tracked-gate version marker from anywhere in the file."""
    return _version_at(path, GATE_VERSION_MARKER)


def is_damaged(path: pathlib.Path) -> bool:
    """True for a DFS gate that was interrupted mid-write (0 bytes)."""
    return path.is_file() and path.stat().st_size == 0


def install_gates(target: pathlib.Path, dry_run: bool) -> None:
    wanted_key = version_key(GATE_VERSION)
    for template, dest_rel in GATE_TEMPLATES:
        dest = target / dest_rel
        rel = dest_rel.as_posix()
        damaged = is_damaged(dest)
        installed = None if damaged else installed_version(dest)
        if damaged:
            say("WARN", f"{rel} is 0 bytes (an upgrade was interrupted) — rewriting from template")
        elif dest.exists() and installed is None:
            say("OK", f"{rel} present (project-owned, no gate version marker) — preserved")
            say("NEXT", f"run `python scripts/bootstrap.py --doctor --target <repo>` to see whether "
                        f"{rel} lacks upstream fixes")
            continue
        key = version_key(installed) if installed else None
        if key is not None and wanted_key is not None and key == wanted_key:
            say("OK", f"{rel} already at gate version {GATE_VERSION}")
            continue
        if key is not None and wanted_key is not None and key > wanted_key:
            say("OK", f"{rel} is newer (v{installed} > v{GATE_VERSION}) — left as is")
            continue
        if not template.is_file():
            say("ERR", f"gate template missing: {template}")
            raise SystemExit(2)
        body = template.read_text(encoding="utf-8")
        backup = f", previous kept as {dest.name}.dfsbak" if dest.exists() else ""
        if dry_run:
            verb = f"v{installed} -> v{GATE_VERSION}" if installed else f"v{GATE_VERSION}"
            say("DRY", f"would write {rel} {verb}{backup}")
            continue
        if dest.exists():
            keep_backup(dest)
        write_text(dest, body, False)
        if installed:
            say("OK", f"upgraded {rel} v{installed} -> v{GATE_VERSION} (previous kept as {dest.name}.dfsbak)")
        elif damaged:
            say("OK", f"repaired {rel} to v{GATE_VERSION} (damaged copy kept as {dest.name}.dfsbak)")
        else:
            say("OK", f"installed {rel} v{GATE_VERSION} (stdlib only, no third-party imports)")


def install_local_gate(target: pathlib.Path, dry_run: bool) -> bool:
    """Install/upgrade the private fingerprint gate; True means a usable gate is present."""
    dest = target / LOCAL_GATE_DEST
    rel = LOCAL_GATE_DEST.as_posix()
    damaged = is_damaged(dest)
    installed = None if damaged else _version_at(dest, LOCAL_GATE_VERSION_MARKER)
    key = version_key(installed) if installed else None
    wanted = version_key(LOCAL_GATE_VERSION)

    if dest.exists() and not damaged and installed is None:
        say("OK", f"{rel} present (project-owned, no local version marker) — preserved")
        return True
    if key is not None and wanted is not None and key > wanted:
        say("OK", f"{rel} is newer (v{installed} > v{LOCAL_GATE_VERSION}) — left as is")
        return True
    if key is not None and wanted is not None and key == wanted:
        say("OK", f"{rel} already at local gate version {LOCAL_GATE_VERSION}")
        return True
    if not LOCAL_GATE_TEMPLATE.is_file():
        say("ERR", f"local gate template missing: {LOCAL_GATE_TEMPLATE}")
        raise SystemExit(2)

    body = LOCAL_GATE_TEMPLATE.read_text(encoding="utf-8")
    backup = f", previous kept as {dest.name}.dfsbak" if dest.exists() else ""
    if dry_run:
        verb = f"v{installed} -> v{LOCAL_GATE_VERSION}" if installed else f"v{LOCAL_GATE_VERSION}"
        say("DRY", f"would write {rel} {verb}{backup}")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        keep_backup(dest)
    write_text(dest, body, False)
    if damaged:
        say("OK", f"repaired {rel} to v{LOCAL_GATE_VERSION} (damaged copy kept as {dest.name}.dfsbak)")
        return True
    if installed:
        say("OK", f"upgraded {rel} v{installed} -> v{LOCAL_GATE_VERSION} "
                  f"(previous kept as {dest.name}.dfsbak)")
        return True
    say("OK", f"installed {rel} v{LOCAL_GATE_VERSION} (private .git/ state, pattern files untouched)")
    return True
