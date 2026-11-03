#!/usr/bin/env python3
"""`install.py` — tier-aware installation into a harness skills directory.

Drives the real CLI against a temp directory. Tier expectations come from an independent tree
measurement, not from README or install.py's own parser.
"""

import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
INSTALL = REPO / "install.py"
ROW = re.compile(r"^\|\s*(?:\*\*(?:主链|chain)\*\*\s+)?`(dfs[a-z0-9-]*)`\s*\|[^|]*\|([^|]*)\|", re.M)
TREE = sorted(p.name for p in REPO.glob("dfs*") if p.is_dir())


def readme_tiers() -> dict[str, str]:
    """Independent tier measurement shared with the catalogue tests."""
    spec = importlib.util.spec_from_file_location(
        "_readme_table", REPO / "tests" / "test_readme_skill_table.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {name: values["tier"] for name, values in module.skill_measurements().items()}


def run_install(target: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), "--target", str(target), *args],
                          capture_output=True, text=True)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmp.name) / "skills"

    def tearDown(self):
        self._tmp.cleanup()

    def test_00_the_manifest_covers_the_tree(self):
        """Anti-vacuity: if this parse found nothing, every assertion below would be meaningless."""
        tiers = readme_tiers()
        self.assertEqual(set(tiers), set(TREE), "README prerequisite column and the tree disagree")
        self.assertEqual(sorted(set(tiers.values())), ["A", "B", "C"],
                         "unexpected prerequisite tiers in the tree measurement")

    def test_01_installs_every_skill_in_copy_mode(self):
        proc = run_install(self.target, "--mode", "copy")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        installed = sorted(p.name for p in self.target.iterdir())
        self.assertEqual(installed, TREE)
        for name in TREE:
            self.assertTrue((self.target / name / "SKILL.md").is_file(), f"{name}/SKILL.md missing")

    def test_02_tier_filter_selects_exactly_the_labelled_skills(self):
        for tier, label in (("A", "A"), ("C", "C")):
            with self.subTest(tier=tier):
                shutil.rmtree(self.target, ignore_errors=True)
                expected = sorted(n for n, lab in readme_tiers().items() if lab == label)
                proc = run_install(self.target, "--tier", tier, "--mode", "copy")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(sorted(p.name for p in self.target.iterdir()), expected)
                self.assertGreater(len(expected), 0)

    def test_03_refuses_to_clobber_without_force(self):
        dest = self.target / "dfs-tdd"
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("hand-written, do not lose me\n", encoding="utf-8")
        proc = run_install(self.target, "--mode", "copy")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "hand-written, do not lose me\n",
                         "install overwrote an existing skill without --force")
        self.assertIn("SKIP", proc.stdout)

    def test_04_force_replaces_it(self):
        dest = self.target / "dfs-tdd"
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("stale\n", encoding="utf-8")
        proc = run_install(self.target, "--mode", "copy", "--force")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        body = (dest / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("dfs-tdd", body, "content was not replaced by the real skill")

    def test_05_dry_run_writes_nothing(self):
        proc = run_install(self.target, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(self.target.exists(), "--dry-run created the target directory")
        self.assertIn("DRY", proc.stdout)

    def test_06_bad_usage_is_loud(self):
        missing_parent = pathlib.Path(self._tmp.name) / "nope" / "skills"
        self.assertEqual(run_install(missing_parent).returncode, 2)
        self.assertEqual(run_install(self.target, "--tier", "Z").returncode, 2)

    def test_07_link_mode_creates_symlinks_where_the_os_allows(self):
        if os.name == "nt":
            self.skipTest("symlink semantics differ on Windows; covered by the copy-mode tests")
        proc = run_install(self.target, "--mode", "link")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        entry = self.target / "dfs-tdd"
        self.assertTrue(entry.is_symlink(), "link mode did not create a symlink")
        self.assertTrue((entry / "SKILL.md").is_file(), "symlink does not resolve to the skill")

    def test_08_prints_the_mcp_registration_snippet(self):
        proc = run_install(self.target, "--dry-run")
        self.assertIn("knowledge_server.py", proc.stdout)
        self.assertIn("coding-vault-search", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
