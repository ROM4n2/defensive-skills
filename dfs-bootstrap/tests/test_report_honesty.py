#!/usr/bin/env python3
"""Block: report honesty. A tag has to describe what happened, not what was intended.

`--dry-run` used to print `[OK] added 13 required pattern(s)` next to its `[DRY]` line, because each
writer printed its success message unconditionally. An agent that filters on `[OK]` — the obvious way
to read this output — believed the plan was the result. The same pattern produced
`installed .githooks/pre-commit (mode 0755, ...)` for a hook git had recorded as 100644.

Run: python -B tests/test_report_honesty.py
"""
from __future__ import annotations

import unittest

from harness import OwnerHarness, git, run_bootstrap


class TestDryRunHonesty(OwnerHarness):
    def test_dry_run_prints_plans_not_results(self) -> None:
        proc = run_bootstrap(
            ["--target", str(self.repo), "--vault-root", str(self.vault), "--dry-run"], self.root
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[DRY] would append 13 required pattern(s)", proc.stdout)
        for claim in ("installed .githooks/pre-commit", "created AGENTS.md", "added 13 required"):
            self.assertNotIn(claim, proc.stdout, f"dry run must not claim '{claim}'")
        self.assertFalse((self.repo / ".gitignore").exists())
        self.assertFalse((self.repo / "AGENTS.md").exists())

    def test_dry_run_names_the_backup_side_effect(self) -> None:
        gate = self.repo / "scripts" / "check_repo_hygiene.py"
        gate.parent.mkdir()
        stale = "#!/usr/bin/env python3\n# dfs-bootstrap-gate-version: 1\n"
        gate.write_text(stale, encoding="utf-8", newline="\n")
        proc = run_bootstrap(
            ["--target", str(self.repo), "--vault-root", str(self.vault), "--dry-run"], self.root
        )
        self.assertIn("previous kept as check_repo_hygiene.py.dfsbak", proc.stdout)
        self.assertEqual(gate.read_text(encoding="utf-8"), stale, "dry run must not upgrade")

    def test_real_run_reports_the_index_mode_it_recorded(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["add", ".githooks/pre-commit"], self.repo)
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("100755", proc.stdout, "the report must quote the index, not a wish")
        mode = git(["ls-files", "-s", ".githooks/pre-commit"], self.repo).stdout.split()[0]
        self.assertEqual(mode, "100755")


if __name__ == "__main__":
    unittest.main(verbosity=2)
