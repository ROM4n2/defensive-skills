#!/usr/bin/env python3
"""Block: repair paths. Every "preserved" branch needs a way back, or a damaged file is permanent.

Four states used to be dead ends: a 0-byte gate (interrupted upgrade) was classified as
"project-owned — preserved"; a gate whose marker sat below line 5 was reclassified the same way; a
newer gate was silently downgraded; `AGENTS.dfs.md` and a custom `CLAUDE.md` were rewritten (or never
fixed) instead of kept. `WORKMEMORY/` was keyed on the directory, so a partial scaffold stayed
partial forever.

Run: python -B tests/test_repair_paths.py
"""
from __future__ import annotations

import pathlib
import unittest

from harness import ConflictHarness, OwnerHarness

POINTER_BODY = (
    "@AGENTS.md\n"
    "<!-- Canonical rules live in AGENTS.md; read ./AGENTS.md directly if your runtime does not "
    "expand @imports. -->\n"
)


class TestGateRepair(OwnerHarness):
    def _gate(self) -> pathlib.Path:
        gate = self.repo / "scripts" / "check_repo_hygiene.py"
        gate.parent.mkdir(parents=True, exist_ok=True)
        return gate

    def test_zero_byte_gate_is_repaired_not_preserved(self) -> None:
        gate = self._gate()
        gate.write_bytes(b"")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("0 bytes", proc.stdout)
        self.assertIn("repaired scripts/check_repo_hygiene.py", proc.stdout)
        self.assertGreater(gate.stat().st_size, 0, "a 0-byte gate must never be left in place")

    def test_marker_below_line_five_is_still_detected(self) -> None:
        gate = self._gate()
        header = "#!/usr/bin/env python3\n" + "".join(f"# note {i}\n" for i in range(6))
        gate.write_text(header + "# dfs-bootstrap-gate-version: 1\n", encoding="utf-8", newline="\n")
        proc = self.bootstrap()
        self.assertIn("upgraded scripts/check_repo_hygiene.py v1 -> v4", proc.stdout)

    def test_newer_gate_is_not_downgraded(self) -> None:
        gate = self._gate()
        newer = "#!/usr/bin/env python3\n# dfs-bootstrap-gate-version: 99\nprint('future')\n"
        gate.write_text(newer, encoding="utf-8", newline="\n")
        proc = self.bootstrap()
        self.assertIn("is newer (v99 > v4)", proc.stdout)
        self.assertEqual(gate.read_text(encoding="utf-8"), newer)


class TestAnchorRepair(OwnerHarness):
    def test_custom_claude_md_becomes_the_pointer_with_a_backup(self) -> None:
        pointer = self.repo / "CLAUDE.md"
        custom = "# Project Guidelines\n\n- run make test\n"
        pointer.write_text(custom, encoding="utf-8", newline="\n")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(pointer.read_text(encoding="utf-8"), POINTER_BODY)
        backup = self.repo / "CLAUDE.md.dfsbak"
        self.assertEqual(backup.read_text(encoding="utf-8"), custom, "the old rules must be kept")

    def test_workmemory_partial_scaffold_is_completed_per_file(self) -> None:
        memory = self.repo / "WORKMEMORY"
        memory.mkdir()
        history = "# demo work.log\n\n### 2026-01-01 00:00 | x | NOTE\nreal history\n"
        (memory / "work.log").write_text(history, encoding="utf-8", newline="\n")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        for name in ("PROTOCOL.md", "INDEX.md", "INDEX-topics.md", "PROJECT_OVERVIEW.md"):
            self.assertTrue((memory / name).is_file(), f"{name} must be scaffolded")
        self.assertEqual((memory / "work.log").read_text(encoding="utf-8"), history)


class TestPrivateAnchorIsAppendOnly(ConflictHarness):
    def test_user_edits_to_the_private_anchor_survive_a_rerun(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        private = self.repo / "AGENTS.dfs.md"
        self.assertTrue(private.is_file())
        with private.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n- USER EDIT: keep this line\n")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("USER EDIT: keep this line", private.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
