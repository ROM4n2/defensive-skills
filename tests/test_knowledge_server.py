#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end check for mcp/knowledge_server.py.

Drives the real server over stdio JSON-RPC against a throwaway knowledge root built in a temp
dir — no mocking of the protocol layer, because the protocol layer is what breaks silently.

Also asserts the server's tool list equals the conformance canon (`KNOWN_MCP_TOOLS`), so the
server and the skills' declared `mcp_tools` contracts cannot drift apart unnoticed.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SERVER = _REPO_ROOT / "mcp" / "knowledge_server.py"

sys.path.insert(0, str(_REPO_ROOT / "mcp"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from knowledge_server import KnowledgeBase, load_layout, tool_search_vault  # noqa: E402
from test_skills_conformance import KNOWN_MCP_TOOLS  # noqa: E402

RULE_NOTE = """---
title: "Universal coding rules"
status: stable
tags:
  - category/rules
  - topic/concurrency
---

# Universal rules

## Naming
Use intent-revealing names. See [[GO-STANDARDS]].

## Error handling
Never swallow an error without logging it.

## Concurrency
A global lock is a known ceiling; see `ponytail:` comments.
"""

GO_STANDARDS = """---
title: "Go standards"
tags:
  - lang/go
  - topic/concurrency
---

# Go standards

## Worker pools
Bound the pool with a semaphore channel. TODO: document the cancellation path.
"""

CAREER_NOTE = """---
title: "Interview: distributed locks"
tags:
  - category/interview
---

# Distributed locks

Redis redlock, fencing tokens, and why a lease needs a monotonic clock.
"""

RESEARCHER_PROMPT = "You are the codebase researcher. Follow the reuse ladder.\n"
WORKER_POOL = "package main\n\nfunc workerPool() {}\n"


def build_root(base: pathlib.Path) -> pathlib.Path:
    base.mkdir(parents=True, exist_ok=True)
    (base / "AGENTS.md").write_text("# knowledge root marker\n", encoding="utf-8")
    (base / "01-Rules").mkdir(parents=True)
    (base / "01-Rules" / "CODING-UNIVERSAL.md").write_text(RULE_NOTE, encoding="utf-8")
    (base / "03-Languages" / "GO").mkdir(parents=True)
    (base / "03-Languages" / "GO" / "GO-STANDARDS.md").write_text(GO_STANDARDS, encoding="utf-8")
    (base / "09-Career").mkdir()
    (base / "09-Career" / "DISTRIBUTED-LOCKS.md").write_text(CAREER_NOTE, encoding="utf-8")
    (base / "Templates" / "code" / "go").mkdir(parents=True)
    (base / "Templates" / "code" / "go" / "worker-pool.go").write_text(WORKER_POOL, encoding="utf-8")
    (base / "05-Tools" / "Subagents").mkdir(parents=True)
    (base / "05-Tools" / "Subagents" / "SUBAGENT-RESEARCHER.md").write_text(RESEARCHER_PROMPT, encoding="utf-8")
    return base


class Server:
    """Minimal JSON-RPC client over the server's stdio."""

    def __init__(self, root: "pathlib.Path | None" = None, env_extra=None, cwd=None):
        args = [sys.executable, str(_SERVER)]
        if root is not None:
            args += ["--root", str(root)]
        # Strip every knowledge-base variable: this machine exports $WIKI_PATH, so without this a
        # test written for "a stranger's box" would silently test the author's setup instead.
        env = {k: v for k, v in __import__("os").environ.items()
               if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH", "DFS_INBOX")}
        env.update(env_extra or {})
        self.proc = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", env=env, cwd=str(cwd) if cwd else None,
        )
        self._id = 0

    def call(self, method: str, params=None):
        self._id += 1
        req = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            req["params"] = params
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise AssertionError(f"server closed stdout on {method}; stderr={self.proc.stderr.read()}")
        return json.loads(line)

    def text(self, tool: str, **args) -> str:
        resp = self.call("tools/call", {"name": tool, "arguments": args})
        return resp["result"]["content"][0]["text"]

    def is_error(self, tool: str, **args) -> bool:
        resp = self.call("tools/call", {"name": tool, "arguments": args})
        return bool(resp["result"].get("isError"))

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def finish(self) -> str:
        """Close stdin and return everything the server wrote to stderr."""
        self.close()
        return self.proc.stderr.read() if self.proc.stderr else ""


class TestKnowledgeServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="dfs-kb-"))
        cls.root = build_root(cls.tmp / "kb")
        cls.srv = Server(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.srv.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_01_initialize_and_tool_canon(self):
        init = self.srv.call("initialize", {"protocolVersion": "2024-11-05"})
        self.assertEqual(init["result"]["serverInfo"]["name"], "coding-vault-search")
        tools = [t["name"] for t in self.srv.call("tools/list")["result"]["tools"]]
        self.assertEqual(sorted(tools), sorted(KNOWN_MCP_TOOLS),
                         "server tool list drifted from the conformance canon")
        for tool in self.srv.call("tools/list")["result"]["tools"]:
            self.assertIn("inputSchema", tool, f"{tool['name']} has no inputSchema")

    def test_02_get_note_reads_and_lists(self):
        out = self.srv.text("get_note", rel_path="01-Rules/CODING-UNIVERSAL.md")
        self.assertIn("Universal rules", out)
        out = self.srv.text("get_note", rel_path="01-Rules")
        self.assertIn("CODING-UNIVERSAL.md", out)

    def test_03_get_note_rejects_traversal(self):
        # Verify the property, not a message: nothing outside the root may ever be readable.
        sentinel = "SENTINEL-OUTSIDE-CONTENT"
        secret = self.tmp / "outside-secret.md"
        secret.write_text(sentinel + "\n", encoding="utf-8")
        attempts = [
            "../outside-secret.md",
            "../../outside-secret.md",
            "..\\outside-secret.md",
            "01-Rules/../../../outside-secret.md",
            str(secret),          # absolute path to a file that really exists, outside the root
            "/etc/passwd",
            "C:\\Windows\\win.ini",
        ]
        for bad in attempts:
            with self.subTest(attempt=bad):
                out = self.srv.text("get_note", rel_path=bad)
                self.assertNotIn(sentinel, out, f"leaked a file outside the root via {bad!r}")
                self.assertNotIn("root:x:", out, f"leaked /etc/passwd via {bad!r}")
                self.assertTrue(out.startswith(("Refused:", "Note not found:")),
                                f"unexpected response for {bad!r}: {out[:160]}")

    def test_04_get_rule_snippet_slices_one_section(self):
        out = self.srv.text("get_rule_snippet", rule_name="CODING-UNIVERSAL", section="error handling")
        self.assertIn("Never swallow an error", out)
        self.assertNotIn("Use intent-revealing names", out, "snippet leaked a neighbouring section")
        missing = self.srv.text("get_rule_snippet", rule_name="CODING-UNIVERSAL", section="no-such-section")
        self.assertIn("No section matching", missing)

    def test_05_search_vault_scores_and_filters(self):
        hit = self.srv.text("search_vault", query="concurrency", format="compact")
        self.assertIn("GO-STANDARDS.md", hit)
        self.assertNotIn("DISTRIBUTED-LOCKS.md", hit)
        tagged = self.srv.text("search_vault", query="locks", tag="category/interview")
        self.assertIn("DISTRIBUTED-LOCKS.md", tagged)
        none = self.srv.text("search_vault", query="zzz-nonexistent-zzz")
        self.assertIn("No relevant notes found", none)

    def test_06_omni_search_short_circuits_on_local_hit(self):
        hit = self.srv.text("omni_search", query="worker pool", scope="ladder")
        self.assertIn("L1_KNOWLEDGE_HIT", hit)
        miss = self.srv.text("omni_search", query="zzz-nonexistent-zzz", scope="ladder")
        self.assertIn("NOT_IN_KNOWLEDGE", miss)
        self.assertIn("save_inbox_draft", miss, "escalation must tell the agent how to stop the next miss")

    def test_07_a_mac_gate_rejects_then_accepts(self):
        self.assertIn("Rejected", self.srv.text("save_inbox_draft", title="x", content="short"))
        self.assertIn("Rejected", self.srv.text("save_inbox_draft", title="fine title", content="also too short"))

        out = self.srv.text("save_inbox_draft", title="Windows GBK stdout fix",
                            content="Symptom: mojibake. Root cause: cp936 codec. Fix: reconfigure stdout to utf-8.",
                            tags=["lang/python", "category/troubleshooting"], source="unit test")
        self.assertIn("A-MAC passed", out)
        drafts = sorted((self.root / "99-Inbox").glob("*.md"))
        self.assertEqual(len(drafts), 1, f"expected exactly 1 draft, found {drafts}")
        body = drafts[0].read_text(encoding="utf-8")
        self.assertIn("status: draft", body)
        self.assertIn("category/troubleshooting", body)
        self.srv._draft = drafts[0].name

    def test_08_promote_moves_and_flips_status(self):
        # Self-contained on purpose: no ordering dependency on test_07.
        name = "2026-01-01-promote-me.md"
        inbox = self.root / "99-Inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / name).write_text(
            '---\ntitle: "Promote me"\nstatus: draft\nupdated: 2020-01-01\n---\n\nbody with detail\n',
            encoding="utf-8")
        out = self.srv.text("promote_inbox_draft", draft_filename=name, target_dir="01-Rules")
        self.assertIn("Promoted", out)
        promoted = self.root / "01-Rules" / name
        self.assertTrue(promoted.is_file(), "promoted file missing at destination")
        self.assertFalse((inbox / name).exists(), "draft not removed from inbox")
        self.assertIn("status: stable", promoted.read_text(encoding="utf-8"))
        refused = self.srv.text("promote_inbox_draft", draft_filename=name, target_dir="../../outside")
        self.assertTrue(refused.startswith("Refused:"), refused[:120])

    def test_09_list_standards_and_code_template(self):
        out = self.srv.text("list_standards")
        self.assertIn("GO-STANDARDS.md", out)
        self.assertIn("CODING-UNIVERSAL.md", out)
        self.assertIn("DISTRIBUTED-LOCKS.md", out)
        tpl = self.srv.text("get_code_template", template_name="worker-pool", lang="go")
        self.assertIn("func workerPool", tpl)
        self.assertIn("Code template:", tpl)

    def test_10_proactive_scan_finds_debt(self):
        project = self.tmp / "proj"
        (project / "src").mkdir(parents=True)
        (project / "src" / "a.py").write_text(
            "def f():\n    pass  # TODO: bound the retry loop\n    # FIXME: leaky abstraction\n", encoding="utf-8")
        (project / "src" / "skipme.xyz").write_text("# TODO: not a source file\n", encoding="utf-8")
        out = self.srv.text("vault_proactive_scan", project_path=str(project), limit=10)
        self.assertIn("TODO", out)
        self.assertIn("FIXME", out)
        self.assertNotIn("skipme.xyz", out)
        self.assertIn("a.py", out)

    def test_11_unknown_tool_is_an_error_not_a_guess(self):
        self.assertTrue(self.srv.is_error("serch_vault", query="x"))
        self.assertTrue(self.srv.is_error("no_such_tool"))

    def test_12_prompts_list_and_get(self):
        names = [p["name"] for p in self.srv.call("prompts/list")["result"]["prompts"]]
        self.assertIn("vault-researcher", names)
        got = self.srv.call("prompts/get", {"name": "vault-researcher"})
        self.assertIn("researcher", got["result"]["messages"][0]["content"]["text"])


class TestRootResolution(unittest.TestCase):
    """The root contract: --root wins, env is next, and there is NO hardcoded fallback."""

    def _run(self, args, env_root=None, cwd=None):
        env = dict(**{k: v for k, v in __import__("os").environ.items()
                      if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH", "DFS_INBOX")})
        if env_root:
            env["WIKI_PATH"] = env_root
        proc = subprocess.run([sys.executable, str(_SERVER), *args], input="",
                              capture_output=True, text=True, encoding="utf-8", env=env, cwd=cwd)
        return proc

    def test_env_var_resolves_the_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = build_root(pathlib.Path(td) / "kb")
            proc = self._run([], env_root=str(root))
            self.assertEqual(proc.returncode, 0)
            self.assertIn("serving", proc.stderr)

    def test_no_root_anywhere_starts_in_drafts_only_mode(self):
        """Tier 3: no knowledge base is a state a user can be in, so the server must survive it."""
        with tempfile.TemporaryDirectory() as td:
            proc = self._run([], cwd=td)
            self.assertEqual(proc.returncode, 0, "the server must still start without a knowledge base")
            self.assertIn("DRAFTS-ONLY", proc.stderr)
            self.assertIn(str(pathlib.Path(td) / ".dfs-inbox"), proc.stderr,
                          "the drop box must be named by absolute path")
            self.assertNotIn("Obsidian", proc.stderr, "must not hint at the author's own path")

    def test_bad_root_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            proc = self._run(["--root", str(pathlib.Path(td) / "nope")])
            self.assertEqual(proc.returncode, 2,
                             "a --root the user named must fail, never silently become a drop box")

    def test_broken_knowledge_json_is_fatal_not_a_drop_box(self):
        """A found root with a bad config is a config error; degrading would hide it."""
        with tempfile.TemporaryDirectory() as td:
            root = build_root(pathlib.Path(td) / "kb")
            (root / "knowledge.json").write_text('{"nonsense": 1}', encoding="utf-8")
            proc = self._run(["--root", str(root)])
            self.assertEqual(proc.returncode, 2)
            self.assertIn("unknown keys", proc.stderr)


class TestDraftsOnlyMode(unittest.TestCase):
    """Tier 3 in use: saving must work, retrieval must refuse out loud, nothing may be silent."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.cwd = self.tmp / "project"
        self.cwd.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def draft(self, srv, title="cp936 codec on Windows CI"):
        return srv.text("save_inbox_draft", title=title,
                        content="Symptom: mojibake on stdout. Root cause: cp936. Fix: reconfigure stdin/stdout.")

    def test_20_saving_works_and_names_the_absolute_path(self):
        srv = Server(cwd=self.cwd)
        try:
            text = self.draft(srv)
            self.assertIn("NO KNOWLEDGE BASE IS CONFIGURED", text)
            drop = self.cwd / ".dfs-inbox"
            drafts = [f for f in drop.glob("*.md") if f.name != "README.md"]
            self.assertEqual(len(drafts), 1, f"expected one draft in {drop}, got {drafts}")
            self.assertIn(str(drafts[0]), text, "the absolute path is what makes it findable again")
            self.assertIn("$DFS_INBOX", text)
        finally:
            srv.close()

    def test_21_the_drop_box_explains_itself(self):
        srv = Server(cwd=self.cwd)
        try:
            self.draft(srv)
            marker = (self.cwd / ".dfs-inbox" / "README.md").read_text(encoding="utf-8")
            self.assertIn("*not* a", marker)
            self.assertIn("WIKI_PATH", marker)
            self.assertIn("vault-inbox-consolidate.py", marker)
        finally:
            srv.close()

    def test_22_retrieval_refuses_instead_of_reporting_nothing(self):
        srv = Server(cwd=self.cwd)
        try:
            for tool, args in (("search_vault", {"query": "concurrency"}),
                               ("omni_search", {"query": "concurrency"}),
                               ("list_standards", {})):
                with self.subTest(tool=tool):
                    resp = srv.call("tools/call", {"name": tool, "arguments": args})
                    self.assertTrue(resp["result"].get("isError"), f"{tool} answered without a root")
                    self.assertIn("no knowledge base is configured", resp["result"]["content"][0]["text"])
        finally:
            srv.close()

    def test_23_dfs_inbox_env_moves_the_drop_box(self):
        stable = self.tmp / "stable-drop"
        srv = Server(cwd=self.cwd, env_extra={"DFS_INBOX": str(stable)})
        try:
            text = self.draft(srv)
            self.assertTrue(list(stable.glob("*.md")), "draft did not land in $DFS_INBOX")
            self.assertIn(str(stable), text)
            self.assertFalse((self.cwd / ".dfs-inbox").exists(), "cwd drop box created anyway")
        finally:
            srv.close()

    def test_24_the_marker_is_never_promoted_as_a_draft(self):
        """A rooted inbox can also contain the marker — promote must refuse it, not file it."""
        with tempfile.TemporaryDirectory() as td:
            root = build_root(pathlib.Path(td) / "kb")
            inbox = root / "99-Inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            (inbox / "README.md").write_text("# DFS draft drop box\n", encoding="utf-8")
            srv = Server(root)
            try:
                text = srv.text("promote_inbox_draft", draft_filename="README.md", target_dir="01-Rules")
                self.assertIn("marker", text)
                self.assertTrue((inbox / "README.md").is_file(), "the marker was filed")
            finally:
                srv.close()

    def test_25_a_draft_survives_into_a_real_knowledge_base(self):
        """The point of the drop box: once a root exists, what was saved there is usable."""
        with tempfile.TemporaryDirectory() as td:
            root = build_root(pathlib.Path(td) / "kb")
            srv = Server(cwd=self.cwd)
            try:
                drop = self.cwd / ".dfs-inbox"
                self.draft(srv)
                drafts = [f for f in drop.glob("*.md") if f.name != "README.md"]
            finally:
                srv.close()
            (root / "99-Inbox").mkdir(parents=True, exist_ok=True)
            shutil.copy(drafts[0], root / "99-Inbox" / drafts[0].name)
            srv2 = Server(root)
            try:
                text = srv2.text("promote_inbox_draft", draft_filename=drafts[0].name,
                                 target_dir="01-Rules")
                self.assertIn("01-Rules", text)
            finally:
                srv2.close()


class TestKnowledgeBaseCache(unittest.TestCase):
    def test_cache_hit_avoids_disk_reread(self):
        with tempfile.TemporaryDirectory() as td:
            root = build_root(pathlib.Path(td) / "kb")
            layout = load_layout(root)
            kb = KnowledgeBase(root, layout)
            self.assertEqual(kb._cache, {})

            note_path = root / "01-Rules" / "CODING-UNIVERSAL.md"
            note1 = kb.get_cached_note(note_path)

            self.assertIn(note_path, kb._cache)
            self.assertEqual(note1["title"], "Universal coding rules")
            self.assertEqual(note1["tags"], ["category/rules", "topic/concurrency"])
            self.assertIn("universal rules", note1["headings"])
            self.assertIn("GO-STANDARDS", note1["neighbours"])
            self.assertEqual(note1["path_s"], "01-rules/coding-universal.md")
            self.assertIn("never swallow an error", note1["body_s"])
            self.assertIn("Universal rules", note1["text"])
            self.assertEqual(note1["mtime_ns"], note_path.stat().st_mtime_ns)

            read_calls = []
            orig_read = kb.read
            kb.read = lambda p: (read_calls.append(p), orig_read(p))[1]

            note2 = kb.get_cached_note(note_path)
            self.assertIs(note1, note2)
            self.assertEqual(len(read_calls), 0, "Cache hit must avoid disk read")

            # Mtime change invalidates cache
            new_mtime = note1["mtime_ns"] + 10_000_000
            os.utime(note_path, ns=(new_mtime, new_mtime))
            note3 = kb.get_cached_note(note_path)
            self.assertEqual(len(read_calls), 1, "Cache miss on mtime change must call kb.read")
            self.assertEqual(note3["mtime_ns"], new_mtime)

    def test_search_vault_uses_cache_and_avoids_disk_reread(self):
        with tempfile.TemporaryDirectory() as td:
            root = build_root(pathlib.Path(td) / "kb")
            layout = load_layout(root)
            kb = KnowledgeBase(root, layout)

            # First search populates cache
            out1 = tool_search_vault(kb, "rules")
            self.assertIn("CODING-UNIVERSAL.md", out1)
            self.assertIn("see-also: GO-STANDARDS", out1)

            # Track read calls on second search
            read_calls = []
            orig_read = kb.read
            kb.read = lambda p: (read_calls.append(p), orig_read(p))[1]

            out2 = tool_search_vault(kb, "rules")
            self.assertEqual(out1, out2)
            self.assertEqual(len(read_calls), 0, "Repeated search_vault must hit cache and do zero disk reads")

            # JSON and compact formats also hit cache without reading disk
            json_out = tool_search_vault(kb, "rules", output_format="json")
            self.assertEqual(len(read_calls), 0, "JSON format search must also use cache")
            parsed = json.loads(json_out)
            self.assertTrue(any("CODING-UNIVERSAL.md" in item["path"] for item in parsed))

            compact_out = tool_search_vault(kb, "rules", output_format="compact")
            self.assertEqual(len(read_calls), 0, "Compact format search must also use cache")
            self.assertIn("CODING-UNIVERSAL.md", compact_out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
