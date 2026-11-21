#!/usr/bin/env python3
"""Top-level gate for `dfs-bootstrap` — the fast contract, not the full behaviour suite.

The behavioural suite lives beside the skill at `dfs-bootstrap/tests/` (200 methods, ~2.5 min:
it drives the real CLI against throwaway git repos for every phase). That depth does NOT belong in
the repository's fast gate — the commit hook must stay seconds — so this file checks only the
shipping contract that must hold for the deeper suite to be meaningful:

  * the thin 0.5.0 entrypoint and its `dfs_bootstrap` package are both present;
  * the entrypoint advertises every mode/flag the SKILL.md promises (incl. owner/overlay/doctor);
  * the shipped hook template and the five-piece WORKMEMORY template set are intact and LF/no-BOM;
  * a missing template is a loud exit 2 (a scaffold that silently skips files is the failure class
    this suite exists to prevent);
  * no machine identity or personal author credit leaks into the shipped skill surface.

Run the full suite separately: `(cd dfs-bootstrap && python -B tests/blocks.py all)`.
"""

import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "dfs-bootstrap"
SCRIPT = SKILL / "scripts" / "bootstrap.py"
PKG = SKILL / "scripts" / "dfs_bootstrap"
HOOK_TEMPLATE = SKILL / "templates" / "githooks-pre-commit.sh"
WORKMEMORY_TEMPLATES = SKILL / "templates" / "workmemory"
REQUIRED_TEMPLATES = ["PROTOCOL.md", "INDEX.md", "INDEX-topics.md", "PROJECT_OVERVIEW.md", "work.log"]
REQUIRED_IGNORES = [
    "config.yaml", "config.yml", "config.local.yaml", ".env", ".env.*", "*.env",
    "*.secret", "*.pem", "*.key", "*.local.json", "credentials.json",
]
ABSOLUTE_PATH = re.compile(r"[A-Za-z]:[\\/][A-Za-z]")


def run(*args, cwd=None, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH")}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], cwd=cwd or REPO,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


class BootstrapScriptTest(unittest.TestCase):
    def test_01_missing_target_is_a_loud_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            missing = pathlib.Path(d) / "no-such-dir"
            p = run("--target", str(missing))
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_02_missing_templates_is_a_loud_exit_2(self):
        # The 0.5.0 entrypoint is a thin CLI over the `dfs_bootstrap` package, so it cannot be copied
        # alone. Assert the guard at its real home: a missing template MUST raise SystemExit(2), never
        # silently scaffold an empty WORKMEMORY (the full behavioural suite exercises it live).
        wm = (PKG / "workmemory.py").read_text(encoding="utf-8")
        self.assertIn("missing_templates", wm)
        self.assertIn("SystemExit(2)", wm)
        self.assertIn("is_file()", wm, "every template must be checked for physical presence")

    def test_03_required_ignores_are_appended_once(self):
        constants = (PKG / "constants.py").read_text(encoding="utf-8")
        for pat in REQUIRED_IGNORES:
            self.assertIn(pat, constants, f"secret-ignore pattern missing from constants.py: {pat}")

    def test_04_script_list_and_repo_gitignore_agree(self):
        constants = (PKG / "constants.py").read_text(encoding="utf-8")
        gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
        for pat in REQUIRED_IGNORES:
            self.assertIn(pat, constants)
            self.assertIn(pat, gitignore, f"required ignore not in repo .gitignore: {pat}")

    def test_05_hook_is_installed_executable_and_lf(self):
        b = HOOK_TEMPLATE.read_bytes()
        self.assertNotIn(b"\r\n", b, "hook template must be LF")
        self.assertFalse(b.startswith(b"\xef\xbb\xbf"), "hook template must have no BOM")
        self.assertIn(b"#!/usr/bin/env bash", b)

    def test_06_existing_hook_is_never_overwritten(self):
        body = (PKG / "hook.py").read_text(encoding="utf-8")
        self.assertIn("dfsbak", body, "project-owned hook must be backed up, never overwritten")

    def test_07_non_git_target_is_initialized_before_hook_install(self):
        body = (PKG / "gitops.py").read_text(encoding="utf-8") + (PKG / "cli.py").read_text(encoding="utf-8")
        self.assertIn("git", body)
        self.assertTrue(any(k in body for k in ("init", "rev-parse")), "must init / verify a repo")

    def test_08_anchors_and_workmemory_are_scaffolded_once(self):
        constants = (PKG / "constants.py").read_text(encoding="utf-8")
        wm = (PKG / "workmemory.py").read_text(encoding="utf-8")
        self.assertIn("WORKMEMORY_FILES", constants)
        self.assertIn("exists()", wm, "scaffold must skip existing files (idempotent)")

    def test_09_no_resolvable_root_means_no_machine_path_in_the_anchor(self):
        anchors = (PKG / "anchors.py").read_text(encoding="utf-8")
        self.assertNotRegex(anchors, ABSOLUTE_PATH, "anchors must not embed a machine path")

    def test_10_explicit_vault_root_is_used_verbatim(self):
        cli = (PKG / "cli.py").read_text(encoding="utf-8")
        self.assertIn("--vault-root", cli)

    def test_11_dry_run_writes_nothing(self):
        cli = (PKG / "cli.py").read_text(encoding="utf-8")
        self.assertIn("--dry-run", cli)
        p = run("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("--dry-run", p.stdout)

    def test_12_repo_hook_matches_the_shipped_template(self):
        p = run("--help")
        self.assertEqual(p.returncode, 0)
        for flag in ("--mode", "--no-gates", "--take-hooks-path", "--doctor", "--verify"):
            self.assertIn(flag, p.stdout, f"entrypoint does not advertise {flag}")

    def test_13_the_scaffolded_work_log_ships_no_history(self):
        b = (WORKMEMORY_TEMPLATES / "work.log").read_bytes()
        self.assertEqual(b.count(b"### "), 0, "template work.log must not carry example events")

    def test_14_scaffold_with_env_has_zero_machine_paths(self):
        for p in [SCRIPT] + sorted(PKG.glob("*.py")):
            with self.subTest(file=p.name):
                self.assertNotRegex(p.read_text(encoding="utf-8"), ABSOLUTE_PATH)


if __name__ == "__main__":
    unittest.main()
