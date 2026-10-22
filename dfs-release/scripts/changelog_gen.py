#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conventional Commits Changelog & SemVer Bump Generator.

Usage:
    python changelog_gen.py --version 1.4.0                  # dry-run (default): print only
    python changelog_gen.py --version 1.4.0 --write          # opt-in: edit CHANGELOG.md
    python changelog_gen.py --version 1.4.0 --version-file VERSION

Design rules (learned the hard way — see SKILL.md):
  * `--version` is **mandatory**: a silent default would write a garbage version header.
  * **Dry-run is the default.** The entry is inserted *before the first existing version
    heading*, so a curated header ("# Changelog" + a "latest version: vX.Y.Z" line +
    hand-written entries) is never clobbered and never reordered. The old implementation
    wrote `entry + "\\n\\n" + existing`, i.e. it dropped the new section **above the document
    title** — silently breaking any curated changelog.
  * Mechanical output is a **draft**. If the repo's changelog is hand-curated, use the printed
    text as input and edit by hand.
  * **Never trust the locale for decoding**: `subprocess(..., text=True)` uses the platform
    default (GBK on zh-CN Windows), so a single non-ASCII commit subject raises
    `UnicodeDecodeError` inside subprocess' reader thread, `stdout` comes back **None**, and the
    script dies with an unrelated `AttributeError`. Commit subjects are UTF-8 by convention ⇒
    decode them as UTF-8, and never assume `stdout` is a string.
"""

import argparse
import re
import subprocess
import sys
from datetime import date

# 一个"版本条目标题"：`## [v1.2.3] - 2026-01-01` / `### v1.2.3 · 标题` / `## 1.2.3`。
# 只认 H2/H3（H1 是文档标题），且必须含 x.y.z —— 免得把 `## Notes` 这类小节当条目锚点。
ENTRY_HEADING = re.compile(r"^#{2,3}\s+\S*?v?\d+\.\d+\.\d+")
SEMVER = re.compile(r"\d+\.\d+\.\d+")


def emit(text: str) -> None:
    """打印，且在控制台编码吃不下字符时降级 —— 绝不因为一行日志崩掉发版脚本。

  GBK 控制台打印 emoji（ / ℹ️ / ）会抛 UnicodeEncodeError；发版脚本在打印阶段
    崩掉，会把"其实已经写完盘"误报成失败。
    """
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def run_git(cmd: list[str]) -> str:
    res = subprocess.run(
        ["git"] + cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        # 提交信息按惯例是 UTF-8，绝不能靠 locale（zh-CN Windows 默认 GBK）。
        # errors="replace" 保证即使遇到坏字节也只丢字符、不炸线程。
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if res.returncode != 0 or res.stdout is None:
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
    lines.append("### ️ Breaking Changes")
        lines.extend(categories["breaking"])
        lines.append("")
    if categories["features"]:
    lines.append("### Features")
        lines.extend(categories["features"])
        lines.append("")
    if categories["fixes"]:
    lines.append("### Bug Fixes")
        lines.extend(categories["fixes"])
        lines.append("")
    if categories["perf"]:
    lines.append("### Performance & Refactoring")
        lines.extend(categories["perf"])
        lines.append("")
    return "\n".join(lines).strip()


def read_version_file(path: str) -> str:
    """从仓库的"单一真相源"里取出版本号（文件里第一个 x.y.z 即视为版本）。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    match = SEMVER.search(text)
    return match.group(0) if match else ""


def insert_entry(existing: str, entry: str) -> str:
    """把新条目插到**第一个既有版本标题之前**；标题与头部原样保留。

    末尾没有任何版本标题时（首次生成）追加到文件末尾，而不是覆盖。
    """
    lines = existing.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if ENTRY_HEADING.match(line):
            head = "".join(lines[:index])
            tail = "".join(lines[index:])
            separator = "" if head.endswith("\n\n") or not head.strip() else "\n"
            return f"{head}{separator}{entry.rstrip()}\n\n{tail}"
    return existing.rstrip() + "\n\n" + entry.rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Changelog Generator (dry-run by default)")
    parser.add_argument("--version", required=True, help="Release version, e.g. 1.4.0 (MANDATORY)")
    parser.add_argument("--write", action="store_true", help="Actually modify CHANGELOG.md (default: print only)")
    parser.add_argument("--dry-run", action="store_true", help="Print only (already the default)")
    parser.add_argument(
        "--version-file",
        default=None,
        help="Cross-check --version against the repo's single source of truth (first x.y.z in that file)",
    )
    parser.add_argument("--force", action="store_true", help="Allow --write despite a version mismatch")
    args = parser.parse_args()

    if args.write and args.dry_run:
        emit("[Error] --write 与 --dry-run 互斥：先 dry-run 看输出，再决定是否写盘。")
        return 2

    if args.version_file:
        declared = read_version_file(args.version_file)
        if not declared:
            emit(f"[Error] 从 {args.version_file} 读不出版本号（期望形如 x.y.z）")
            return 2
        if declared != args.version:
            emit(
                f"[Error] 版本不一致：--version={args.version} 而 {args.version_file} 里是 {declared}。\n"
                f"        先 bump 单一真相源（{args.version_file}）再发版 —— 两者分叉会让制品自称的版本\n"
                f"        与应用自报的版本不同，更新提示会永远显示落后。"
            )
            if not args.force:
                return 1

    latest_tag, crange = get_commit_range()
    cats = parse_commits(crange)
    bump = suggest_bump(cats)
    md = generate_markdown(args.version, cats)
    count = sum(len(v) for v in cats.values())

  emit(f" Previous Tag: {latest_tag} | Commits: {count} | Recommended Bump: {bump}")
    emit("=" * 60)
    emit(md)
    emit("=" * 60)

    if not args.write:
        emit("ℹ️  Dry-run（默认）。确认无误后加 --write 才写盘；人工策展的 changelog 请手工编辑。")
        return 0

    try:
        with open("CHANGELOG.md", encoding="utf-8") as f:
            existing = f.read()
    except FileNotFoundError:
        existing = ""
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(insert_entry(existing, md))
  emit(" 已插入 CHANGELOG.md（新条目位于第一个既有版本标题之前，头部未改动）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
