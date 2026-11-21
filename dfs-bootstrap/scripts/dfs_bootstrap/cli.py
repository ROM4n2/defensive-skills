"""Argument parsing and phase order. Nothing here inspects file formats; it delegates."""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

from . import anchors, doctor as doctor_mod, gitops, hook, repo_config, workmemory
from .constants import (
    OWNER_MODE,
    OVERLAY_MODE,
    TEMPLATES,
    VAULT_ROOT_TOKEN,
)
from .report import say


def resolve_vault_root(explicit: str | None) -> str | None:
    """Read the knowledge-base root from the explicit argument or WIKI_PATH.

    The value is validated and reported, but never embedded in a generated file: anchors refer to
    the root as ``$WIKI_PATH`` so the scaffold stays portable and passes its own host-path gate.
    """
    value = explicit or os.environ.get("WIKI_PATH")
    return pathlib.Path(value).expanduser().as_posix() if value else None


def ensure_git_repository(target: pathlib.Path, dry_run: bool) -> None:
    """Bootstrap is project initialization: a directory outside any repo means git init."""
    if (target / ".git").exists():
        say("OK", "git repository already initialized")
        return
    if dry_run:
        say("DRY", f"would run: git -C {target} init")
        say("DRY", "would confirm the initial branch with git symbolic-ref --short HEAD")
        return
    proc = gitops.run_git(target, "init")
    if proc.returncode != 0:
        say("ERR", f"git init failed: {proc.stderr.strip()}")
        say("ERR", f"next step: run `git -C {target} init`, then rerun bootstrap")
        raise SystemExit(2)
    branch = gitops.run_git(target, "symbolic-ref", "--short", "HEAD")
    if branch.returncode != 0 or not branch.stdout.strip():
        say("ERR", f"could not confirm the initial branch: {branch.stderr.strip()}")
        raise SystemExit(2)
    say("GIT", f"initialized repository on branch {branch.stdout.strip()}")


def _apply_scaffold(target: pathlib.Path, args: argparse.Namespace, overlay: bool) -> None:
    """Run the write phases in dependency order."""
    if overlay:
        if not (target / ".git").exists() and not args.dry_run:
            print("[ERR] overlay mode needs an existing git repository", file=sys.stderr)
            raise SystemExit(2)
        repo_config.ensure_local_exclude(target, args.dry_run)
        repo_config.ensure_local_attributes(target, args.dry_run)
    else:
        repo_config.ensure_gitignore(target, args.dry_run)
        repo_config.ensure_gitattributes(target, args.dry_run)
    hook.install_hook(
        target, args.dry_run, force=args.force_hook, overlay=overlay,
        take_hooks_path=args.take_hooks_path,
    )
    if args.no_gates:
        say("WARN", "gates skipped (--no-gates): the installed hook calls them and will skip "
                    "them silently until they exist; the private fingerprint gate is skipped too")
    else:
        from .gates import install_gates, install_local_gate

        install_gates(target, args.dry_run)
        install_local_gate(target, args.dry_run)
    anchors.write_agents_ssot(
        target, args.dry_run, legacy_aliases=args.legacy_aliases, overlay=overlay
    )
    workmemory.scaffold(target, args.dry_run)
    anchors.inject_workmemory_anchor(target, args.dry_run, overlay=overlay)
    environment_baseline(target)


def environment_baseline(target: pathlib.Path) -> None:
    checks = [
        ("Python", "*.py", "reconfigure sys.stdout to UTF-8 (errors='replace') before printing non-ASCII"),
        ("Node/TS", "package.json", "tsconfig.json must set 'strict': true"),
        ("Go", "go.mod", "errgroup / context propagation standards"),
        ("Rust", "Cargo.toml", "thiserror / anyhow error-handling patterns"),
    ]
    found = []
    for label, marker, note in checks:
        hit = (
            list(target.glob(marker))
            if marker == "*.py"
            else ([target / marker] if (target / marker).exists() else [])
        )
        if hit:
            found.append(f"{label}: {note}")
    for line in found:
        say("BASE", line)
    if not found:
        say("BASE", "no language markers detected — nothing to check")


def _report_overlay_cleanliness(target: pathlib.Path) -> None:
    """Prove the overlay left the tracked tree untouched — read the result, do not assume it."""
    status, diff, staged = gitops.cleanliness(target)
    if not status and not diff and not staged:
        say("OK", "upstream tree is clean (git status / diff / staged all empty)")
        return
    say("ERR", "overlay left tracked changes — inspect before committing to upstream:")
    for label, body in (("status", status), ("diff", diff), ("staged", staged)):
        if body:
            for line in body.splitlines()[:10]:
                print(f"         {label}: {line}")


def _add_core_flags(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--target", default=".", help="target repository (default: cwd)")
    ap.add_argument("--vault-root", default=None, help="knowledge base root (default: $WIKI_PATH)")
    ap.add_argument(
        "--allow-missing-vault-agents",
        action="store_true",
        help="proceed even when the knowledge base root has no AGENTS.md (the rules anchor then "
             "has nothing to point at)",
    )
    ap.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    ap.add_argument(
        "--mode",
        choices=(OWNER_MODE, OVERLAY_MODE),
        default=OWNER_MODE,
        help=(
            "owner: you own the repo, artifacts are tracked. "
            "overlay: secondary development on upstream — artifacts are written but excluded "
            "locally (.git/info/exclude + .git/info/attributes + hook inside .git), so no tracked "
            "file is modified and nothing leaks into a pull request"
        ),
    )


def _add_write_flags(ap: argparse.ArgumentParser) -> None:
    ap.add_argument(
        "--legacy-aliases",
        action="store_true",
        help="also write the rules anchor into .agent-rules.md / .cursorrules (legacy runtimes)",
    )
    ap.add_argument(
        "--no-gates",
        "--no-hygiene-gate",
        dest="no_gates",
        action="store_true",
        help="skip installing scripts/check_repo_hygiene.py and scripts/check_repo_structure.py",
    )
    ap.add_argument(
        "--force-hook",
        action="store_true",
        help="overwrite an existing hook even when it carries no DFS version marker",
    )
    ap.add_argument(
        "--take-hooks-path",
        action="store_true",
        help="allow bootstrap to repoint core.hooksPath when it currently points elsewhere "
             "(hooks in the old directory stop running; the old value is saved in git config)",
    )


def _add_readonly_flags(ap: argparse.ArgumentParser) -> None:
    ap.add_argument(
        "--emit-ci",
        choices=("github",),
        help="print reviewed CI wiring snippets to stdout (never writes a workflow file)",
    )
    ap.add_argument(
        "--emit-checks",
        action="store_true",
        help="print a sourceable dfs-checks.sh for project-owned hooks (read-only)",
    )
    ap.add_argument(
        "--doctor",
        action="store_true",
        help="report capability gaps without modifying anything (exit 0 clean / 1 gaps / 2 cannot run)",
    )
    ap.add_argument(
        "--doctor-mode",
        choices=("auto", OWNER_MODE, OVERLAY_MODE),
        default="auto",
        help="which hook layout to inspect (default: auto-detect from .git/dfs-hooks)",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="with --doctor: execute the installed hook against a synthetic secret",
    )


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="DFS cross-platform workspace bootstrap")
    _add_core_flags(ap)
    _add_write_flags(ap)
    _add_readonly_flags(ap)
    return ap


def _emit_checks() -> int:
    path = TEMPLATES / "githooks-dfs-checks.sh"
    if not path.is_file():
        print(f"[ERR] dfs-checks template missing: {path}", file=sys.stderr)
        return 2
    print(path.read_text(encoding="utf-8"))
    return 0


def _emit_ci() -> int:
    steps = TEMPLATES / "repo" / "ci-steps-github.yml"
    test = TEMPLATES / "repo" / "ci-wiring-guard-test.py.txt"
    for label, path in (("CI steps", steps), ("guard test", test)):
        if not path.is_file():
            print(f"[ERR] {label} template missing: {path}", file=sys.stderr)
            return 2
        print(f"# ===== {label}: {path.name} =====")
        print(path.read_text(encoding="utf-8"))
    return 0


def _run_readonly_mode(args: argparse.Namespace) -> int | None:
    """Handle the read-only subcommands; ``None`` means fall through to the write path."""
    if args.emit_checks:
        return _emit_checks()
    if args.emit_ci:
        return _emit_ci()
    if args.doctor:
        target = pathlib.Path(args.target).expanduser()
        if not target.is_dir():
            print(f"[ERR] target is not a directory: {target}", file=sys.stderr)
            return 2
        return doctor_mod.doctor(target, mode=args.doctor_mode, verify=args.verify)
    return None


def _refuse_subdirectory_of_a_repo(target: pathlib.Path) -> int | None:
    """Running inside a subdirectory used to create a nested repo and write into the outer one."""
    top = gitops.toplevel(target)
    if top is None or top == target:
        return None
    print(
        f"[ERR] --target {target} is inside the repository at {top}; bootstrap writes at the root.\n"
        f"      next step: re-run with `--target {top}` (nothing was written)",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    readonly = _run_readonly_mode(args)
    if readonly is not None:
        return readonly

    target = pathlib.Path(args.target).expanduser()
    if not target.is_dir():
        print(f"[ERR] target is not a directory: {target}", file=sys.stderr)
        return 2
    target = target.resolve()
    refused = _refuse_subdirectory_of_a_repo(target)
    if refused is not None:
        return refused
    if not TEMPLATES.is_dir():
        print(f"[ERR] skill templates not found at {TEMPLATES} — run this from the DFS repo", file=sys.stderr)
        return 2

    overlay = args.mode == OVERLAY_MODE
    vault_root = resolve_vault_root(args.vault_root)
    if not vault_root:
        print("[ERR] --vault-root or WIKI_PATH is required (it is validated here and written as "
              f"{VAULT_ROOT_TOKEN} in anchors)", file=sys.stderr)
        return 2
    print(f"DFS bootstrap -> {target}  [mode={args.mode}{', dry-run' if args.dry_run else ''}]")
    print("-" * 68)
    say("OK", f"knowledge base root: {vault_root} (written as {VAULT_ROOT_TOKEN} in anchors)")
    if not (pathlib.Path(vault_root) / "AGENTS.md").is_file():
        if not args.allow_missing_vault_agents:
            print(
                f"[ERR] {vault_root} has no AGENTS.md — refusing to scaffold a rules anchor that "
                "points at a non-existent source. Pass --allow-missing-vault-agents to override.",
                file=sys.stderr,
            )
            return 2
        say("WARN", f"{vault_root} has no AGENTS.md (allowed by --allow-missing-vault-agents)")
    if overlay:
        say("OK", "overlay mode: private artifacts go to .git/info/exclude, LF pins to "
                  ".git/info/attributes, hook to .git/dfs-hooks — tracked files are never modified")

    ensure_git_repository(target, args.dry_run)
    _apply_scaffold(target, args, overlay)
    print("-" * 68)
    if overlay and not args.dry_run:
        _report_overlay_cleanliness(target)
    say("DONE", "dry run — nothing was written" if args.dry_run else "bootstrap complete")
    return 0


__all__ = ["main", "ensure_git_repository", "environment_baseline", "resolve_vault_root"]
