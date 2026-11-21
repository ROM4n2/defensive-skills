"""Rules anchors: AGENTS.md is the single source of truth, CLAUDE.md a pointer, plus the overlay
private layer.

Three behaviors were wrong and are fixed here:

* anchor detection used to require the literal token ``$WIKI_PATH/AGENTS.md`` — a private vault's
  layout. Any repo whose routing table named the vault *and* the sink tool was reported as already
  anchored, so the rules were never written. The block header plus a tool call identifies the anchor
  without assuming any directory names.
* the overlay private anchor was rewritten from the template on every run, silently discarding what
  the user appended to it. It is append-only now.
* a custom CLAUDE.md produced a WARN and nothing else, so the checked-in criterion ("CLAUDE.md is
  exactly the 2-line pointer") was unreachable by any flag. The pointer now replaces the copy and
  keeps the previous bytes as ``CLAUDE.md.dfsbak``.
* the anchor used to name a vault path (``$WIKI_PATH/AGENTS.md``). No harness expands a shell
  variable inside markdown and nothing read that line, so it was inert: the anchor now names the
  *tools* that reach the knowledge base and carries no external path at all.
"""
from __future__ import annotations

import pathlib

from . import gitops
from .constants import (
    ANCHOR_HEADER,
    ANCHOR_TOOL_TOKENS,
    LEGACY_ALIAS_FILES,
    POINTER_BODY,
    POINTER_FILE,
    PRIVATE_ANCHOR_FILE,
    RULES_SSOT_FILE,
    WM_ANCHOR_FILES,
    WM_MARKER,
)
from .fsio import append_text, keep_backup, write_text
from .report import say


PROJECT_MEMORY_BOUNDARY = (
    "- `AGENTS.md` 只记录稳定规则与事实；问题、决策、踩坑和交接优先写入 WORKMEMORY。\n"
)


def rule_anchor_text() -> str:
    return (
        f"\n{ANCHOR_HEADER}\n\n"
        "- 检索避坑规范：调用 `search_vault` MCP\n"
        "- 稳定经验调用 `save_inbox_draft` 沉淀；临时问题、决策和踩坑写入 WORKMEMORY。\n"
    )


def workmemory_anchor_text() -> str:
    return (
        "\n## 共享工作记忆 (WORKMEMORY)\n\n"
        f"{PROJECT_MEMORY_BOUNDARY}"
        "- 非只读或涉及状态变更时，按 `WORKMEMORY/INDEX.md` 读 `PROJECT_OVERVIEW.md` 与 `work.log` 最新 ≤15 条事件；"
        "发现未闭合 WORK_START 先询问用户。\n"
        "- 工作中：决策/踩坑/交接 MUST 以 ≤4KB 事件追加 WORKMEMORY/work.log"
        "（schema 见 WORKMEMORY/PROTOCOL.md）。\n"
        "- 稳定经验再通过 `search_vault` / `dfs-save` 沉淀到知识库。\n"
    )


def has_rule_anchor(text: str) -> bool:
    """True only for the full anchor block — not a same-titled routing row, not a bare mention."""
    return ANCHOR_HEADER in text and any(token in text for token in ANCHOR_TOOL_TOKENS)


def has_workmemory_anchor(text: str) -> bool:
    return WM_MARKER in text


def has_project_memory_boundary(text: str) -> bool:
    return PROJECT_MEMORY_BOUNDARY.rstrip() in text


def _ensure_project_memory_boundary(
    path: pathlib.Path, text: str, dry_run: bool
) -> None:
    if has_project_memory_boundary(text):
        return
    append_text(
        path,
        "\n" + PROJECT_MEMORY_BOUNDARY,
        dry_run,
        planned=f"would append the AGENTS.md/WORKMEMORY boundary to {path.name}",
    )
    if not dry_run:
        say("OK", f"added the AGENTS.md/WORKMEMORY boundary to {path.name}")


def _write_private_anchor(target: pathlib.Path, dry_run: bool) -> pathlib.Path:
    """Overlay fallback: our rules go into a private file when the canonical one is upstream-owned.

    Append-or-create, never rewrite: the file's own text invites the user to extend it.
    """
    dest = target / PRIVATE_ANCHOR_FILE
    if dest.exists():
        text = dest.read_text(encoding="utf-8", errors="replace")
        if has_rule_anchor(text) and has_workmemory_anchor(text):
            if not has_project_memory_boundary(text):
                _ensure_project_memory_boundary(dest, text, dry_run)
            say("OK", f"{PRIVATE_ANCHOR_FILE} already carries both anchors — left as is")
            return dest
        missing = ""
        if not has_rule_anchor(text):
            missing += rule_anchor_text()
        if not has_workmemory_anchor(text):
            missing += workmemory_anchor_text()
        append_text(dest, missing, dry_run,
                    planned=f"would append the missing anchor block(s) to {PRIVATE_ANCHOR_FILE}")
        if not dry_run:
            say("OK", f"appended the missing anchor(s) to {PRIVATE_ANCHOR_FILE} (existing content kept)")
        return dest
    body = (
        "# DFS private rules (not part of upstream)\n"
        "\n"
        f"`{RULES_SSOT_FILE}` is owned by upstream and is never modified by DFS bootstrap. This file\n"
        "carries the private layer instead. Point your agent runtime at it, or copy the block below\n"
        f"into `{RULES_SSOT_FILE}` yourself if you decide the change is worth upstreaming.\n"
        f"{rule_anchor_text()}"
        f"{workmemory_anchor_text()}"
    )
    write_text(dest, body, dry_run, planned=f"would create {PRIVATE_ANCHOR_FILE}")
    if not dry_run:
        say("OK", f"wrote the private anchor to {PRIVATE_ANCHOR_FILE} (upstream {RULES_SSOT_FILE} untouched)")
    return dest


def _ensure_rule_anchor(target: pathlib.Path, dry_run: bool, *, overlay: bool) -> None:
    path = target / RULES_SSOT_FILE
    if overlay and gitops.is_tracked(target, RULES_SSOT_FILE):
        text = path.read_text(encoding="utf-8", errors="replace")
        if has_rule_anchor(text):
            say("OK", f"{RULES_SSOT_FILE} is upstream-owned and already carries a rules anchor")
            return
        say("WARN", f"{RULES_SSOT_FILE} is upstream-owned — not modified; private rules go to "
                    f"{PRIVATE_ANCHOR_FILE}")
        _write_private_anchor(target, dry_run)
        return

    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if has_rule_anchor(text):
        say("OK", f"{RULES_SSOT_FILE} already carries the rules anchor")
        if has_workmemory_anchor(text):
            _ensure_project_memory_boundary(path, text, dry_run)
    elif path.exists():
        append_text(path, rule_anchor_text(), dry_run,
                    planned=f"would append {len(rule_anchor_text())} bytes to {RULES_SSOT_FILE}")
        if not dry_run:
            say("OK", f"injected the rules anchor into {RULES_SSOT_FILE}")
    else:
        write_text(
            path,
            "# Project Guidelines\n\n"
            "> 本文件只记录本项目的稳定规则与事实；临时状态和问题写入 WORKMEMORY。\n"
            + rule_anchor_text(),
            dry_run,
                   planned=f"would create {RULES_SSOT_FILE} with the rules anchor")
        if not dry_run:
            say("OK", f"created {RULES_SSOT_FILE} with the rules anchor")


def _ensure_pointer(target: pathlib.Path, dry_run: bool, *, overlay: bool) -> None:
    """CLAUDE.md is a 2-line pointer — never a copy, never an edit to an upstream-owned file."""
    pointer = target / POINTER_FILE
    if overlay and gitops.is_tracked(target, POINTER_FILE):
        say("OK", f"{POINTER_FILE} is upstream-owned — not modified")
        return
    pointer_text = pointer.read_text(encoding="utf-8", errors="replace") if pointer.exists() else ""
    if pointer_text == POINTER_BODY:
        say("OK", f"{POINTER_FILE} is a 2-line @{RULES_SSOT_FILE} pointer")
        return
    if pointer_text:
        if dry_run:
            say("DRY", f"would replace {POINTER_FILE} ({len(pointer_text.splitlines())} lines of rules) "
                       f"with the 2-line pointer, previous kept as {POINTER_FILE}.dfsbak")
        else:
            backup = keep_backup(pointer)
            say("WARN", f"{POINTER_FILE} held {len(pointer_text.splitlines())} lines of its own rules; "
                        f"replaced by the pointer, previous kept as {backup.name}")
    write_text(pointer, POINTER_BODY, dry_run,
               planned=f"would write {POINTER_FILE} as the 2-line @{RULES_SSOT_FILE} pointer")
    if not dry_run:
        say("OK", f"{POINTER_FILE} is a 2-line @{RULES_SSOT_FILE} pointer")


def _write_legacy_aliases(target: pathlib.Path, dry_run: bool) -> None:
    block = rule_anchor_text()
    for name in LEGACY_ALIAS_FILES:
        alias = target / name
        if alias.exists() and has_rule_anchor(alias.read_text(encoding="utf-8", errors="replace")):
            say("OK", f"legacy alias {name} already carries the rules anchor")
            continue
        if alias.exists():
            append_text(alias, block, dry_run, planned=f"would append the anchor to {name}")
            if not dry_run:
                say("OK", f"injected the rules anchor into legacy alias {name}")
            continue
        write_text(alias, "# Project Guidelines\n" + block, dry_run,
                   planned=f"would create {name} with the rules anchor")
        if not dry_run:
            say("OK", f"created legacy alias {name} with the rules anchor")


def _warn_legacy_aliases(target: pathlib.Path) -> None:
    ssot = target / RULES_SSOT_FILE
    for name in LEGACY_ALIAS_FILES:
        alias = target / name
        if not alias.exists():
            continue
        same = ssot.exists() and alias.read_bytes() == ssot.read_bytes()
        detail = "byte-identical duplicate of AGENTS.md" if same else "differs from AGENTS.md"
        say("WARN", f"legacy alias {name} present ({detail}); not generated, consider deleting it")


def write_agents_ssot(
    target: pathlib.Path, dry_run: bool, *, legacy_aliases: bool, overlay: bool = False
) -> None:
    """AGENTS.md carries the rules; CLAUDE.md is a thin pointer. Nothing else is generated."""
    _ensure_rule_anchor(target, dry_run, overlay=overlay)
    _ensure_pointer(target, dry_run, overlay=overlay)
    if legacy_aliases:
        _write_legacy_aliases(target, dry_run)
        return
    _warn_legacy_aliases(target)


def inject_workmemory_anchor(target: pathlib.Path, dry_run: bool, *, overlay: bool = False) -> None:
    for name in WM_ANCHOR_FILES:
        path = target / name
        if not path.exists():
            if name != RULES_SSOT_FILE:  # AGENTS.md is the cross-agent anchor; the rest are append-only
                continue
            write_text(path, "# Project Guidelines\n" + workmemory_anchor_text(), dry_run,
                       planned=f"would create {name} with the WORKMEMORY anchor")
            if not dry_run:
                say("OK", f"created {name} with the WORKMEMORY anchor")
            continue
        if overlay and gitops.is_tracked(target, name):
            say("OK", f"{name} is upstream-owned — WORKMEMORY anchor not injected")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if has_workmemory_anchor(text):
            say("OK", f"{name} already carries the WORKMEMORY anchor")
            if not has_project_memory_boundary(text):
                _ensure_project_memory_boundary(path, text, dry_run)
            continue
        append_text(path, workmemory_anchor_text(), dry_run,
                    planned=f"would append the WORKMEMORY anchor to {name}")
        if not dry_run:
            say("OK", f"injected the WORKMEMORY anchor into {name}")
