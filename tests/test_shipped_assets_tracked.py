#!/usr/bin/env python3
"""A shipped asset must actually be tracked — a green local run is not evidence.

This gate exists because a real defect walked past a fully green suite. `.gitignore` held an
unanchored `WORKMEMORY/`, which matches at ANY depth, and git's ignore matching is
case-insensitive on Windows: it silently swallowed `dfs-bootstrap/templates/workmemory/`. Those
four files were therefore never tracked in any commit. On the author's machine every gate passed,
because the ignored files were sitting on disk — the suites all measured the disk, and none
measured what a clone actually receives. A stranger's clone got a `dfs-bootstrap` whose
bootstrap.py exits 2 with "WORKMEMORY template(s) missing", and conformance Rule 5 went red.

So two assertions, both about the *published* artifact rather than the working copy:

  1. no shipped path is git-ignored (build caches excepted — they are not content), and
  2. nothing under a shipped path is left untracked.

Skipped when git is absent or this is not a work tree: the invariant is about tracking, so
outside git there is nothing to verify (an unpacked tarball contains only tracked files anyway).
"""

import pathlib
import re
import shutil
import subprocess
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent

# The product. `tests/` is in scope on purpose: a broken gate is a shipped defect too.
SHIPPED = ["dfs*", "scripts", "mcp", "tests", "install.py"]

# Legitimately ignorable wherever they appear, because they are derived, not authored.
# Anchored to path segments so a file merely *named* like a cache is still checked.
BUILD_ARTIFACT = re.compile(
    r"(?:^|/)(?:__pycache__|\.mypy_cache|\.pytest_cache|\.ruff_cache"
    r"|\.venv|venv|\.worktrees|\.agent-cache)(?:/|$)"
)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def git_usable() -> bool:
    if shutil.which("git") is None:
        return False
    return git("rev-parse", "--is-inside-work-tree").returncode == 0


def paths(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.strip()]


@unittest.skipUnless(git_usable(), "requires git and a work tree — nothing to check otherwise")
class ShippedAssetsTrackedTest(unittest.TestCase):
    def test_00_the_scan_is_not_vacuous(self):
        """A pathspec that matches nothing would make both assertions below pass silently."""
        tracked = paths(git("ls-files", "--", *SHIPPED).stdout)
        self.assertGreater(
            len(tracked), 50, f"the shipped pathspec matched only {len(tracked)} tracked file(s)"
        )
        skills = [p for p in tracked if p.startswith("dfs-")]
        self.assertGreater(len(skills), 20, f"only {len(skills)} tracked skill file(s)")

    def test_01_no_shipped_path_is_git_ignored(self):
        ignored = [p for p in paths(git("ls-files", "--others", "--ignored",
                                        "--exclude-standard", "--", *SHIPPED).stdout)
                   if not BUILD_ARTIFACT.search(p)]
        self.assertEqual(
            ignored, [],
            "ship-path content is git-ignored, so a clone will not receive it: "
            f"{ignored} — anchor the pattern (see .gitignore)",
        )

    def test_02_no_shipped_path_is_left_untracked(self):
        untracked = paths(git("ls-files", "--others", "--exclude-standard", "--", *SHIPPED).stdout)
        self.assertEqual(
            untracked, [],
            f"shipped file(s) exist on disk but are not tracked, so a clone won't have them: {untracked}",
        )

    def test_03_the_bootstrap_templates_are_tracked(self):
        """The specific regression, named — the bug above was four templates going missing."""
        tracked = set(paths(git("ls-files", "--", *SHIPPED).stdout))
        missing = [f"dfs-bootstrap/templates/workmemory/{name}"
                   for name in ("PROTOCOL.md", "INDEX.md", "PROJECT_OVERVIEW.md", "work.log")
                   if f"dfs-bootstrap/templates/workmemory/{name}" not in tracked]
        self.assertEqual(missing, [], "untracked — dfs-bootstrap cannot ship these")


if __name__ == "__main__":
    unittest.main(verbosity=2)