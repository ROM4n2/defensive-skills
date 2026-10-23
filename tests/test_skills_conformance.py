#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conformance gate for the Defensive Skills tree — repo port, stdlib only.

Ported from the private vault-side gate of the same name (12 rules, 14 test methods). Two
deliberate divergences from the vault original:

1. Skill root: `DFS_SKILLS_DIR` env var, else this repo root. The vault copy defaults to
   `~/.cc-switch/skills`, which resolves to nothing in a public checkout.
2. No PyYAML. The vault copy does `import yaml`; a zero-dependency gate cannot, and the
   default `python` on the author machine does not have PyYAML installed at all, so the
   vault copy is not runnable there. Frontmatter is parsed with `re` (see parse_skill_file).

Rule 13 is this repo's own addition (the vault original stops at 12), so it has no upstream
counterpart: the ported rules above describe what a skill SAYS, and none of them notices an
on-demand file that no body ever points a reader at.

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

# The 24 shipped Defensive Skills. Declared, not derived: Rule 1 exists to catch a skill being
# silently added or dropped, which a disk-derived set can never notice.
# `dfs-agent-sdk` is deliberately NOT here: it vendors a THIRD-PARTY pi-agent SDK doc corpus
# (the `dg-piagent` skill from github.com/buchidonggua/dg-ai-notes; docs are CC-BY-SA-4.0) —
# not this author's work, and not published here. It still lives in the author's private
# skills tree, so the two trees intentionally differ — see scripts/README.md.
SKILL_NAMES = [
    "dfs-verify",
    "dfs-orchestrate",
    "dfs-maintain",
    "dfs-gate",
    "dfs",
    "dfs-adr",
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
    "dfs-upgrade",
]

BANNED_MARKETING_PATTERNS = [
    r"\(?priority\s+\d+\)?",
    r"#1\s+choice",
    r"best-in-class",
]

# Rule 3a. A description that only says what the skill DOES is the classic failure mode: the skill
# installs and then never fires, because selection keys off the trigger, not the feature list. So a
# description must carry an explicit trigger clause, and the cap is 320 (the spec allows 1024) —
# the always-loaded index stays cheap while leaving room for the clause. Note the deliberately loose
# marker regex: this asserts the clause is PRESENT and greppable, not that it is well-worded. There
# is no keyword-matching "trigger eval" here on purpose — that would be a fake-green proxy.
DESCRIPTION_MAX_CHARS = 320
TRIGGER_CLAUSE = re.compile(
    r"use when|use whenever|load when|when the user|when working|when asked|when you need",
    re.IGNORECASE,
)

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

# Rule 15: Progressive disclosure size budget constants
V040_DISCLOSURE_SKILLS = {
    "dfs-refactor",
    "dfs-tdd",
    "dfs-migrate",
    "dfs-gate",
    "dfs-release",
    "dfs-verify",
    "dfs-spark",
    "dfs-orchestrate",
    "dfs-review",
    "dfs-debug",
    "dfs-agent-sdk",
}
MAX_SKILL_MD_LINES_GLOBAL = 180
MAX_SKILL_MD_LINES_V040 = 120
MAX_SKILL_MD_BYTES_V040 = 8500

# Rule 8 exemptions — references to tooling that is deliberately NOT shipped, because it inspects
# the author's own knowledge base structure and would be wrong-by-default in any other one. Each
# entry is documented in scripts/README.md under "Optional integrations", and an entry that stops
# being referenced makes Rule 8 fail (see the rule's docstring): this is a declaration, not a mute.
OPTIONAL_SCRIPT_POINTERS = {
    "scripts/vault-healthcheck.py",
    "scripts/vault-inbox-triage.py",
}

# Rule 13 declarations — on-demand assets that are reached through a shipped PROGRAM rather than a
# markdown pointer in a body. Key: `<skill>/<references|templates>/<rel>`; value: the program that
# must actually name the file, relative to the skills root.
#
# The four `WORKMEMORY/` templates are read by `bootstrap.py` when it scaffolds a new repo, and the
# body routes the reader to that script rather than to the individual files. Requiring a body
# pointer for each would be a false positive, so each is declared instead.
#
# This is a declaration, not a mute, and it self-invalidates three ways (see the rule): the asset
# becoming body-routed, the asset leaving the tree, or the named program no longer mentioning it —
# each of those turns the declaration stale and fails Rule 13.
CODE_ROUTED_ASSETS = {
    "dfs-bootstrap/templates/workmemory/INDEX.md": "dfs-bootstrap/scripts/bootstrap.py",
    "dfs-bootstrap/templates/workmemory/PROJECT_OVERVIEW.md": "dfs-bootstrap/scripts/bootstrap.py",
    "dfs-bootstrap/templates/workmemory/PROTOCOL.md": "dfs-bootstrap/scripts/bootstrap.py",
    "dfs-bootstrap/templates/workmemory/work.log": "dfs-bootstrap/scripts/bootstrap.py",
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
    # 后缀白名单 MUST 含 json（公开树里有 `scripts/routing.example.json`），且末尾 MUST 带
    # 负向边界断言：否则 `routing.example.json` 会被截成 `routing.example.js`，报一个并不存在
    # 的文件（子串碰撞假阳性）。与 vault 侧同名闸门同步修正。
    raw = re.findall(
        r"scripts/(?:tests/)?[A-Za-z0-9_\-\.]+?\.(?:json|ps1|py|sh|js|ts|go)(?![A-Za-z0-9])",
        text,
    )
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


def _list_values(head: str, key: str) -> list[str]:
    """Parse a list declared either inline (`key: [a, b]`) or as a block (`key:` + `  - a`).

    Both shapes are real: this repo ships block lists (the open Agent Skills shape — a flow
    list is rejected by the spec's skills-ref validator), while DFS_SKILLS_DIR may point at a
    vault-side tree that still uses inline flow lists. Silent-empty is the dangerous outcome:
    an unparsed declaration would make Rules 7/9/11 pass vacuously. Loud beats silent.
    """
    inline = re.search(rf"(?m)^[ \t]*{re.escape(key)}:\s*\[(.*?)\]\s*$", head)
    if inline:
        return [s.strip().strip("\"'") for s in inline.group(1).split(",") if s.strip()]
    block = re.search(
        rf"(?m)^(?P<ind>[ \t]+){re.escape(key)}:[ \t]*\r?\n"
        rf"(?P<items>(?:[ \t]+-[ \t]+.+(?:\r?\n|$))+)",
        head,
    )
    if block:
        return [
            m.group(1).strip().strip("\"'")
            for m in re.finditer(r"(?m)^[ \t]+-[ \t]+(.+?)\s*$", block.group("items"))
        ]
    return []


def parse_skill_file(skill_dir: pathlib.Path) -> tuple[dict, str]:
    """Parse SKILL.md into a frontmatter dict and markdown body.

    ponytail: flat-regex parse of the fields the 14 rules consume. Ceiling: no anchors or
    arbitrary nesting beyond `metadata.hermes`; lists are inline-flow or block (see
    _list_values). Swap in PyYAML if the frontmatter convention outgrows that.
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
    # Post-2026-10 the flag lives under `metadata:` (2-space indent) per the Agent Skills
    # extension slot; the top-level form is still accepted for vault-side trees.
    frontmatter["disable-model-invocation"] = bool(
        re.search(r"""(?m)^(?:  )?disable-model-invocation:\s*["']?true["']?\s*$""", head)
    )
    hermes = frontmatter["metadata"]["hermes"]
    for key in ("mcp_tools", "related_skills"):
        values = _list_values(head, key)
        if values:
            hermes[key] = values
    return frontmatter, body


def resolve_context_pointer(
    skills_root: pathlib.Path, carrier: pathlib.Path, ptr: str
) -> pathlib.Path:
    """Where a `references/...` / `templates/...` pointer points, from the skill that carried it.

    A `dfs-<name>/...`-qualified pointer resolves against the skills root; a bare one resolves
    against the carrying skill. Rule 5 (does the target exist?) and Rule 13 (does anything point
    AT it?) must agree on this, so both resolve through here rather than keeping two copies that
    can drift apart.
    """
    if ptr.startswith("dfs/") or ptr.startswith("dfs-"):
        skill_name, _, subpath = ptr.partition("/")
        return skills_root / skill_name / subpath
    return carrier / ptr


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
    """14 rules across all DFS skills in this repo."""

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

    def test_rule_3a_description_has_trigger_clause(self):
        """Rule 3a: description carries an explicit trigger clause and stays <= 320 chars.

        Two independent failure modes are reported separately: a description with no trigger clause
        (the "installs but never fires" defect), and one over the length cap.
        """
        offenders = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            desc = str(fm.get("description", "")).strip()
            if not TRIGGER_CLAUSE.search(desc):
                offenders.append(
                    f"  - {sdir.name}: description has no trigger clause "
                    f"(expected a marker such as 'Use when ...')\n    Content: {desc!r}"
                )
            if len(desc) > DESCRIPTION_MAX_CHARS:
                offenders.append(
                    f"  - {sdir.name}: length {len(desc)} chars "
                    f"(> {DESCRIPTION_MAX_CHARS} limit by {len(desc) - DESCRIPTION_MAX_CHARS})\n"
                    f"    Content: {desc!r}"
                )
        if offenders:
            self.fail(
                f"Rule 3a violation: {len(offenders)} description(s) missing a trigger clause "
                f"or over the {DESCRIPTION_MAX_CHARS}-char limit:\n" + "\n".join(offenders)
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
        """Rule 4: router skill 'dfs' must carry the disable-model-invocation flag.

        Since 2026-10 the flag rides in `metadata` (`disable-model-invocation: "true"`), the
        Agent Skills extension slot, rather than a non-spec top-level key. The harness-neutral
        enforcement is the file-top banner pinned by test_harness_field_mapping.test_06.
        """
        router_dirs = [d for d in self.skill_dirs if d.name == "dfs"]
        self.assertTrue(router_dirs, "Router skill 'dfs' not found among skill directories")
        fm, _ = parse_skill_file(router_dirs[0])
        self.assertIs(
            fm.get("disable-model-invocation"), True,
            "Router skill 'dfs' must carry disable-model-invocation (metadata string \"true\" "
            f"or the legacy top-level key), got {fm.get('disable-model-invocation')!r}",
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
                target = resolve_context_pointer(self.skills_root, sdir, ptr)
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
        """Rule 6: no `~/.claude/agents/` hardcoding without a neutral fallback.

        Scope is SKILL.md + `templates/**.md` + `references/**.md`, matching Rules 8/10/11 — a
        Claude-only route is no safer for being written in a reference file than in the body. Until
        this was widened, the rule had zero subjects in the tree: the two skills that named the path
        moved their dispatch prose into `dfs/references/subagent-dispatch.md`, so the rule's stated
        intent was left unenforced exactly where the paths now live.

        The pairing is checked **per file**, not per skill. A neutral keyword three files away does
        not rescue a path hardcoded here — and per-file is what makes a probe possible at all, since
        the one reference that legitimately names the path also names `delegate_task`.
        """
        violations = []
        for sdir in self.skill_dirs:
            texts: dict[str, str] = {}
            skill_md = sdir / "SKILL.md"
            if skill_md.is_file():
                texts["SKILL.md"] = skill_md.read_text(encoding="utf-8", errors="replace")
            for sub in ("templates", "references"):
                sub_dir = sdir / sub
                if sub_dir.is_dir():
                    for f in sorted(sub_dir.rglob("*.md")):
                        texts[f"{sub}/{f.relative_to(sub_dir).as_posix()}"] = f.read_text(
                            encoding="utf-8", errors="replace"
                        )
            for origin, text in texts.items():
                if "~/.claude/agents" not in text and ".claude/agents" not in text:
                    continue
                has_fallback = (
                    "delegate_task" in text
                    or "neutral fallback" in text.lower()
                    or "runtime fallback" in text.lower()
                    or "runtime-neutral" in text.lower()
                    or "standard delegate" in text.lower()
                )
                if not has_fallback:
                    violations.append(
                        f"  - {sdir.name}/{origin}: hardcodes Claude agent paths (~/.claude/agents/) "
                        f"without a neutral fallback or standard delegate_task alternatives."
                    )
        if violations:
            self.fail(
                f"Rule 6 violation: {len(violations)} file(s) violate runtime neutrality:\n"
                + "\n".join(violations)
            )

    def test_rule_7_related_skills_resolve_to_real_skills(self):
        """Rule 7: every related_skills entry names a real skill; no entry is listed twice.

        The duplicate assertion is not cosmetic: a repeated entry is dead weight in the always-loaded
        index and no other rule would notice it (the list still parses and still resolves).
        """
        violations = []
        for sdir in self.skill_dirs:
            try:
                fm, _ = parse_skill_file(sdir)
            except Exception:
                continue
            related = extract_related_skills(fm)
            for ref in related:
                if ref in KNOWN_SKILL_NAMES or ref in EXTERNAL_SKILL_ALLOWLIST:
                    continue
                violations.append(
                    f"  - {sdir.name}: related_skills entry '{ref}' resolves to no skill on disk."
                )
            dups = sorted({r for r in related if related.count(r) > 1})
            if dups:
                violations.append(
                    f"  - {sdir.name}: related_skills lists {dups} more than once."
                )
        if violations:
            self.fail(
                f"Rule 7 violation: {len(violations)} dangling or duplicate related_skills "
                f"pointer(s):\n" + "\n".join(violations)
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

    def test_rule_13_on_demand_assets_are_routed_from_a_body(self):
        """Rule 13: every shipped `references/` + `templates/` asset is reachable from a body.

        Rules 1-12 all describe what a skill SAYS. None of them notices the opposite defect: a file
        that ships, costs bytes in the clone, and that no body ever points a reader at. Rule 5 is
        the same relation read the wrong way round — it checks that a pointer finds a file, never
        that a file is found by a pointer. Measured, not assumed: planting an unreferenced
        `dfs/references/orphan.md`, fixing the README's `refs×N` count and `git add`-ing it left
        all 12 rules green.

        Why `references/` and `templates/` and not `scripts/`: a script has its own reachability
        semantics (it is invoked, or imported by another script), so a "must be mentioned in prose"
        requirement would be wrong for a library module. Docs and templates have no such channel —
        prose is the only way one reaches them.

        Two ways to satisfy this: point at the file from a body, or declare it in
        `CODE_ROUTED_ASSETS` with the program that reads it. The declaration self-invalidates, so it
        cannot rot into a blanket mute.

        A skill whose frontmatter does not parse is out of scope for this rule: its body cannot be
        read, so it is impossible to tell "nothing points at these assets" from "I could not look".
        Rule 2 owns that failure. Reporting an orphan anyway would be a false allegation — it sends
        a developer to delete a good declaration — so the assets are skipped, and any declaration
        they carry is treated as seen rather than stale.
        """
        bodies: dict[str, str] = {}
        unreadable = set()
        for sdir in self.skill_dirs:
            try:
                _, bodies[sdir.name] = parse_skill_file(sdir)
            except Exception:
                unreadable.add(sdir.name)

        routed: set[tuple[str, str, str]] = set()
        for carrier, body in bodies.items():
            for ptr in extract_context_pointers(body):
                target = resolve_context_pointer(self.skills_root, self.skills_root / carrier, ptr)
                try:
                    rel = target.relative_to(self.skills_root)
                except ValueError:
                    continue
                parts = rel.parts
                if len(parts) >= 3 and parts[1] in ("references", "templates"):
                    # parts[0] is the owning skill; a cross-skill `dfs-x/...` pointer lands here too
                    routed.add((parts[0], parts[1], "/".join(parts[2:])))

        assets = []
        for sdir in self.skill_dirs:
            if sdir.name in unreadable:
                continue
            for sub in ("references", "templates"):
                sub_dir = sdir / sub
                if not sub_dir.is_dir():
                    continue
                for f in sorted(sub_dir.rglob("*")):
                    if f.is_file() and "__pycache__" not in f.parts:
                        assets.append((sdir.name, sub, "/".join(f.relative_to(sub_dir).parts)))

        violations = []
        seen_declared = set()
        for owner, sub, rel in assets:
            if (owner, sub, rel) in routed:
                continue
            key = f"{owner}/{sub}/{rel}"
            consumer_rel = CODE_ROUTED_ASSETS.get(key)
            if consumer_rel is None:
                violations.append(
                    f"  - {key}: no SKILL.md body points at it. Either reference it from a body, "
                    f"or declare its consumer in CODE_ROUTED_ASSETS."
                )
                continue
            seen_declared.add(key)
            consumer = self.skills_root / consumer_rel
            basename = pathlib.PurePosixPath(rel).name
            if not consumer.is_file():
                violations.append(
                    f"  - {key}: declared as read by '{consumer_rel}', which does not exist."
                )
            elif basename not in consumer.read_text(encoding="utf-8", errors="replace"):
                violations.append(
                    f"  - {key}: declared as read by '{consumer_rel}', but that program never "
                    f"mentions '{basename}' — the declaration is stale, remove it."
                )

        # Declarations belonging to an out-of-scope skill are not judged either way.
        in_scope = {k for k in CODE_ROUTED_ASSETS if k.split("/", 1)[0] not in unreadable}
        stale = sorted(in_scope - seen_declared)
        if stale:
            violations.append(
                f"  - stale declaration(s) in CODE_ROUTED_ASSETS: {stale}. Each of these is now "
                f"body-routed or no longer on disk, so the declaration is dead weight (and a mute "
                f"waiting to swallow a future orphan). Remove the entry."
            )
        if violations:
            self.fail(
                f"Rule 13 violation: {len(violations)} unreachable on-demand asset(s):\n"
                + "\n".join(violations)
            )

    def test_rule_14_claimed_counts_match_the_enumeration(self):
        """Rule 14: a heading claiming `<N>-<Stage|Step|Phase>` must enumerate exactly N.

        The first rule here to check **content** rather than structure, and the scope is deliberately
        the smallest defensible slice of it. Three real defects of this shape shipped past 13 green
        rules: `dfs-pipeline` headed "8-Stage" over nine stages, `dfs-review` "3-Step" over four, and
        `dfs-bootstrap` "3-Phase" over four (Phase 1, 2, 3.5, 4). A count in a heading is a claim
        about the text underneath it, and it is the one kind of claim a gate can check.

        What it CANNOT check, and does not pretend to: whether a description matches its body in
        meaning. "a design or plan" over a skill that audits code, or "0-to-1" over a skill whose
        Phase 1 includes a scoped tweak to existing code, are both invisible here. Those need a
        reader; this rule only catches the arithmetic.

        Deliberately same-noun: a `3-Stage` claim is compared against enumerated `Stage`s, so
        `dfs-exec` ("3-Stage" over `[Step 1..3]`) is skipped rather than judged — comparing across
        nouns would make the rule loose enough to miss a real mismatch. A claim with nothing to
        compare is skipped too (`dfs-migrate/templates/migration-plan-schema.md` says "5-Step" and
        enumerates none), because firing there would be a false positive on day one.

        Measured before writing it: 15 claims in the tree, 13 verifiable, 0 mismatches, and 0
        matches from mid-prose lines — so the pattern does not accuse ordinary sentences.
        """
        claim = re.compile(r"(?m)^#{1,6}[^\n]*?\b(\d+)[-\s](Stage|Step|Phase)\b", re.IGNORECASE)
        # An enumeration starts a line: a heading, or a boxed ledger row. Never mid-prose.
        enumerated = re.compile(
            r"(?m)^[ \t]*(?:#{1,6}[ \t]*)?(?:[│|][ \t]*)?[-*•]?[ \t]*"
            r"(Stage|Step|Phase)[ \t]+(\d+(?:\.\d+)?)\b",
            re.IGNORECASE,
        )

        violations = []
        for sdir in self.skill_dirs:
            texts: dict[str, str] = {}
            skill_md = sdir / "SKILL.md"
            if skill_md.is_file():
                texts["SKILL.md"] = skill_md.read_text(encoding="utf-8", errors="replace")
            for sub in ("templates", "references"):
                sub_dir = sdir / sub
                if sub_dir.is_dir():
                    for f in sorted(sub_dir.rglob("*.md")):
                        texts[f"{sub}/{f.relative_to(sub_dir).as_posix()}"] = f.read_text(
                            encoding="utf-8", errors="replace"
                        )
            for origin, text in texts.items():
                by_kind: dict[str, set[str]] = {}
                for kind, num in enumerated.findall(text):
                    by_kind.setdefault(kind.lower(), set()).add(num)
                for n_str, kind in claim.findall(text):
                    found = by_kind.get(kind.lower(), set())
                    if not found or len(found) == int(n_str):
                        continue  # nothing to compare, or they agree
                    violations.append(
                        f"  - {sdir.name}/{origin}: a heading claims {n_str}-{kind} but the file "
                        f"enumerates {sorted(found)} ({len(found)} of them)."
                    )
        if violations:
            self.fail(
                f"Rule 14 violation: {len(violations)} heading count(s) that the text "
                f"contradicts:\n" + "\n".join(violations)
            )

    def test_rule_15_skill_md_progressive_disclosure_budget(self):
        """Rule 15: Progressive disclosure size budget for SKILL.md.

        All skills must stay <= 180 lines.
        Skills refactored for v0.4.0 3-tier progressive disclosure must stay
        <= 120 lines and <= 8,500 bytes. Extended checklists, examples, and
        catalogs belong in references/<topic>.md (Tier 3).
        """
        violations = []
        for sdir in self.skill_dirs:
            skill_md = sdir / "SKILL.md"
            if not skill_md.is_file():
                continue
            content = skill_md.read_bytes()
            lines = content.decode("utf-8", errors="replace").splitlines()
            line_count = len(lines)
            byte_count = len(content)

            if line_count > MAX_SKILL_MD_LINES_GLOBAL:
                violations.append(
                    f"  - {sdir.name}/SKILL.md: {line_count} lines (> global limit {MAX_SKILL_MD_LINES_GLOBAL})"
                )

            if sdir.name in V040_DISCLOSURE_SKILLS:
                if line_count > MAX_SKILL_MD_LINES_V040:
                    violations.append(
                        f"  - {sdir.name}/SKILL.md: {line_count} lines (> v0.4.0 limit {MAX_SKILL_MD_LINES_V040})"
                    )
                if byte_count > MAX_SKILL_MD_BYTES_V040:
                    violations.append(
                        f"  - {sdir.name}/SKILL.md: {byte_count} bytes (> v0.4.0 limit {MAX_SKILL_MD_BYTES_V040})"
                    )
        if violations:
            self.fail(
                f"Rule 15 violation: {len(violations)} SKILL.md file(s) exceed progressive disclosure budget:\n"
                + "\n".join(violations)
            )


if __name__ == "__main__":
    unittest.main()
