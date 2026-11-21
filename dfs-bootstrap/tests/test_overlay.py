"""Overlay mode: private scaffolding that never reaches upstream.

Three scenarios, one file:

1. **Plain fork** — upstream owns `.gitignore` / `.gitattributes`; nothing private may become visible.
2. **Conflicting fork** — upstream already owns `AGENTS.md`, `CLAUDE.md` and a `pre-commit` hook. Naive
   implementations append to the tracked rules file (dirtying `git status`) and repoint `core.hooksPath`
   (silently disabling the upstream gate). Both are asserted here.
3. **Owner mode** — the same script with `--mode owner` must still track artifacts and edit `.gitignore`.

Run: python -B tests/test_overlay.py
"""
from __future__ import annotations

import pathlib
import sys
import unittest

from harness import (
    ConflictHarness, OwnerHarness, OverlayHarness, git,
    UPSTREAM_AGENTS, UPSTREAM_CLAUDE, UPSTREAM_GITATTRIBUTES, UPSTREAM_GITIGNORE,
)


class TestUpstreamIsUntouched(OverlayHarness):
    def test_status_diff_and_staged_are_all_empty(self) -> None:
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.porcelain(), "", "overlay must leave git status clean")
        self.assertEqual(git(["diff"], self.repo).stdout, "")
        self.assertEqual(git(["diff", "--cached", "--name-only"], self.repo).stdout, "")

    def test_tracked_ignore_and_attributes_are_byte_identical(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual((self.repo / ".gitignore").read_bytes(), UPSTREAM_GITIGNORE.encode())
        self.assertEqual((self.repo / ".gitattributes").read_bytes(), UPSTREAM_GITATTRIBUTES.encode())
        self.assertEqual(git(["show", "HEAD:.gitignore"], self.repo).stdout, UPSTREAM_GITIGNORE)
        self.assertEqual(git(["show", "HEAD:.gitattributes"], self.repo).stdout, UPSTREAM_GITATTRIBUTES)

    def test_git_add_all_stages_nothing_private(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["add", "-A"], self.repo)
        staged = git(["diff", "--cached", "--name-only"], self.repo).stdout
        for private in ("AGENTS.md", "CLAUDE.md", "WORKMEMORY", "check_repo_hygiene", "check_repo_structure"):
            self.assertNotIn(private, staged, f"{private} must never be staged")
        self.assertEqual(staged.strip(), "", f"nothing at all should be staged, got: {staged!r}")

    def test_head_commit_is_unchanged(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(self.head(), self.baseline)


class TestPrivateArtifactsExist(OverlayHarness):
    def test_private_files_are_written_to_the_worktree(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        for rel in ("AGENTS.md", "CLAUDE.md", "WORKMEMORY/work.log",
                    "scripts/check_repo_hygiene.py", "scripts/check_repo_structure.py"):
            self.assertTrue((self.repo / rel).is_file(), f"{rel} missing")

    def test_hook_lives_inside_dot_git(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertTrue((self.repo / ".git" / "dfs-hooks" / "pre-commit").is_file())
        self.assertFalse((self.repo / ".githooks" / "pre-commit").exists(),
                         "overlay must not create a tracked .githooks/ directory")
        self.assertEqual(git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".git/dfs-hooks")

    def test_local_attributes_pin_lf_without_touching_tracked_file(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        local = self.repo / ".git" / "info" / "attributes"
        self.assertTrue(local.is_file())
        self.assertIn("WORKMEMORY/** text eol=lf", local.read_text(encoding="utf-8"))
        attr = git(["check-attr", "eol", "--", "WORKMEMORY/work.log"], self.repo).stdout
        self.assertIn("eol: lf", attr)

    def test_local_exclude_lists_private_paths(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        text = (self.repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
        for path in ("AGENTS.md", "CLAUDE.md", "WORKMEMORY/", ".env", "credentials.json"):
            self.assertIn(path, text)


class TestSurvivesGitOperations(OverlayHarness):
    def test_private_files_survive_checkout_and_reset(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["checkout", "--", "."], self.repo)
        git(["reset", "-q", "--hard", self.baseline], self.repo)
        self.assertTrue((self.repo / "AGENTS.md").is_file(), "AGENTS.md lost by checkout/reset")
        self.assertTrue((self.repo / "WORKMEMORY" / "work.log").is_file())
        self.assertTrue((self.repo / ".git" / "dfs-hooks" / "pre-commit").is_file())
        self.assertTrue((self.repo / ".git" / "info" / "exclude").is_file())

    def test_upstream_commit_keeps_overlay_clean(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8", newline="\n")
        git(["add", "-A"], self.repo)
        proc = self.commit("upstream change")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.porcelain(), "", "a real upstream commit must not surface private files")


class TestTrackedRulesAreNeverModified(ConflictHarness):
    def test_agents_md_is_byte_identical_after_bootstrap(self) -> None:
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((self.repo / "AGENTS.md").read_text(encoding="utf-8"), UPSTREAM_AGENTS)
        self.assertEqual(git(["show", "HEAD:AGENTS.md"], self.repo).stdout, UPSTREAM_AGENTS)

    def test_claude_md_is_byte_identical_after_bootstrap(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual((self.repo / "CLAUDE.md").read_text(encoding="utf-8"), UPSTREAM_CLAUDE)

    def test_private_anchor_carries_the_rules_instead(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        anchor = self.repo / "AGENTS.dfs.md"
        self.assertTrue(anchor.is_file(), "private anchor must exist when AGENTS.md is upstream-owned")
        text = anchor.read_text(encoding="utf-8")
        self.assertIn("工程规范与避坑检索", text)
        self.assertIn("search_vault", text)
        self.assertIn("WORKMEMORY", text)

    def test_private_anchor_is_invisible_to_git(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertNotIn("AGENTS.dfs.md", self.porcelain())
        git(["add", "-A"], self.repo)
        self.assertNotIn("AGENTS.dfs.md", git(["diff", "--cached", "--name-only"], self.repo).stdout)

    def test_whole_tree_stays_clean(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(self.porcelain(), "", "no tracked file may change")
        self.assertEqual(git(["diff"], self.repo).stdout, "")
        self.assertEqual(self.head(), self.baseline)


class TestUpstreamHookKeepsRunning(ConflictHarness):
    def test_hook_chain_reports_the_upstream_hook(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "touched.txt").write_text("x=1\n", encoding="utf-8", newline="\n")
        git(["add", "touched.txt"], self.repo)
        proc = self.commit("probe")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("UPSTREAM_HOOK_RAN", combined, "the upstream hook must still execute")
        self.assertIn("[CHAIN] upstream hook passed", combined)

    def test_upstream_hook_failure_blocks_the_commit(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        hook = self.repo / ".githooks" / "pre-commit"
        hook.write_text("#!/usr/bin/env bash\necho UPSTREAM_SAYS_NO\nexit 1\n", encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        (self.repo / "touched.txt").write_text("x=1\n", encoding="utf-8", newline="\n")
        git(["add", "touched.txt"], self.repo)
        proc = self.commit("should be blocked")
        self.assertNotEqual(proc.returncode, 0, "an upstream hook failure must abort the commit")
        self.assertIn("[CHAIN] upstream hook failed", proc.stdout + proc.stderr)
        self.assertEqual(self.head(), self.baseline)

    def test_our_own_gate_still_fires_alongside_the_chain(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "demo.py").write_text('p = "D:/Code/other/x.py"\n', encoding="utf-8", newline="\n")  # git:allow-abs-path
        git(["add", "src/demo.py"], self.repo)
        proc = self.commit("abspath")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[ABS_PATH]", proc.stdout + proc.stderr)

    def test_chain_does_not_recurse_into_itself(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "touched.txt").write_text("x=1\n", encoding="utf-8", newline="\n")
        git(["add", "touched.txt"], self.repo)
        combined = self.commit("probe").stdout + self.commit("probe").stderr
        self.assertNotIn("dfs-hooks", combined)


class TestHookChainAbsent(ConflictHarness):
    def test_no_chain_output_when_upstream_has_no_hook(self) -> None:
        (self.repo / ".githooks" / "pre-commit").unlink()
        git(["add", "-A"], self.repo)
        git(["commit", "-qm", "drop upstream hook"], self.repo)
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "touched.txt").write_text("x=1\n", encoding="utf-8", newline="\n")
        git(["add", "touched.txt"], self.repo)
        proc = self.commit("probe")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("[CHAIN]", proc.stdout + proc.stderr)


class TestOwnerMode(OwnerHarness):
    def test_owner_mode_tracks_artifacts_and_edits_gitignore(self) -> None:
        proc = self.bootstrap("--mode", "owner")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((self.repo / ".githooks" / "pre-commit").is_file())
        self.assertIn(".worktrees/", (self.repo / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn("AGENTS.md", self.porcelain(), "owner mode leaves artifacts visible to git")


class TestOverlayNeedsGit(OwnerHarness):
    def test_overlay_initialises_git_when_absent(self) -> None:
        plain = self.root / "no-git"
        plain.mkdir()
        import subprocess
        proc = subprocess.run(
            [sys.executable, "-B", str(pathlib.Path(__file__).resolve().parent.parent / "scripts" / "bootstrap.py"),
             "--target", str(plain), "--vault-root", str(self.vault), "--mode", "overlay"],
            cwd=str(self.root), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((plain / ".git").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
