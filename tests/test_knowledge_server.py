#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end check for mcp/knowledge_server.py.

Drives the real server over stdio JSON-RPC against a throwaway knowledge root built in a temp
dir — no mocking of the protocol layer, because the protocol layer is what breaks silently.

Also asserts the server's tool list equals the conformance canon (`KNOWN_MCP_TOOLS`), so the
server and the skills' declared `mcp_tools` contracts cannot drift apart unnoticed.
"""

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SERVER = _REPO_ROOT / "mcp" / "knowledge_server.py"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
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

    def __init__(self, root: pathlib.Path):
        self.proc = subprocess.Popen(
            [sys.executable, str(_SERVER), "--root", str(root)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8",
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
                      if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH")})
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

    def test_no_root_anywhere_fails_loudly(self):
        with tempfile.TemporaryDirectory() as td:
            proc = self._run([], cwd=td)
            self.assertEqual(proc.returncode, 2, "missing root must exit non-zero, not pick a default")
            self.assertIn("No knowledge root found", proc.stderr)
            self.assertNotIn("Obsidian", proc.stderr, "must not hint at the author's own path")

    def test_bad_root_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            proc = self._run(["--root", str(pathlib.Path(td) / "nope")])
            self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
