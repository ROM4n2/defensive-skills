#!/usr/bin/env python3
"""Install the Defensive Skills into a harness skills directory.

Tiers come from `README.md`'s catalogue table rather than a third copy of the rule: that table is
verified against the tree by `tests/test_readme_skill_table.py`, so it is the manifest. One place
defines what a skill depends on, and a gate keeps it true.

    python install.py --target ~/.codex/skills              # all 23
    python install.py --target ~/.claude/skills --tier A    # only the 5 with no prerequisites
    python install.py --target ./vendor/skills --mode copy --dry-run

Exit codes: 0 installed, 2 bad usage/precondition, 3 refused to overwrite.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent
ROW = re.compile(
    r"^\|\s*(?:\*\*(?:主链|chain)\*\*\s+)?`(?P<name>dfs[a-z0-9-]*)`\s*\|[^|]*\|(?P<tier>[^|]*)\|",
    re.M,
)
LABEL_TO_TIER = {"—": "A", "需知识库": "B", "knowledge base": "B", "需额外资产": "C", "extra assets": "C"}


def tiers_from_readme() -> dict[str, str]:
    readme = REPO / "README.md"
    if not readme.is_file():
        print(f"[ERR] {readme} not found — run this from a DFS checkout", file=sys.stderr)
        raise SystemExit(2)
    tiers = {}
    for m in ROW.finditer(readme.read_text(encoding="utf-8")):
        label = m.group("tier").strip()
        if label not in LABEL_TO_TIER:
            print(f"[ERR] unrecognised prerequisite label {label!r} for {m.group('name')} in README.md",
                  file=sys.stderr)
            raise SystemExit(2)
        tiers[m.group("name")] = LABEL_TO_TIER[label]
    if len(tiers) < 20:
        print(f"[ERR] parsed only {len(tiers)} skill rows from README.md — refusing to install a partial set",
              file=sys.stderr)
        raise SystemExit(2)
    return tiers


def default_mode() -> str:
    return "copy" if os.name == "nt" else "link"


def install_one(src: pathlib.Path, dest: pathlib.Path, mode: str, force: bool, dry_run: bool) -> str:
    if dest.exists() or dest.is_symlink():
        if not force:
            return f"SKIP (exists, and no --force): {dest}"
        if not dry_run:
            shutil.rmtree(dest) if dest.is_dir() and not dest.is_symlink() else dest.unlink()
    if dry_run:
        return f"DRY would {mode} {src.name} -> {dest}"
    if mode == "link":
        try:
            os.symlink(src.resolve(), dest, target_is_directory=True)
            return f"LINK {dest}"
        except OSError as exc:  # Windows without developer mode, for instance
            print(f"  [WARN] symlink failed ({exc}); falling back to copy")
            mode = "copy"
    shutil.copytree(src, dest)
    return f"COPY {dest}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Install Defensive Skills into a harness skills directory")
    ap.add_argument("--target", required=True, help="harness skills directory (created if absent)")
    ap.add_argument("--tier", default="all", choices=["all", "A", "B", "C"],
                    help="A: no prerequisites, B: needs a knowledge base, C: needs extra assets")
    ap.add_argument("--mode", default=default_mode(), choices=["link", "copy"])
    ap.add_argument("--force", action="store_true", help="replace an existing destination entry")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    tiers = tiers_from_readme()
    wanted = sorted(n for n, t in tiers.items() if args.tier == "all" or t == args.tier)
    if not wanted:
        print(f"[ERR] no skills match tier {args.tier}", file=sys.stderr)
        return 2

    target = pathlib.Path(args.target).expanduser()
    if not target.parent.exists():
        print(f"[ERR] parent of --target does not exist: {target.parent}", file=sys.stderr)
        return 2
    missing = [n for n in wanted if not (REPO / n / "SKILL.md").is_file()]
    if missing:
        print(f"[ERR] README lists skills with no SKILL.md on disk: {missing}", file=sys.stderr)
        return 2

    print(f"DFS install -> {target}  ({len(wanted)} skills, tier={args.tier}, mode={args.mode}"
          f"{', dry-run' if args.dry_run else ''})")
    print("-" * 68)
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)
    refused = 0
    for name in wanted:
        line = install_one(REPO / name, target / name, args.mode, args.force, args.dry_run)
        refused += line.startswith("SKIP")
        print(f"  {line}")
    print("-" * 68)
    if refused and not args.force:
        print(f"  {refused} destination(s) already existed; re-run with --force to replace them")
    print("Knowledge layer (optional): register the bundled MCP server so the skills can retrieve")
    print(f"  {{ \"mcpServers\": {{ \"coding-vault-search\": {{ \"command\": \"python\",")
    print(f"    \"args\": [\"{REPO / 'mcp' / 'knowledge_server.py'}\", \"--root\", \"<your knowledge root>\"] }} }} }}")
    print("  Or use the file-level fallback table in mcp/README.md.")
    return 3 if refused and not args.force else 0


if __name__ == "__main__":
    raise SystemExit(main())
