#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conformance gate for the Defensive Skills tree — repo port, stdlib only.

Ported from `D:\\Obsidian\\Coding\\scripts\\tests\\test_dfs_skills_conformance.py`
(12 rules, 14 test methods). Two deliberate divergences from the vault original:

1. Skill root: `DFS_SKILLS_DIR` env var, else this repo root. The vault copy defaults to
   `~/.cc-switch/skills`, which resolves to nothing in a public checkout.
2. No PyYAML. The vault copy does `import yaml`; a zero-dependency gate cannot, and the
   default `python` on the author machine does not have PyYAML installed at all, so the
   vault copy is not runnable there. Frontmatter is parsed with `re` (see parse_skill_file).

Rule 8 resolves `scripts/...` against repo-local roots only — never the author's Vault. That is
intentional: a script reference that only resolves on the author's machine is a publication
blocker, so it MUST fail here rather than pass by borrowing a path from outside the repo.

Rule 12's scope is deliberately narrow (vault/MCP family + edit-distance <= 2 typos); a generic
`bogus_tool()` is not caught. That is a trade-off, not an oversight — see the vault original.

Every rule was mutation-tested in the vault original. Re-run the mutation check after editing
this file, or a green run means nothing:

    cp -r . "$TMPDIR/dfs-mut" && rm "$TMPDIR/dfs-mut/.git" -rf
    sed -i 's/related_skills: \\[dfs-save, dfs-exec\\]/related_skills: [dfs-does-not-exist]/' \\
        "$TMPDIR/dfs-mut/dfs-handoff/SKILL.md"
    DFS_SKILLS_DIR="$TMPDIR/dfs-mut" python tests/test_skills_conformance.py   # must FAIL
"""

import os
import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# The 24 Defensive Skills. Declared, not derived: Rule 1 exists to catch a skill being
# silently added or dropped, which a disk-derived set can never notice.
SKILL_NAMES = [
    "dfs",
    "dfs-adr",
    "dfs-agent-sdk",
    "dfs-bootstrap",
    "dfs-debug",
    "dfs-exec",
    "dfs-grill",
    "dfs-handoff",
    "dfs-inbox-consolidate",
    "dfs-incident",
    "dfs-interview",
    "dfs-migrate",
    "dfs-onboard",
    "dfs-perf",
    "dfs-pipeline",
    "dfs-plan",
    "dfs-refactor",
    "dfs-release",
    "dfs-research",
    "dfs-review",
    "dfs-save",
    "dfs-spark",
    "dfs-tdd",
    "dfs-team",
]

BANNED_MARKETING_PATTERNS = [
    r"\(?priority\s+\d+\)?",
    r"#1\s+choice",
    r"best-in-class",
]

# Rule 9: canonical tool names exposed by the `coding-vault-search` MCP server.
KNOWN_MCP_TOOLS = [
    "omni_search",
    "search_vault",
    "get_note",
    "get_code_template",
    "get_rule_snippet",
    "list_standards",
    "save_inbox_draft",
    "promote_inbox_draft",
    "vault_proactive_scan",
]

# Rule 12: tools the agent runtime or plain prose legitimately calls.
KNOWN_NATIVE_TOOLS = {
    "read_file", "write_file", "patch", "terminal", "search_files", "delegate_task",
    "clarify", "skill_view", "skills_list", "skill_manage", "memory", "fact_store",
    "fact_feedback", "browser_exec", "js", "fill_input", "click_at_xy", "page_info",
    "new_tab", "goto_url", "wait_for_load", "capture_screenshot", "cdp", "ensure_real_tab",
    "process", "todo_list", "execute_code", "vision_analyze", "tool_search",
    "tool_describe", "tool_call", "session_search", "cronjob",
    "run_command", "list_tables", "query_sqlite", "describe_table", "check_port",
    "get_system_resources", "get_wsl_docker_status", "kill_port_process",
    "query_docs", "resolve_library_id", "bing_search_to_markdown", "context7", "fetch",
    "os_path_join", "os_path_exists", "os_getcwd", "re_search", "re_sub", "re_compile",
    "re_findall", "json_dumps", "json_loads", "subprocess_run", "pathlib_path",
    "datetime_now", "str_replace", "sys_exit", "set_up", "set_visible", "add_route",
}

KNOWN_SKILL_NAMES = set(SKILL_NAMES)
# Names legitimately outside the DFS suite (external skills referenced by related_skills).
EXTERNAL_SKILL_ALLOWLIST = {"systematic-debugging", "test-driven-development"}

# Rule 8 exemptions — references to tooling that is deliberately NOT shipped, because it inspects
# the author's own knowledge base structure and would be wrong-by-default in any other one. Each
# entry is documented in scripts/README.md under "Optional integrations", and an entry that stops
# being referenced makes Rule 8 fail (see the rule's docstring): this is a declaration, not a mute.
OPTIONAL_SCRIPT_POINTERS = {
    "scripts/vault-healthcheck.py",
    "scripts/vault-inbox-triage.py",
    "scripts/bootstrap.ps1",
}


def skills_root() -> pathlib.Path:
    """Skill root: `DFS_SKILLS_DIR` if set and real, else this repo root."""
    env = os.environ.get("DFS_SKILLS_DIR")
    if env and pathlib.Path(env).is_dir():
        return pathlib.Path(env)
    return _REPO_ROOT


def get_skill_dirs() -> list[pathlib.Path]:
    root = skills_root()
    return [root / name for name in SKILL_NAMES]


def get_script_roots() -> list[pathlib.Path]:
    """Repo-local directories where a referenced `scripts/<file>` may live.

    `root/scripts` is the shared-script home: skills invoke `{vault_root}/scripts/<file>`, and the
    shipped engines live at `<repo>/scripts/`. The upstream gate resolved these through a hardcoded
    absolute path on the author's machine; that root is deliberately NOT ported — a reference
    resolves only if the file physically ships in this repo.
    """
    root = skills_root()
    roots = [root, root / "scripts"]
    for sdir in sorted(root.iterdir()):
        if sdir.is_dir() and (sdir.name == "dfs" or sdir.name.startswith("dfs-")):
            roots.append(sdir)
            roots.append(sdir / "scripts")
    return roots


def extract_script_pointers(text: str) -> set[str]:
    """Extract `scripts/<name>.<ext>` and `scripts/tests/<name>.py` references."""
    raw = re.findall(r"scripts/(?:tests/)?[A-Za-z0-9_\-\.]+\.(?:py|sh|ps1|js|ts|go)", text)
    return {p.rstrip(".,;:)]}\"'`") for p in raw if p}


def extract_mcp_contract(frontmatter: dict) -> list[str]:
    meta = frontmatter.get("metadata") or {}
    if not isinstance(meta, dict):
        return []
    hermes_meta = meta.get("hermes") or {}
    if not isinstance(hermes_meta, dict):
        return []
    declared = hermes_meta.get("mcp_tools") or []
    if isinstance(declared, str):
        return [declared]
    if isinstance(declared, list):
        return [str(t) for t in declared]
    return []


def extract_related_skills(frontmatter: dict) -> list[str]:
    meta = frontmatter.get("metadata") or {}
    if not isinstance(meta, dict):
        return []
    hermes_meta = meta.get("hermes") or {}
    if not isinstance(hermes_meta, dict):
        return []
    related = hermes_meta.get("related_skills") or []
    if isinstance(related, str):
        return [related]
    if isinstance(related, list):
        return [str(r) for r in related]
    return []


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _inline_list(head: str, key: str) -> list[str]:
    """Parse `key: [a, b]`. A block-style list raises instead of parsing as empty.

    Silent-empty is the dangerous outcome: an unparsed `mcp_tools` block would make Rule 9
    pass vacuously. Loud beats silent.
    """
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*\[(.*?)\]\s*$", head)
    if match:
        return [s.strip().strip("\"'") for s in match.group(1).split(",") if s.strip()]
    if re.search(rf"(?m)^\s*{re.escape(key)}:\s*$", head):
        raise ValueError(
            f"frontmatter key '{key}' uses a block-style list; this stdlib parser supports "
            f"only inline flow lists (`{key}: [a, b]`)"
        )
    return []


def parse_skill_file(skill_dir: pathlib.Path) -> tuple[dict, str]:
    """Parse SKILL.md into a frontmatter dict and markdown body.

    ponytail: flat-regex parse of the five fields the 12 rules consume. Ceiling: no nested
    structures, anchors, or block lists beyond what _inline_list raises on. Swap in PyYAML
    if the frontmatter convention outgrows `key: value` + inline flow lists.
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")
    content = skill_file.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError(f"SKILL.md in {skill_dir.name} does not start with frontmatter '---'")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"SKILL.md in {skill_dir.name} has unclosed frontmatter '---'")
    head, body = parts[1], parts[2]

    frontmatter: dict = {"metadata": {"hermes": {}}}
    for key in ("name", "description"):
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", head)
        if match:
            frontmatter[key] = _unquote(match.group(1))
    frontmatter["disable-model-invocation"] = bool(
        re.search(r"(?m)^disable-model-invocation:\s*true\s*$", head)
    )
    hermes = frontmatter["metadata"]["hermes"]
    for key in ("mcp_tools", "related_skills"):
        values = _inline_list(head, key)
        if values:
            hermes[key] = values
    return frontmatter, body


def extract_context_pointers(text: str) -> set[str]:
    """`templates/<file>` / `references/<file>`, plain or `dfs[-<name>]/` qualified."""
    pattern = r"(?:dfs(?:-[a-z0-9\-]+)?/)?(?:templates|references)/[A-Za-z0-9_\-\./]+"
    raw_matches = re.findall(pattern, text)
    cleaned_pointers = set()
    for m in raw_matches:
        cleaned = re.sub(r"[\),;:\"'`\]]+$", "", m)
        if cleaned.endswith("."):
            cleaned = cleaned[:-1]
        if cleaned:
            cleaned_pointers.add(cleaned)
    return cleaned_pointers


class TestSkillsConformance(unittest.TestCase):
    """12 rules across all DFS skills in this repo."""

    @classmethod
    def setUpClass(cls):
        cls.skill_dirs = get_skill_dirs()
        cls.skills_root = skills_root()

    def test_rule_1_every_skill_dir_contains_skill_md(self):
        """Rule 1: Every skill dir must exist and contain a valid, non-empty SKILL.md."""
        expected_total = len(SKILL_NAMES)
        self.assertEqual(
            len(self.skill_dirs), expected_total,
            f"Expected exactly {expected_total} Defensive Skills, found {len(self.skill_dirs)}",
        )
        missing = []
        for sdir in self.skill_dirs:
            if not sdir.is_dir():
                missing.append(f"Directory missing: {sdir}")
                continue
            skill_file = sdir / "SKILL.md"
            if not skill_file.is_file():
                missing.append(f"SKILL.md missing: {skill_file}")
                continue
            if skill_file.stat().st_size == 0:
                missing.append(f"SKILL.md is empty: {skill_file}")
        self.assertEqual(missing, [], "Rule 1 violations:\n" + "\n".join(missing))

    def test_rule_2_frontmatter_schema(self):
        """Rule 2: Frontmatter parses, has non-empty 'name' and 'description'."""
        schema_errors = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception as e:
                schema_errors.append(f"  - {sdir.name}: failed to parse SKILL.md: {e}")
                continue
            name = fm.get("name")
            if not name or not isinstance(name, str):
                schema_errors.append(f"  - {sdir.name}: missing or invalid 'name' in frontmatter")
            elif name != sdir.name:
                schema_errors.append(
                    f"  - {sdir.name}: frontmatter name '{name}' does not match directory name '{sdir.name}'"
                )
            desc = fm.get("description")
            if not desc or not isinstance(desc, str):
                schema_errors.append(f"  - {sdir.name}: missing or invalid 'description' in frontmatter")
        self.assertEqual(schema_errors, [], f"Rule 2 violations ({len(schema_errors)} skills):\n" + "\n".join(schema_errors))

    def test_rule_3_description_length_under_60_chars(self):
        """Rule 3a: description length <= 60 chars."""
        offenders = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            desc = str(fm.get("description", "")).strip()
            if len(desc) > 60:
                offenders.append(
                    f"  - {sdir.name}: length {len(desc)} chars (> 60 limit by {len(desc) - 60})\n"
                    f"    Content: {desc!r}"
                )
        if offenders:
            self.fail(
                f"Rule 3a violation: {len(offenders)} skill(s) exceed the 60-character description limit:\n"
                + "\n".join(offenders)
            )

    def test_rule_3_description_period_termination(self):
        """Rule 3b: description must end with '.'."""
        offenders = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            desc = str(fm.get("description", "")).strip()
            if not desc.endswith("."):
                offenders.append(
                    f"  - {sdir.name}: ends with {desc[-1:] if desc else '<empty>'!r} instead of '.'\n"
                    f"    Content: {desc!r}"
                )
        if offenders:
            self.fail(
                f"Rule 3b violation: {len(offenders)} skill(s) description do not end with a period:\n"
                + "\n".join(offenders)
            )

    def test_rule_3_description_no_banned_marketing_phrases(self):
        """Rule 3c: description must not contain banned marketing phrases."""
        offenders = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            desc = str(fm.get("description", "")).strip()
            found = [m.group(0) for p in BANNED_MARKETING_PATTERNS
                     for m in [re.search(p, desc, re.IGNORECASE)] if m]
            if found:
                offenders.append(f"  - {sdir.name}: banned phrase(s) {found}\n    Content: {desc!r}")
        if offenders:
            self.fail(
                f"Rule 3c violation: banned marketing phrases in {len(offenders)} description(s):\n"
                + "\n".join(offenders)
            )

    def test_rule_4_router_disable_model_invocation(self):
        """Rule 4: router skill 'dfs' must set 'disable-model-invocation: true'."""
        router_dirs = [d for d in self.skill_dirs if d.name == "dfs"]
        self.assertTrue(router_dirs, "Router skill 'dfs' not found among skill directories")
        fm, _ = parse_skill_file(router_dirs[0])
        self.assertIs(
            fm.get("disable-model-invocation"), True,
            f"Router skill 'dfs' must have 'disable-model-invocation: true', got {fm.get('disable-model-invocation')!r}",
        )

    def test_rule_5_context_pointers_resolve_physically(self):
        """Rule 5: templates/ and references/ pointers must resolve on disk."""
        unresolved = []
        for sdir in self.skill_dirs:
            try:
                _, body = parse_skill_file(sdir)
            except Exception:
                continue
            for ptr in sorted(extract_context_pointers(body)):
                if ptr.startswith("dfs/") or ptr.startswith("dfs-"):
                    skill_name, _, subpath = ptr.partition("/")
                    target = self.skills_root / skill_name / subpath
                else:
                    target = sdir / ptr
                if not target.exists():
                    unresolved.append(
                        f"  - {sdir.name}: references '{ptr}', but '{target}' does not exist on disk."
                    )
        if unresolved:
            self.fail(
                f"Rule 5 violation: {len(unresolved)} unresolved context pointer(s):\n"
                + "\n".join(unresolved)
            )

    def test_rule_6_runtime_neutrality(self):
        """Rule 6: no ~/.claude/agents/ hardcoding without a neutral fallback."""
        violations = []
        for sdir in self.skill_dirs:
            try:
                _, body = parse_skill_file(sdir)
            except Exception:
                continue
            if "~/.claude/agents" in body or ".claude/agents" in body:
                has_fallback = (
                    "delegate_task" in body
                    or "neutral fallback" in body.lower()
                    or "runtime fallback" in body.lower()
                    or "runtime-neutral" in body.lower()
                    or "standard delegate" in body.lower()
                )
                if not has_fallback:
                    violations.append(
                        f"  - {sdir.name}: hardcodes Claude agent paths (~/.claude/agents/) "
                        f"without neutral fallback or standard delegate_task alternatives."
                    )
        if violations:
            self.fail(
                f"Rule 6 violation: {len(violations)} skill(s) violate runtime neutrality:\n"
                + "\n".join(violations)
            )

    def test_rule_7_related_skills_resolve_to_real_skills(self):
        """Rule 7: every related_skills entry names a real skill or allowlisted external one."""
        violations = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            for ref in extract_related_skills(fm):
                if ref in KNOWN_SKILL_NAMES or ref in EXTERNAL_SKILL_ALLOWLIST:
                    continue
                violations.append(
                    f"  - {sdir.name}: related_skills entry '{ref}' resolves to no skill on disk."
                )
        if violations:
            self.fail(
                f"Rule 7 violation: {len(violations)} dangling related_skills pointer(s):\n"
                + "\n".join(violations)
            )

    def test_rule_8_script_pointers_resolve_physically(self):
        """Rule 8: every scripts/<file> reference must exist in-repo. Never borrow the Vault.

        Exemptions are narrow and self-invalidating: `OPTIONAL_SCRIPT_POINTERS` names references to
        deliberately unshipped tooling (documented in scripts/README.md), and the rule FAILS if an
        exempted pointer stops being referenced anywhere — so the list cannot rot into a blanket
        mute that silently swallows future dangling references.
        """
        script_roots = get_script_roots()
        unresolved = []
        seen_optional = set()
        for sdir in self.skill_dirs:
            try:
                _, body = parse_skill_file(sdir)
            except Exception:
                continue
            texts = {"SKILL.md": body}
            for sub in ("templates", "references"):
                sub_dir = sdir / sub
                if sub_dir.is_dir():
                    for f in sorted(sub_dir.rglob("*.md")):
                        texts[f"{sub}/{f.relative_to(sub_dir).as_posix()}"] = f.read_text(encoding="utf-8")
            for origin, text in texts.items():
                for line in text.splitlines():
                    if "upstream" in line.lower():
                        continue
                    for ptr in sorted(extract_script_pointers(line)):
                        if ptr in OPTIONAL_SCRIPT_POINTERS:
                            seen_optional.add(ptr)
                            continue
                        rel = ptr[len("scripts/"):] if ptr.startswith("scripts/") else ptr
                        candidates = [sdir / ptr, sdir / rel]
                        for root in script_roots:
                            candidates.append(root / rel)
                            candidates.append(root / pathlib.Path(rel).name)
                        if not any(c.is_file() for c in candidates):
                            unresolved.append(
                                f"  - {sdir.name}/{origin}: references '{ptr}', but no such file "
                                f"exists anywhere in the repo."
                            )
        stale = sorted(OPTIONAL_SCRIPT_POINTERS - seen_optional)
        if stale:
            unresolved.append(
                "  - stale exemption(s) in OPTIONAL_SCRIPT_POINTERS, no skill references them any "
                f"more: {stale}. Remove the entry (and its README paragraph)."
            )
        if unresolved:
            self.fail(
                f"Rule 8 violation: {len(unresolved)} dangling script reference(s):\n"
                + "\n".join(unresolved)
            )

    def test_rule_9_mcp_contract_tools_are_canonical(self):
        """Rule 9: declared mcp_tools must name canonical coding-vault-search tools only."""
        violations = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            for tool in extract_mcp_contract(fm):
                if tool not in KNOWN_MCP_TOOLS:
                    violations.append(
                        f"  - {sdir.name}: declares MCP tool '{tool}' not exposed by the "
                        f"coding-vault-search server. Canonical: {sorted(KNOWN_MCP_TOOLS)}"
                    )
        if violations:
            self.fail(
                f"Rule 9 violation: {len(violations)} non-canonical MCP tool declaration(s):\n"
                + "\n".join(violations)
            )

    def test_rule_10_no_hardcoded_absolute_vault_paths(self):
        """Rule 10: no hardcoded absolute Obsidian Vault path; use {vault_root} / env vars."""
        pattern = re.compile(r"[A-Za-z]:[\\/]+Obsidian[\\/][A-Za-z0-9_.\-]+", re.IGNORECASE)
        violations = []
        for sdir in self.skill_dirs:
            texts = {}
            skill_md = sdir / "SKILL.md"
            if skill_md.is_file():
                texts["SKILL.md"] = skill_md.read_text(encoding="utf-8")
            for sub in ("templates", "references"):
                sub_dir = sdir / sub
                if sub_dir.is_dir():
                    for f in sorted(sub_dir.rglob("*.md")):
                        texts[f"{sub}/{f.relative_to(sub_dir).as_posix()}"] = f.read_text(encoding="utf-8")
            for origin, text in texts.items():
                for lineno, line in enumerate(text.splitlines(), 1):
                    for m in pattern.finditer(line):
                        violations.append(
                            f"  - {sdir.name}/{origin}:{lineno}: hardcodes absolute vault path "
                            f"'{m.group(0)}'. Use '{{vault_root}}/...' or $WIKI_PATH instead."
                        )
        if violations:
            self.fail(
                f"Rule 10 violation: {len(violations)} hardcoded absolute vault path(s):\n"
                + "\n".join(violations)
            )

    def test_rule_11_declared_mcp_contract_covers_actual_usage(self):
        """Rule 11: every canonical MCP tool invoked in a body must be declared in mcp_tools."""
        usage_pattern = re.compile(r"`(" + "|".join(KNOWN_MCP_TOOLS) + r")\s*\(")
        violations = []
        for sdir in self.skill_dirs:
            try:
                fm, body = parse_skill_file(sdir)
            except Exception:
                continue
            declared = set(extract_mcp_contract(fm))
            used = set(usage_pattern.findall(body))
            for sub in ("templates", "references"):
                sub_dir = sdir / sub
                if sub_dir.is_dir():
                    for f in sorted(sub_dir.rglob("*.md")):
                        used |= set(usage_pattern.findall(f.read_text(encoding="utf-8")))
            for tool in sorted(used - declared):
                violations.append(
                    f"  - {sdir.name}: body invokes '{tool}(...)' but frontmatter "
                    f"`metadata.hermes.mcp_tools` does not declare it."
                )
        if violations:
            self.fail(
                f"Rule 11 violation: {len(violations)} undeclared MCP tool usage(s):\n"
                + "\n".join(violations)
            )

    def test_rule_12_vault_mcp_call_sites_are_canonical(self):
        """Rule 12: vault/MCP-shaped call sites must be canonical; near-miss typos rejected."""
        call_site = re.compile(r"`([a-z][a-z0-9_]*)\s*\(")
        family = re.compile(r"(_vault$|^vault_|_inbox_|^omni_|_standards$|rule_snippet|code_template)")
        fenced = re.compile(r"```.*?```", re.DOTALL)
        canonical = set(KNOWN_MCP_TOOLS)

        def close_to_canonical(name: str) -> str | None:
            for c in sorted(canonical):
                if name == c:
                    continue
                if abs(len(name) - len(c)) > 2:
                    continue
                prev = list(range(len(c) + 1))
                for i, ch_a in enumerate(name, 1):
                    cur = [i]
                    for j, ch_b in enumerate(c, 1):
                        cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ch_a != ch_b)))
                    prev = cur
                if prev[-1] <= 2:
                    return c
            return None

        violations = []
        for sdir in self.skill_dirs:
            try:
                _, body = parse_skill_file(sdir)
            except Exception:
                continue
            texts = {"SKILL.md": body}
            for sub in ("templates", "references"):
                sub_dir = sdir / sub
                if sub_dir.is_dir():
                    for f in sorted(sub_dir.rglob("*.md")):
                        texts[f"{sub}/{f.relative_to(sub_dir).as_posix()}"] = f.read_text(encoding="utf-8")
            for origin, text in texts.items():
                prose = fenced.sub("", text)
                for name in sorted(set(call_site.findall(prose))):
                    if name in canonical or name in KNOWN_NATIVE_TOOLS:
                        continue
                    near = close_to_canonical(name)
                    if near is not None:
                        violations.append(
                            f"  - {sdir.name}/{origin}: calls `{name}(...)` — near-miss typo of "
                            f"canonical MCP tool '{near}'."
                        )
                    elif family.search(name):
                        violations.append(
                            f"  - {sdir.name}/{origin}: calls `{name}(...)` — vault/MCP-shaped name "
                            f"that is not a canonical tool."
                        )
        if violations:
            self.fail(
                f"Rule 12 violation: {len(violations)} non-canonical vault/MCP call site(s):\n"
                + "\n".join(violations)
            )


if __name__ == "__main__":
    unittest.main()
