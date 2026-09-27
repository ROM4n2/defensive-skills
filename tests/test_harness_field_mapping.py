#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Keep `dfs/references/harness-field-mapping.md` honest — stdlib only.

That document tells a reader which harness honors which frontmatter key. It is exactly the kind of
doc that rots silently: someone adds a key, or moves a skill to `disable-model-invocation: true`,
and the table keeps claiming things about a suite it no longer describes. So every factual claim in
it is re-derived here from the tree.

Deliberately NOT asserted: prose quality, or that the §2.1 gap is closed — the gap is real and
documented as open; the doc says so, and test_06 pins that it keeps saying so.
"""

import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
DOC = REPO / "dfs" / "references" / "harness-field-mapping.md"
SKILLS = sorted(p.name for p in REPO.glob("dfs*") if p.is_dir())
TOP_KEY = re.compile(r"(?m)^([a-zA-Z][\w-]*):")
HERMES_KEY = re.compile(r"(?m)^\s{2,}([a-z_]+):")


def frontmatter(skill: str) -> str:
    text = (REPO / skill / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        raise AssertionError(f"{skill}/SKILL.md has no frontmatter block")
    return m.group(1)


def keys_of(skill: str) -> set[str]:
    head = frontmatter(skill)
    keys = {m.group(1) for m in TOP_KEY.finditer(head)}
    keys.discard("metadata")
    if re.search(r"(?m)^metadata:\s*$", head):
        after = head.split("metadata:", 1)[1]
        keys |= {f"metadata.hermes.{m.group(1)}" for m in HERMES_KEY.finditer(after)
                 if m.group(1) != "hermes"}
    return keys


def doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


def doc_section(heading: str, stop: str) -> str:
    text = doc_text()
    i = text.find(heading)
    if i < 0:
        raise AssertionError(f"{DOC.name} lost its {heading!r} section")
    j = text.find(stop, i)
    return text[i:j if j > 0 else len(text)]


def table_keys(section: str) -> set[str]:
    out = set()
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip()
        out |= set(re.findall(r"`([a-zA-Z][\w.-]*)`", cell))
    return out


class HarnessFieldMappingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.per_skill = {s: keys_of(s) for s in SKILLS}
        cls.used = set().union(*cls.per_skill.values())
        cls.portable = {k for k in cls.used if all(k in ks for ks in cls.per_skill.values())}
        cls.doc = doc_text()

    def test_00_the_scan_found_something(self):
        """Anti-vacuity: a broken parser would make every assertion below pass on nothing."""
        self.assertGreaterEqual(len(self.per_skill), 20,
                                f"only parsed {len(self.per_skill)} skills")
        self.assertGreaterEqual(len(self.used), 5, f"only found keys {sorted(self.used)}")
        self.assertIn("name", self.portable)
        self.assertIn("description", self.portable)

    def test_01_every_key_used_in_the_tree_is_documented(self):
        missing = sorted(k for k in self.used if f"`{k}`" not in self.doc)
        self.assertEqual(missing, [], f"frontmatter keys not documented in {DOC.name}: {missing}")

    def test_02_the_portable_core_matches_reality(self):
        documented = table_keys(doc_section("## 1. Portable core", "## 2."))
        self.assertEqual(documented, self.portable,
                         "the doc's §1 'safe everywhere' list drifted from what the skills carry")

    def test_03_the_disable_model_invocation_roster_matches_reality(self):
        measured = {s for s, ks in self.per_skill.items()
                    if "disable-model-invocation" in ks}
        row = [ln for ln in self.doc.splitlines() if "disable-model-invocation" in ln and ln.startswith("|")]
        self.assertEqual(len(row), 1, "expected exactly one table row about disable-model-invocation")
        listed = set(re.findall(r"`(dfs[a-z-]*)`", row[0]))
        self.assertEqual(listed, measured,
                         f"the doc lists {sorted(listed)} but the tree has {sorted(measured)}")

    def test_04_mcp_tools_is_documented_as_suite_internal(self):
        row = [ln for ln in self.doc.splitlines() if "`metadata.hermes.mcp_tools`" in ln]
        self.assertTrue(row, "mcp_tools is not in the mapping table at all")
        self.assertIn("DFS-internal", row[0],
                      "mcp_tools must be described as this suite's own contract — no harness reads it")
        self.assertIn("no harness support", row[0])

    def test_05_the_ignored_case_has_an_actionable_lever(self):
        for lever in ("skillOverrides", "permission rule", "one line to each"):
            self.assertIn(lever, self.doc, f"no lever documented for a harness that ignores a key: {lever}")

    def test_06_the_open_gap_is_stated_not_hidden(self):
        section = doc_section("### 2.1", "## 3.")
        self.assertIn("not done yet", section,
                      "§2.1 must keep stating that the portable prose line is not applied yet")
        self.assertRegex(section, r"grep .*SKILL\.md",
                         "§2.1's claim needs the command that verifies it")

    def test_07_the_doc_is_reachable_from_the_front_page(self):
        for readme in ("README.md", "README.en.md"):
            self.assertIn("harness-field-mapping.md", (REPO / readme).read_text(encoding="utf-8"),
                          f"{readme} does not link the mapping doc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
