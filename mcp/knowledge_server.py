#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Knowledge-base MCP server for the Defensive Skills (DFS) suite.

Stdio JSON-RPC, standard library only. Ported from the author's private
`vault_search_mcp.py` (849 lines, which shelled out to two private 1100/660-line helper
scripts). The *tool contract* is ported verbatim — the nine canonical tool names and their
argument schemas are what `metadata.hermes.mcp_tools` declares and Conformance Rule 9 checks,
so they MUST NOT drift. The *backends* are reimplemented here against a configurable knowledge
root, so this file has no dependency on the author's machine.

ponytail: ceilings kept deliberately, each with its upgrade path —
  * `search_vault` is a weighted keyword/tag/heading scorer, not the original's BM25 + 1-hop
    graph retriever. Adequate for the note-scale corpora this targets; drop in a real ranker
    if corpora grow past ~10k notes.
  * `omni_search`'s L0 rung names the harness's own code search instead of probing for a
    specific `codegraph` binary — harness-agnostic and one less private tool to depend on.
  * `vault_proactive_scan` is a regex TODO/FIXME/HACK/debt scanner over source files, not an
    AST analyser with ROI scoring.

Layout is configurable, not assumed: see `knowledge.json` / DEFAULT_LAYOUT below.
Root is resolved by the documented contract: flag -> env -> upward search -> **drafts-only mode**
(`degraded_root()`), never a hardcoded absolute path, because a stranger has no such path. In
drafts-only mode `save_inbox_draft` still works and lands in a local, self-describing drop box;
every retrieval tool refuses out loud instead of reporting an empty corpus, because "nothing
found" and "no knowledge base wired up" must never look the same.

Register in a harness MCP config as:
    {"command": "python", "args": ["<repo>/mcp/knowledge_server.py", "--root", "<kb root>"]}
"""

import json
import os
import pathlib
import re
import sys
import traceback
from datetime import date
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SERVER_NAME = "coding-vault-search"
SERVER_VERSION = "3.0.0"

# ---------------------------------------------------------------------------
# Layout: every directory name the tools touch is configurable.
# Defaults mirror the layout the DFS skills were written against.
# ---------------------------------------------------------------------------
DEFAULT_LAYOUT: Dict[str, Any] = {
    "content_dirs": [
        "00-MOC", "01-Rules", "02-Fundamentals", "03-Languages", "04-Systems", "05-Tools",
        "06-Sources", "07-Academics", "08-Projects", "09-Career", "10-Daily", "99-Inbox",
        "Templates",
    ],
    "rules_dir": "01-Rules",
    "languages_dir": "03-Languages",
    "career_dir": "09-Career",
    "inbox_dir": "99-Inbox",
    "code_template_dir": "Templates/code",
    "prompts_dir": "05-Tools/Subagents",
}
CONFIG_FILENAME = "knowledge.json"

# Tier 3 of the root contract: no knowledge base at all. Saving a draft is the one operation that
# still makes sense, so it must not be blocked behind knowledge-base setup — but a drop box is not
# a knowledge base, so retrieval stays off and says why.
DROPDIR_ENV = "DFS_INBOX"
DROPDIR_NAME = ".dfs-inbox"
DROPDIR_MARKER = "README.md"
DEGRADED_TOOLS = frozenset({"save_inbox_draft"})
DROPDIR_README = """# DFS draft drop box

No knowledge base was configured, so `save_inbox_draft` wrote drafts here instead of failing.

**What this is**: a plain folder of markdown drafts saved by the Defensive Skills. It is *not* a
knowledge base. Retrieval tools (`search_vault`, `omni_search`, `get_note`, ...) stay disabled
until a root is configured, because searching this folder would answer "nothing found" when the
truth is "no knowledge base is wired up".

**How to leave this state** — any one is enough:

* `export WIKI_PATH=/path/to/your/knowledge/base` (or `OBSIDIAN_VAULT_PATH`)
* register this server with `--root /path/to/your/knowledge/base`
* `export DFS_INBOX=/some/stable/dir` — moves this drop box, e.g. out of a project directory

**How to promote what is already here**: once a root is configured, call `promote_inbox_draft` per
draft, or let the consolidator file them:

    python <repo>/scripts/vault-inbox-consolidate.py --inbox <this folder> --vault-path <your root> --execute

This file is a marker. The consolidator skips it and so should `promote_inbox_draft`.
"""

# Directories never scanned: tool assets, VCS, and harness state.
SKIP_DIR_NAMES = {".git", ".obsidian", ".claude", ".venv", "node_modules", "__pycache__", "scripts"}


class LayoutError(RuntimeError):
    """Raised when no usable knowledge root can be resolved."""


def resolve_root(explicit: Optional[str] = None) -> pathlib.Path:
    """Resolve the knowledge root: explicit flag -> env -> upward search -> hard failure.

    Mirrors `dfs/references/vault-root-resolution.md` Tier 1/2. There is deliberately no
    hardcoded Tier 3 path: the vault copy's Tier 3 was an absolute path on the author's machine,
    which for anyone else is a silent wrong answer. Failing loudly here is the feature, and the
    caller turns that failure into the drop box below — the same "degrade, but never silently"
    shape the skills use.
    """
    if explicit:
        root = pathlib.Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise LayoutError(f"--root does not exist or is not a directory: {root}")
        return root

    for env_name in ("WIKI_PATH", "OBSIDIAN_VAULT_PATH"):
        val = os.environ.get(env_name)
        if val and pathlib.Path(val).is_dir():
            return pathlib.Path(val).resolve()

    d = pathlib.Path.cwd().resolve()
    while True:
        if (d / "AGENTS.md").is_file() or (d / ".obsidian").is_dir():
            return d
        if d.parent == d:
            break
        d = d.parent

    raise LayoutError(
        "No knowledge root found. Set $WIKI_PATH (or $OBSIDIAN_VAULT_PATH) to your markdown "
        "knowledge base, pass --root <path>, or run from inside it. Expected an AGENTS.md or "
        ".obsidian/ marker when discovering by upward search."
    )


def degraded_root() -> pathlib.Path:
    """The drop box used when no knowledge root resolves. $DFS_INBOX wins, else <cwd>/.dfs-inbox.

    Deliberately not a name like `docs/`: that is a directory a real project already owns, and
    agent drafts landing in someone's documentation tree are indistinguishable from content
    afterwards. An unstable cwd is a real hazard here, which is why $DFS_INBOX exists and why
    every message prints the absolute path.
    """
    val = os.environ.get(DROPDIR_ENV)
    return (pathlib.Path(val).expanduser() if val else pathlib.Path.cwd() / DROPDIR_NAME).resolve()


def load_layout(root: pathlib.Path) -> Dict[str, Any]:
    """Merge an optional `<root>/knowledge.json` over DEFAULT_LAYOUT."""
    layout = dict(DEFAULT_LAYOUT)
    cfg = root / CONFIG_FILENAME
    if cfg.is_file():
        try:
            override = json.loads(cfg.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise LayoutError(f"{cfg} is not valid JSON: {e}") from e
        if not isinstance(override, dict):
            raise LayoutError(f"{cfg} must contain a JSON object")
        unknown = set(override) - set(DEFAULT_LAYOUT)
        if unknown:
            raise LayoutError(f"{cfg} has unknown keys: {sorted(unknown)}. Known: {sorted(DEFAULT_LAYOUT)}")
        layout.update(override)
    return layout


class KnowledgeBase:
    def __init__(self, root: pathlib.Path, layout: Dict[str, Any], degraded: bool = False):
        self.root = root
        self.layout = layout
        self.degraded = degraded
        self._cache: Dict[pathlib.Path, Dict[str, Any]] = {}

    # -- paths -------------------------------------------------------------
    def layer(self, key: str) -> pathlib.Path:
        return self.root / self.layout[key]

    def inside(self, path: pathlib.Path) -> bool:
        try:
            path.relative_to(self.root)
            return True
        except ValueError:
            return False

    def iter_notes(self) -> List[pathlib.Path]:
        """All markdown notes under the configured content dirs, skipping tool/VCS dirs."""
        notes: List[pathlib.Path] = []
        for dirname in self.layout["content_dirs"]:
            base = self.root / dirname
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.md")):
                if any(part in SKIP_DIR_NAMES or part.startswith(".") for part in path.relative_to(self.root).parts):
                    continue
                if path.is_file():
                    notes.append(path)
        return notes

    def rel(self, path: pathlib.Path) -> str:
        return path.relative_to(self.root).as_posix()

    def read(self, path: pathlib.Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")

    # -- frontmatter -------------------------------------------------------
    def frontmatter(self, text: str) -> Dict[str, Any]:
        """Flat frontmatter parse: the fields the tools read, no YAML dependency."""
        if not text.startswith("---"):
            return {}
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}
        head = parts[1]
        fm: Dict[str, Any] = {}
        for key in ("title", "status", "type", "source"):
            m = re.search(rf"(?m)^{key}:\s*(.+?)\s*$", head)
            if m:
                fm[key] = m.group(1).strip().strip("\"'")
        tags = re.search(r"(?m)^tags:\s*\[(.*?)\]\s*$", head)
        if tags:
            fm["tags"] = [t.strip().strip("\"'") for t in tags.group(1).split(",") if t.strip()]
        else:
            block = re.search(r"(?ms)^tags:\s*\n((?:\s*-\s*.+\n?)+)", head)
            fm["tags"] = [m.group(1).strip().strip("\"'") for m in re.finditer(r"(?m)^\s*-\s*(.+?)\s*$", block.group(1))] if block else []
        return fm

    def title_of(self, path: pathlib.Path, text: str) -> str:
        fm = self.frontmatter(text)
        if fm.get("title"):
            return str(fm["title"])
        m = re.search(r"(?m)^#\s+(.+?)\s*$", text)
        return m.group(1).strip() if m else path.stem

    def prune_missing(self) -> List[pathlib.Path]:
        missing = [p for p in list(self._cache.keys()) if not p.is_file()]
        for p in missing:
            self._cache.pop(p, None)
        return missing

    def prune_stale(self) -> List[pathlib.Path]:
        return self.prune_missing()

    def get_cached_note(self, path: pathlib.Path) -> Dict[str, Any]:
        if not path.is_file():
            self._cache.pop(path, None)
            raise FileNotFoundError(f"Note not found: {path}")

        mtime_ns = path.stat().st_mtime_ns
        cached = self._cache.get(path)
        if cached is not None and cached.get("mtime_ns") == mtime_ns:
            return cached

        text = self.read(path)
        fm = self.frontmatter(text)
        title = self.title_of(path, text)
        tags = [str(t).lower() for t in fm.get("tags", [])]
        headings = " ".join(re.findall(r"(?m)^#{1,6}\s+(.+)$", text)).lower()
        body_s = re.sub(r"```.*?```", " ", text, flags=re.DOTALL).lower()
        path_s = self.rel(path).lower()
        neighbours = [w for w in re.findall(r"\[\[([^\]|#]+)", text)][:5]

        note_data: Dict[str, Any] = {
            "mtime_ns": mtime_ns,
            "text": text,
            "frontmatter": fm,
            "title": title,
            "tags": tags,
            "headings": headings,
            "body_s": body_s,
            "path_s": path_s,
            "neighbours": neighbours,
        }
        self._cache[path] = note_data
        return note_data


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def _matching_lines(text: str, terms: List[str]) -> List[str]:
    lines = []
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if not line.strip() or not any(term in low for term in terms):
            continue
        lines.append(f"    L{lineno}: {line.strip()[:200]}")
    return lines


def tool_search_vault(kb: KnowledgeBase, query: str, tag: Optional[str] = None,
                      top: int = 5, output_format: str = "detailed") -> str:
    terms = [t for t in re.split(r"\s+", query.strip().lower()) if t]
    if not terms:
        return "Search query must not be empty."

    kb.prune_missing()
    hits = []
    for path in kb.iter_notes():
        cached = kb.get_cached_note(path)
        tags = cached["tags"]
        if tag and not any(tag.lower() in t for t in tags):
            continue

        path_s = cached["path_s"]
        title_s = cached["title"].lower()
        headings = cached["headings"]
        body_s = cached["body_s"]
        text = cached["text"]

        score = sum(
            6.0 * title_s.count(term)
            + 4.0 * sum(1 for t in tags if term in t)
            + 3.0 * headings.count(term)
            + 2.0 * path_s.count(term)
            + 1.0 * body_s.count(term)
            for term in terms
        )
        if score <= 0:
            continue
        hits.append((score, path, cached))

    if not hits:
        return "No relevant notes found in the knowledge base."

    hits.sort(key=lambda h: (-h[0], h[1].as_posix()))
    hits = hits[:max(1, top)]

    if output_format == "json":
        payload = [{"path": kb.rel(p), "title": c["title"], "score": round(s, 2),
                    "tags": c["frontmatter"].get("tags", [])} for s, p, c in hits]
        return json.dumps(payload, ensure_ascii=False, indent=2)

    lines = [f"Knowledge base hits for {query!r} ({len(hits)} of {len(hits)}):"]
    for rank, (score, path, cached) in enumerate(hits, 1):
        if output_format == "compact":
            lines.append(f"[{rank}] {kb.rel(path)} ({round(score, 1)} pts)")
            continue
        lines.append(f"\n[{rank}] {kb.rel(path)} ({round(score, 1)} pts)")
        lines.append(f"    title: {cached['title']}")
        tags = cached["frontmatter"].get("tags", [])
        if tags:
            lines.append(f"    tags: {', '.join(str(t) for t in tags)}")
        lines.extend(_matching_lines(cached["text"], terms))
        neighbours = cached.get("neighbours", [])
        if neighbours:
            lines.append(f"    see-also: {', '.join(sorted(set(n.strip() for n in neighbours)))}")
    return "\n".join(lines)


def tool_omni_search(kb: KnowledgeBase, query: str, scope: str = "ladder", top: int = 5) -> str:
    """The retrieval escalation gateway: L1 knowledge base -> L0 code -> L2 docs -> L3 web."""
    q = query.strip()
    if not q:
        return "Search query must not be empty."
    mode = (scope or "ladder").lower().strip()

    if mode == "vault":
        return "# [L1_KNOWLEDGE] Knowledge-base retrieval\n\n" + tool_search_vault(kb, q, top=top)

    vault_res = tool_search_vault(kb, q, top=top, output_format="detailed")
    if "No relevant notes found" not in vault_res:
        return (
            f"# [L1_KNOWLEDGE_HIT] Local knowledge base answered this\n\n{vault_res}\n\n"
            "Hint: the knowledge base already records this convention or pitfall — follow it "
            "and do not spend a network round-trip on it."
        )

    if mode == "code":
        return _l0_guidance(q)
    if mode == "doc":
        return f"# [L2_DOCS]\n\nQuery official documentation for {q!r} (e.g. a docs MCP server or the library's site)."
    if mode == "web":
        return f"# [L3_WEB]\n\nSearch the web for {q!r}."

    # mode == ladder
    return (
        f"# [NOT_IN_KNOWLEDGE] Escalation ladder engaged for {q!r}\n\n"
        f"1. L1 knowledge base: no note covers this.\n"
        f"2. L0 local code: {_l0_guidance(q, inline=True)}\n"
        f"3. L2 upstream docs: use a docs lookup for the library's own API surface.\n"
        f"4. L3 web: fall back to web search for issue trackers and release notes.\n\n"
        f"After solving it, save the non-obvious part with `save_inbox_draft` — that is what "
        f"makes the next occurrence an L1 hit."
    )


def _l0_guidance(query: str, inline: bool = False) -> str:
    text = (f"search the local codebase for {query!r} with your harness's own search tool "
            f"(e.g. `search_files` / ripgrep) before writing anything new")
    return text if inline else f"# [L0_CODE]\n\nReuse before rewrite: {text}."


def tool_get_note(kb: KnowledgeBase, rel_path: str) -> str:
    raw = rel_path.strip()
    if not raw:
        return "rel_path must not be empty."

    clean = raw.strip("[]")
    if "|" in clean:
        clean = clean.split("|")[0].strip()
    clean = clean.strip().lstrip("/\\")

    target = (kb.root / clean).resolve()
    if not kb.inside(target):
        return f"Refused: '{rel_path}' resolves outside the knowledge root."

    if not target.exists() and not target.suffix and target.with_suffix(".md").exists():
        target = target.with_suffix(".md")

    if not target.exists():
        query_name = pathlib.Path(clean).stem.lower()
        candidates = [n for n in kb.iter_notes() if query_name and query_name in n.stem.lower()]
        exact = [c for c in candidates if c.stem.lower() == query_name]
        if exact:
            target = exact[0]
        elif len(candidates) == 1:
            target = candidates[0]
        elif len(candidates) > 1:
            listing = "\n".join(f"- `{kb.rel(c)}`" for c in candidates[:10])
            return f"Multiple notes match '{rel_path}'. Specify one:\n{listing}"
        else:
            return (f"Note not found: '{rel_path}'\n"
                    f"Try `search_vault` or `omni_search` by keyword instead.")

    if target.is_dir():
        rel_dir = kb.rel(target)
        readme = target / "README.md"
        if readme.is_file():
            return f"# Directory overview: {rel_dir} (README.md)\n\n{kb.read(readme)}"
        md_files = [f for f in sorted(target.iterdir()) if f.is_file() and f.suffix == ".md"]
        sub_dirs = [d for d in sorted(target.iterdir()) if d.is_dir() and not d.name.startswith(".")]
        lines = [f"# Directory: `{rel_dir}/`"]
        if sub_dirs:
            lines.append("\n## Subdirectories")
            lines += [f"- `{d.name}/`" for d in sub_dirs]
        if md_files:
            lines.append("\n## Documents")
            for f in md_files:
                text = kb.read(f)[:400]
                lines.append(f"- `{rel_dir}/{f.name}` — {kb.title_of(f, text)}")
        if not md_files and not sub_dirs:
            lines.append("*(no markdown documents in this directory)*")
        return "\n".join(lines)

    return f"# {kb.rel(target)}\n\n{kb.read(target)}"


def tool_get_rule_snippet(kb: KnowledgeBase, rule_name: str, section: Optional[str] = None) -> str:
    """JIT micro-slice: return only the matching section, so a whole rules file never floods context."""
    note = tool_get_note(kb, rule_name)
    if note.startswith(("Refused:", "Note not found:", "Multiple notes match")):
        return note

    lines = note.splitlines()
    if not section or not section.strip():
        return "\n".join(lines[:45]) + "\n\n*(pass `section='<heading keyword>'` for one section)*"

    sec_query = section.strip().lower()
    chunks: List[str] = []
    current: List[str] = []
    in_target = False
    current_level = 2

    for line in lines:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line.lstrip("#").strip().lower()
            if in_target and level <= current_level:
                chunks.append("\n".join(current))
                current = []
                in_target = False
            if sec_query in heading:
                in_target = True
                current_level = level
                current.append(line)
                continue
        if in_target:
            current.append(line)

    if in_target and current:
        chunks.append("\n".join(current))

    if not chunks:
        headings = "\n".join(f"- {l}" for l in lines if re.match(r"^#{2,4}\s+", l))[:1500]
        return f"No section matching '{section}' in `{rule_name}`.\n\nAvailable sections:\n{headings}"

    return f"# [JIT slice: {rule_name} -> {section}]\n\n" + "\n\n---\n\n".join(chunks)


def tool_list_standards(kb: KnowledgeBase) -> str:
    lines = ["# Knowledge base catalogue"]

    lang_dir = kb.layer("languages_dir")
    if lang_dir.is_dir():
        lines.append(f"\n## Language standards ({kb.layout['languages_dir']}/)")
        for sub in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
            standard = [f.name for f in sorted(sub.glob("*-STANDARDS.md"))]
            cheat = [f.name for f in sorted(sub.glob("*-CHEATSHEET.md"))]
            lines.append(f"- **{sub.name}**: standards `{standard[0] if standard else '-'}` | cheatsheet `{cheat[0] if cheat else '-'}`")

    rules_dir = kb.layer("rules_dir")
    if rules_dir.is_dir():
        lines.append(f"\n## Cross-cutting rules ({kb.layout['rules_dir']}/)")
        lines += [f"- `{kb.layout['rules_dir']}/{f.name}`" for f in sorted(rules_dir.glob("*.md"))]

    career_dir = kb.layer("career_dir")
    if career_dir.is_dir():
        lines.append(f"\n## Career material ({kb.layout['career_dir']}/)")
        lines += [f"- `{kb.rel(f)}`" for f in sorted(career_dir.rglob("*.md"))]

    if len(lines) == 1:
        lines.append("\n*(no configured content directories exist yet — check `knowledge.json`)*")
    return "\n".join(lines)


def tool_get_code_template(kb: KnowledgeBase, template_name: str, lang: Optional[str] = None) -> str:
    tpl_dir = kb.layer("code_template_dir")
    if not tpl_dir.is_dir():
        return f"No code template directory at `{kb.layout['code_template_dir']}`."

    clean = template_name.strip().lower()
    matches = [f for f in sorted(tpl_dir.rglob("*"))
               if f.is_file() and clean in f.name.lower() and (not lang or lang.lower() in (f.parent.name + f.name).lower())]
    if not matches:
        available = sorted({f.parent.name for f in tpl_dir.rglob("*") if f.is_file()})
        return (f"No template matching '{template_name}'"
                + (f" for language '{lang}'" if lang else "")
                + f". Available groups: {', '.join(available) or '-'}")

    target = matches[0]
    return f"// === Code template: {kb.rel(target)} ===\n\n{kb.read(target)}"


def tool_save_inbox_draft(kb: KnowledgeBase, title: str, content: str,
                          tags: Optional[List[str]] = None, source: Optional[str] = None) -> str:
    """A-MAC admission gate: reject one-off/trivial records before they pollute the knowledge base."""
    t_clean = title.strip()
    c_clean = content.strip()
    if len(t_clean) < 4:
        return "Rejected (A-MAC): title too short — name the technical subject explicitly."
    if len(c_clean) < 30:
        return "Rejected (A-MAC): content too short (<30 chars) — include symptom, root cause, and the fix."
    if t_clean.lower() in {"test", "temp", "123", "todo", "fix typo", "tmp"}:
        return "Rejected (A-MAC): looks like a throwaway scratch record."

    inbox = kb.layer("inbox_dir")
    inbox.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%Y-%m-%d")
    slug = re.sub(r"-+", "-", re.sub(r'[\\/:*?"<>|\s]+', "-", t_clean.lower())).strip("-") or "knowledge-note"
    target = inbox / f"{today}-{slug}.md"
    counter = 1
    while target.exists():
        target = inbox / f"{today}-{slug}-{counter}.md"
        counter += 1

    tag_list = [str(t).lstrip("#") for t in (tags if isinstance(tags, list) else [])]
    for required in ("status/draft",):
        if required not in tag_list:
            tag_list.append(required)
    if not any(t.startswith("category/") for t in tag_list):
        tag_list.append("category/notes")

    frontmatter = (
        "---\n"
        f'title: "{t_clean}"\n'
        f"created: {today}\n"
        f"updated: {today}\n"
        "type: source-notes\n"
        "tags:\n" + "".join(f"  - {t}\n" for t in tag_list) +
        "status: draft\n"
        "audience: both\n"
        f'source: "{(source or "session harvest").strip()}"\n'
        "---\n\n"
    )
    try:
        target.write_text(frontmatter + c_clean + "\n", encoding="utf-8")
    except OSError as e:
        return f"Failed to write draft: {e}"

    if kb.degraded:
        marker = kb.root / DROPDIR_MARKER
        marker_note = ""
        if not marker.exists():
            try:
                marker.write_text(DROPDIR_README, encoding="utf-8")
                marker_note = f"\n- `{DROPDIR_MARKER}` written so the next reader knows what this folder is"
            except OSError as e:
                marker_note = f"\n- [WARN] could not write the drop-box marker: {e}"
        return ("Draft saved (A-MAC passed) — **NO KNOWLEDGE BASE IS CONFIGURED**.\n\n"
                f"- path: `{target}` (absolute){marker_note}\n"
                f"- title: {t_clean}\n- tags: {', '.join(tag_list)}\n\n"
                f"This is a drop box, not a knowledge base: retrieval tools refuse until a root is set "
                f"(`$WIKI_PATH`, or `--root <path>` when registering the server). If `{kb.root}` is not "
                f"where you want drafts to accumulate, set `$DFS_INBOX` to a stable directory.\n"
                f"Promote later with `promote_inbox_draft` once a root exists, or file them with "
                f"`vault-inbox-consolidate.py --inbox {kb.root}`.")

    return (f"Draft saved (A-MAC passed).\n\n"
            f"- path: `{kb.rel(target)}`\n- title: {t_clean}\n- tags: {', '.join(tag_list)}\n\n"
            f"Promote it later with `promote_inbox_draft`.")


def tool_promote_inbox_draft(kb: KnowledgeBase, draft_filename: str, target_dir: str) -> str:
    inbox = kb.layer("inbox_dir")
    dest_dir = (kb.root / target_dir.strip().lstrip("/\\")).resolve()
    if not kb.inside(dest_dir):
        return f"Refused: target directory '{target_dir}' is outside the knowledge root."

    draft = (inbox / draft_filename).resolve()
    if not kb.inside(inbox.resolve()) or not str(draft).startswith(str(inbox.resolve())):
        return f"Refused: '{draft_filename}' is not inside {kb.layout['inbox_dir']}/."

    if draft.exists() and draft.name == DROPDIR_MARKER:
        return f"Refused: '{DROPDIR_MARKER}' is the drop-box marker, not a draft."

    if not draft.exists():
        matches = sorted(inbox.glob(f"*{draft_filename}*"))
        if len(matches) > 1:
            return f"Multiple drafts match — be specific: {', '.join(m.name for m in matches[:5])}"
        if not matches:
            return f"No draft matching '{draft_filename}' in {kb.layout['inbox_dir']}/."
        draft = matches[0].resolve()

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / draft.name
    try:
        text = kb.read(draft)
        today = date.today().strftime("%Y-%m-%d")
        text = re.sub(r"status:\s*draft", "status: stable", text)
        text = re.sub(r"updated:\s*\S+", f"updated: {today}", text)
        dest.write_text(text, encoding="utf-8")
        draft.unlink()
    except OSError as e:
        return f"Promotion failed: {e}"
    return (f"Promoted to a stable asset.\n\n- path: `{kb.rel(dest)}`\n"
            f"- status: `status: stable`\n- updated: `{today}`")


SCAN_PATTERNS = [
    ("TODO", re.compile(r"\bTODO\b[:\s]*(.{0,120})", re.IGNORECASE)),
    ("FIXME", re.compile(r"\bFIXME\b[:\s]*(.{0,120})", re.IGNORECASE)),
    ("HACK", re.compile(r"\bHACK\b[:\s]*(.{0,120})", re.IGNORECASE)),
    ("WORKAROUND", re.compile(r"\bWORKAROUND\b[:\s]*(.{0,120})", re.IGNORECASE)),
    ("XXX", re.compile(r"\bXXX\b[:\s]*(.{0,120})", re.IGNORECASE)),
]
SCAN_EXT = {".py", ".go", ".c", ".h", ".cc", ".cpp", ".hpp", ".rs", ".java", ".kt", ".ts", ".tsx",
            ".js", ".jsx", ".sql", ".sh", ".ps1", ".yml", ".yaml", ".toml", ".md", ".proto"}
SCAN_SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target"}


def tool_vault_proactive_scan(project_path: Optional[str] = None, limit: int = 15) -> str:
    """Regex debt scan. ponytail: no AST, no ROI model — a candidate list for a human to rank."""
    roots = []
    if project_path:
        cand = pathlib.Path(project_path).expanduser()
        if not cand.is_dir():
            return f"Not a directory: {project_path}"
        roots = [cand.resolve()]
    else:
        code_root = os.environ.get("CODE_ROOT")
        if not code_root or not pathlib.Path(code_root).is_dir():
            return ("No project given and $CODE_ROOT is unset. Pass project_path=<dir>.")
        roots = [p for p in sorted(pathlib.Path(code_root).iterdir()) if p.is_dir()]
        if not roots:
            return f"No project directories under {code_root}."

    findings = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SCAN_EXT:
                continue
            rel_parts = path.relative_to(root).parts
            if any(part in SCAN_SKIP or part.startswith(".") for part in rel_parts):
                continue
            try:
                if path.stat().st_size > 2_000_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for label, pattern in SCAN_PATTERNS:
                for match in pattern.finditer(text):
                    lineno = text.count("\n", 0, match.start()) + 1
                    findings.append((label, path.relative_to(root).as_posix(), lineno, match.group(1).strip()[:120]))
            if len(findings) >= limit * 4:
                break

    if not findings:
        return "No TODO/FIXME/HACK/WORKAROUND markers found."

    findings = findings[: max(1, limit)]
    lines = [f"| # | Kind | Location | Note |", "|---|---|---|---|"]
    for i, (label, rel, lineno, note) in enumerate(findings, 1):
        lines.append(f"| {i} | {label} | `{rel}:{lineno}` | {note or '-'} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP protocol surface
# ---------------------------------------------------------------------------
def _schema(props: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


TOOLS_DEFINITION = [
    {"name": "search_vault",
     "description": "Keyword/tag retrieval over the knowledge base (rules, pitfalls, templates). "
                    "Call this BEFORE writing code, designing, or searching the web.",
     "inputSchema": _schema({
         "query": {"type": "string", "description": "Keywords or an error pattern"},
         "tag": {"type": "string", "description": "Optional tag filter, e.g. 'lang/go'"},
         "top": {"type": "integer", "description": "Max results (default 5)", "default": 5},
         "format": {"type": "string", "enum": ["compact", "detailed", "json"], "default": "detailed"}},
         ["query"])},
    {"name": "omni_search",
     "description": "Retrieval escalation gateway: L1 knowledge base, then L0 local code, L2 upstream "
                    "docs, L3 web. Short-circuits on an L1 hit so nothing is re-derived.",
     "inputSchema": _schema({
         "query": {"type": "string", "description": "Keywords, error text, or a technical need"},
         "scope": {"type": "string", "enum": ["ladder", "vault", "code", "doc", "web"], "default": "ladder"},
         "top": {"type": "integer", "default": 5}},
         ["query"])},
    {"name": "get_note",
     "description": "Read one note or list one directory by knowledge-base-relative path.",
     "inputSchema": _schema({
         "rel_path": {"type": "string", "description": "e.g. '01-Rules/CODING-UNIVERSAL.md'"}},
         ["rel_path"])},
    {"name": "get_rule_snippet",
     "description": "Token-cheap JIT slice: one section of a rules file instead of the whole file.",
     "inputSchema": _schema({
         "rule_name": {"type": "string", "description": "Rule note name or relative path"},
         "section": {"type": "string", "description": "Heading keyword, e.g. 'naming' or 'errors'"}},
         ["rule_name"])},
    {"name": "get_code_template",
     "description": "Extract a production code template by name and language, without markdown wrapping.",
     "inputSchema": _schema({
         "template_name": {"type": "string", "description": "e.g. 'worker-pool', 'multistage'"},
         "lang": {"type": "string", "description": "e.g. 'go', 'python', 'docker'"}},
         ["template_name"])},
    {"name": "list_standards",
     "description": "Enumerate available standards, cross-cutting rules, and career material.",
     "inputSchema": _schema({})},
    {"name": "save_inbox_draft",
     "description": "Save a non-obvious pitfall/workaround/decision as a draft in the inbox, behind the "
                    "A-MAC admission gate.",
     "inputSchema": _schema({
         "title": {"type": "string", "description": "Names the technical subject"},
         "content": {"type": "string", "description": "Symptom, root cause, fix (with code block)"},
         "tags": {"type": "array", "items": {"type": "string"}},
         "source": {"type": "string"}},
         ["title", "content"])},
    {"name": "promote_inbox_draft",
     "description": "Promote an inbox draft into a destination directory, flipping it to stable.",
     "inputSchema": _schema({
         "draft_filename": {"type": "string", "description": "Filename or keyword"},
         "target_dir": {"type": "string", "description": "Destination relative dir"}},
         ["draft_filename", "target_dir"])},
    {"name": "vault_proactive_scan",
     "description": "Scan a project for TODO/FIXME/HACK/WORKAROUND debt and return a ranked candidate list.",
     "inputSchema": _schema({
         "project_path": {"type": "string", "description": "Project dir; defaults to $CODE_ROOT's children"},
         "limit": {"type": "integer", "default": 15}},
         [])},
]

PROMPT_FILES = {
    "vault-researcher": "SUBAGENT-RESEARCHER.md",
    "vault-code-reviewer": "SUBAGENT-CODE-REVIEWER.md",
    "vault-interview-coach": "SUBAGENT-INTERVIEW-COACH.md",
    "vault-grill-master": "SUBAGENT-REFACTORER.md",
}

TOOL_DISPATCH = {
    "search_vault": lambda kb, a: tool_search_vault(kb, a.get("query", ""), tag=a.get("tag"),
                                                    top=int(a.get("top", 5)),
                                                    output_format=a.get("format", "detailed")),
    "omni_search": lambda kb, a: tool_omni_search(kb, a.get("query", ""), scope=a.get("scope", "ladder"),
                                                  top=int(a.get("top", 5))),
    "get_note": lambda kb, a: tool_get_note(kb, a.get("rel_path", "")),
    "get_rule_snippet": lambda kb, a: tool_get_rule_snippet(kb, a.get("rule_name", ""), section=a.get("section")),
    "get_code_template": lambda kb, a: tool_get_code_template(kb, a.get("template_name", ""), lang=a.get("lang")),
    "list_standards": lambda kb, a: tool_list_standards(kb),
    "save_inbox_draft": lambda kb, a: tool_save_inbox_draft(kb, a.get("title", ""), a.get("content", ""),
                                                            tags=a.get("tags"), source=a.get("source")),
    "promote_inbox_draft": lambda kb, a: tool_promote_inbox_draft(kb, a.get("draft_filename", ""),
                                                                  a.get("target_dir", "")),
    "vault_proactive_scan": lambda kb, a: tool_vault_proactive_scan(a.get("project_path"),
                                                                    int(a.get("limit", 15))),
}


def handle_request(kb: KnowledgeBase, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params") or {}

    def ok(result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "initialize":
        return ok({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}, "prompts": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS_DEFINITION})
    if method == "prompts/list":
        return ok({"prompts": [{"name": n, "description": f"Standard prompt: {n}", "arguments": []}
                               for n in PROMPT_FILES]})
    if method == "prompts/get":
        name = params.get("name", "")
        path = kb.layer("prompts_dir") / PROMPT_FILES[name] if name in PROMPT_FILES else None
        if path and path.is_file():
            text = kb.read(path)
        else:
            text = f"You are an expert engineering assistant grounded in the knowledge base at {kb.root}."
        return ok({"description": f"Standard prompt for {name}",
                   "messages": [{"role": "user", "content": {"type": "text", "text": text}}]})
    if method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments") or {}
        handler = TOOL_DISPATCH.get(name)
        if handler is None:
            return ok({"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True})
        if kb.degraded and name not in DEGRADED_TOOLS:
            return ok({"content": [{"type": "text", "text": (
                f"Refused: no knowledge base is configured, so `{name}` cannot answer — and reporting "
                f"an empty result would be a silent wrong answer. Only `save_inbox_draft` works here; "
                f"it writes to the drop box at {kb.root}. Set $WIKI_PATH, $OBSIDIAN_VAULT_PATH or "
                f"register the server with --root <path> to enable retrieval.")}], "isError": True})
        try:
            return ok({"content": [{"type": "text", "text": handler(kb, arguments)}]})
        except Exception as e:  # a tool crash must be reported, not swallowed
            return ok({"content": [{"type": "text", "text": f"Tool error: {e}\n{traceback.format_exc()}"}],
                       "isError": True})
    if req_id is not None:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return None


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    explicit = None
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            sys.stderr.write("--root requires a path\n")
            return 2
        explicit = argv[i + 1]

    degraded = False
    try:
        root = resolve_root(explicit)
    except LayoutError as e:
        if explicit:
            # A root the user named must not be second-guessed: falling back to a drop box here
            # would be the silent wrong answer this whole contract exists to prevent.
            sys.stderr.write(f"{SERVER_NAME}: {e}\n")
            return 2
        dropbox = degraded_root()
        kb = KnowledgeBase(dropbox, dict(DEFAULT_LAYOUT, inbox_dir=".", content_dirs=[]), degraded=True)
        degraded = True
        sys.stderr.write(
            f"{SERVER_NAME}: no knowledge base resolved ({e})\n"
            f"{SERVER_NAME}: DRAFTS-ONLY mode — `save_inbox_draft` writes to {dropbox}; every "
            f"retrieval tool will refuse. Set $WIKI_PATH, $OBSIDIAN_VAULT_PATH or --root to fix this.\n")
    else:
        try:
            kb = KnowledgeBase(root, load_layout(root))
        except LayoutError as e:
            # A root was found but its knowledge.json is broken: a config error, not "no KB".
            sys.stderr.write(f"{SERVER_NAME}: {e}\n")
            return 2

    sys.stderr.write(f"{SERVER_NAME} {SERVER_VERSION} serving {kb.root}{' (drafts-only)' if degraded else ''}\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle_request(kb, req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
