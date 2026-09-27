#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conventional Commits Changelog & SemVer Bump Generator.

Usage:
    python changelog_gen.py [--version <new_ver>] [--dry-run]
"""

import argparse
import re
import subprocess
import sys
from datetime import date


def run_git(cmd: list[str]) -> str:
    res = subprocess.run(["git"] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if res.returncode != 0:
        return ""
    return res.stdout.strip()


def get_commit_range() -> tuple[str, str]:
    latest_tag = run_git(["describe", "--tags", "--abbrev=0"])
    if latest_tag:
        return latest_tag, f"{latest_tag}..HEAD"
    first_commit = run_git(["rev-list", "--max-parents=0", "HEAD"])
    return "Initial", f"{first_commit}..HEAD" if first_commit else "HEAD"


def parse_commits(commit_range: str) -> dict[str, list[str]]:
    raw = run_git(["log", commit_range, "--pretty=format:%h %s"])
    categories = {
        "breaking": [],
        "features": [],
        "fixes": [],
        "perf": [],
        "others": [],
    }
    if not raw:
        return categories

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        sha = parts[0]
        msg = parts[1] if len(parts) > 1 else ""

        if "BREAKING CHANGE:" in msg or "!:" in msg:
            categories["breaking"].append(f"- **{msg}** (`{sha}`)")
        elif msg.startswith("feat"):
            categories["features"].append(f"- {msg} (`{sha}`)")
        elif msg.startswith("fix"):
            categories["fixes"].append(f"- {msg} (`{sha}`)")
        elif msg.startswith("perf") or msg.startswith("refactor"):
            categories["perf"].append(f"- {msg} (`{sha}`)")
        else:
            categories["others"].append(f"- {msg} (`{sha}`)")
    return categories


def suggest_bump(categories: dict[str, list[str]]) -> str:
    if categories["breaking"]:
        return "MAJOR"
    if categories["features"]:
        return "MINOR"
    return "PATCH"


def generate_markdown(version: str, categories: dict[str, list[str]]) -> str:
    today = date.today().isoformat()
    lines = [f"## [v{version}] - {today}\n"]
    if categories["breaking"]:
        lines.append("### ⚠️ Breaking Changes")
        lines.extend(categories["breaking"])
        lines.append("")
    if categories["features"]:
        lines.append("### 🚀 Features")
        lines.extend(categories["features"])
        lines.append("")
    if categories["fixes"]:
        lines.append("### 🐛 Bug Fixes")
        lines.extend(categories["fixes"])
        lines.append("")
    if categories["perf"]:
        lines.append("### ⚡ Performance & Refactoring")
        lines.extend(categories["perf"])
        lines.append("")
    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Changelog Generator")
    parser.add_argument("--version", default="0.1.0", help="Release version")
    parser.add_argument("--dry-run", action="store_true", help="Print without modifying CHANGELOG.md")
    args = parser.parse_args()

    latest_tag, crange = get_commit_range()
    cats = parse_commits(crange)
    bump = suggest_bump(cats)
    md = generate_markdown(args.version, cats)

    print(f"📦 Previous Tag: {latest_tag} | Recommended Bump: {bump}")
    print("=" * 60)
    print(md)
    print("=" * 60)

    if not args.dry_run:
        try:
            with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                existing = f.read()
        except FileNotFoundError:
            existing = ""
        with open("CHANGELOG.md", "w", encoding="utf-8") as f:
            f.write(md + "\n\n" + existing)
        print("✅ Prepend complete to CHANGELOG.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
