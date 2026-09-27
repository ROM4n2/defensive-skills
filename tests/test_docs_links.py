#!/usr/bin/env python3
"""Shipped docs must not carry dangling or unshippable links — stdlib only.

The class of bug this catches is real and was hit twice while preparing the first public
commit: `README.md` kept linking `HANDOFF.md` and `WORKMEMORY/` after those files were
untracked, so a stranger's clone would 404 on the links the README itself hands out.

No git dependency on purpose — the ignore list is read straight from `.gitignore` so the
check also works from an unpacked tarball.
"""

import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DOCS = [p for p in (
    REPO / "README.md",
    REPO / "README.en.md",
    REPO / "mcp" / "README.md",
    REPO / "scripts" / "README.md",
) if p.exists()]

LINK = re.compile(r"\]\(([^)\s]+)\)")


def links(path: pathlib.Path) -> list[tuple[str, pathlib.Path]]:
    return [(m.group(1), path) for m in LINK.finditer(path.read_text(encoding="utf-8"))]


def all_links() -> list[tuple[str, pathlib.Path]]:
    """Every (target, source doc) pair across the shipped docs."""
    return [pair for doc in DOCS for pair in links(doc)]


def unshippable_names() -> set[str]:
    """Bare names `.gitignore` marks as never-published. Wildcards are skipped: a glob is
    not a name, and guessing which side of it a link falls on is how a silent gate starts.

    A leading `/` (a root anchor) is stripped along with the trailing `/`: link targets are
    normalised the same way in test_02, so keeping the anchor would mean `/WORKMEMORY` never
    equals `WORKMEMORY/work.log` — the gate would stop catching links into ignored state
    exactly when someone anchors a pattern. `test_04` pins that.
    """
    names = set()
    for raw in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or any(c in line for c in "*?["):
            continue
        names.add(line.strip("/"))
    return names


class ShippedDocsResolveTest(unittest.TestCase):
    def test_00_the_docs_were_actually_found(self):
        """A link gate that finds no links passes vacuously — refuse that.

        The two flagship READMEs hand out the repo map and must carry links; the sub-READMEs
        reference paths in inline code, so they are not held to a link count.
        """
        self.assertEqual(len(DOCS), 4, f"expected the 4 shipped docs, found {[p.name for p in DOCS]}")
        flagship = [d for d in DOCS if d.parent == REPO]
        self.assertEqual(len(flagship), 2, "expected README.md and README.en.md at the repo root")
        for doc in flagship:
            self.assertGreaterEqual(
                len(links(doc)), 5, f"{doc.name} carries the repo map but yielded {len(links(doc))} links"
            )
        self.assertGreaterEqual(len(all_links()), 10, "link scan found suspiciously few links")

    def test_01_relative_links_resolve_on_disk(self):
        broken = []
        for target, doc in all_links():
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not (doc.parent / target.split("#")[0]).resolve().exists():
                broken.append(f"{doc.relative_to(REPO)} -> {target}")
        self.assertEqual(broken, [], f"dangling links in shipped docs: {broken}")

    def test_02_no_link_points_at_never_published_state(self):
        """README must not hand out links to files it deliberately does not ship."""
        off_limits = unshippable_names()
        bad = []
        for target, doc in all_links():
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            t = target.split("#")[0].strip("./").rstrip("/")
            # an ignored directory ignores everything under it — WORKMEMORY/work.log counts too
            if any(t == n or t.startswith(n + "/") for n in off_limits):
                bad.append(f"{doc.relative_to(REPO)} -> {target}")
        self.assertEqual(bad, [], f"shipped docs link to git-ignored state: {bad}")

    def test_03_language_switchers_are_reciprocal(self):
        """Must be an actual link (markdown or <a href>) — a bare mention of the filename
        is not a switcher, and a gate that accepts one is the silent kind."""
        zh = (REPO / "README.md").read_text(encoding="utf-8")
        en = (REPO / "README.en.md").read_text(encoding="utf-8")
        self.assertRegex(zh, re.compile(r'(\]\(|href=")README\.en\.md'),
                         "README.md does not link to the English edition")
        self.assertRegex(en, re.compile(r'(\]\(|href=")README\.md'),
                         "README.en.md does not link back to the Chinese edition")


    def test_04_anchored_ignore_patterns_still_flag_links_into_them(self):
        """Anchoring a pattern must not turn this gate into a silent one.

        `.gitignore` anchors its per-machine block with a leading `/` — that anchor is what stops
        `WORKMEMORY/` from swallowing the shipped `dfs-bootstrap/templates/workmemory/`. The
        matcher normalises link targets with `.strip("./")`, so the pattern has to be normalised
        the same way; otherwise `/WORKMEMORY` never equals `WORKMEMORY/work.log` and links into
        ignored state sail straight through. Checked here rather than trusted.
        """
        off_limits = unshippable_names()
        for name in ("WORKMEMORY", "HANDOFF.md", "AGENTS.md"):
            with self.subTest(pattern=name):
                self.assertIn(name, off_limits, "anchored pattern did not survive normalisation")

        def flagged(target: str) -> bool:
            t = target.split("#")[0].strip("./").rstrip("/")
            return any(t == n or t.startswith(n + "/") for n in off_limits)

        for target in ("WORKMEMORY/work.log", "WORKMEMORY/", "HANDOFF.md"):
            with self.subTest(target=target):
                self.assertTrue(flagged(target), f"a link to {target!r} would no longer be caught")
        self.assertFalse(flagged("README.md"), "a shipped file must not be flagged")


if __name__ == "__main__":
    unittest.main(verbosity=2)
