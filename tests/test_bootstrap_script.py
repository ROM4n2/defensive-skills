#!/usr/bin/env python3
"""`dfs-bootstrap/scripts/bootstrap.py` — the cross-platform Phase 3.5 port.

Every test drives the real CLI through a subprocess against a fresh temp target: this script's whole
job is writing files into someone else's repo, so the only meaningful assertion is what lands on disk.

The two assertions that matter most:
  * with no knowledge base root resolvable, the GENERATED ANCHOR must not contain any absolute path —
    that is the leak this repo just spent a commit removing from its own tree (Rule 10's reason).
  * the required-ignore list in the script and this repo's own `.gitignore` must agree, or the
    "single source of truth" claim is just prose.
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "dfs-bootstrap" / "scripts" / "bootstrap.py"
HOOK_TEMPLATE = REPO / "dfs-bootstrap" / "templates" / "githooks-pre-commit.sh"
REQUIRED_IGNORES = [
    "config.yaml", "config.yml", "config.local.yaml", ".env", ".env.*", "*.env",
    "*.secret", "*.pem", "*.key", "*.local.json", "credentials.json",
]
ABSOLUTE_PATH = re.compile(r"[A-Za-z]:[\\/][A-Za-z]")


def run_bootstrap(target: pathlib.Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH")}
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--target", str(target), *args],
        capture_output=True, text=True, env=env,
    )


class BootstrapScriptTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("git"), "git is required to test the hook installation")
        self._tmp = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def as_git_repo(self):
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)
        return self.target

    # --- preconditions -------------------------------------------------
    def test_01_missing_target_is_a_loud_exit_2(self):
        proc = run_bootstrap(self.target / "does-not-exist")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("not a directory", proc.stderr)

    def test_02_missing_templates_is_a_loud_exit_2(self):
        """A scaffold that silently skips missing templates is the failure class this suite bans."""
        with tempfile.TemporaryDirectory() as tmp:
            orphan = pathlib.Path(tmp) / "scripts"
            orphan.mkdir(parents=True)
            shutil.copy2(SCRIPT, orphan / "bootstrap.py")  # no sibling templates/
            proc = subprocess.run([sys.executable, str(orphan / "bootstrap.py"), "--target", str(self.target)],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("skill templates not found", proc.stderr)

    # --- phase 1: .gitignore ------------------------------------------
    def test_03_required_ignores_are_appended_once(self):
        first = run_bootstrap(self.target)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        content = (self.target / ".gitignore").read_text(encoding="utf-8")
        for pattern in REQUIRED_IGNORES:
            self.assertIn(pattern, content.splitlines(), f"{pattern} missing from the fresh .gitignore")
        second = run_bootstrap(self.target)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        again = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(content, again, "second run rewrote .gitignore — not idempotent")
        self.assertIn("already excludes", second.stdout)

    def test_04_script_list_and_repo_gitignore_agree(self):
        """The script claims to be the single source of truth; this is where that is checked."""
        source = SCRIPT.read_text(encoding="utf-8")
        match = re.search(r"REQUIRED_IGNORES = \[(.*?)\]", source, re.S)
        if match is None:
            self.fail("REQUIRED_IGNORES not found in bootstrap.py")
        declared = re.findall(r'"([^"]+)"', match.group(1))
        self.assertEqual(declared, REQUIRED_IGNORES, "bootstrap.py's list drifted from this test's copy")
        repo_ignores = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
        missing = [p for p in declared if p not in repo_ignores]
        self.assertEqual(missing, [], f"this repo's own .gitignore is missing {missing}")

    # --- phase 2: hook -------------------------------------------------
    def test_05_hook_is_installed_executable_and_lf(self):
        self.as_git_repo()
        proc = run_bootstrap(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        hook = self.target / ".githooks" / "pre-commit"
        self.assertTrue(hook.is_file(), "hook not installed")
        self.assertEqual(hook.read_bytes(), HOOK_TEMPLATE.read_bytes(),
                         "installed hook differs from the shipped template")
        self.assertNotIn(b"\r\n", hook.read_bytes(), "CRLF would break the shebang on Linux/macOS")
        self.assertNotEqual(hook.read_bytes()[:3], b"\xef\xbb\xbf", "BOM breaks the shebang")
        if os.name != "nt":
            self.assertTrue(hook.stat().st_mode & 0o111, "hook is not executable")
        cfg = subprocess.run(["git", "-C", str(self.target), "config", "core.hooksPath"],
                             capture_output=True, text=True)
        self.assertEqual(cfg.stdout.strip(), ".githooks")

    def test_06_existing_hook_is_never_overwritten(self):
        self.as_git_repo()
        hook = self.target / ".githooks" / "pre-commit"
        hook.parent.mkdir()
        hook.write_text("#!/usr/bin/env bash\necho project gatekeeper\n", encoding="utf-8", newline="\n")
        proc = run_bootstrap(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("preserved", proc.stdout)
        self.assertIn("project gatekeeper", hook.read_text(encoding="utf-8"))

    def test_07_non_git_target_skips_the_hook(self):
        proc = run_bootstrap(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("not a git repository", proc.stdout)
        self.assertFalse((self.target / ".githooks").exists())

    # --- phase 3/3.5/3.6: anchors + WORKMEMORY -------------------------
    def test_08_anchors_and_workmemory_are_scaffolded_once(self):
        first = run_bootstrap(self.target)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        for name in ("CLAUDE.md", ".agent-rules.md", ".cursorrules", "AGENTS.md"):
            self.assertTrue((self.target / name).is_file(), f"{name} not created")
        files = sorted(p.name for p in (self.target / "WORKMEMORY").iterdir())
        self.assertEqual(files, ["INDEX-topics.md", "INDEX.md", "PROJECT_OVERVIEW.md", "PROTOCOL.md", "work.log"])
        overview = (self.target / "WORKMEMORY" / "PROJECT_OVERVIEW.md").read_text(encoding="utf-8")
        self.assertIn(self.target.name, overview, "{{PROJECT_NAME}} was not substituted")
        self.assertNotIn("{{", overview, "unsubstituted placeholder left in PROJECT_OVERVIEW.md")

        edit = self.target / "WORKMEMORY" / "work.log"
        edit.write_text("# hand-edited by the agent\n", encoding="utf-8", newline="\n")
        run_bootstrap(self.target)
        self.assertEqual(edit.read_text(encoding="utf-8"), "# hand-edited by the agent\n",
                         "second run clobbered an existing WORKMEMORY file")
        for name in ("CLAUDE.md", ".agent-rules.md", ".cursorrules"):
            text = (self.target / name).read_text(encoding="utf-8")
            self.assertEqual(text.count("工程规范与避坑检索"), 1, f"rules anchor duplicated in {name}")
            self.assertEqual(text.count("共享工作记忆"), 1, f"WORKMEMORY anchor duplicated in {name}")

    def test_09_no_resolvable_root_means_no_machine_path_in_the_anchor(self):
        """The generated anchor must degrade to the documented contract, never to one machine's layout."""
        proc = run_bootstrap(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no knowledge base root resolved", proc.stdout)
        for name in ("CLAUDE.md", ".agent-rules.md", ".cursorrules", "AGENTS.md"):
            text = (self.target / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, ABSOLUTE_PATH, f"{name} leaks an absolute path")
            self.assertIn("$WIKI_PATH", text)
        for pattern in ("{{VAULT_ROOT}}", "{{PROJECT_NAME}}", "{{TIMESTAMP}}"):
            self.assertNotIn(pattern, "".join(
                p.read_text(encoding="utf-8") for p in (self.target / "WORKMEMORY").iterdir()))

    def test_10_explicit_vault_root_is_used_verbatim(self):
        proc = run_bootstrap(self.target, "--vault-root", "/kb/example")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = (self.target / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("`/kb/example/AGENTS.md`", text)
        self.assertNotIn("\\", text.split("检索避坑规范")[0].split("核心规范源")[1],
                         "path separator is not normalized to forward slashes")
        self.assertNotIn("<your knowledge base root>", text)

    def test_11_dry_run_writes_nothing(self):
        before = set(p.name for p in self.target.iterdir())
        proc = run_bootstrap(self.target, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(set(p.name for p in self.target.iterdir()), before, "--dry-run created files")
        self.assertIn("nothing was written", proc.stdout)

    def test_12_repo_hook_matches_the_shipped_template(self):
        """This repo bootstrapped itself with this tool — if the two drift, one of them is wrong."""
        self.assertEqual((REPO / ".githooks" / "pre-commit").read_bytes(), HOOK_TEMPLATE.read_bytes())

    def test_13_the_scaffolded_work_log_ships_no_history(self):
        """work.log is append-only history, so its template may contribute comments only.

        The shipped template used to carry a ready-made event signed `claude-sonnet-4-6__claude-code`
        claiming "bootstrap complete" — so every bootstrapped repo opened with a stranger's history,
        one that never happened. Structure ships (the other three templates are skeletons); events
        and claims do not. A comment is inert, so comments are the only content allowed here — and a
        `###` line is an event declaration however it is spaced, never inert. The trailing newline is
        part of the contract too: without it the next `cat >>` lands on the last comment line instead
        of starting a new event.
        """
        proc = run_bootstrap(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        raw = (self.target / "WORKMEMORY" / "work.log").read_bytes()
        self.assertTrue(raw.endswith(b"\n"), "work.log does not end with a newline — appends corrupt it")
        live = [line for line in raw.decode("utf-8").splitlines()
                if line.strip() and (line.startswith("###") or not line.lstrip().startswith("#"))]
        self.assertEqual(live, [], f"the scaffolded work.log ships real content, not just structure: {live}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
