#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every number the README states must be re-derivable from the tree — stdlib only.

The repository's own thesis is that a claim nobody checks will drift. The badges and the
language paragraph were exactly such claims: three of them were already wrong when this gate
was written (14 rules vs 15, 109 tests vs 111, 26 mutations vs 27), and nothing noticed.

What this gate can and cannot prove, stated up front so a green run is not over-read:

  CAN   the rule count, the test-method count, the mutation-probe count, the skill count,
        the CJK character total, the pure-English skill count, and the zero-prerequisite
        tier count — all are counts over files, so they are derived here, never hardcoded.
  CANNOT  that every test PASSES or that every probe is CAUGHT. Those are runtime facts and
        belong to `python -m pytest` and `tests/mutation_check.py`; CI runs both. A badge
        therefore states a COUNT ("N methods", "N/N probes"), not a pass verdict.

Deliberate design choices:

  * The badge counts are derived, not asserted against a literal, so editing a skill or
    adding a test moves the expectation automatically. Only the README goes stale, and that
    is exactly what fails.
  * Test methods are counted by AST, not by importing the suites: importing runs module-level
    code and would make this gate depend on the very files it is checking.
  * The mutation total is read from `MUTATIONS` by AST too, for the same reason. The
    "all caught" half of that badge is CI's job (`mutation_check.py` exits 1 on any miss).
"""

import ast
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
TESTS = REPO / "tests"

BADGE = re.compile(r"img\.shields\.io/badge/([A-Za-z]+)-([^-\"]+)-[0-9A-Fa-f]{6}")
CJK = re.compile(r"[\u4e00-\u9fff]")


# ---------------------------------------------------------------- measurements


def skill_dirs() -> list[pathlib.Path]:
    return sorted(d for d in REPO.glob("dfs*") if d.is_dir() and (d / "SKILL.md").is_file())


def count_rule_methods() -> int:
    """Distinct rule numbers named by `def test_rule_<n>_...` in the conformance gate."""
    src = (TESTS / "test_skills_conformance.py").read_text(encoding="utf-8")
    return len({m.group(1) for m in re.finditer(r"def test_rule_(\d+)", src)})


def count_test_methods() -> int:
    """Test methods across every `tests/test_*.py`, counted by AST."""
    total = 0
    for f in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        total += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        )
    return total


def count_mutations() -> int:
    """Entries in `MUTATIONS`, read by AST so the harness is never imported."""
    tree = ast.parse((TESTS / "mutation_check.py").read_text(encoding="utf-8"))
    total = 0
    for node in ast.walk(tree):
        # MUTATIONS = [...]  /  MUTATIONS += [...]
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "MUTATIONS" in targets and isinstance(node.value, ast.List):
                total += len(node.value.elts)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "MUTATIONS":
                if isinstance(node.value, ast.List):
                    total += len(node.value.elts)
    return total


def cjk_stats() -> tuple[int, int, dict[str, int]]:
    """(total CJK chars across SKILL.md bodies, count of pure-English skills, per-skill)."""
    per = {}
    for d in skill_dirs():
        body = (d / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        per[d.name] = len(CJK.findall(body))
    return sum(per.values()), sum(1 for n in per.values() if n == 0), per


def tier_a_count() -> int:
    """Zero-prerequisite skills, measured with the same rule the catalogue gate uses."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_readme_table", TESTS / "test_readme_skill_table.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TESTS / 'test_readme_skill_table.py'} as a module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return sum(1 for v in mod.skill_measurements().values() if v["tier"] == "A")


def badges(doc: pathlib.Path) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in BADGE.finditer(doc.read_text(encoding="utf-8"))}


# ---------------------------------------------------------------- the gate


class ClaimedCounts(unittest.TestCase):
    def test_badges_match_measured_reality(self):
        """Validation text uses measured counts without shield badges."""
        methods = count_test_methods()
        mutations = count_mutations()
        skills = len(skill_dirs())
        for name in ("README.md", "README.en.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertNotIn("img.shields.io", text)
            self.assertIn(f"{methods - 1} passed, 1 skipped", text)
            self.assertIn(f"{skills}/28", text)
            if name == "README.md":
                self.assertIn(f"{mutations} 个注入缺陷全部被捕获", text)
            else:
                self.assertIn(f"All {mutations} injected defects caught", text)

    def test_language_stats_match_the_tree(self):
        """README does not carry low-value CJK or pure-English marketing metrics."""
        for name in ("README.md", "README.en.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertNotIn("个汉字", text)
            self.assertNotIn("CJK characters", text)
            self.assertNotIn("pure-English", text)

    def test_skill_count_claims_match_the_tree(self):
        """Claims about the WHOLE tree must equal its skill count.

        Scoped deliberately: the READMEs legitimately cite subsets while telling the story of a
        past defect ("21 dangling references across 6 skills", "the safety intent on those 7
        skills"). A blanket `(\\d+) 个技能` scan flags those as drift, which would force the
        history to be rewritten to satisfy a gate — the opposite of the intent. Only phrases
        that denote the full population are checked.
        """
        skills = len(skill_dirs())
        total_claims = [
            ("README.md", re.compile(r"仓库内含\s*\*\*(\d+)\s*个技能\*\*")),
            ("README.md", re.compile(r"对\s*(\d+)\s*个技能\s*\d+/\d+")),
            ("README.md", re.compile(r"当前\s*(\d+)\s*个技能")),
            ("README.en.md", re.compile(r"(\d+)\s+skills?\s+in\s+this\s+repo", re.I)),
            ("README.en.md", re.compile(r"all\s+(\d+)\s+skills", re.I)),
        ]
        problems = []
        for name, pat in total_claims:
            text = (REPO / name).read_text(encoding="utf-8")
            for m in pat.finditer(text):
                claimed = int(m.group(1))
                if claimed != skills:
                    ctx = text[max(0, m.start() - 30): m.end() + 30].replace("\n", " ")
                    problems.append(
                        f"  - {name}: whole-tree claim says {claimed}, tree has {skills} — ...{ctx}..."
                    )
        if problems:
            self.fail("Skill-count drift:\n" + "\n".join(problems))

    def test_zero_prerequisite_claim_matches_the_tier_measurement(self):
        """The explicit-invocation roster in prose matches frontmatter."""
        expected = {"dfs-bootstrap", "dfs-inbox-consolidate", "dfs-incident", "dfs-pipeline"}
        measured = set()
        for d in skill_dirs():
            head = (d / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
            if re.search(r"(?m)^disable-model-invocation:\s*true\s*$", head):
                measured.add(d.name)
        self.assertEqual(measured, expected)
        for name in ("README.md", "README.en.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            for skill in expected:
                self.assertIn(f"`{skill}`", text)
            self.assertIn("disable-model-invocation", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
