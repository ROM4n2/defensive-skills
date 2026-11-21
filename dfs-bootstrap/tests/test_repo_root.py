#!/usr/bin/env python3
"""Block: repository root. Running inside a subdirectory must not create a nested repo.

Before the guard, `--target src/` inside an existing checkout did `git init` right there, which made
every `git ls-files` answer relative to the new repo — so the overlay "never touch upstream" check
reported a clean tree while the outer repo's AGENTS.md had just been appended to.

Run: python -B tests/test_repo_root.py
"""
from __future__ import annotations

import unittest

from harness import OwnerHarness, run_bootstrap


class TestRepositoryRootGuard(OwnerHarness):
    def test_subdirectory_target_is_refused_and_writes_nothing(self) -> None:
        sub = self.repo / "src"
        sub.mkdir()
        (sub / "inner.py").write_text("VALUE = 1\n", encoding="utf-8")
        before = self.porcelain()
        proc = run_bootstrap(
            ["--target", str(sub), "--vault-root", str(self.vault)], self.root
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("is inside the repository at", proc.stderr)
        self.assertFalse((sub / ".git").exists(), "a nested repository must never be created")
        self.assertFalse((sub / "AGENTS.md").exists())
        self.assertEqual(self.porcelain(), before, "the outer repo must be byte-identical")

    def test_repository_root_as_target_still_works(self) -> None:
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue((self.repo / ".githooks" / "pre-commit").is_file())

    def test_directory_outside_any_repository_is_still_initialized(self) -> None:
        fresh = self.root / "fresh"
        fresh.mkdir()
        proc = run_bootstrap(
            ["--target", str(fresh), "--vault-root", str(self.vault)], self.root
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((fresh / ".git").exists(), "a bare directory is still a bootstrap target")


if __name__ == "__main__":
    unittest.main(verbosity=2)
