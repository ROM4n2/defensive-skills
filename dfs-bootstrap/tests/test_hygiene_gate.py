"""Scope-granular hygiene ratchet: self-measured baselines, zero-tolerance clean scopes.

A single global count would let a new host path in `delector/` hide under hundreds of historical
`docs/` paths. These tests pin the bucket semantics: unlisted (category, scope) pairs allow zero,
correctness classes can never be ratcheted away, and the guard detects both a raised bucket and a
newly introduced bucket.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parent.parent
GATE = SKILL / "templates" / "repo" / "check_repo_hygiene.py"
PINS = ".githooks/** text eol=lf\nWORKMEMORY/** text eol=lf\n"
HOST_LINE = "see C:/Users/someone/project for details\n"  # git:allow-abs-path


class HygieneHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        for args in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "t@example.invalid"],
            ["git", "config", "user.name", "T"],
        ):
            subprocess.run(args, cwd=self.root, capture_output=True, check=True)
        self.write(".gitattributes", PINS)
        self.write("main.py", "def main():\n    return 0\n")
        self.commit("baseline")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, rel: str, body: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8", newline="\n")
        # The hygiene gate enumerates `git ls-files`, so fixtures must enter the index to be seen.
        subprocess.run(["git", "add", "--", rel], cwd=self.root, capture_output=True, check=True)

    def commit(self, message: str) -> None:
        subprocess.run(["git", "add", "-A"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.root, capture_output=True, check=True)

    def config(self, payload: dict[str, object]) -> None:
        path = self.root / "data" / "repo_hygiene.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")

    def gate(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(GATE), "--root", str(self.root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )


class TestCleanTree(HygieneHarness):
    def test_clean_repo_passes(self) -> None:
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestScopeBuckets(HygieneHarness):
    def test_unlisted_production_scope_is_rejected(self) -> None:
        """A bucket absent from config allows zero — the whole point of scope granularity."""
        self.write("delector/code.py", HOST_LINE)
        self.config({"ratchet": {"ABS_PATH|docs": 50}})
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[ABS_PATH] delector/code.py", proc.stderr)

    def test_existing_debt_bucket_is_absorbed_and_named(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.config({"ratchet": {"ABS_PATH|docs": 1}})
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ABS_PATH|docs 1/1", proc.stdout)

    def test_one_more_than_bucket_allowance_is_rejected(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.write("docs/also-old.md", HOST_LINE)
        self.config({"ratchet": {"ABS_PATH|docs": 1}})
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ABS_PATH|docs 1/2", proc.stderr)

    def test_root_scope_is_a_separate_bucket(self) -> None:
        """A docs allowance must not absorb a host path in a top-level file."""
        self.write("README.md", HOST_LINE)
        self.config({"ratchet": {"ABS_PATH|docs": 50}})
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[ABS_PATH] README.md", proc.stderr)
        self.assertNotIn("baseline tolerated", proc.stdout)

    def test_correctness_class_is_never_ratcheted(self) -> None:
        """A conflict marker stays fatal even if a config tries to grant it an allowance."""
        self.write("docs/conflict.md", "<<<<<<< HEAD\n")
        self.config({"ratchet": {"CONFLICT|docs": 99}})
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[CONFLICT]", proc.stderr)


class TestBaselineAutomation(HygieneHarness):
    def test_emit_baseline_self_measures_with_provenance(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.write("tools/script.py", HOST_LINE)
        proc = self.gate("--emit-baseline")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads((self.root / "data" / "repo_hygiene.json").read_text(encoding="utf-8"))
        self.assertEqual(data["ratchet"], {"ABS_PATH|docs": 1, "ABS_PATH|tools": 1})
        self.assertIn("measured_at_commit", data["_provenance"])

    def test_emitted_baseline_result_passes_the_audit(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        proc = self.gate("--all")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_guard_fails_when_bucket_rose(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        self.commit("baseline config")
        data = json.loads((self.root / "data" / "repo_hygiene.json").read_text(encoding="utf-8"))
        data["ratchet"]["ABS_PATH|docs"] = 5
        self.config(data)
        proc = self.gate("--ratchet-guard")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ratchet violated", proc.stderr)

    def test_guard_catches_newly_added_bucket(self) -> None:
        """Adding a bucket with a positive value is an increase from implicit zero."""
        self.write("docs/old.md", HOST_LINE)
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        self.commit("baseline config")
        data = json.loads((self.root / "data" / "repo_hygiene.json").read_text(encoding="utf-8"))
        data["ratchet"]["ABS_PATH|delector"] = 4
        self.config(data)
        proc = self.gate("--ratchet-guard")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ABS_PATH|delector", proc.stderr)

    def test_guard_passes_when_bucket_fell(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        self.commit("baseline config")
        data = json.loads((self.root / "data" / "repo_hygiene.json").read_text(encoding="utf-8"))
        data["ratchet"]["ABS_PATH|docs"] = 0
        self.config(data)
        proc = self.gate("--ratchet-guard")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ratchet intact", proc.stdout)


class TestNoGitMode(unittest.TestCase):
    """--no-git self-audits a plain directory — no temp git repo wrapper needed."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "data").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def gate(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(GATE), "--root", str(self.root), "--no-git", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def write(self, rel: str, body: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8", newline="\n")

    def test_plain_directory_audits_without_git(self) -> None:
        self.write("main.py", "def main():\n    return 0\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("filesystem file(s)", proc.stdout)

    def test_catches_host_path_in_plain_directory(self) -> None:
        self.write("delector/code.py", HOST_LINE)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[ABS_PATH] delector/code.py", proc.stderr)

    def test_skips_scratch_dirs_like_structure_gate(self) -> None:
        self.write(".ruff_cache/junk.txt", HOST_LINE)
        self.write("__pycache__/junk.py", HOST_LINE)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_eol_pin_is_git_only(self) -> None:
        """No git ⇒ no checkout CRLF risk; EOL_PIN must not fire on a plain tree."""
        self.write("main.py", "def main():\n    return 0\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("EOL_PIN", proc.stderr + proc.stdout)

    def test_staged_is_rejected_with_no_git(self) -> None:
        proc = self.gate("--staged")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot be combined with --no-git", proc.stderr)

    def test_ratchet_guard_is_rejected_with_no_git(self) -> None:
        proc = self.gate("--ratchet-guard")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot be combined with --no-git", proc.stderr)

    def test_json_and_emit_baseline_work_without_git(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        proc = self.gate("--json")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["by_bucket"]["ABS_PATH|docs"], 1)
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        baseline = json.loads((self.root / "data" / "repo_hygiene.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["ratchet"], {"ABS_PATH|docs": 1})
        self.assertEqual(baseline["_provenance"]["measured_at_commit"], "unknown")


class TestIntrospection(HygieneHarness):
    def test_json_reports_buckets_and_verdict(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.config({"ratchet": {"ABS_PATH|docs": 1}})
        proc = self.gate("--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["verdict"], "pass")
        self.assertEqual(data["by_bucket"]["ABS_PATH|docs"], 1)
        self.assertEqual(data["tolerated_by_bucket"]["ABS_PATH|docs"], {"absorbed": 1, "total": 1})

    def test_explain_shows_buckets_and_provenance(self) -> None:
        self.write("docs/old.md", HOST_LINE)
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        proc = self.gate("--explain")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ABS_PATH|docs = 1", proc.stdout)
        self.assertIn("measured_at_commit=", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
