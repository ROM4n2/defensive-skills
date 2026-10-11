#!/usr/bin/env python3
"""The README skill table must be re-derivable from the tree — stdlib only.

A hand-maintained catalogue rots: a skill gets renamed, a description edited, a tier drift, and the
README keeps advertising the old thing to strangers. Every cell here is checked against the files
themselves, including the three-tier "prerequisite" column, so the table cannot be edited by hand
into something the tree does not support.

Tier rule (the same one the generator uses; stated once, here, executably):
  C  references a `scripts/<file>` that ships nowhere in this repo (a genuinely unshipped tool)
  B  declares `mcp_tools`, or mentions the knowledge-base taxonomy dirs, or mentions `{vault_root}`
  A  none of the above — runs standalone

Scope for B/C signals is SKILL.md + `templates/**.md` + `references/**.md`, matching the conformance
gate's Rule 8 scope. Implementation files (a local `.py`) are deliberately out of scope: a docstring
mentioning an unshipped path must not silently move a skill between tiers.
"""

import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
CHAIN = ["dfs", "dfs-plan", "dfs-exec", "dfs-debug", "dfs-save", "dfs-handoff", "dfs-team"]
TAXONOMY_DIRS = ["01-Rules", "03-Languages", "09-Career", "99-Inbox", "Templates/code"]
SCRIPT_REF = re.compile(r"scripts/([A-Za-z0-9_.\-]+\.(?:py|ps1|sh))")
ROW = re.compile(
    r"^\|\s*(?:\*\*(?:主链|chain)\*\*\s+)?`(?P<name>dfs[a-z0-9-]*)`\s*\|(?P<desc>[^|]*)\|"
    r"(?P<tier>[^|]*)\|(?P<mcp>[^|]*)\|(?P<assets>[^|]*)\|\s*$",
    re.M,
)
TIER_LABEL = {"A": {"—"}, "B": {"需知识库", "knowledge base"}, "C": {"需额外资产", "extra assets"}}

# Build/editor artifacts are git-ignored but still sit on disk, and this gate measures the DISK.
# Counting them made the assertion order-dependent: one background `mypy` run left
# `dfs-migrate/scripts/.mypy_cache/` behind, `glob("*")` counted it, and `scripts×1` measured as
# `scripts×2` — so the "fix" offered to a developer was to bake a cache directory into the
# published README table. Ignore dot-entries and `__pycache__`; `test_06` pins this behaviour.
IGNORED_ENTRY = re.compile(r"^(?:\.|__pycache__$)")


def asset_entries(path: pathlib.Path) -> list[pathlib.Path]:
    """Everything a directory actually contributes to a published asset count."""
    return [p for p in path.glob("*") if not IGNORED_ENTRY.match(p.name)]


def shipped_script_names() -> set[str]:
    names = {p.name for p in (REPO / "scripts").glob("*")}
    for d in REPO.glob("dfs*"):
        if (d / "scripts").is_dir():
            names |= {p.name for p in (d / "scripts").glob("*")}
    return names


SHIPPED_SCRIPTS = shipped_script_names()


def skill_measurements() -> dict[str, dict]:
    out = {}
    for d in sorted(p for p in REPO.glob("dfs*") if p.is_dir()):
        texts = {"SKILL.md": (d / "SKILL.md").read_text(encoding="utf-8", errors="replace")}
        for sub in ("templates", "references"):
            sub_dir = d / sub
            if sub_dir.is_dir():
                for f in sorted(sub_dir.rglob("*.md")):
                    texts[f"{sub}/{f.name}"] = f.read_text(encoding="utf-8", errors="replace")
        blob = "\n".join(texts.values())
        fm = re.match(r"^---\r?\n(.*?)\r?\n---", texts["SKILL.md"], re.S)
        if fm is None:
            raise AssertionError(f"{d.name}/SKILL.md has no frontmatter")
        head = fm.group(1)
        desc = re.search(r'^description:\s*"?(.*?)"?\s*$', head, re.M)
        # mcp_tools ships as a block list (Agent Skills shape); inline flow still accepted.
        mcp_tools: list[str] = []
        inline = re.search(r"mcp_tools:\s*\[(.*?)\]", head, re.S)
        if inline:
            mcp_tools = [t.strip() for t in inline.group(1).split(",") if t.strip()]
        else:
            block = re.search(r"(?ms)^[ \t]+mcp_tools:[ \t]*\r?\n((?:[ \t]+-[ \t]+.+(?:\r?\n|$))+)", head)
            if block:
                mcp_tools = [
                    m.group(1).strip()
                    for m in re.finditer(r"(?m)^[ \t]+-[ \t]+(.+?)\s*$", block.group(1))
                ]
        priv = {s for s in SCRIPT_REF.findall(blob) if s not in SHIPPED_SCRIPTS}
        assets = {}
        for key, sub in (("tpl", "templates"), ("refs", "references"), ("scripts", "scripts")):
            if (d / sub).is_dir():
                assets[key] = len(asset_entries(d / sub))
        if priv:
            tier = "C"
        elif mcp_tools or any(blob.count(t) for t in TAXONOMY_DIRS) or "{vault_root}" in blob:
            tier = "B"
        else:
            tier = "A"
        out[d.name] = {
            "desc": (desc.group(1) if desc else "").strip(),
            "mcp": mcp_tools,
            "tier": tier,
            "assets": assets,
        }
    return out


def parse_table(readme: pathlib.Path) -> dict[str, dict]:
    rows = {}
    for m in ROW.finditer(readme.read_text(encoding="utf-8")):
        rows[m.group("name")] = {
            "desc": m.group("desc").strip(),
            "tier": m.group("tier").strip(),
            "mcp": m.group("mcp").strip(),
            "assets": m.group("assets").strip(),
        }
    return rows


class ReadmeSkillTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measured = skill_measurements()
        cls.tree = set(cls.measured)
        cls.zh = parse_table(REPO / "README.md")
        cls.en = parse_table(REPO / "README.en.md")

    def test_00_both_tables_were_actually_found(self):
        """Anti-vacuity: a table parser that matches nothing would pass every assertion below."""
        self.assertGreaterEqual(len(self.zh), 20, f"parsed only {len(self.zh)} rows from README.md")
        self.assertGreaterEqual(len(self.en), 20, f"parsed only {len(self.en)} rows from README.en.md")

    def test_01_table_matches_the_tree_in_both_directions(self):
        self.assertEqual(set(self.zh), self.tree, "README.md lists skills the tree does not have (or vice versa)")
        self.assertEqual(set(self.en), self.tree, "README.en.md lists skills the tree does not have (or vice versa)")

    def test_02_descriptions_and_mcp_columns_match_frontmatter(self):
        for name, row in self.zh.items():
            with self.subTest(skill=name, column="description"):
                self.assertEqual(row["desc"], self.measured[name]["desc"], "README description drifted from SKILL.md")
            with self.subTest(skill=name, column="mcp"):
                expected = ", ".join(self.measured[name]["mcp"]) or "—"
                self.assertEqual(row["mcp"], expected, "README MCP column drifted from the declared contract")
        for name, row in self.en.items():
            self.assertEqual(row["desc"], self.measured[name]["desc"], f"README.en.md description drifted for {name}")

    def test_03_prerequisite_tier_matches_measured_coupling(self):
        for table, rows in (("README.md", self.zh), ("README.en.md", self.en)):
            for name, row in rows.items():
                tier = self.measured[name]["tier"]
                self.assertIn(row["tier"], TIER_LABEL[tier],
                              f"{table}: {name} is labelled '{row['tier']}' but measures as tier {tier}")

    def test_04_asset_column_matches_the_directories(self):
        for name, row in self.zh.items():
            assets = self.measured[name]["assets"]
            # fixed order, not alphabetical: the table reads tpl → refs → scripts
            expected = " ".join(f"{k}×{assets[k]}" for k in ("tpl", "refs", "scripts") if k in assets) or "—"
            self.assertEqual(row["assets"].split(), expected.split(),
                             f"README asset column drifted for {name}: table={row['assets']!r} tree={expected!r}")

    def test_05_headings_and_badge_state_the_real_count(self):
        total, chain = len(self.tree), len(set(CHAIN) & self.tree)
        zh = (REPO / "README.md").read_text(encoding="utf-8")
        en = (REPO / "README.en.md").read_text(encoding="utf-8")
        for text, doc in ((zh, "README.md"), (en, "README.en.md")):
            self.assertIn(f"Skills-{total}", text, f"{doc} badge does not say {total} skills")
            self.assertIn(str(total), text)
        self.assertIn(f"（{total} 个 · 主链 {chain} 个）", zh, "README.md catalogue heading is stale")
        self.assertIn(f"({total} skills · {chain} on the main chain)", en, "README.en.md heading is stale")


    def test_06_ignored_build_artifacts_do_not_move_the_asset_count(self):
        """The probe must be visible to a naive count BEFORE asserting the measurement ignores it.

        Without that first assertion this test would pass even with the bug present. The bug was
        real: a background `mypy` run dropped `dfs-migrate/scripts/.mypy_cache/`, the gate counted
        it, and the README was reported as drifted — the tempting repair being to write `scripts×2`
        into the published table, i.e. bake a build artifact into release data.

        The probe name is dot-prefixed on purpose: if this test ever dies mid-flight it leaves
        behind an entry the (fixed) measurement ignores, instead of a landmine for `test_04`.
        """
        target = REPO / "dfs-migrate" / "scripts"
        self.assertTrue(target.is_dir(), "fixture skill lost its scripts/ directory")
        naive_before = len(list(target.glob("*")))
        before = skill_measurements()["dfs-migrate"]["assets"]["scripts"]

        probe = target / ".dfs-probe-artifact"
        probe.mkdir()
        try:
            self.assertEqual(len(list(target.glob("*"))), naive_before + 1,
                             "probe is invisible even to a naive glob — this test proves nothing")
            after = skill_measurements()["dfs-migrate"]["assets"]["scripts"]
            self.assertEqual(after, before,
                             "a git-ignored build artifact moved the published asset count")
        finally:
            probe.rmdir()


if __name__ == "__main__":
    unittest.main(verbosity=2)
