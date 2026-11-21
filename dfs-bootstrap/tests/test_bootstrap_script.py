#!/usr/bin/env python3
"""Behavioural tests for the patched dfs-bootstrap.

Every assertion runs the real script against a real throwaway git repo and reads real files back.
Nothing is mocked, because the defects this suite guards against (stale hook, duplicated rules,
absolute-path anchors, CRLF in LF-pinned files) are all invisible to a mock.

Run: python -B tests/test_bootstrap_script.py
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
BOOTSTRAP = SKILL_DIR / "scripts" / "bootstrap.py"
HOOK_TEMPLATE = SKILL_DIR / "templates" / "githooks-pre-commit.sh"
HYGIENE_TEMPLATE = SKILL_DIR / "templates" / "repo" / "check_repo_hygiene.py"

POINTER_BODY = (
    "@AGENTS.md\n"
    "<!-- Canonical rules live in AGENTS.md; read ./AGENTS.md directly if your runtime does not "
    "expand @imports. -->\n"
)


def run(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(BOOTSTRAP), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


class BootstrapHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.repo = self.root / "demo-repo"
        self.repo.mkdir()
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.vault / "AGENTS.md").write_text("# vault rules\n", encoding="utf-8")
        git(["init", "-q"], self.repo)
        git(["config", "user.email", "t@example.invalid"], self.repo)
        git(["config", "user.name", "T"], self.repo)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def bootstrap(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return run(["--target", str(self.repo), "--vault-root", str(self.vault), *extra], self.root)


class TestFilesWritten(BootstrapHarness):
    def test_writes_gitignore_gitattributes_hook_hygiene_and_workmemory(self) -> None:
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        gi = (self.repo / ".gitignore").read_text(encoding="utf-8")
        for pattern in (".env", "*.pem", "credentials.json", ".worktrees/", ".vault-exec-ledger.json"):
            self.assertIn(pattern, gi)

        ga = (self.repo / ".gitattributes").read_text(encoding="utf-8")
        for pin in (".githooks/** text eol=lf", "WORKMEMORY/** text eol=lf", "*.sh text eol=lf"):
            self.assertIn(pin, ga)

        hook = self.repo / ".githooks" / "pre-commit"
        self.assertTrue(hook.is_file())
        raw = hook.read_bytes()
        self.assertNotIn(b"\r\n", raw, "hook must be installed with LF endings")
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "hook must not carry a BOM")
        self.assertIn(b"dfs-bootstrap-hook-version:", raw)
        self.assertIn(b"check_repo_hygiene.py", raw)
        self.assertIn(b".githooks/*", raw, "the hook must scan its own directory for CRLF")

        self.assertTrue((self.repo / "scripts" / "check_repo_hygiene.py").is_file())
        for name in ("INDEX.md", "INDEX-topics.md", "PROTOCOL.md", "PROJECT_OVERVIEW.md", "work.log"):
            self.assertTrue((self.repo / "WORKMEMORY" / name).is_file(), name)

        hooks_path = git(["config", "core.hooksPath"], self.repo).stdout.strip()
        self.assertEqual(hooks_path, ".githooks")


class TestRulesSingleSource(BootstrapHarness):
    def test_agents_md_carries_rules_and_claude_md_is_only_a_pointer(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        agents = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("工程规范与避坑检索", agents)
        self.assertIn("临时状态和问题写入 WORKMEMORY", agents)
        self.assertIn("问题、决策、踩坑和交接优先写入 WORKMEMORY", agents)
        self.assertEqual((self.repo / "CLAUDE.md").read_text(encoding="utf-8"), POINTER_BODY)

    def test_routing_row_titled_like_anchor_is_not_a_false_positive(self) -> None:
        """DeLector's routing table row '工程规范与避坑检索（3 行锚点）' is not the DFS anchor."""
        agents = self.repo / "AGENTS.md"
        agents.write_text(
            "# Project entry\n\n| 需要什么 | 去哪 |\n| --- | --- |\n"
            "| 工程规范与避坑检索（3 行锚点） | `CLAUDE.md` / `.cursorrules` |\n",
            encoding="utf-8", newline="\n",
        )
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("injected the rules anchor", proc.stdout)
        self.assertIn("search_vault", agents.read_text(encoding="utf-8"))

    def test_real_anchor_is_recognized_and_not_duplicated(self) -> None:
        agents = self.repo / "AGENTS.md"
        agents.write_text(
            "# Project Guidelines\n\n## [NOTE] 工程规范与避坑检索\n\n"
            "- 发现新踩坑自动沉淀：调用 `save_inbox_draft`\n",
            encoding="utf-8", newline="\n",
        )
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("already carries the rules anchor", proc.stdout)
        self.assertEqual(agents.read_text(encoding="utf-8").count("save_inbox_draft"), 1)

    def test_existing_anchors_receive_memory_boundary_without_duplication(self) -> None:
        agents = self.repo / "AGENTS.md"
        agents.write_text(
            "# Project Guidelines\n\n## [NOTE] 工程规范与避坑检索\n\n"
            "- 发现新踩坑自动沉淀：调用 `save_inbox_draft`\n\n"
            "## 共享工作记忆 (WORKMEMORY)\n\n"
            "- 进入会话先读 WORKMEMORY/INDEX.md\n",
            encoding="utf-8", newline="\n",
        )
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        text = agents.read_text(encoding="utf-8")
        self.assertEqual(text.count("## 共享工作记忆 (WORKMEMORY)"), 1)
        self.assertEqual(text.count("问题、决策、踩坑和交接优先写入 WORKMEMORY"), 1)

    def test_legacy_alias_files_are_not_generated_by_default(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        for name in (".agent-rules.md", ".cursorrules"):
            self.assertFalse((self.repo / name).exists(), f"{name} must not be generated")

    def test_existing_legacy_alias_is_reported_not_overwritten(self) -> None:
        alias = self.repo / ".cursorrules"
        alias.write_text("# hand-written cursor rules\n", encoding="utf-8")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("legacy alias .cursorrules", proc.stdout)
        self.assertEqual(alias.read_text(encoding="utf-8"), "# hand-written cursor rules\n")

    def test_legacy_aliases_flag_still_writes_the_anchor(self) -> None:
        self.assertEqual(self.bootstrap("--legacy-aliases").returncode, 0)
        for name in (".agent-rules.md", ".cursorrules"):
            self.assertIn("工程规范与避坑检索", (self.repo / name).read_text(encoding="utf-8"))


class TestVaultRootIsValidated(BootstrapHarness):
    """A wrong knowledge-base root must stop the run, not warn and scaffold anyway."""

    def _empty_vault(self) -> pathlib.Path:
        empty = self.root / "not-a-vault"
        empty.mkdir()
        return empty

    def test_missing_agents_md_fails_closed_and_writes_nothing(self) -> None:
        proc = self.bootstrap("--vault-root", str(self._empty_vault()))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("[ERR]", proc.stderr)
        self.assertIn("has no AGENTS.md", proc.stderr)
        self.assertFalse((self.repo / "AGENTS.md").exists(), "refusal must write nothing")
        self.assertFalse((self.repo / ".githooks").exists())
        self.assertFalse((self.repo / "WORKMEMORY").exists())

    def test_dry_run_refuses_too(self) -> None:
        """Fail-closed covers dry-run as well: a plan built on a wrong root is not a plan."""
        proc = self.bootstrap("--vault-root", str(self._empty_vault()), "--dry-run")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("has no AGENTS.md", proc.stderr)

    def test_allow_flag_overrides_the_refusal(self) -> None:
        proc = self.bootstrap("--vault-root", str(self._empty_vault()),
                              "--allow-missing-vault-agents")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[WARN]", proc.stdout)
        self.assertTrue((self.repo / "WORKMEMORY" / "INDEX.md").is_file())


class TestAnchorPortability(BootstrapHarness):
    def test_anchor_names_a_tool_and_carries_no_path(self) -> None:
        """Resolvable, not decorative: the anchor names tools and carries no external path.

        An unexpanded ``$WIKI_PATH/AGENTS.md`` is never reached — no harness expands a shell
        variable inside markdown, and the search tool resolves the knowledge base itself.
        """
        self.assertEqual(self.bootstrap().returncode, 0)
        agents = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## [NOTE] 工程规范与避坑检索", agents)
        # Scope to the rules-anchor block: the WORKMEMORY anchor below it also names `search_vault`,
        # so a file-wide assertIn would stay green even if THIS anchor lost its only tool pointer —
        # which is exactly the mutation `anchor-loses-its-tool-pointer` injects.
        block = agents.split("## [NOTE] 工程规范与避坑检索", 1)[1].split("\n## ", 1)[0]
        self.assertIn("search_vault", block)
        self.assertIn("save_inbox_draft", block)
        self.assertNotIn("$WIKI_PATH", agents, "an unexpanded variable is not a pointer")
        self.assertNotIn(str(self.vault).replace("\\", "/"), agents)

    def test_anchor_does_not_hardcode_one_machines_vault_directories(self) -> None:
        """The anchor is shipped to every repo: it must not name a private vault's directories.

        A literal sink like ``$WIKI_PATH/99-Inbox/`` describes MY knowledge base, not the target
        repo's; on a public repo it either leaks a private layout or points at a directory that
        does not exist. The sink stays a tool call, the directory stays the vault's own business.
        """
        self.assertEqual(self.bootstrap().returncode, 0)
        agents = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        for private_dir in ("99-Inbox", "08-Projects", "01-Rules", "01-ADR"):
            self.assertNotIn(private_dir, agents, f"anchor hardcodes the private dir {private_dir}")

    def test_scaffolded_repo_passes_its_own_hygiene_gate(self) -> None:
        """The anchor bootstrap writes must not trip the gate bootstrap installs."""
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["add", "-A"], self.repo)
        proc = subprocess.run(
            [sys.executable, "-B", "scripts/check_repo_hygiene.py", "--staged"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestIdempotency(BootstrapHarness):
    def test_second_run_changes_nothing(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        snapshot = {
            p.relative_to(self.repo).as_posix(): p.read_bytes()
            for p in sorted(self.repo.rglob("*"))
            if p.is_file() and ".git/" not in p.as_posix()
        }
        self.assertEqual(self.bootstrap().returncode, 0)
        after = {
            p.relative_to(self.repo).as_posix(): p.read_bytes()
            for p in sorted(self.repo.rglob("*"))
            if p.is_file() and ".git/" not in p.as_posix()
        }
        self.assertEqual(set(snapshot), set(after))
        for name, body in snapshot.items():
            self.assertEqual(body, after[name], f"{name} changed on the second run")

    def test_workmemory_history_is_never_rescaffolded(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        log = self.repo / "WORKMEMORY" / "work.log"
        log.write_text(
            "# demo work.log\n\n### 2026-01-01 00:00 | model__harness | NOTE\nreal history\n",
            encoding="utf-8",
        )
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertIn("real history", log.read_text(encoding="utf-8"))


class TestLocalGateInstall(BootstrapHarness):
    """Bootstrap must install the private fingerprint gate at project init, not by hand."""

    @property
    def gate(self) -> pathlib.Path:
        return self.repo / ".git" / "local-gates" / "fingerprint-gate.sh"

    @property
    def pattern_file(self) -> pathlib.Path:
        return self.gate.parent / "fingerprints.txt"

    @staticmethod
    def sha256(path: pathlib.Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_bootstrap_installs_the_private_gate(self) -> None:
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(self.gate.is_file(), "bootstrap must install the local gate into .git/")
        self.assertIn(b"dfs-bootstrap-local-gate-version:", self.gate.read_bytes())
        self.assertNotIn(b"\r\n", self.gate.read_bytes(), "gate must stay LF like the hook")

    def test_second_bootstrap_is_byte_identical(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertTrue(self.gate.is_file())
        before = self.sha256(self.gate)
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(self.sha256(self.gate), before)

    def test_user_patterns_are_never_overwritten(self) -> None:
        self.pattern_file.parent.mkdir(parents=True, exist_ok=True)
        mine = "# my machine only\n/home/example/private-vault\n"
        self.pattern_file.write_text(mine, encoding="utf-8", newline="\n")
        allow = self.pattern_file.with_name("fingerprint-allow.txt")
        allow.write_text("<user>|$HOME\n", encoding="utf-8", newline="\n")

        for _ in range(2):
            self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(self.pattern_file.read_text(encoding="utf-8"), mine)
        self.assertEqual(allow.read_text(encoding="utf-8"), "<user>|$HOME\n")

    def test_gate_never_enters_the_tracked_tree(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(git(["add", "-A"], self.repo).returncode, 0)
        tracked = git(["ls-files"], self.repo).stdout.splitlines()
        self.assertFalse([p for p in tracked if p.startswith("local-gates/")], tracked)
        self.assertFalse([p for p in tracked if p.endswith("fingerprint-gate.sh")], tracked)

    def test_no_gates_skips_the_local_gate(self) -> None:
        proc = self.bootstrap("--no-gates")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(self.gate.exists(), "--no-gates must also skip the local gate")

    def test_dry_run_reports_without_writing_the_local_gate(self) -> None:
        proc = self.bootstrap("--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(self.gate.exists(), "--dry-run must not install the local gate")
        self.assertIn("would write .git/local-gates/fingerprint-gate.sh", proc.stdout)


class TestHookUpgrade(BootstrapHarness):
    def test_project_owned_hook_without_marker_is_preserved(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        custom = "#!/usr/bin/env bash\n# hand-written gatekeeper\nexit 0\n"
        hook.write_text(custom, encoding="utf-8", newline="\n")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("project-owned", proc.stdout)
        self.assertEqual(hook.read_text(encoding="utf-8"), custom)

    def test_project_owned_hook_keeps_custom_hooks_path(self) -> None:
        """DeLector chains .git/local-hooks; resetting it would silently disable the local gate."""
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
        git(["config", "core.hooksPath", ".git/local-hooks"], self.repo)
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("core.hooksPath stays .git/local-hooks", proc.stdout)
        self.assertEqual(
            git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".git/local-hooks"
        )

    def test_written_hook_sets_hooks_path(self) -> None:
        """The guard above must not disable the normal install path."""
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(git(["config", "core.hooksPath"], self.repo).stdout.strip(), ".githooks")

    def test_older_dfs_hook_is_upgraded_with_backup(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        stale = "#!/usr/bin/env bash\n# dfs-bootstrap-hook-version: 1\nexit 0\n"
        hook.write_text(stale, encoding="utf-8", newline="\n")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("upgraded hook v1", proc.stdout)
        self.assertIn(b"check_repo_hygiene.py", hook.read_bytes())
        backup = hook.with_suffix(".dfsbak")
        self.assertTrue(backup.is_file())
        self.assertEqual(backup.read_text(encoding="utf-8"), stale)

    def test_force_hook_overwrites_a_project_owned_hook(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
        proc = self.bootstrap("--force-hook")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("force-installed", proc.stdout)
        self.assertIn(b"check_repo_hygiene.py", hook.read_bytes())


class TestHookEnforcesLineEndings(BootstrapHarness):
    def _run_hook(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", ".githooks/pre-commit"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_hook_rejects_crlf_in_the_hook_directory(self) -> None:
        """A CRLF file under `.githooks/` cannot be executed by bash; the hook must refuse it.

        The probe targets a *sibling* file, not the running hook: overwriting the executing script
        makes bash fail with a parse error (exit 2) instead of exercising the gate.
        """
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / ".githooks" / "pre-push").write_bytes(b"#!/usr/bin/env bash\r\nexit 0\r\n")
        git(["add", "-A"], self.repo)
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[EOL]", proc.stdout + proc.stderr)
        self.assertIn(".githooks/pre-push", proc.stdout + proc.stderr)

    def test_git_normalizes_pinned_files_so_a_blob_crlf_gate_would_be_dead_code(self) -> None:
        """Pins the *reason* the naive gate was removed: the index blob is LF by construction."""
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "deploy.sh").write_bytes(b"#!/usr/bin/env bash\r\necho hi\r\n")
        git(["add", "-A"], self.repo)
        blob = subprocess.run(
            ["git", "show", ":deploy.sh"], cwd=str(self.repo), capture_output=True
        ).stdout
        self.assertNotIn(b"\r\n", blob, "git must normalize a text eol=lf file on add")

    def test_hook_passes_on_a_clean_lf_tree(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["add", "-A"], self.repo)
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_hook_invokes_the_hygiene_gate(self) -> None:
        """End-to-end: the gate must be reached *through the hook*, not only when invoked directly.

        Without this the wiring can be deleted while every direct-invocation test stays green —
        which is exactly what the mutation check caught.
        """
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / "src").mkdir(exist_ok=True)
        (self.repo / "src" / "demo.py").write_text(
            'p = "D:/Code/other-repo/file.py"\n', encoding="utf-8", newline="\n"  # git:allow-abs-path
        )
        git(["add", "-A"], self.repo)
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[ABS_PATH]", proc.stderr, "the hook must reach the hygiene gate")

    def test_hook_still_blocks_a_synthetic_secret(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        probe = self.repo / "probe.py"
        probe.write_text("k = " + "sk-" + "0" * 32 + "\n", encoding="utf-8")
        git(["add", "-A"], self.repo)
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[LINE]", proc.stdout + proc.stderr)


class TestGitattributesPinGate(BootstrapHarness):
    def _gate(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", "scripts/check_repo_hygiene.py", "--staged"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_missing_pin_is_reported(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        attrs = self.repo / ".gitattributes"
        kept = [
            line
            for line in attrs.read_text(encoding="utf-8").splitlines()
            if not line.startswith(".githooks/**")
        ]
        attrs.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
        git(["add", "-A"], self.repo)
        proc = self._gate()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[EOL_PIN]", proc.stderr)
        self.assertIn(".githooks/** text eol=lf", proc.stderr)

    def test_deleted_gitattributes_is_reported(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        (self.repo / ".gitattributes").unlink()
        git(["add", "-A"], self.repo)
        proc = self._gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[EOL_PIN]", proc.stderr)

    def test_present_pins_pass(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        git(["add", "-A"], self.repo)
        proc = self._gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestHygieneGate(BootstrapHarness):
    def _stage(self, rel: str, body: bytes) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        git(["add", "-A"], self.repo)

    def _gate(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", "scripts/check_repo_hygiene.py", "--staged"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_rejects_host_absolute_path(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self._stage("src/demo.py", b'p = "D:/Code/other-repo/file.py"\n')  # git:allow-abs-path
        proc = self._gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[ABS_PATH]", proc.stderr)

    def test_rejects_conflict_marker(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self._stage("src/conflict.py", b"a = 1\n<<<<<<< HEAD\nb = 2\n=======\n")
        proc = self._gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[CONFLICT]", proc.stderr)

    def test_rejects_bloated_agents_md(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        bloated = "\n".join(f"- rule {i}" for i in range(85)).encode()
        self._stage("AGENTS.md", bloated + b"\n")
        proc = self._gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[BUDGET]", proc.stderr)

    def test_rejects_oversized_module(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        body = "\n".join(f"x_{i} = {i}" for i in range(1001)).encode() + b"\n"
        self._stage("src/monolith.py", body)
        proc = self._gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[BLOAT]", proc.stderr)

    def test_malformed_config_exits_two_not_one(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self._stage("data/repo_hygiene.json", b"{not json")
        proc = self._gate()
        self.assertEqual(proc.returncode, 2, "an unusable gate must not report as a clean pass or a finding")

    def test_large_file_override_is_honoured(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        self._stage(
            "data/repo_hygiene.json",
            b'{"large_file_patterns": {"data/raw/**": 5242880}}',
        )
        self._stage("data/raw/blob.csv", b"x" * (600 * 1024))
        proc = self._gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestEmitCi(BootstrapHarness):
    """--emit-ci is read-only: no vault root, no target mutation, both snippets present."""

    def test_emit_ci_works_without_vault_root_or_existing_target(self) -> None:
        proc = run(["--emit-ci", "github", "--target", str(self.repo)], self.repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # Pin each template's own unique line — a loose substring check would stay green when
        # one template is mutated because the other still contains "--ratchet-guard".
        self.assertIn("run: python3 scripts/check_repo_structure.py --ratchet-guard", proc.stdout)
        self.assertIn("check_repo_structure.py --all", proc.stdout)
        self.assertIn(
            'self.assertIn("--ratchet-guard", text, "the ratchet guard must be wired next to the audit")',
            proc.stdout,
        )
        self.assertIn("def test_ratchet_guard_step_is_wired", proc.stdout)

    def test_emit_ci_does_not_mutate_target(self) -> None:
        before = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        proc = run(["--emit-ci", "github", "--target", str(self.repo)], self.repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        after = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        self.assertEqual(before, after, "--emit-ci must not write into the target repo")

    def test_emit_ci_rejects_unsupported_provider(self) -> None:
        proc = run(["--emit-ci", "gitlab", "--target", str(self.repo)], self.repo)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)


class TestDoctorAndChecks(BootstrapHarness):
    """doctor reports gaps read-only; --emit-checks gives project-owned hooks the gates."""

    def test_doctor_reports_missing_hook_as_gap(self) -> None:
        proc = run(["--doctor", "--target", str(self.repo)], self.repo)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("pre-commit missing", proc.stdout)

    def test_doctor_detects_project_hook_gaps(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/usr/bin/env bash\n# 提交前扫描暂存内容里的密钥\nexit 0\n",
                        encoding="utf-8", newline="\n")
        proc = run(["--doctor", "--target", str(self.repo)], self.repo)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("no DFS version marker", proc.stdout)
        for missing in ("EOL check", "upstream chain", "hygiene gate", "structure gate"):
            self.assertIn(f"[GAP] {missing}", proc.stdout,
                          "doctor must mark the capability GAP, not merely print its label")

    def test_doctor_labels_textual_detection_and_still_reports_real_gaps(self) -> None:
        """A hook whose text merely mentions the capabilities is NOT a clean report.

        The previous version of this test asserted `6/6 capabilities present` and exit 0 for a
        six-line hook with no logic in it — dead-green: it passed whether or not the capability
        existed. Detection stays textual (a project hook can be any shape) but says so, and the
        things doctor *can* verify — gate versions, core.hooksPath — still decide the exit code.
        """
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        hook.write_text(
            "# dfs-bootstrap-hook-version: 5\n"
            "chain_upstream \"$@\"\n# EOL check\ntr -cd '\\r'\n"
            "# NAME / 密钥 scan with delector:allow-secret\n"
            "check_repo_hygiene.py\ncheck_repo_structure.py\n",
            encoding="utf-8", newline="\n",
        )
        proc = run(["--doctor", "--target", str(self.repo)], self.repo)
        self.assertIn("declared in hook text", proc.stdout)
        self.assertIn("capability detection is textual", proc.stdout)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("[GAP] scripts/check_repo_hygiene.py missing", proc.stdout)

    def test_doctor_never_modifies_the_hook(self) -> None:
        hook = self.repo / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True)
        original = "#!/usr/bin/env bash\nexit 0\n"
        hook.write_text(original, encoding="utf-8", newline="\n")
        run(["--doctor", "--target", str(self.repo)], self.repo)
        self.assertEqual(hook.read_text(encoding="utf-8"), original)

    def test_emit_checks_is_read_only_and_sourceable(self) -> None:
        before = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        proc = run(["--emit-checks", "--target", str(self.repo)], self.repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('"$dfs_checks_root/scripts/check_repo_hygiene.py" --staged 2>&1', proc.stdout)
        self.assertIn('"$dfs_checks_root/scripts/check_repo_structure.py" --all 2>&1', proc.stdout)
        self.assertIn('${DFS_STRUCTURE_LOCAL:-0}', proc.stdout,
                      "structure must be opt-in locally — CI is the authoritative 8s run")
        self.assertIn("return 0 2>/dev/null || exit 0", proc.stdout)
        after = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        self.assertEqual(before, after)


class TestTemplatesArePortable(unittest.TestCase):
    def test_templates_are_lf_without_bom(self) -> None:
        for path in sorted((SKILL_DIR / "templates").rglob("*")):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            self.assertNotIn(b"\r\n", raw, f"{path.name} carries CRLF")
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), f"{path.name} carries a BOM")

    def test_no_stale_generated_copy_header(self) -> None:
        for path in sorted((SKILL_DIR / "templates" / "workmemory").glob("*")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("sync-workmemory-template", text, f"{path.name} points at a script that does not exist")

    def test_hook_template_has_no_double_escaped_jwt(self) -> None:
        """A `\\\\.` in the pattern makes the JWT regex dead; it must be a single-backslash dot."""
        text = HOOK_TEMPLATE.read_text(encoding="utf-8")
        jwt = next(line for line in text.splitlines() if line.startswith("JWT"))
        pattern = jwt.split("|", 1)[1]
        self.assertEqual(pattern.count("\\"), 2, f"JWT pattern must escape exactly two dots: {pattern!r}")

    def test_hygiene_template_imports_only_stdlib(self) -> None:
        text = HYGIENE_TEMPLATE.read_text(encoding="utf-8")
        imports = set(re.findall(r"^(?:import|from)\s+([A-Za-z_][\w.]*)", text, re.MULTILINE))
        allowed = {"argparse", "ast", "json", "pathlib", "re", "subprocess", "sys", "__future__"}
        self.assertEqual(imports - allowed, set(), f"non-stdlib imports in the hook-time gate: {imports - allowed}")

    def test_bootstrap_script_compiles(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "py_compile", str(BOOTSTRAP)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
