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


def clean_env(**overrides):
    """os.environ with every knowledge-base variable stripped — i.e. a stranger's machine.

    Without this the gate would pass on the author's box (where $WIKI_PATH is exported) and
    quietly test nothing.
    """
    env = {k: v for k, v in os.environ.items()
           if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH", "DFS_INBOX")}
    env.update(overrides)
    return env


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
        empty_cwd = pathlib.Path(self.tmp.name)
        p = run([str(CONSOLIDATE)], cwd=str(empty_cwd), env=clean_env())
        self.assertEqual(p.returncode, 2, f"expected a loud failure, got {p.returncode}: {p.stdout}")
        self.assertIn("无法解析知识库根目录", p.stderr)

    # -- tier 3: no knowledge base, drafts still land somewhere findable --------------------
    def make_dropbox(self, name="dropbox"):
        drop = pathlib.Path(self.tmp.name) / name
        drop.mkdir()
        (drop / "2026-09-27-alt.md").write_text(DRAFT_BODY, encoding="utf-8")
        return drop

    def test_06_inbox_flag_files_drafts_from_an_arbitrary_directory(self):
        drop = self.make_dropbox()
        p = run([str(CONSOLIDATE), "--vault-path", str(self.root), "--inbox", str(drop),
                 "--execute"], cwd=str(self.tmp.name), env=clean_env())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(list((self.root / "06-Sources").glob("*.md"))), 1)
        self.assertFalse((drop / "2026-09-27-alt.md").exists(), "archived draft was not removed")
        self.assertTrue((self.root / "99-Inbox" / "2026-09-27-gbk.md").is_file(),
                        "--inbox leaked into the default queue")

    def test_07_drop_box_without_a_root_lists_but_never_files(self):
        drop = self.make_dropbox()
        p = run([str(CONSOLIDATE), "--inbox", str(drop)], cwd=str(self.tmp.name), env=clean_env())
        self.assertEqual(p.returncode, 0, f"listing must work without a root: {p.stderr}")
        self.assertIn(str(drop), p.stdout, "the absolute drop-box path is the whole point")
        self.assertIn("2026-09-27-alt.md", p.stdout)
        self.assertIn("--execute", p.stdout, "the user must be told how to promote")
        self.assertTrue((drop / "2026-09-27-alt.md").is_file(), "listing must not move anything")

    def test_08_execute_without_a_root_is_refused(self):
        drop = self.make_dropbox()
        p = run([str(CONSOLIDATE), "--inbox", str(drop), "--execute"],
                cwd=str(self.tmp.name), env=clean_env())
        self.assertEqual(p.returncode, 2, f"filing without a destination must fail loudly: {p.stdout}")
        self.assertIn("无知识库根目录", p.stderr)
        self.assertTrue((drop / "2026-09-27-alt.md").is_file(), "refused run still moved the draft")

    def test_09_drop_box_is_discovered_from_the_working_directory(self):
        cwd = pathlib.Path(self.tmp.name) / "project"
        (cwd / ".dfs-inbox").mkdir(parents=True)
        (cwd / ".dfs-inbox" / "2026-09-27-local.md").write_text(DRAFT_BODY, encoding="utf-8")
        p = run([str(CONSOLIDATE)], cwd=str(cwd), env=clean_env())
        self.assertEqual(p.returncode, 0, f"tier 3 was not discovered from cwd: {p.stderr}")
        self.assertIn("2026-09-27-local.md", p.stdout)

    def test_10_the_drop_box_marker_is_never_treated_as_a_draft(self):
        drop = self.make_dropbox()
        (drop / "README.md").write_text("# DFS draft drop box\n", encoding="utf-8")
        p = run([str(CONSOLIDATE), "--vault-path", str(self.root), "--inbox", str(drop),
                 "--execute"], cwd=str(self.tmp.name), env=clean_env())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(list((self.root / "06-Sources").glob("*.md"))), 1,
                         "the marker was filed as knowledge")
        self.assertTrue((drop / "README.md").is_file(), "the marker was deleted or moved")


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


class TestDeletionBounds(unittest.TestCase):
    """The path bound must survive --inbox: only an explicitly declared root is ever extra."""

    def setUp(self):
        import vault_transaction as vt
        self.vt = vt
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.root = self.tmp / "kb"
        self.drop = self.tmp / "drop"
        self.elsewhere = self.tmp / "elsewhere"
        for d in (self.root, self.drop, self.elsewhere):
            d.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_an_undeclared_path_is_still_refused(self):
        victim = self.elsewhere / "notes.md"
        victim.write_text("do not touch\n", encoding="utf-8")
        with self.assertRaises(self.vt.TransactionError):
            with self.vt.VaultTransaction(self.root, tx_id="tx-bounds") as tx:
                tx.stage_deletion(victim)
        self.assertTrue(victim.is_file(), "an out-of-root deletion actually happened")

    def test_a_declared_extra_root_may_be_deleted(self):
        draft = self.drop / "draft.md"
        draft.write_text("draft\n", encoding="utf-8")
        with self.vt.VaultTransaction(self.root, tx_id="tx-inbox", extra_roots=[self.drop]) as tx:
            tx.stage_deletion(draft)
        self.assertFalse(draft.exists(), "the consumed draft should be removed")

    def test_writes_stay_inside_the_root_even_with_an_extra_root(self):
        outside = self.elsewhere / "target.md"
        with self.assertRaises(self.vt.TransactionError):
            with self.vt.VaultTransaction(self.root, tx_id="tx-write", extra_roots=[self.elsewhere]) as tx:
                tx.stage(outside, new_text="nope")
        self.assertFalse(outside.exists(), "the extra root leaked into the write path")


if __name__ == "__main__":
    unittest.main(verbosity=2)
