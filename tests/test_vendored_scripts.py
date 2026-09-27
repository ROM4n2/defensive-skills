#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runnable checks for the shipped engine scripts (scripts/vault_*.py).

Two layers, because they fail differently:
  * CLI level — the ledger lifecycle and the transactional inbox archival, run as a real process so
    the `from vault_transaction import ...` import path is exercised the way a user invokes it.
  * Unit level — the transaction's rollback, which the CLI can only reach on a real mid-commit
    failure. An injected `os.replace` failure is the cheapest way to prove no half-written state
    survives, and it is the reason `--execute` is safe to run unattended.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
EXEC_STATE = SCRIPTS / "vault_exec_state.py"
CONSOLIDATE = SCRIPTS / "vault-inbox-consolidate.py"

sys.path.insert(0, str(SCRIPTS))

DRAFT_BODY = """---
title: "Windows GBK 乱码修复"
created: 2026-09-27
updated: 2026-09-27
type: source-notes
tags:
  - category/notes
  - status/draft
status: draft
---

Symptom: mojibake on stdout. Root cause: cp936 codec. Fix: reconfigure stdout to utf-8.
"""

UNROUTED_BODY = """---
title: "Unrouted note"
type: source-notes
tags:
  - topic/nobody-routes-this
status: draft
---

Falls back to the config's `source-notes` branch.
"""


def run(cmd, cwd=None, env=None):
    return subprocess.run([sys.executable, *cmd], capture_output=True, text=True,
                          encoding="utf-8", cwd=cwd, env=env)


class TestExecStateLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args):
        return run([str(EXEC_STATE), "--workdir", str(self.work), *args])

    def test_lifecycle(self):
        # --tasks takes each label verbatim as the task id (only --plan-file synthesises `Task-<n>`),
        # so the labels must already carry the `Task-1` shape to be addressable by --task-id.
        p = self.cli("init", "--tasks", "Task-1,Task-2")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((self.work / ".vault-exec-ledger.json").is_file())

        data = json.loads(self.cli("status", "--json").stdout)
        self.assertEqual(data["total_tasks"], 2)
        self.assertEqual(data["completed_count"], 0)

        self.assertEqual(self.cli("start-task", "--task-id", "Task-2").returncode, 0)
        self.assertEqual(json.loads(self.cli("status", "--json").stdout)["active_task_id"], "Task-2")

        # resume reports the first unfinished task, which is still Task-1
        self.assertIn("Task-1", self.cli("resume", "--json").stdout)

        self.assertEqual(self.cli("complete-task", "--task-id", "Task-2",
                                  "--commit", "abc1234", "--reviewer", "PASS").returncode, 0)
        after = json.loads(self.cli("status", "--json").stdout)
        self.assertEqual(after["completed_count"], 1)
        self.assertIsNone(after["active_task_id"])
        done = [t for t in after["tasks"] if t["id"] == "Task-2"][0]
        self.assertEqual(done["commit_hash"], "abc1234")
        self.assertEqual(done["reviewer_verdict"], "PASS")
        self.assertIn("Task-1", self.cli("resume", "--json").stdout)

    def test_plan_file_init_extracts_ids_and_roles(self):
        """The path dfs-exec actually uses: task ids and implementer roles come from the plan."""
        plan = self.work / "implementation_plan.md"
        plan.write_text(
            "# Plan\n\n"
            "### Task 1: Add the parser [Subagent: TDD]\n"
            "### Task 2: Wire the CLI [Subagent: reviewer]\n",
            encoding="utf-8")
        p = self.cli("init", "--plan-file", str(plan))
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(self.cli("status", "--json").stdout)
        self.assertEqual([t["id"] for t in data["tasks"]], ["Task-1", "Task-2"])
        self.assertEqual([t["title"] for t in data["tasks"]],
                         ["Add the parser [Subagent: TDD]", "Wire the CLI [Subagent: reviewer]"])
        self.assertEqual(data["tasks"][0]["implementer"], "TDD")
        self.assertEqual(data["tasks"][1]["implementer"], "reviewer")

    def test_error_paths_are_loud(self):
        self.assertEqual(self.cli("start-task", "--task-id", "Task-9").returncode, 1,
                         "starting a task with no ledger must fail")
        self.cli("init", "--tasks", "Task 1")
        p = self.cli("complete-task", "--task-id", "Task-9")
        self.assertEqual(p.returncode, 1, "unknown task id must fail")
        p = self.cli("init")
        self.assertEqual(p.returncode, 1, "init without tasks or a plan file must fail")


class TestInboxConsolidate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / "kb"
        (self.root / "99-Inbox").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("# marker\n", encoding="utf-8")
        (self.root / "99-Inbox" / "2026-09-27-gbk.md").write_text(DRAFT_BODY, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, cwd=None, env=None):
        return run([str(CONSOLIDATE), "--vault-path", str(self.root), *args], cwd=cwd, env=env)

    def test_01_no_local_routing_json_shadowing_the_example(self):
        local = SCRIPTS / "routing.json"
        self.assertFalse(
            local.is_file(),
            f"{local} exists and shadows routing.example.json; this test asserts example-config "
            f"behaviour. Move it aside (it is git-ignored) or update the test's expectations.",
        )

    def test_02_dry_run_writes_nothing(self):
        p = self.cli("--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("PREVIEW", p.stdout)
        self.assertIn("06-Sources", p.stdout)
        self.assertFalse((self.root / "06-Sources").exists(), "dry-run created the target directory")
        self.assertTrue((self.root / "99-Inbox" / "2026-09-27-gbk.md").is_file())

    def test_03_execute_archives_and_deletes_the_original(self):
        p = self.cli("--execute")
        self.assertEqual(p.returncode, 0, p.stderr)
        archived = sorted((self.root / "06-Sources").glob("*.md"))
        self.assertEqual(len(archived), 1, f"expected exactly one archived note, got {archived}")
        text = archived[0].read_text(encoding="utf-8")
        # The engine quotes the value it writes (`status: "stable"`); assert the state, not the
        # quoting style, so a future change to either does not produce a false failure here.
        self.assertRegex(text, r'status:\s*"?stable"?')
        self.assertIn("cp936 codec", text)
        self.assertFalse((self.root / "99-Inbox" / "2026-09-27-gbk.md").exists(),
                         "original draft was not removed")

    def test_04_unrouted_draft_uses_the_fallback_branch(self):
        (self.root / "99-Inbox" / "2026-09-27-unrouted.md").write_text(UNROUTED_BODY, encoding="utf-8")
        p = self.cli("--execute")
        self.assertEqual(p.returncode, 0, p.stderr)
        names = sorted(f.name for f in (self.root / "06-Sources").glob("*.md"))
        self.assertEqual(len(names), 2, f"fallback route not applied: {names}")

    def test_05_missing_root_fails_loudly_instead_of_reporting_empty(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH")}
        empty_cwd = pathlib.Path(self.tmp.name)
        p = run([str(CONSOLIDATE)], cwd=str(empty_cwd), env=env)
        self.assertEqual(p.returncode, 2, f"expected a loud failure, got {p.returncode}: {p.stdout}")
        self.assertIn("无法解析知识库根目录", p.stderr)


class TestTransactionRollback(unittest.TestCase):
    def test_injected_commit_failure_leaves_no_half_written_state(self):
        import vault_transaction as vt

        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            first, second = root / "a.md", root / "b.md"
            first.write_text("A-original", encoding="utf-8")
            second.write_text("B-original", encoding="utf-8")

            real_replace = os.replace
            calls = {"n": 0}

            def flaky_replace(src, dst):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise OSError("injected replace failure")
                return real_replace(src, dst)

            vt.os.replace = flaky_replace
            try:
                with self.assertRaises(Exception):
                    with vt.VaultTransaction(root, tx_id="tx-injected") as tx:
                        tx.stage(first, new_text="A-new")
                        tx.stage(second, new_text="B-new")
            finally:
                vt.os.replace = real_replace

            self.assertEqual(first.read_text(encoding="utf-8"), "A-original")
            self.assertEqual(second.read_text(encoding="utf-8"), "B-original")
            self.assertFalse((root / "a.md.tmp").exists(), "temp file left behind")
            self.assertFalse((root / "b.md.tmp").exists(), "temp file left behind")
            journal = json.loads((root / ".vault-tx" / "tx-injected.json").read_text(encoding="utf-8"))
            self.assertEqual(journal["status"], "rolled_back")


if __name__ == "__main__":
    unittest.main(verbosity=2)
