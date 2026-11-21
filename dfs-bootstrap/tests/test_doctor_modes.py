#!/usr/bin/env python3
"""Block: doctor. It must look where the hook actually is, and its exit code must mean something.

Two defects, both found by asking "what does a user do next": in overlay mode the hook lives in
`.git/dfs-hooks`, which doctor never looked at, so it said "missing — run bootstrap" forever; and gate
version gaps were printed but never reached the exit code, so `doctor || exit 1` passed on a stale gate.

Run: python -B tests/test_doctor_modes.py
"""
from __future__ import annotations

import pathlib
import unittest

from harness import OwnerHarness, OverlayHarness, run_bootstrap


def _doctor(repo: pathlib.Path, *extra: str) -> "object":
    return run_bootstrap(["--doctor", "--target", str(repo), *extra], repo)


class TestDoctorOverlayMode(OverlayHarness):
    def test_overlay_hook_is_found_where_it_was_installed(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        proc = _doctor(self.repo)
        text = str(proc.stdout) + str(proc.stderr)
        self.assertIn("[mode=overlay]", text)
        self.assertNotIn("pre-commit missing", text)
        self.assertEqual(proc.returncode, 0, text)

    def test_doctor_switches_mode_automatically(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        proc = _doctor(self.repo, "--doctor-mode", "owner")
        self.assertIn("[mode=owner]", str(proc.stdout))
        self.assertIn("pre-commit missing", str(proc.stdout))

    def test_doctor_writes_nothing(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        before = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        _doctor(self.repo)
        after = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        self.assertEqual(before, after, "doctor is read-only")


class TestDoctorExitCodes(OwnerHarness):
    def test_stale_gate_gap_reaches_the_exit_code(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        gate = self.repo / "scripts" / "check_repo_hygiene.py"
        gate.write_text("#!/usr/bin/env python3\n# dfs-bootstrap-gate-version: 1\nprint('stale')\n",
                        encoding="utf-8", newline="\n")
        proc = _doctor(self.repo)
        self.assertEqual(proc.returncode, 1, "a stale gate must not exit 0")
        self.assertIn("[GAP] scripts/check_repo_hygiene.py v1", str(proc.stdout))

    def test_clean_repository_exits_zero(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        proc = _doctor(self.repo)
        self.assertEqual(proc.returncode, 0, str(proc.stdout) + str(proc.stderr))

    def test_verify_executes_the_hook_against_a_synthetic_secret(self) -> None:
        """Textual `token in text` detection cannot tell a working scan from a comment about one."""
        self.assertEqual(self.bootstrap().returncode, 0)
        proc = _doctor(self.repo, "--verify")
        text = str(proc.stdout) + str(proc.stderr)
        self.assertIn("secret scan probe", text)
        self.assertIn("blocked the synthetic secret", text)
        self.assertEqual(proc.returncode, 0, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
