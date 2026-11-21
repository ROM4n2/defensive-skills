"""Performance contracts for the pre-commit hook and the gates.

These are not micro-benchmarks; each one asserts a property that, if lost, makes the hook slow enough
that contributors bypass it with `--no-verify` — which silently disables every check.

Run: python -B tests/test_performance.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

from harness import HYGIENE_GATE, STRUCTURE_GATE, git

HOOK = pathlib.Path(__file__).resolve().parent.parent / "templates" / "githooks-pre-commit.sh"

# A repo large enough that O(N) process spawns dominate. 300 files keeps the test under ~10 s while
# still separating 0.2 s (batch) from 8 s (per-file).
MODULE_COUNT = 300


class TestHygieneReadsBlobsInOnePass(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        git(["init", "-q"], self.root)
        git(["config", "user.email", "t@example.invalid"], self.root)
        git(["config", "user.name", "T"], self.root)
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "check_repo_hygiene.py").write_bytes(HYGIENE_GATE.read_bytes())
        for i in range(MODULE_COUNT):
            d = self.root / "src" / f"pkg{i:03d}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "__init__.py").write_text("", encoding="utf-8", newline="\n")
            (d / "mod.py").write_text(f"def f{i}(x):\n    return x\n", encoding="utf-8", newline="\n")
        (self.root / ".gitattributes").write_text(
            ".githooks/** text eol=lf\nWORKMEMORY/** text eol=lf\n", encoding="utf-8", newline="\n"
        )
        git(["add", "-A"], self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_staged_scan_of_300_files_finishes_quickly(self) -> None:
        """`--staged` must not spawn one `git show` per file.

        Measured: per-file `git show` costs ~32 ms, so 300 files alone would take ~9.6 s; the batch
        reader does the whole index in ~1 s. The 6 s ceiling separates the two implementations with
        room for slow CI disks while still failing the O(N) form.
        """
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, "-B", "scripts/check_repo_hygiene.py", "--staged"],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        elapsed = time.perf_counter() - t0
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # __init__.py + mod.py per package, plus the gate script and .gitattributes.
        expected = len(git(["diff", "--cached", "--name-only"], self.root).stdout.split())
        self.assertIn(f"{expected} staged file(s)", proc.stdout)
        self.assertLess(elapsed, 6.0, f"staged scan took {elapsed:.1f}s; is it back to per-file git show?")

    def test_batch_reader_still_finds_a_defect(self) -> None:
        """The fast path must not have traded correctness for speed."""
        bad = self.root / "src" / "bad.py"
        bad.write_text('p = "D:/Code/other/x.py"\n', encoding="utf-8", newline="\n")  # git:allow-abs-path
        git(["add", "src/bad.py"], self.root)
        proc = subprocess.run(
            [sys.executable, "-B", "scripts/check_repo_hygiene.py", "--staged"],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[ABS_PATH]", proc.stderr)

    def test_empty_index_is_clean_and_fast(self) -> None:
        git(["reset", "-q"], self.root)
        proc = subprocess.run(
            [sys.executable, "-B", "scripts/check_repo_hygiene.py", "--staged"],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestHookRunsGatesInParallel(unittest.TestCase):
    """Scheduling contracts asserted by OBSERVED behaviour, not by wall-clock ceilings.

    An absolute ceiling ("under 3.4 s") encodes this machine's `git commit` + hook overhead into the
    assertion: measured here at ~2.2 s before any gate starts, so a correct parallel run already
    exceeded a 3.0 s budget and the test failed while the hook was provably fine. Cross-process
    timing magnitude is not a correctness property — starting the 2nd gate in parallel makes it
    add ~0 s, sequential makes it add ~2 s, and only the OVERLAP of the two gate lifetimes can
    distinguish those regardless of how slow the host is. Stubs therefore stamp their own start/end.

    Run: HOOK_STUB_SLEEP controls the stub sleep (default 2 s); STUB_TEMPLATE writes the stamps.
    """

    STUB_SLEEP = 2.0
    STUB_TEMPLATE = (
        "import pathlib, sys, time\n"
        "here = pathlib.Path(__file__).resolve().parent\n"
        "(here / '{name}.start').write_text(repr(time.time()))\n"
        "time.sleep({sleep})\n"
        "(here / '{name}.end').write_text(repr(time.time()))\n"
        "sys.exit(0)\n"
    )

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        git(["init", "-q"], self.root)
        git(["config", "user.email", "t@example.invalid"], self.root)
        git(["config", "user.name", "T"], self.root)
        (self.root / ".githooks").mkdir()
        hook = self.root / ".githooks" / "pre-commit"
        hook.write_bytes(HOOK.read_bytes())
        hook.chmod(0o755)
        git(["config", "core.hooksPath", ".githooks"], self.root)
        (self.root / "scripts").mkdir()
        # Stub gates record their own lifetime, so the assertion is about scheduling, not gate logic.
        for name in ("check_repo_hygiene", "check_repo_structure"):
            (self.root / "scripts" / f"{name}.py").write_text(
                self.STUB_TEMPLATE.format(name=name, sleep=self.STUB_SLEEP),
                encoding="utf-8", newline="\n",
            )
        (self.root / ".gitattributes").write_text(".githooks/** text eol=lf\n", encoding="utf-8", newline="\n")
        (self.root / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8", newline="\n")
        git(["add", "-A"], self.root)
        git(["commit", "-qm", "base"], self.root)
        # The base commit above ALSO runs the hook, leaving sentinels from THAT run. Clear them so
        # each test observes only the commit it makes — otherwise a skipped gate looks "present".
        for stale in (self.root / "scripts").glob("*.start"):
            stale.unlink()
        for stale in (self.root / "scripts").glob("*.end"):
            stale.unlink()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _lifetime(self, name: str) -> tuple[float, float] | None:
        """(start, end) of a stub gate, or None when it never ran."""
        scripts = self.root / "scripts"
        start, end = scripts / f"{name}.start", scripts / f"{name}.end"
        if not start.is_file() or not end.is_file():
            return None
        return float(start.read_text(encoding="utf-8")), float(end.read_text(encoding="utf-8"))

    def _commit(self, message: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "commit", "-m", message], cwd=self.root,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def test_two_gates_run_concurrently(self) -> None:
        """Their lifetimes must OVERLAP. Sequential would make the second start only after the
        first ended (overlap <= 0); parallel keeps ~2 s of shared time no matter the host speed."""
        (self.root / "b.py").write_text("def b():\n    return 2\n", encoding="utf-8", newline="\n")
        git(["add", "b.py"], self.root)
        proc = self._commit("parallel")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        hygiene = self._lifetime("check_repo_hygiene")
        structure = self._lifetime("check_repo_structure")
        self.assertIsNotNone(hygiene, "hygiene gate did not run on a staged .py")
        self.assertIsNotNone(structure, "structure gate did not run on a staged .py")
        overlap = min(hygiene[1], structure[1]) - max(hygiene[0], structure[0])
        self.assertGreater(
            overlap, 1.0,
            f"gates overlapped only {overlap:.2f}s; they may have gone sequential",
        )

    def test_a_failing_gate_still_blocks_the_commit(self) -> None:
        (self.root / "scripts" / "check_repo_hygiene.py").write_text(
            "import sys\nprint('[ABS_PATH] demo', file=sys.stderr)\nsys.exit(1)\n",
            encoding="utf-8", newline="\n",
        )
        (self.root / "c.py").write_text("def c():\n    return 3\n", encoding="utf-8", newline="\n")
        git(["add", "c.py"], self.root)
        proc = self._commit("blocked")
        self.assertNotEqual(proc.returncode, 0, "a failing gate must abort the commit")
        self.assertIn("[ABS_PATH]", proc.stdout + proc.stderr)

    def test_structure_gate_skipped_when_no_python_is_staged(self) -> None:
        """The structure gate must not even START on a docs-only commit — proven by its sentinel
        being absent, not by how long the commit took."""
        (self.root / "notes.md").write_text("# notes\n", encoding="utf-8", newline="\n")
        git(["add", "notes.md"], self.root)
        proc = self._commit("docs")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIsNotNone(self._lifetime("check_repo_hygiene"), "hygiene gate must still run")
        self.assertIsNone(
            self._lifetime("check_repo_structure"),
            "structure gate ran on a docs-only commit; the expensive gate is no longer skipped",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
