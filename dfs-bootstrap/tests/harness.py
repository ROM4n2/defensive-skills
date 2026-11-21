"""Shared fixtures for the dfs-bootstrap test suites.

Every suite builds a throwaway git repository and runs the real script against it — nothing is mocked.
This module holds the three harnesses so each test file carries only its own assertions.

Import: `from harness import BootstrapHarness, GateHarness, git, run_gate`
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
BOOTSTRAP = SKILL_DIR / "scripts" / "bootstrap.py"
STRUCTURE_GATE = SKILL_DIR / "templates" / "repo" / "check_repo_structure.py"
HYGIENE_GATE = SKILL_DIR / "templates" / "repo" / "check_repo_hygiene.py"

UPSTREAM_GITIGNORE = "*.log\nnode_modules/\nbuild/\n"
UPSTREAM_GITATTRIBUTES = "* text=auto\n*.png binary\n"
UPSTREAM_AGENTS = "# Upstream rules\n\n- Use tabs.\n- PRs target main.\n"
UPSTREAM_CLAUDE = "# Upstream Claude rules\n\nAlways run make test before pushing.\n"
UPSTREAM_HOOK = "#!/usr/bin/env bash\necho UPSTREAM_HOOK_RAN\nexit 0\n"


def run_bootstrap(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run the CLI with explicit arguments — for cases the harness's fixed invocation cannot express."""
    return subprocess.run(
        [sys.executable, "-B", str(BOOTSTRAP), *args],
        cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def git(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def run_gate(root: pathlib.Path, gate: pathlib.Path = STRUCTURE_GATE) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(gate), "--root", str(root)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


class GitRepoHarness(unittest.TestCase):
    """A temporary directory plus a vault, with optional pre-populated upstream content."""

    upstream_gitignore: str | None = None
    upstream_gitattributes: str | None = None
    upstream_agents: str | None = None
    upstream_claude: str | None = None
    upstream_hook: str | None = None
    extra_files: dict[str, str] = {}

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.vault / "AGENTS.md").write_text("# vault\n", encoding="utf-8")

        git(["init", "-q"], self.repo)
        git(["config", "user.email", "t@example.invalid"], self.repo)
        git(["config", "user.name", "T"], self.repo)

        if self.upstream_gitignore is not None:
            (self.repo / ".gitignore").write_text(self.upstream_gitignore, encoding="utf-8", newline="\n")
        if self.upstream_gitattributes is not None:
            (self.repo / ".gitattributes").write_text(self.upstream_gitattributes, encoding="utf-8", newline="\n")
        if self.upstream_agents is not None:
            (self.repo / "AGENTS.md").write_text(self.upstream_agents, encoding="utf-8", newline="\n")
        if self.upstream_claude is not None:
            (self.repo / "CLAUDE.md").write_text(self.upstream_claude, encoding="utf-8", newline="\n")
        if self.upstream_hook is not None:
            hooks = self.repo / ".githooks"
            hooks.mkdir()
            hook = hooks / "pre-commit"
            hook.write_text(self.upstream_hook, encoding="utf-8", newline="\n")
            hook.chmod(0o755)
        (self.repo / "main.py").write_text("def main():\n    return 0\n", encoding="utf-8", newline="\n")
        for rel, body in self.extra_files.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8", newline="\n")

        git(["add", "-A"], self.repo)
        git(["commit", "-qm", "baseline"], self.repo)
        if self.upstream_hook is not None:
            git(["config", "core.hooksPath", ".githooks"], self.repo)
        self.baseline = git(["rev-parse", "HEAD"], self.repo).stdout.strip()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def bootstrap(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(BOOTSTRAP), "--target", str(self.repo),
             "--vault-root", str(self.vault), *extra],
            cwd=str(self.root), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def commit(self, message: str) -> subprocess.CompletedProcess[str]:
        return git(["commit", "-m", message], self.repo)

    def porcelain(self) -> str:
        return git(["status", "--porcelain"], self.repo).stdout

    def head(self) -> str:
        return git(["rev-parse", "HEAD"], self.repo).stdout.strip()


class OwnerHarness(GitRepoHarness):
    """Owner mode: no upstream content."""


class OverlayHarness(GitRepoHarness):
    """A realistic fork: upstream owns .gitignore, .gitattributes and source."""
    upstream_gitignore = UPSTREAM_GITIGNORE
    upstream_gitattributes = UPSTREAM_GITATTRIBUTES

    def bootstrap(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return super().bootstrap("--mode", "overlay", *extra)


class ConflictHarness(GitRepoHarness):
    """A fork where upstream already owns AGENTS.md, CLAUDE.md and a pre-commit hook."""
    upstream_agents = UPSTREAM_AGENTS
    upstream_claude = UPSTREAM_CLAUDE
    upstream_hook = UPSTREAM_HOOK

    def bootstrap(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return super().bootstrap("--mode", "overlay", *extra)


class GateHarness(unittest.TestCase):
    """A bare directory with a `data/` config dir for exercising a gate directly."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "data").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, rel: str, body: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8", newline="\n")

    def config(self, **kw: int) -> None:
        import json
        (self.root / "data" / "repo_structure.json").write_text(
            json.dumps(kw), encoding="utf-8", newline="\n"
        )

    def gate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(STRUCTURE_GATE), "--root", str(self.root), *extra],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
