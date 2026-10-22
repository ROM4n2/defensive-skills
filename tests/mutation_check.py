#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutation check for tests/test_skills_conformance.py.

A green gate only means something if injecting each defect turns it red. This copies the repo
to a scratch dir, injects one defect per rule, runs the gate against the copy via
`DFS_SKILLS_DIR`, and asserts the corresponding test failed.

Usage:  python tests/mutation_check.py
Exit 0 = every rule's defect was caught. Exit 1 = at least one rule is a no-op.
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
GATE = REPO / "tests" / "test_skills_conformance.py"

# Probes are not limited to one gate any more: the field-mapping and README-catalogue gates used to be
# hand-probed because the harness only ever ran `GATE`. Route each expected failure to the file that
# owns it; anything not listed runs against the conformance gate as before.
GATE_OF: dict[str, pathlib.Path] = {
    "02_the_portable_core_matches_reality": REPO / "tests" / "test_harness_field_mapping.py",
    "03_the_disable_model_invocation_roster_matches_reality": REPO / "tests" / "test_harness_field_mapping.py",
    "02_descriptions_and_mcp_columns_match_frontmatter": REPO / "tests" / "test_readme_skill_table.py",
    "01_table_matches_the_tree_in_both_directions": REPO / "tests" / "test_readme_skill_table.py",
}

# The pristine tree is expected to be FULLY GREEN: published blocker B4 (the dangling script
# references Rule 8 was catching) is fixed, so no rule is expected to be red. An EMPTY baseline is
# the stronger assertion — every mutation must introduce its own failure, and any failure present
# before mutation is a regression the harness reports instead of absorbing.
KNOWN_RED_BASELINE: set[str] = set()


def set_description(text: str, value: str) -> str:
    return re.sub(r"(?m)^description:.*$", f'description: "{value}"', text, count=1)


# (expected failing test key, relative file, transform)
MUTATIONS = [
    ("rule_1_every_skill_dir_contains_skill_md",
     "dfs-interview/SKILL.md", lambda t: None),
    ("rule_2_frontmatter_schema",
     "dfs-team/SKILL.md", lambda t: t.replace("name: dfs-team", "name: dfs-typo", 1)),
    # Rule 3a has two independent failure modes, so it gets two probes: a description with no
    # trigger clause (the "installs but never fires" defect), and one that HAS the clause but blows
    # the length cap. Either alone must turn Rule 3a red.
    ("rule_3a_description_has_trigger_clause",
     "dfs-team/SKILL.md", lambda t: set_description(t, "Execute TDD plans with no trigger clause at all.")),
    ("rule_3a_description_has_trigger_clause",
     "dfs-team/SKILL.md", lambda t: set_description(t, "Use when " + "x" * 330 + ".")),
    # 3b's probe deliberately keeps a valid trigger clause, so ONLY the period check can fire —
    # clean attribution instead of a description that trips both 3a and 3b at once.
    ("rule_3_description_period_termination",
     "dfs-team/SKILL.md", lambda t: set_description(t, "Use when implementing a feature test-first")),
    ("rule_4_router_disable_model_invocation",
     "dfs/SKILL.md", lambda t: t.replace('  disable-model-invocation: "true"',
                                         '  disable-model-invocation: "false"', 1)),
    # Rule 8 needs its own mutation now that the baseline is empty: while B4 was open the gate
    # merely *expected* rule_8 to fail, which proves nothing about the check itself. The injected
    # pointer is deliberately NOT in OPTIONAL_SCRIPT_POINTERS, so it also proves the exemption list
    # cannot swallow a fresh dangling reference.
    ("rule_8_script_pointers_resolve_physically",
     "dfs-adr/SKILL.md", lambda t: t + "\nRun `python scripts/ghost-helper.py` first.\n"),
    ("rule_5_context_pointers_resolve_physically",
     "dfs-adr/SKILL.md", lambda t: t + "\nSee `templates/does-not-exist.md`.\n"),
    ("rule_6_runtime_neutrality",
     "dfs-adr/SKILL.md", lambda t: t + "\nSpawn from ~/.claude/agents/reviewer.md\n"),
    # Rule 6's scope was widened from the body to templates/ + references/ because the two skills
    # that named the Claude path moved their dispatch prose into a reference file, leaving the rule
    # with zero subjects. Two probes, because the widening covers two directories: probing only the
    # reference would leave the templates half of the extension unproven. Both targets deliberately
    # lack every fallback keyword, so the injected path cannot be excused by a keyword elsewhere in
    # the file — the rule pairs the path with its fallback per file, not per skill.
    ("rule_6_runtime_neutrality",
     "dfs/references/a-mac-gate.md",
     lambda t: t + "\nSpawn every reviewer from `~/.claude/agents/code-reviewer.md`.\n"),
    ("rule_6_runtime_neutrality",
     "dfs-adr/templates/adr-template.md",
     lambda t: t + "\nSpawn the author subagent from `~/.claude/agents/code-reviewer.md`.\n"),
    # related_skills ships as a block list; the probe prepends a dangling item to it.
    # Target MUST be a skill that actually carries the BLOCK shape: dfs-handoff carries the inline
    # `[a, b]` form, where a `^    related_skills:\n` regex matches nothing and the probe silently
    # mutated nothing — two vacuous probes that reported the rule as unenforced. `main()` now
    # rejects a transform that returns its input unchanged, so this class cannot come back quietly.
    ("rule_7_related_skills_resolve_to_real_skills",
     "dfs-adr/SKILL.md", lambda t: re.sub(
         r"(?m)^    related_skills:\r?\n",
         "    related_skills:\n      - dfs-does-not-exist\n", t, count=1)),
    # A repeated entry still RESOLVES, so the dangling check stays silent and only the no-duplicate
    # assertion can catch it. The duplicated entry is a real one already listed, on purpose.
    ("rule_7_related_skills_resolve_to_real_skills",
     "dfs-adr/SKILL.md", lambda t: re.sub(
         r"(?ms)^(    related_skills:\n)(      - )([^\n]+)",
         r"\1\2\3\n\2\3", t, count=1)),
    # Inline flow lists remain a supported shape (vault-side trees), so this probe injects the
    # bogus tool declaration the old-fashioned way: it must still be parsed, then rejected.
    ("rule_9_mcp_contract_tools_are_canonical",
     "dfs-adr/SKILL.md", lambda t: t.replace("    related_skills:",
                                             "    mcp_tools: [search_vault, bogus_tool]\n    related_skills:", 1)),
    # fixture: the path is deliberately shaped to match Rule 10's pattern. "ExampleVault" is
    # fake on purpose — never swap in a real vault name, that is the leak this rule bans.
    ("rule_10_no_hardcoded_absolute_vault_paths",
     "dfs-adr/SKILL.md", lambda t: t + "\nRead D:/Obsidian/ExampleVault/01-Rules/SOME-RULE.md\n"),
    ("rule_11_declared_mcp_contract_covers_actual_usage",
     "dfs-adr/SKILL.md", lambda t: t + "\nCall `search_vault(\"x\")` first.\n"),
    ("rule_12_vault_mcp_call_sites_are_canonical",
     "dfs-adr/SKILL.md", lambda t: t + "\nCall `serch_vault(\"x\")` first.\n"),
    # Rule 13 has two failure modes, so two probes. The first produces the orphan state — an asset
    # sits on disk with nothing routing to it — by deleting the only pointer instead of by planting
    # a file: the end state (and therefore what the rule must catch) is identical. Rule 5 stays
    # green here on purpose, because no pointer is left to dangle, so any red is Rule 13's own.
    ("rule_13_on_demand_assets_are_routed_from_a_body",
     "dfs-adr/SKILL.md", lambda t: t.replace("templates/adr-template.md", "adr-template.md")),
    # The second exercises the self-invalidation path: route one of the declared code-consumed
    # templates from a body and the declaration becomes dead weight. The injected pointer resolves
    # to a real file, so Rule 5 stays green and only the stale-declaration check can fire.
    ("rule_13_on_demand_assets_are_routed_from_a_body",
     "dfs-bootstrap/SKILL.md",
     lambda t: t + "\nRead `templates/workmemory/PROTOCOL.md` before scaffolding.\n"),
    # Rule 14 checks the one kind of content a gate can check: a heading's claimed count against
    # the items below it. Two probes, one per direction of that comparison, because either side can
    # drift -- an author edits the claim, or adds a step and forgets the claim.
    ("rule_14_claimed_counts_match_the_enumeration",
     "dfs-tdd/SKILL.md",
     lambda t: t.replace("## The 5-Step Industrial TDD Lifecycle",
                         "## The 6-Step Industrial TDD Lifecycle", 1)),
    ("rule_14_claimed_counts_match_the_enumeration",
     "dfs-tdd/SKILL.md",
     lambda t: t + "\n### Step 6: Ship It\n"),
    # Block lists are a SUPPORTED shape since the 2026-10 Agent Skills migration, so the old
    # "block list must raise" probe retired with the parser that raised. Its replacement: an
    # empty `name:` — distinct from the dfs-team typo probe (which exercises the directory-match
    # assertion), this one exercises "missing required field". Rule 13 must NOT show up in this
    # mutation's `also:` list: it skips skills whose frontmatter fails to parse, on purpose.
    ("rule_2_frontmatter_schema",
     "dfs-adr/SKILL.md", lambda t: t.replace("name: dfs-adr", "name:", 1)),
]

# Two gates had no automatic probe: they were hand-checked once (inject / observe red / restore) and
# that receipt went stale the moment either file changed. A manual probe is a probe you will not
# re-run. These four put them on the same mechanical terms as every rule above.
MUTATIONS += [
    # Portable-core drift: harness-field-mapping.md claims the portable core is
    # {description, license, name, metadata.platforms, metadata.version}. Drop one from a skill and
    # the doc/reality comparison must notice. test_01 stays green — the key is still documented, the
    # defect is the missing value.
    ("02_the_portable_core_matches_reality",
     "dfs-release/SKILL.md", lambda t: t.replace("  platforms: linux, macos, windows\n", "", 1)),
    # Roster drift: §2 states how many skills carry the flag and names them; stripping it from one
    # makes the doc a claim about a tree that no longer exists. The value is quoted either way in the
    # tree ('true' / "true"), so the probe accepts both instead of silently mutating nothing.
    ("03_the_disable_model_invocation_roster_matches_reality",
     "dfs-pipeline/SKILL.md",
     lambda t: re.sub(r"^  disable-model-invocation: [\"']true[\"']\n", "", t, count=1, flags=re.M)),
    # Catalogue drift, one word: every README description is re-derived from the skill's own
    # frontmatter, so a paraphrase that "reads the same" is still a lie the gate can name.
    ("02_descriptions_and_mcp_columns_match_frontmatter",
     "README.md", lambda t: t.replace("or check whether a release actually shipped.",
                                      "or check whether a release shipped.", 1)),
    # Catalogue drift, one entry: a row with no skill behind it. A phantom row is a promise to the
    # reader that `install.py` cannot keep.
    ("01_table_matches_the_tree_in_both_directions",
     "README.md", lambda t: t.replace(
         "| `dfs-research` |",
         "| `dfs-ghost` | Does not exist. Use when you want a gate to fail. | — | — | — |\n"
         "| `dfs-research` |", 1)),
]


def failing_tests(workdir: pathlib.Path, gate: pathlib.Path) -> set[str]:
    env = dict(os.environ, DFS_SKILLS_DIR=str(workdir))
    proc = subprocess.run([sys.executable, str(workdir / gate.relative_to(REPO))],
                          capture_output=True, text=True, env=env)
    names = re.findall(r"^FAIL: (\S+)", proc.stderr, re.M)
    # unittest prints the method name ("test_rule_7_..."); keys here are rule names.
    return {n[len("test_"):] if n.startswith("test_") else n for n in names}


def fresh_copy(tmp: pathlib.Path, name: str) -> pathlib.Path:
    dest = tmp / name
    shutil.copytree(REPO, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return dest


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        baseline = failing_tests(fresh_copy(tmp, "baseline"), GATE)
        if baseline != KNOWN_RED_BASELINE:
            print(f"BASELINE MOVED: expected {sorted(KNOWN_RED_BASELINE)}, got {sorted(baseline)}")
            print("Update KNOWN_RED_BASELINE deliberately, not reflexively.")
            return 1
        print(f"baseline: {len(baseline)} known-red test(s) -> {sorted(baseline)}")

        # Every gate a probe targets must be green before mutation, or a probe can be "caught" by a
        # failure that was already there. Same assertion as above, per gate.
        for gate in sorted(set(GATE_OF.values()) - {GATE}):
            pre = failing_tests(fresh_copy(tmp, "pre_" + gate.stem), gate)
            if pre:
                print(f"BASELINE MOVED in {gate.name}: {sorted(pre)}")
                return 1
            print(f"baseline {gate.name}: green")

        missed = []
        for i, (expected, relpath, transform) in enumerate(MUTATIONS):
            copy = fresh_copy(tmp, f"mut{i}")
            target = copy / relpath
            original = target.read_text(encoding="utf-8")
            mutated = transform(original)
            if mutated is None:
                target.unlink()  # delete-the-file mutation
            elif mutated == original:
                # A transform that produces identical text injected NOTHING, so the gate cannot go
                # red for it and "caught" would be a lie. Report the vacuous probe as a miss.
                print(f"  [NO-OP] {expected} ({relpath}) — transform changed nothing")
                missed.append((expected, relpath))
                shutil.rmtree(copy, ignore_errors=True)
                continue
            else:
                target.write_text(mutated, encoding="utf-8")

            failed = failing_tests(copy, GATE_OF.get(expected, GATE))
            caught = expected in failed
            extra = sorted(failed - baseline - {expected})
            status = "CAUGHT" if caught else "MISSED"
            print(f"  [{status}] {expected} ({relpath})" + (f"  also: {extra}" if extra else ""))
            if not caught:
                missed.append((expected, relpath))
            shutil.rmtree(copy, ignore_errors=True)

    if missed:
        print(f"\n{len(missed)} rule(s) NOT enforced by the gate: {missed}")
        return 1
    print(f"\nAll {len(MUTATIONS)} injected defects were caught. The gate has teeth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
