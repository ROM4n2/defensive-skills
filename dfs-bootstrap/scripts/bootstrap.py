#!/usr/bin/env python3
"""DFS bootstrap — cross-platform port of the private vault's PowerShell bootstrap.

Idempotent. Everything it writes is UTF-8 without BOM, LF endings.

  1. .gitignore  — appends the 11 required secret patterns if any is missing
  2. git hook    — installs `templates/githooks-pre-commit.sh` as `.githooks/pre-commit` and sets
                   `core.hooksPath`; an existing hook is never overwritten (projects keep their own
                   gatekeeper script)
  3. anchors     — injects the 3-line knowledge-base anchor into CLAUDE.md / .agent-rules.md /
                   .cursorrules (creating them if absent)
  4. WORKMEMORY  — scaffolds the 5-piece shared working memory from `templates/workmemory/` and
                   injects its anchor into the project's agent files
  5. baseline    — prints the language-defense reminders for whatever the target actually uses

Deliberate divergences from the PowerShell original (grep `DFS-PORT`):
  * Anchors are always written with the DOCUMENTED resolution contract
    (`$WIKI_PATH` -> `$OBSIDIAN_VAULT_PATH` -> upward search for `AGENTS.md`). What goes into a file
    is: the contract line, plus a root path IF one resolves. Nothing this repo ships ever carries a
    resolved path — only files generated inside the TARGET repo do, and with no root resolvable they
    degrade to the literal `<your knowledge base root>` instead of a guess. The PowerShell version
    resolved at injection time and had no unresolved case, which is how one machine's layout ended up
    looking like everyone's.
  * Paths inside generated text use forward slashes (`D:/kb/AGENTS.md`, `WORKMEMORY/INDEX.md`): the
    PowerShell original joined native separators, which produces mixed `/`+`\` strings the moment a
    POSIX-style path meets Windows. The idempotency marker stays separator-agnostic so anchors
    written by the old script are still recognised.
  * Templates come from this skill's own `templates/` (shipped), not from a private vault's
    `Templates/workmemory/`.
  * The vault search CLI is gone; the anchor points at the `search_vault` MCP tool with the
    file-level fallback documented in the DFS repo's `mcp/README.md`.
  * A missing template is a hard exit 2, not a warning: a scaffold that silently skips files is
    the exact failure class this suite exists to prevent.
  * Bracketed tokens instead of emoji — Windows console codepages mangle emoji, and this runs on
    whatever shell the user has.

Usage:
    python bootstrap.py [--target DIR] [--vault-root PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

# Single source of truth for the required secret exclusions; the DFS repo's own .gitignore keeps
# this block byte-identical, and tests/test_bootstrap_script.py fails if the two drift apart.
REQUIRED_IGNORES = [
    "config.yaml",
    "config.yml",
    "config.local.yaml",
    ".env",
    ".env.*",
    "*.env",
    "*.secret",
    "*.pem",
    "*.key",
    "*.local.json",
    "credentials.json",
]
IGNORE_HEADER = "# Sensitive credentials & secrets"

WORKMEMORY_FILES = ["PROTOCOL.md", "INDEX.md", "INDEX-topics.md", "PROJECT_OVERVIEW.md", "work.log"]
# AGENTS.md is first on purpose: the anchor's own text says the knowledge base root resolves by
# searching upward for AGENTS.md — writing one without the other leaves the two mechanisms
# disagreeing about what this file is for. (The PowerShell original skipped it here.)
RULE_ANCHOR_FILES = ["AGENTS.md", "CLAUDE.md", ".agent-rules.md", ".cursorrules"]
WM_ANCHOR_FILES = ["CLAUDE.md", "AGENTS.md", "GEMINI.md", ".agent-rules.md", ".cursorrules"]

RULE_MARKER = "工程规范与避坑检索"
WM_MARKER = re.compile(r"WORKMEMORY[\\/]INDEX\.md")  # separator-agnostic: the PS version learned this

UNRESOLVED_ROOT = "<your knowledge base root>"


def say(tag: str, message: str) -> None:
    print(f"  [{tag}] {message}")


def write_text(path: pathlib.Path, text: str, dry_run: bool) -> None:
    """UTF-8, no BOM, LF — a BOM breaks the hook's shebang and pollutes the first byte of work.log."""
    if dry_run:
        say("DRY", f"would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def append_text(path: pathlib.Path, text: str, dry_run: bool) -> None:
    if dry_run:
        say("DRY", f"would append {len(text)} bytes to {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def resolve_vault_root(explicit: str | None) -> str | None:
    """Explicit `--vault-root` only. Never inlines host environment variables into
    generated files by default, ensuring all bootstrapped repositories are portable,
    zero-PII, and safe for open-source distribution.
    """
    if explicit:
        return str(pathlib.Path(explicit).expanduser())
    return None


def ensure_gitignore(target: pathlib.Path, dry_run: bool) -> list[str]:
    path = target / ".gitignore"
    existing = path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []
    missing = [p for p in REQUIRED_IGNORES if p not in existing]
    if not missing:
        say("OK", f".gitignore already excludes all {len(REQUIRED_IGNORES)} required secret patterns")
        return []
    header = "" if not existing else "\n"
    append_text(path, f"{header}{IGNORE_HEADER}\n" + "\n".join(missing) + "\n", dry_run)
    say("OK", f"added {len(missing)} required secret pattern(s) to .gitignore: {', '.join(missing)}")
    return missing


def install_hook(target: pathlib.Path, dry_run: bool) -> None:
    if not (target / ".git").exists():
        say("SKIP", "not a git repository — skipping the pre-commit hook")
        return
    if not (TEMPLATES / "githooks-pre-commit.sh").is_file():
        say("ERR", f"hook template missing: {TEMPLATES / 'githooks-pre-commit.sh'}")
        raise SystemExit(2)
    hook = target / ".githooks" / "pre-commit"
    if hook.exists():
        say("OK", "existing .githooks/pre-commit preserved (not overwritten)")
    else:
        body = (TEMPLATES / "githooks-pre-commit.sh").read_bytes()
        if dry_run:
            say("DRY", f"would install {hook} ({len(body)} bytes, LF, no BOM)")
        else:
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_bytes(body)
            os.chmod(hook, 0o755)
            say("OK", f"installed {hook.relative_to(target)} (mode 0755, LF, no BOM)")
    if dry_run:
        say("DRY", "would run: git config core.hooksPath .githooks")
        return
    proc = subprocess.run(
        ["git", "-C", str(target), "config", "core.hooksPath", ".githooks"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        say("GIT", "core.hooksPath -> .githooks")
    else:
        say("WARN", f"git config failed (exit {proc.returncode}): {proc.stderr.strip()}")


def posix_join(root: str, *parts: str) -> str:
    """Forward slashes regardless of host OS: `Path('D:/kb','AGENTS.md').as_posix()` -> `D:/kb/AGENTS.md`.

    os.path.join on Windows would emit `D:/kb\\AGENTS.md` for a POSIX-style input — the mixed-separator
    class the PowerShell original warned about in a comment and then still produced.
    """
    return pathlib.Path(root, *parts).as_posix()


def rule_anchor_text(vault_root: str | None = None) -> str:
    if vault_root:
        return (
            "\n## 工程规范与避坑检索\n\n"
            f"- 核心规范源：`{posix_join(vault_root, 'AGENTS.md')}`（解析契约：`$WIKI_PATH` → "
            "`$OBSIDIAN_VAULT_PATH` → 向上查找 `AGENTS.md`）\n"
            "- 检索避坑规范：调用 `search_vault` MCP（无 MCP 时用 `search_files` / `read_file` 直接检索；"
            "服务与降级表见 DFS 仓库 `mcp/README.md`）\n"
            f"- 发现新踩坑自动沉淀：写草稿至 `{posix_join(vault_root, '99-Inbox', 'YYYY-MM-DD-{topic}.md')}`\n"
        )
    return (
        "\n## [NOTE] 工程规范与避坑检索\n\n"
        "- 核心规范源：优先通过 `search_vault` MCP 或环境变量 `$WIKI_PATH`/`$OBSIDIAN_VAULT_PATH` 解析；"
        "无外部知识库时以本仓 `AGENTS.md` 及 `docs/` 为自闭环规范源\n"
        "- 检索避坑规范：调用 `search_vault` MCP；无 MCP 时检索本地工程文档与测试套件\n"
        "- 发现新踩坑自动沉淀：优先调用 `save_inbox_draft`；无外部知识库时写草稿至 `WORKMEMORY/notes/YYYY-MM-DD-{topic}.md`\n"
    )


def workmemory_anchor_text() -> str:
    return (
        "\n## 共享工作记忆 (WORKMEMORY)\n\n"
        "- 进入会话先读 WORKMEMORY/INDEX.md → PROJECT_OVERVIEW.md → work.log 尾部 50 行；"
        "发现未闭合 WORK_START 先询问用户。\n"
        "- 工作中：决策/踩坑/交接 MUST 以 ≤4KB 事件追加 WORKMEMORY/work.log"
        "（schema 见 WORKMEMORY/PROTOCOL.md）。\n"
        "- 语义知识检索：调用 `search_vault` MCP（无 MCP 时用文件级检索）；成熟知识沉淀走 `dfs-save` 技能。\n"
    )


def inject_anchors(target: pathlib.Path, vault_root: str | None, dry_run: bool) -> None:
    for name in RULE_ANCHOR_FILES:
        path = target / name
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        if RULE_MARKER in text:
            say("OK", f"{name} already carries the rules anchor")
            continue
        block = rule_anchor_text(vault_root)
        if path.exists():
            append_text(path, block, dry_run)
            say("OK", f"injected the rules anchor into {name}")
        else:
            write_text(path, "# Project Guidelines\n" + block, dry_run)
            say("OK", f"created {name} with the rules anchor")


def scaffold_workmemory(target: pathlib.Path, vault_root: str | None, dry_run: bool) -> None:
    dest = target / "WORKMEMORY"
    if dest.exists():
        say("OK", "WORKMEMORY/ already exists, skipping the scaffold (agent keeps its own history)")
        return
    missing = [f for f in WORKMEMORY_FILES if not (TEMPLATES / "workmemory" / f).is_file()]
    if missing:
        say("ERR", f"WORKMEMORY template(s) missing from {TEMPLATES / 'workmemory'}: {missing}")
        raise SystemExit(2)
    project = target.resolve().name
    stamp = time.strftime("%Y-%m-%d %H:%M")
    fallback_root = vault_root or "$WIKI_PATH"
    for name in WORKMEMORY_FILES:
        body = (TEMPLATES / "workmemory" / name).read_text(encoding="utf-8")
        body = body.replace("{{PROJECT_NAME}}", project)
        body = body.replace("{{TIMESTAMP}}", stamp)
        body = body.replace("{{VAULT_ROOT}}", fallback_root)
        write_text(dest / name, body, dry_run)
    say("OK", f"scaffolded {len(WORKMEMORY_FILES)} files into WORKMEMORY/ for '{project}'")


def inject_workmemory_anchor(target: pathlib.Path, vault_root: str | None, dry_run: bool) -> None:
    for name in WM_ANCHOR_FILES:
        path = target / name
        if not path.exists():
            if name != "AGENTS.md":  # AGENTS.md is the cross-agent anchor; the rest are append-only
                continue
            write_text(path, "# Project Guidelines\n" + workmemory_anchor_text(), dry_run)
            say("OK", "created AGENTS.md with the WORKMEMORY anchor")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if WM_MARKER.search(text):
            continue
        append_text(path, workmemory_anchor_text(), dry_run)
        say("OK", f"injected the WORKMEMORY anchor into {name}")


def environment_baseline(target: pathlib.Path) -> None:
    checks = [
        ("Python", "*.py", "reconfigure sys.stdout to UTF-8 (errors='replace') before printing non-ASCII"),
        ("Node/TS", "package.json", "tsconfig.json must set 'strict': true"),
        ("Go", "go.mod", "errgroup / context propagation standards"),
        ("Rust", "Cargo.toml", "thiserror / anyhow error-handling patterns"),
    ]
    found = []
    for label, marker, note in checks:
        hit = list(target.glob(marker)) if marker == "*.py" else ([target / marker] if (target / marker).exists() else [])
        if hit:
            found.append(f"{label}: {note}")
    for line in found:
        say("BASE", line)
    if not found:
        say("BASE", "no language markers detected — nothing to check")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DFS cross-platform workspace bootstrap")
    ap.add_argument("--target", default=".", help="target repository (default: cwd)")
    ap.add_argument("--vault-root", default=None, help="knowledge base root; else $WIKI_PATH / $OBSIDIAN_VAULT_PATH")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    args = ap.parse_args(argv)

    target = pathlib.Path(args.target).expanduser()
    if not target.is_dir():
        print(f"[ERR] target is not a directory: {target}", file=sys.stderr)
        return 2
    if not TEMPLATES.is_dir():
        print(f"[ERR] skill templates not found at {TEMPLATES} — run this from the DFS repo", file=sys.stderr)
        return 2

    vault_root = resolve_vault_root(args.vault_root)
    print(f"DFS bootstrap -> {target.resolve()}")
    print("-" * 68)
    if not vault_root:
        say("OK", "no knowledge base root resolved; using portable dynamic anchors (tier-3 degradation enabled)")
    else:
        say("OK", f"knowledge base root (explicit): {vault_root}")

    ensure_gitignore(target, args.dry_run)
    install_hook(target, args.dry_run)
    inject_anchors(target, vault_root, args.dry_run)
    scaffold_workmemory(target, vault_root, args.dry_run)
    inject_workmemory_anchor(target, vault_root, args.dry_run)
    environment_baseline(target)
    print("-" * 68)
    say("DONE", "dry run — nothing was written" if args.dry_run else "bootstrap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
