"""Output vocabulary. One rule: a tag must describe what actually happened.

`--dry-run` used to print `[OK] added 13 pattern(s)` for work it had not done, because each writer
printed its success line unconditionally and the dry-run branch only added a `[DRY]` line next to it.
An agent filtering on `[OK]` then believed the plan was the result. Every writer now calls
:func:`done` with both phrasings and the tag is derived from ``dry_run`` in one place.
"""
from __future__ import annotations


def say(tag: str, message: str) -> None:
    print(f"  [{tag}] {message}")


def done(dry_run: bool, planned: str, performed: str) -> None:
    """Report a write: `[DRY] would ...` before it happens, `[OK] ...` after it did."""
    if dry_run:
        say("DRY", planned)
    else:
        say("OK", performed)


def note(dry_run: bool, planned: str, performed: str) -> None:
    """Same contract as :func:`done` but for `[GIT]`-class side effects."""
    if dry_run:
        say("DRY", planned)
    else:
        say("GIT", performed)
