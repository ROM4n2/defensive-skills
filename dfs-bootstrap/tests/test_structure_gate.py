"""Structure gate: default checks and the three opt-in checks.

The default set (`[CYCLE]`, `[FANOUT]`, `[FUNC_LEN]`, `[NEST]`, `[CLASS]`, `[STUB]`) runs on every commit.
The opt-in set (`[DEAD]`, `[TEST_GAP]`, `[DUP]`) is off until a repo enables it in
`data/repo_structure.json`, because a gate that lands red on day one in an existing repo gets deleted.

Run: python -B tests/test_structure_gate.py
"""
from __future__ import annotations

import unittest

from harness import GateHarness


class TestCleanTree(GateHarness):
    def test_clean_repo_passes(self) -> None:
        self.write("src/a.py", "def add(x, y):\n    return x + y\n")
        self.write("src/b.py", "from src.a import add\n\ndef double(x):\n    return add(x, x)\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[PASS]", proc.stdout)

    def test_empty_repo_passes(self) -> None:
        proc = self.gate()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("no Python modules", proc.stdout)


class TestImportCycle(GateHarness):
    def test_two_module_cycle_is_rejected(self) -> None:
        self.write("src/a.py", "from src.b import thing\n\ndef a():\n    return thing()\n")
        self.write("src/b.py", "from src.a import a\n\ndef thing():\n    return 1\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[CYCLE]", proc.stderr)

    def test_three_module_cycle_is_rejected(self) -> None:
        for name, nxt in (("a", "b"), ("b", "c"), ("c", "a")):
            self.write(f"src/{name}.py", f"from src.{nxt} import f_{nxt}\n\ndef f_{name}():\n    return 1\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[CYCLE]", proc.stderr)

    def test_dag_is_not_a_cycle(self) -> None:
        self.write("src/a.py", "def f():\n    return 1\n")
        self.write("src/b.py", "from src.a import f\n\ndef g():\n    return f()\n")
        self.write("src/c.py", "from src.b import g\n\ndef h():\n    return g()\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestFanout(GateHarness):
    def test_hub_module_is_rejected(self) -> None:
        for i in range(6):
            self.write(f"src/leaf{i}.py", f"def f{i}():\n    return {i}\n")
        imports = "\n".join(f"from src.leaf{i} import f{i}" for i in range(6))
        self.write("src/hub.py", imports + "\n\ndef run():\n    return 0\n")
        self.config(max_fanout=5)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[FANOUT]", proc.stderr)

    def test_fanout_under_limit_passes(self) -> None:
        for i in range(3):
            self.write(f"src/leaf{i}.py", f"def f{i}():\n    return {i}\n")
        imports = "\n".join(f"from src.leaf{i} import f{i}" for i in range(3))
        self.write("src/hub.py", imports + "\n\ndef run():\n    return 0\n")
        self.config(max_fanout=5)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestFunctionLength(GateHarness):
    def test_long_function_is_rejected(self) -> None:
        body = "\n".join(f"    x{i} = {i}" for i in range(70))
        self.write("src/big.py", "def huge():\n" + body + "\n    return x0\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[FUNC_LEN]", proc.stderr)

    def test_threshold_is_configurable(self) -> None:
        body = "\n".join(f"    x{i} = {i}" for i in range(20))
        self.write("src/big.py", "def huge():\n" + body + "\n    return x0\n")
        self.config(max_function_lines=10)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[FUNC_LEN]", proc.stderr)


class TestNesting(GateHarness):
    def test_deep_nesting_is_rejected(self) -> None:
        self.write("src/deep.py", """
            def deep(a, b, c, d, e):
                if a:
                    for _ in b:
                        while c:
                            with open("x") as fh:
                                if d:
                                    return e
                return None
        """)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[NEST]", proc.stderr)

    def test_guard_clauses_pass(self) -> None:
        self.write("src/flat.py", """
            def flat(a, b):
                if not a:
                    return None
                if not b:
                    return None
                return a + b
        """)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestGodClass(GateHarness):
    def test_class_with_too_many_methods_is_rejected(self) -> None:
        methods = "\n".join(f"    def m{i}(self):\n        return {i}\n" for i in range(25))
        self.write("src/god.py", "class God:\n" + methods)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[CLASS]", proc.stderr)


class TestStubSignatures(GateHarness):
    """The bloat signatures: what context-truncated generation actually leaves behind."""

    def test_pass_only_body_is_rejected(self) -> None:
        self.write("src/stub.py", "def do_thing():\n    pass\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)
        self.assertIn("only `pass`", proc.stderr)

    def test_ellipsis_body_is_rejected(self) -> None:
        self.write("src/stub.py", "def do_thing():\n    ...\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)

    def test_not_implemented_error_is_rejected(self) -> None:
        self.write("src/stub.py", "def do_thing():\n    raise NotImplementedError\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)

    def test_abstract_method_is_allowed(self) -> None:
        self.write("src/base.py", """
            from abc import ABC, abstractmethod

            class Base(ABC):
                @abstractmethod
                def run(self):
                    ...
        """)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_elision_comment_is_rejected(self) -> None:
        # Assembled from fragments: this file is itself scanned when the skill self-audits.
        marker = "# " + "." * 3 + " rest of " + "implementation " + "unchanged"
        self.write("src/trunc.py", f"def real():\n    return 1\n\n{marker}\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)
        self.assertIn("elision marker", proc.stderr)

    def test_todo_marker_is_rejected(self) -> None:
        marker = "# " + "TO" + "DO" + ": wire this up"
        self.write("src/todo.py", f"def real():\n    return 1  {marker}\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)
        self.assertIn("placeholder marker", proc.stderr)

    def test_docstring_only_body_is_rejected(self) -> None:
        self.write("src/doc.py", 'def described():\n    """Does the thing."""\n')
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("empty body", proc.stderr)


class TestBaselineTolerance(GateHarness):
    """Ratchet a repo with debt: absorb today's count, reject anything beyond it."""

    def test_default_zero_tolerance_still_rejects(self) -> None:
        self.write("src/stub.py", "def do_thing():\n    pass\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)

    def test_existing_count_is_tolerated_and_reported(self) -> None:
        self.write("src/stub.py", "def do_thing():\n    pass\n")
        self.config(allowed_stub=1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[PASS]", proc.stdout)
        self.assertIn("baseline tolerated: [STUB] 1/1", proc.stdout)

    def test_one_more_than_tolerance_is_rejected(self) -> None:
        self.write("src/a.py", "def a():\n    pass\n")
        self.write("src/b.py", "def b():\n    pass\n")
        self.config(allowed_stub=1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[STUB]", proc.stderr)
        self.assertIn("baseline tolerated: [STUB] 1/2", proc.stderr)

    def test_tolerance_is_count_not_allowlist(self) -> None:
        """Fixing one old finding and adding a new one keeps the gate green — it is a count."""
        self.write("src/a.py", "def a():\n    pass\n")
        self.config(allowed_stub=1)
        self.assertEqual(self.gate().returncode, 0)
        self.write("src/a.py", "def a():\n    return 1\n")
        self.write("src/b.py", "def b():\n    pass\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("baseline tolerated: [STUB] 1/1", proc.stdout)

    def test_tolerance_is_per_class(self) -> None:
        """Tolerating [STUB] must not silently absorb a [FUNC_LEN] violation."""
        body = "\n".join(f"    x{i} = {i}" for i in range(70))
        self.write("src/stub.py", "def do_thing():\n    pass\n")
        self.write("src/big.py", "def huge():\n" + body + "\n    return x0\n")
        self.config(allowed_stub=1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[FUNC_LEN]", proc.stderr)
        self.assertIn("baseline tolerated: [STUB] 1/1", proc.stderr)

    def test_tolerance_never_exceeds_configured_count(self) -> None:
        """A config of 1 must absorb exactly one finding, not every finding of that class."""
        self.write("src/a.py", "def a():\n    pass\n")
        self.write("src/b.py", "def b():\n    pass\n")
        self.write("src/c.py", "def c():\n    pass\n")
        self.config(allowed_stub=2)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("baseline tolerated: [STUB] 2/3", proc.stderr)


class TestBaselineAutomation(GateHarness):
    """--emit-baseline self-measures; --ratchet-guard forbids raising tolerance in CI."""

    def test_emit_baseline_writes_measured_counts_with_provenance(self) -> None:
        import json
        self.write("src/a.py", "def a():\n    pass\n")
        self.write("src/b.py", "def b():\n    pass\n")
        proc = self.gate("--emit-baseline")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        cfg = json.loads((self.root / "data" / "repo_structure.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["allowed_stub"], 2, "must measure the real count, not copy a doc number")
        self.assertIn("measured_at_commit", cfg["_provenance"])

    def test_emit_baseline_result_passes_the_audit(self) -> None:
        self.write("src/a.py", "def a():\n    pass\n")
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        audit = self.gate()
        self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
        self.assertIn("baseline tolerated: [STUB] 1/1", audit.stdout)

    def test_ratchet_guard_fails_when_tolerance_rose(self) -> None:
        """Raise one allowed_* above the committed value -> CI must go red."""
        import json
        self.write("src/a.py", "def a():\n    pass\n")
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        # No git repo in GateHarness: create one so HEAD has the baseline blob.
        from harness import git
        git(["init", "-q"], self.root)
        git(["config", "user.email", "t@example.invalid"], self.root)
        git(["config", "user.name", "T"], self.root)
        git(["add", "-A"], self.root)
        git(["commit", "-qm", "baseline"], self.root)
        cfg_path = self.root / "data" / "repo_structure.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["allowed_stub"] += 1
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8", newline="\n")
        proc = self.gate("--ratchet-guard")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ratchet violated", proc.stderr)
        self.assertIn("allowed_stub", proc.stderr)

    def test_ratchet_guard_passes_when_tolerance_fell(self) -> None:
        import json
        self.write("src/a.py", "def a():\n    pass\n")
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        from harness import git
        git(["init", "-q"], self.root)
        git(["config", "user.email", "t@example.invalid"], self.root)
        git(["config", "user.name", "T"], self.root)
        git(["add", "-A"], self.root)
        git(["commit", "-qm", "baseline"], self.root)
        cfg_path = self.root / "data" / "repo_structure.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["allowed_stub"] = 0
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8", newline="\n")
        proc = self.gate("--ratchet-guard")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ratchet intact", proc.stdout)


class TestJsonOutput(GateHarness):
    """--json is machine-readable and keeps raw/tolerated/reported distinct for trend data."""

    def test_json_reports_counts_and_verdict(self) -> None:
        import json
        self.write("src/a.py", "def a():\n    pass\n")
        self.config(allowed_stub=1)
        proc = self.gate("--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "pass")
        self.assertEqual(payload["findings_total"], 1)
        self.assertEqual(payload["findings_tolerated"], 1)
        self.assertEqual(payload["findings_reported"], 0)
        self.assertEqual(payload["tolerated_by_class"]["[STUB]"], {"absorbed": 1, "total": 1})

    def test_json_exit_one_on_reported_finding(self) -> None:
        import json
        self.write("src/a.py", "def a():\n    pass\n")
        proc = self.gate("--json")
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "fail")
        self.assertEqual(payload["findings_reported"], 1)
        self.assertTrue(any("[STUB]" in f for f in payload["reported_findings"]))

    def test_explain_shows_source_and_provenance(self) -> None:
        self.write("src/a.py", "def a():\n    pass\n")
        self.assertEqual(self.gate("--emit-baseline").returncode, 0)
        proc = self.gate("--explain")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("data/repo_structure.json", proc.stdout)
        self.assertIn("allowed_stub = 1", proc.stdout)
        self.assertIn("provenance: measured_at_commit=", proc.stdout)

    def test_json_is_mutually_exclusive_with_baseline(self) -> None:
        proc = self.gate("--json", "--emit-baseline")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("mutually exclusive", proc.stderr)


class TestExitContract(GateHarness):
    def test_malformed_config_exits_two(self) -> None:
        self.write("src/a.py", "def f():\n    return 1\n")
        (self.root / "data" / "repo_structure.json").write_text("{not json", encoding="utf-8")
        proc = self.gate()
        self.assertEqual(proc.returncode, 2, "an unusable gate must not report 0 or 1")

    def test_non_object_config_exits_two(self) -> None:
        self.write("src/a.py", "def f():\n    return 1\n")
        (self.root / "data" / "repo_structure.json").write_text("[1,2,3]", encoding="utf-8")
        proc = self.gate()
        self.assertEqual(proc.returncode, 2)


class TestScope(GateHarness):
    def test_venv_and_worktrees_are_ignored(self) -> None:
        self.write(".venv/lib/vendored.py", "def f():\n    pass\n")
        self.write(".worktrees/wt/src/x.py", "def g():\n    pass\n")
        self.write("src/ok.py", "def h():\n    return 1\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_syntax_error_module_is_skipped_not_fatal(self) -> None:
        self.write("src/broken.py", "def f(:\n    return 1\n")
        self.write("src/ok.py", "def h():\n    return 1\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


# ---------------------------------------------------------------------------
# Opt-in checks
# ---------------------------------------------------------------------------

class TestDeadExports(GateHarness):
    def test_unreferenced_symbol_is_rejected_when_enabled(self) -> None:
        self.write("src/a.py", "def used():\n    return 1\n\ndef orphan_helper():\n    return 2\n")
        self.write("src/b.py", "from src.a import used\n\ndef go():\n    return used()\n\ngo()\n")
        self.config(max_dead_exports=0)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[DEAD]", proc.stderr)
        self.assertIn("orphan_helper", proc.stderr)

    def test_referenced_symbols_pass(self) -> None:
        self.write("src/a.py", "def used():\n    return 1\n")
        self.write("src/b.py", "from src.a import used\n\ndef go():\n    return used()\n\ngo()\n")
        self.config(max_dead_exports=0)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_disabled_by_default(self) -> None:
        self.write("src/a.py", "def orphan():\n    return 1\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_private_names_are_exempt(self) -> None:
        self.write("src/a.py", "def _internal():\n    return 1\n")
        self.config(max_dead_exports=0)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "leading-underscore names are private, not dead exports")

    def test_main_is_exempt(self) -> None:
        self.write("src/a.py", "def main():\n    return 0\n")
        self.config(max_dead_exports=0)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "an entry point is never a dead export")

    def test_tolerance_allows_n_exports(self) -> None:
        self.write("src/a.py", "def orphan_one():\n    return 1\n\ndef orphan_two():\n    return 2\n")
        self.config(max_dead_exports=2)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "tolerance of 2 must allow 2 dead exports")

    def test_negative_tolerance_disables_the_check(self) -> None:
        self.write("src/a.py", "def orphan():\n    return 1\n")
        self.config(max_dead_exports=-1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestTestGap(GateHarness):
    def test_src_module_without_test_is_rejected_when_enabled(self) -> None:
        self.write("src/covered.py", "def f():\n    return 1\n")
        self.write("src/bare.py", "def g():\n    return 2\n")
        self.write("tests/test_covered.py", "import unittest\n")
        self.config(require_test_for_src=1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[TEST_GAP]", proc.stderr)
        self.assertIn("bare", proc.stderr)
        self.assertNotIn("covered.py: no test file", proc.stderr)

    def test_disabled_by_default(self) -> None:
        self.write("src/bare.py", "def g():\n    return 2\n")
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_init_is_exempt(self) -> None:
        self.write("src/__init__.py", "")
        self.write("src/mod.py", "def f():\n    return 1\n")
        self.write("tests/test_mod.py", "import unittest\n")
        self.config(require_test_for_src=1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_suffix_style_test_name_also_counts(self) -> None:
        self.write("src/widget.py", "def f():\n    return 1\n")
        self.write("tests/widget_test.py", "import unittest\n")
        self.config(require_test_for_src=1)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "widget_test.py must satisfy widget.py")


class TestDuplicates(GateHarness):
    BODY = """
        def work(xs):
            total = 0
            for x in xs:
                total += x
            if total > 0:
                return total
            return 0
    """

    def test_identical_function_bodies_are_rejected_when_enabled(self) -> None:
        self.write("src/a.py", self.BODY)
        self.write("src/b.py", self.BODY.replace("work", "other"))
        self.config(max_dup_lines=4)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[DUP]", proc.stderr)

    def test_distinct_bodies_pass(self) -> None:
        self.write("src/a.py", """
            def alpha(xs):
                total = 0
                for item in xs:
                    total += item
                return total
        """)
        self.write("src/b.py", """
            def beta(mapping):
                result = {}
                for key in mapping:
                    result[key] = mapping[key]
                return result
        """)
        self.config(max_dup_lines=4)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_disabled_by_default(self) -> None:
        self.write("src/a.py", self.BODY)
        self.write("src/b.py", self.BODY.replace("work", "other"))
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_short_functions_are_not_compared(self) -> None:
        self.write("src/a.py", "def f():\n    return 1\n")
        self.write("src/b.py", "def g():\n    return 1\n")
        self.config(max_dup_lines=8)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "two one-liners are not a meaningful clone")

    def test_mirrored_build_tree_is_not_a_duplicate(self) -> None:
        """A build system copying the source tree must not report every function as a clone."""
        self.write("pkg/mod.py", self.BODY)
        self.write("android/app/src/main/python/pkg/mod.py", self.BODY)
        self.config(max_dup_lines=4)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "a mirrored copy is the same file, not a clone")

    def test_genuine_duplicate_in_unrelated_dirs_is_still_caught(self) -> None:
        """The mirror guard must not suppress a real duplicate that happens to share a filename."""
        self.write("pkg/a.py", self.BODY)
        self.write("tools/b.py", self.BODY)
        self.config(max_dup_lines=4)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[DUP]", proc.stderr)

    def test_same_body_different_arity_is_not_a_duplicate(self) -> None:
        """Identical body, different signature = different interface, not a copy-paste."""
        self.write("src/a.py", """
            def collect_one(xs):
                total = 0
                for x in xs:
                    total += x
                return total
        """)
        self.write("src/b.py", """
            def collect_two(xs, weight):
                total = 0
                for x in xs:
                    total += x
                return total
        """)
        self.config(max_dup_lines=4)
        proc = self.gate()
        self.assertEqual(proc.returncode, 0, "different arity must not be reported as a clone")

    def test_same_arity_different_name_is_a_duplicate(self) -> None:
        """The mirror of the test above: same arity, different name, identical body = a clone."""
        self.write("src/a.py", """
            def collect_one(xs):
                total = 0
                for x in xs:
                    total += x
                return total
        """)
        self.write("src/b.py", """
            def collect_two(rows):
                total = 0
                for x in rows:
                    total += x
                return total
        """)
        self.config(max_dup_lines=4)
        proc = self.gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[DUP]", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
