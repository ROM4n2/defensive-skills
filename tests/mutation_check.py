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
     "dfs/SKILL.md", lambda t: t.replace("disable-model-invocation: true",
                                         "disable-model-invocation: false", 1)),
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
    ("rule_7_related_skills_resolve_to_real_skills",
     "dfs-handoff/SKILL.md", lambda t: re.sub(
         r"(?m)^(\s*related_skills:).*$", r"\1 [dfs-does-not-exist]", t, count=1)),
    # A repeated entry still RESOLVES, so the dangling check stays silent and only the no-duplicate
    # assertion can catch it. The appended name is a real skill on purpose.
    ("rule_7_related_skills_resolve_to_real_skills",
     "dfs-handoff/SKILL.md", lambda t: re.sub(
         r"(?m)^(\s*related_skills:\s*\[)([^\]]*)\]", r"\1\2, dfs-save]", t, count=1)),
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
    # A block-style list must fail loudly, not parse as an empty (vacuous-pass) declaration.
    # Attribution note: parse_skill_file RAISES on block lists; Rule 2 owns parse errors, while
    # Rules 9/11 skip unparseable skills (`except Exception: continue`). So the suite goes red via
    # rule_2, not rule_9 — the defect is caught, it is just reported by the parse guard.
    ("rule_2_frontmatter_schema",
     "dfs-adr/SKILL.md", lambda t: t.replace("    related_skills:",
                                             "    mcp_tools:\n      - search_vault\n    related_skills:", 1)),
]


def failing_tests(workdir: pathlib.Path) -> set[str]:
    env = dict(os.environ, DFS_SKILLS_DIR=str(workdir))
    proc = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True, env=env)
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

        baseline = failing_tests(fresh_copy(tmp, "baseline"))
        if baseline != KNOWN_RED_BASELINE:
            print(f"BASELINE MOVED: expected {sorted(KNOWN_RED_BASELINE)}, got {sorted(baseline)}")
            print("Update KNOWN_RED_BASELINE deliberately, not reflexively.")
            return 1
        print(f"baseline: {len(baseline)} known-red test(s) -> {sorted(baseline)}")

        missed = []
        for i, (expected, relpath, transform) in enumerate(MUTATIONS):
            copy = fresh_copy(tmp, f"mut{i}")
            target = copy / relpath
            if transform(target.read_text(encoding="utf-8")) is None:
                target.unlink()  # delete-the-file mutation
            else:
                target.write_text(transform(target.read_text(encoding="utf-8")), encoding="utf-8")

            failed = failing_tests(copy)
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
