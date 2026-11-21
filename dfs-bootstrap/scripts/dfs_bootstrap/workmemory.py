"""The five-piece shared working memory.

The scaffold used to key off the *directory*: `WORKMEMORY/` existing at all meant "agent keeps its own
history, skipping". A repo with only `work.log` therefore stayed incomplete forever while the injected
anchor told every session to read `WORKMEMORY/INDEX.md` — a permanent dead reference. Completion is now
per file, and existing files are never touched.
"""
from __future__ import annotations

import pathlib
import time

from .constants import TEMPLATES, VAULT_ROOT_TOKEN, WORKMEMORY_FILES
from .fsio import write_text
from .report import say


def _render(template: pathlib.Path, project: str, stamp: str) -> str:
    body = template.read_text(encoding="utf-8")
    return (
        body.replace("{{PROJECT_NAME}}", project)
        .replace("{{TIMESTAMP}}", stamp)
        .replace("{{VAULT_ROOT}}", VAULT_ROOT_TOKEN)
    )


def scaffold(target: pathlib.Path, dry_run: bool) -> None:
    dest = target / "WORKMEMORY"
    missing_templates = [name for name in WORKMEMORY_FILES if not (TEMPLATES / "workmemory" / name).is_file()]
    if missing_templates:
        say("ERR", f"WORKMEMORY template(s) missing from {TEMPLATES / 'workmemory'}: {missing_templates}")
        raise SystemExit(2)

    absent = [name for name in WORKMEMORY_FILES if not (dest / name).exists()]
    if not absent:
        say("OK", f"WORKMEMORY/ complete ({len(WORKMEMORY_FILES)}/{len(WORKMEMORY_FILES)}) — nothing to scaffold")
        return

    project = target.resolve().name
    stamp = time.strftime("%Y-%m-%d %H:%M")
    for name in absent:
        write_text(dest / name, _render(TEMPLATES / "workmemory" / name, project, stamp), dry_run,
                   planned=f"would create WORKMEMORY/{name}")
    kept = len(WORKMEMORY_FILES) - len(absent)
    detail = f" ({kept} existing file(s) kept)" if kept else ""
    if not dry_run:
        say("OK", f"scaffolded {len(absent)}/{len(WORKMEMORY_FILES)} file(s) into WORKMEMORY/ "
                  f"for '{project}'{detail}")
