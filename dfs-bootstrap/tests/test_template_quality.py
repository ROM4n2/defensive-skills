"""Quality gates for the artifacts the skill SHIPS — not just the repos it bootstraps.

The 2026-11-17 CI-wide red was caused by an import-order defect in the two gate TEMPLATES: skill
tests were all green while every generated copy failed Ruff I001. A bootstrap tool must hold its own
output to the same standard it enforces downstream. This suite is stdlib-only so it runs anywhere;
if Ruff is importable it additionally runs the real linter over every shipped Python template.
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = pathlib.Path(__file__).resolve().parent.parent
PY_TEMPLATES = tuple(sorted((SKILL / "templates" / "repo").glob("*.py")))


def _leading_import_block(node: ast.Module) -> list[tuple[int, bool]]:
    """Collect the module's leading top-level import block as (lineno, is_from) pairs.

    Stops at the first non-import statement: imports inside functions are out of scope for Ruff
    I001's top-level ordering rule. ``from __future__`` is always first by convention, not a
    violation, so it is skipped rather than recorded.
    """
    block: list[tuple[int, bool]] = []
    for stmt in node.body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if isinstance(stmt.value.value, str):
                continue  # module docstring precedes the import block
        if isinstance(stmt, ast.Import):
            block.append((stmt.lineno, False))
        elif isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
            if stmt.module != "__future__":
                block.append((stmt.lineno, True))
        elif not isinstance(stmt, (ast.Import, ast.ImportFrom)):
            break  # only the leading import block; later imports are inside functions
    return block


def _import_order_violations(path: pathlib.Path) -> list[str]:
    """Ruff I001's core rule: plain `import X` lines precede `from X import Y` in one block."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    seen_from = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module):
            continue
        for lineno, is_from in _leading_import_block(node):
            if is_from:
                seen_from = True
            elif seen_from:
                problems.append(f"{path.name}:{lineno}: plain import after `from ... import`")
    return problems


LOCAL_GATE_PATH_TOKENS = ("local-gates", "fingerprint-gate.sh")
LOCAL_GATE_SOURCE_ROOTS = {"TEMPLATES", "SKILL_DIR"}


def _local_gate_tracked_tree_copies(source: str) -> list[str]:
    """Flag local-gate destinations that are not private `.git/` state or shipped template reads.

    The old rule banned the string outright, which made a correct `.git/` install impossible. A
    tracked-tree copy is still forbidden: any statement naming the local gate must also name the
    private root (`.git`) or a skill template source root (`TEMPLATES` / `SKILL_DIR`).
    """
    problems: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.stmt):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                continue  # docstring, not an install destination
        strings = [
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
        if not any(token in text for text in strings for token in LOCAL_GATE_PATH_TOKENS):
            continue
        names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
        if any(text == ".git" or text.startswith(".git/") for text in strings):
            continue
        if names & LOCAL_GATE_SOURCE_ROOTS:
            continue
        problems.append(f"line {node.lineno}: local gate path is not private .git/ state")
    return problems


class TestShippedPythonTemplates(unittest.TestCase):
    def test_templates_exist(self) -> None:
        self.assertGreaterEqual(len(PY_TEMPLATES), 2, "expected both gate templates to ship")

    def test_leading_import_block_is_ruff_i001_clean(self) -> None:
        problems = [p for path in PY_TEMPLATES for p in _import_order_violations(path)]
        self.assertEqual(problems, [], "; ".join(problems))

    def test_templates_parse(self) -> None:
        for path in PY_TEMPLATES:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_ruff_clean_when_available(self) -> None:
        """Use the real linter when present. Skip (not fail) when Ruff is not installed."""
        ruff = shutil.which("ruff")
        if not ruff:
            self.skipTest("ruff not on PATH; stdlib import-order check above still ran")
        proc = subprocess.run(
            [ruff, "check", *[str(p) for p in PY_TEMPLATES]],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, (proc.stdout or "") + (proc.stderr or ""))

    def test_templates_carry_gate_version_marker(self) -> None:
        """Without a marker, bootstrap can never upgrade an installed copy — the propagation bug."""
        for path in PY_TEMPLATES:
            head = path.read_text(encoding="utf-8").splitlines()[:5]
            self.assertTrue(
                any(line.startswith("# dfs-bootstrap-gate-version:") for line in head),
                f"{path.name} lacks a gate version marker",
            )

    def test_gate_templates_fit_their_own_bloat_budget(self) -> None:
        """A gate that ships a 1000-line BLOAT rule must not itself approach 1000 lines.

        These templates are deployed as ONE file into arbitrary repos (no sibling imports), so
        "split into modules" — the remedy the BLOAT message suggests — is not available here. The
        budget therefore trips 50 lines before the 1000-line limit, so the author still has room to
        trim (or to consciously raise the limit in a reviewed edit) rather than discovering the wall
        when the skill's self-audit turns red on its own source at line 1001.
        """
        BLOAT_LIMIT = 1000  # check_repo_hygiene.py's max_source_lines default
        BUDGET = BLOAT_LIMIT - 50  # 5% safety margin; a 50-line overrun is still fixable by trimming
        for path in PY_TEMPLATES:
            lines = len(path.read_text(encoding="utf-8").splitlines())
            self.assertLess(
                lines, BUDGET,
                f"{path.name} is {lines} lines (budget {BUDGET}, hard limit {BLOAT_LIMIT}); "
                "trim it, or raise the limit deliberately — do not let it hit the BLOAT wall",
            )

    def test_version_markers_match_bootstrap_constants(self) -> None:
        """The shipped marker and the constant that reads it must agree.

        They are three separate strings (two gate markers + one hook marker vs two constants); bump
        one and not the others and bootstrap silently misjudges every installed copy — an older
        marker re-upgrades forever, a newer one never upgrades at all. This is the guard that makes
        'bump the version' a single, checked edit instead of a memory exercise.
        """
        constants = (SKILL / "scripts" / "dfs_bootstrap" / "constants.py").read_text(encoding="utf-8")
        gate = re.search(r'^GATE_VERSION = "([^"]+)"', constants, re.MULTILINE)
        hook = re.search(r'^HOOK_VERSION = "([^"]+)"', constants, re.MULTILINE)
        local = re.search(r'^LOCAL_GATE_VERSION = "([^"]+)"', constants, re.MULTILINE)
        self.assertIsNotNone(gate, "GATE_VERSION constant missing from dfs_bootstrap/constants.py")
        self.assertIsNotNone(hook, "HOOK_VERSION constant missing from dfs_bootstrap/constants.py")
        self.assertIsNotNone(local, "LOCAL_GATE_VERSION constant missing from dfs_bootstrap/constants.py")

        for path in PY_TEMPLATES:
            found = re.search(r"^# dfs-bootstrap-gate-version:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
            self.assertIsNotNone(found, f"{path.name} lacks a gate version marker")
            self.assertEqual(found.group(1), gate.group(1), f"{path.name} marker != GATE_VERSION")

        hook_tpl = SKILL / "templates" / "githooks-pre-commit.sh"
        found = re.search(r"^# dfs-bootstrap-hook-version:\s*(\S+)", hook_tpl.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(found, "hook template lacks a hook version marker")
        self.assertEqual(found.group(1), hook.group(1), "hook marker != HOOK_VERSION")

        local_tpl = SKILL / "templates" / "local-gates" / "fingerprint-gate.sh"
        found = re.search(
            r"^# dfs-bootstrap-local-gate-version:\s*(\S+)",
            local_tpl.read_text(encoding="utf-8"), re.MULTILINE,
        )
        self.assertIsNotNone(found, "local-gate template lacks a version marker")
        self.assertEqual(found.group(1), local.group(1), "local gate marker != LOCAL_GATE_VERSION")


class TestLocalGateTemplate(unittest.TestCase):
    """The local-only fingerprint gate ships as a template; it must never be installed as-is.

    Two invariants, both from real incidents: (1) the template carries no machine identifier of its
    own — patterns come from `$GIT_DIR/local-gates/fingerprints.txt`, so a skill that hardcodes a
    real user path would flag itself; (2) it keeps the move exemption, without which a WORKMEMORY
    rotation looks like newly added leakage and the only exits are "rewrite history" or "never
    rotate".
    """

    def setUp(self) -> None:
        self.template = SKILL / "templates" / "local-gates" / "fingerprint-gate.sh"

    def test_template_exists_lf_without_bom(self) -> None:
        data = self.template.read_bytes()
        self.assertTrue(data.startswith(b"#!/usr/bin/env bash"))
        self.assertNotIn(b"\r\n", data)
        self.assertNotIn(b"\xef\xbb\xbf", data)

    def test_keeps_the_move_exemption(self) -> None:
        text = self.template.read_text(encoding="utf-8")
        self.assertIn("parent_has_line", text)
        self.assertIn("git grep -qF", text)

    def test_carries_no_machine_identifier_of_its_own(self) -> None:
        text = self.template.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"[A-Za-z]:[\\/]", text), "a drive-letter path in a shipped template")
        self.assertIn("fingerprints.txt", text)

    def test_guides_fingerprints_to_identity_bearing_paths_only(self) -> None:
        """Generic tool dir names are not machine identifiers (2026-11-21 false positive).

        Listing `.codebuddy/` etc. as a fingerprint makes the gate block legitimate
        "ignore this dir" comments in .gitignore — the guide must steer readers to
        absolute paths carrying identity instead, in both the template and SKILL.md.
        """
        tpl = self.template.read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("含本机身份的绝对路径", tpl)
        self.assertIn("absolute paths", skill)
        self.assertIn("Do NOT list generic tool dir names", skill)

    def test_is_not_installed_into_a_target_tree(self) -> None:
        """Only `.git/` private state may receive the gate; `git ls-files` must never see it."""
        problems = [
            f"{source.relative_to(SKILL).as_posix()}:{problem}"
            for source in (SKILL / "scripts").rglob("*.py")
            for problem in _local_gate_tracked_tree_copies(source.read_text(encoding="utf-8"))
        ]
        self.assertEqual(problems, [], "; ".join(problems))

    def test_tracked_tree_copy_is_rejected(self) -> None:
        """Mutation proof: the rule above is not vacuous — a tracked-tree destination is caught."""
        bad = '''from pathlib import Path
def install(target: Path) -> None:
    dest = target / "local-gates" / "fingerprint-gate.sh"
    dest.write_text("x", encoding="utf-8")
'''
        safe = '''from pathlib import Path
def install(target: Path) -> None:
    dest = target / Path(".git") / "local-gates" / "fingerprint-gate.sh"
    dest.write_text("x", encoding="utf-8")
'''
        self.assertTrue(_local_gate_tracked_tree_copies(bad))
        self.assertEqual(_local_gate_tracked_tree_copies(safe), [])

    def test_bash_syntax_is_valid(self) -> None:
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash not available")
        proc = subprocess.run([bash, "-n", str(self.template)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestSelfAudit(unittest.TestCase):
    """The gates must pass on the skill's OWN source, not only on bootstrapped repos.

    This is the regression guard for the 2026-11-17 finding: the skill had two FUNC_LEN and one
    NEST violation plus 7 host-path findings in its own tree, yet every downstream repo was green —
    because the skill source is not a git repo and never entered any gate. Now it self-audits via
    `--no-git`; a future edit that bloats a function or leaks a host path turns this red.
    """

    @staticmethod
    def _run(gate: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SKILL / "templates" / "repo" / gate), "--root", str(SKILL), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def test_structure_gate_passes_on_skill_source(self) -> None:
        proc = self._run("check_repo_structure.py", "--all")
        self.assertEqual(proc.returncode, 0, (proc.stdout or "") + (proc.stderr or ""))

    def test_hygiene_gate_passes_on_skill_source(self) -> None:
        proc = self._run("check_repo_hygiene.py", "--no-git", "--all")
        self.assertEqual(proc.returncode, 0, (proc.stdout or "") + (proc.stderr or ""))


class TestGateUpgrade(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        vault = self.root / "vault"
        vault.mkdir()
        (vault / "AGENTS.md").write_text("# vault rules\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@x"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.repo, capture_output=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def bootstrap(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SKILL / "scripts" / "bootstrap.py"),
             "--target", str(self.repo), "--vault-root", str(self.root / "vault")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def test_old_dfs_gate_is_upgraded_with_backup(self) -> None:
        dest = self.repo / "scripts" / "check_repo_hygiene.py"
        dest.parent.mkdir(parents=True)
        dest.write_text("# dfs-bootstrap-gate-version: 0\n# old buggy copy\n", encoding="utf-8")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("upgraded scripts/check_repo_hygiene.py v0 -> v4", proc.stdout)
        self.assertIn("dfs-bootstrap-gate-version: 4", dest.read_text(encoding="utf-8"))
        self.assertTrue(dest.with_suffix(dest.suffix + ".dfsbak").is_file())

    def test_project_owned_gate_is_preserved(self) -> None:
        dest = self.repo / "scripts" / "check_repo_structure.py"
        dest.parent.mkdir(parents=True)
        original = "# my own gate — do not touch\n"
        dest.write_text(original, encoding="utf-8")
        proc = self.bootstrap()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(dest.read_text(encoding="utf-8"), original)
        self.assertIn("project-owned", proc.stdout)

    def test_current_version_is_not_rewritten(self) -> None:
        self.assertEqual(self.bootstrap().returncode, 0)
        dest = self.repo / "scripts" / "check_repo_structure.py"
        before = dest.read_bytes()
        self.assertEqual(self.bootstrap().returncode, 0)
        self.assertEqual(dest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
