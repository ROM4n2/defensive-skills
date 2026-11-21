#!/usr/bin/env python3
"""Block: hook activation. Writing the hook is half the job; `core.hooksPath` is the other half.

`core.hooksPath` is local config and does not travel with a clone, so a hook that is already current
in the tree used to be left completely disconnected on every fresh checkout. The flip side is equally
important: repointing it can disable a repo's own hook chain (DeLector chains a machine-local
fingerprint gate), so that switch requires an explicit flag and is reversible.

Run: python -B tests/test_hook_activation.py
"""
from __future__ import annotations

import unittest

from harness import OwnerHarness, git, run_bootstrap


class TestHookActivation(OwnerHarness):
    def test_unset_hooks_path_is_repaired_when_the_hook_is_already_current(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["config", "--unset", "core.hooksPath"], self.repo)
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("already at version", proc.stdout)
        self.assertEqual(
            git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".githooks",
            "a clone that already has the hook must still get core.hooksPath",
        )

    def test_foreign_hooks_path_survives_a_project_owned_hook(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
        git(["config", "core.hooksPath", ".git/local-hooks"], self.repo)
        proc = self.bootstrap()
        self.assertIn("core.hooksPath stays .git/local-hooks", proc.stdout)
        self.assertEqual(git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".git/local-hooks")

    def test_force_hook_without_take_hooks_path_refuses_the_switch(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
        git(["config", "core.hooksPath", ".git/local-hooks"], self.repo)
        proc = run_bootstrap(
            ["--target", str(self.repo), "--vault-root", str(self.vault), "--force-hook"], self.root
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("not overwriting it", proc.stdout)
        self.assertIn("--take-hooks-path", proc.stdout)
        self.assertEqual(
            git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".git/local-hooks",
            "force-hook alone must not silently disable another directory's hooks",
        )

    def test_take_hooks_path_switches_and_records_the_previous_value(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
        git(["config", "core.hooksPath", ".git/local-hooks"], self.repo)
        proc = run_bootstrap(
            ["--target", str(self.repo), "--vault-root", str(self.vault),
             "--force-hook", "--take-hooks-path"], self.root
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".githooks")
        self.assertEqual(
            git(["config", "dfs.bootstrap.hooksPathBackup"], self.repo).stdout.strip(),
            ".git/local-hooks", "the switch must be reversible",
        )

    def test_exec_bit_is_recorded_in_the_index(self) -> None:
        """`os.chmod` alone is invisible to git on Windows (core.filemode=false) — 100644 ships."""
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["add", ".githooks/pre-commit"], self.repo)
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        mode = git(["ls-files", "-s", ".githooks/pre-commit"], self.repo).stdout.split()[0]
        self.assertEqual(mode, "100755", "a POSIX clone ignores a 100644 hook")


if __name__ == "__main__":
    unittest.main(verbosity=2)
