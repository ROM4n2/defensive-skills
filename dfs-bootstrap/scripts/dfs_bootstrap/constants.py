"""Literals the writers and doctor must agree on. Kept together so a version bump is one edit."""
from __future__ import annotations

import pathlib

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
TEMPLATES = SKILL_DIR / "templates"

# Sensitive exclusions every bootstrapped repo needs. The skill's own tests assert this list is a
# superset of the patterns the shipped hook scans for, so the two cannot drift apart silently.
REQUIRED_IGNORES = [
    "config.yaml",
    "config.yml",
    "config.local.yaml",
    ".env",
    ".env.*",
    "*.env",
    "*.secret",
    "*.pem",
    "*.key",
    "*.local.json",
    "credentials.json",
    # Agent-runtime scratch that must never be committed: worktree checkouts of this same repo,
    # and the dfs-exec task ledger (per-run state, not a deliverable).
    ".worktrees/",
    ".vault-exec-ledger.json",
]
IGNORE_HEADER = "# Sensitive credentials & secrets"

# LF pins the hook itself depends on. Without the .githooks line, a Windows `core.autocrlf=true`
# rewrites the hook to CRLF on checkout and git can no longer spawn it.
GITATTRIBUTES_HEADER = "# DFS bootstrap: deterministic line endings"
GITATTRIBUTES_LINES = [
    ".githooks/** text eol=lf",
    "WORKMEMORY/** text eol=lf",
    "*.sh text eol=lf",
]

WORKMEMORY_FILES = ["PROTOCOL.md", "INDEX.md", "INDEX-topics.md", "PROJECT_OVERVIEW.md", "work.log"]

# AGENTS.md is the one file that carries the rules. CLAUDE.md is a pointer, not a copy: two full
# copies mean every rule edit must be applied twice and the copies drift apart.
RULES_SSOT_FILE = "AGENTS.md"
POINTER_FILE = "CLAUDE.md"
POINTER_BODY = (
    "@AGENTS.md\n"
    "<!-- Canonical rules live in AGENTS.md; read ./AGENTS.md directly if your runtime does not "
    "expand @imports. -->\n"
)
# Files DFS used to generate. They are reported (the user may have hand-written content in them)
# but never created and never deleted by this script.
LEGACY_ALIAS_FILES = [".agent-rules.md", ".cursorrules"]

# Overlay fallback when AGENTS.md is already owned by upstream: the private layer lives here instead,
# and this path is listed in OVERLAY_PRIVATE_PATHS so git never sees it.
PRIVATE_ANCHOR_FILE = "AGENTS.dfs.md"

WM_ANCHOR_FILES = ["AGENTS.md", "GEMINI.md"]

# The anchor is identified by its block header plus a sink/source tool call — NOT by a routing-table
# row that happens to share the title, and not by a private vault's directory names (an earlier
# version required `$WIKI_PATH/AGENTS.md`, which leaked one machine's layout into every repo).
ANCHOR_HEADER = "## [NOTE] 工程规范与避坑检索"
ANCHOR_TOOL_TOKENS = ("save_inbox_draft", "search_vault")
WM_MARKER = "WORKMEMORY/INDEX.md"

HOOK_VERSION_MARKER = "# dfs-bootstrap-hook-version:"
HOOK_VERSION = "5"

GATE_VERSION_MARKER = "# dfs-bootstrap-gate-version:"
GATE_VERSION = "4"
GATE_TEMPLATES: tuple[tuple[pathlib.Path, pathlib.Path], ...] = (
    (TEMPLATES / "repo" / "check_repo_hygiene.py", pathlib.Path("scripts") / "check_repo_hygiene.py"),
    (TEMPLATES / "repo" / "check_repo_structure.py", pathlib.Path("scripts") / "check_repo_structure.py"),
)

# The fingerprint gate is private .git/ state, never a tracked-tree artifact. Only the script is
# installed; the two per-machine pattern files are user-owned and are never created or overwritten.
LOCAL_GATE_VERSION_MARKER = "# dfs-bootstrap-local-gate-version:"
LOCAL_GATE_VERSION = "1"
LOCAL_GATE_TEMPLATE = TEMPLATES / "local-gates" / "fingerprint-gate.sh"
LOCAL_GATE_DEST = pathlib.Path(".git") / "local-gates" / "fingerprint-gate.sh"

VAULT_ROOT_TOKEN = "$WIKI_PATH"

# ---------------------------------------------------------------------------
# Overlay mode: private scaffolding that never reaches upstream.
#
# Every path below is written to the working tree but excluded from git via `.git/info/exclude`,
# and its LF pin goes into `.git/info/attributes` instead of the tracked `.gitattributes`. The
# upstream `.gitignore` / `.gitattributes` are never modified, so `git status` stays clean and a
# pull request contains only real work. Verified by tests/test_overlay.py.
# ---------------------------------------------------------------------------
OVERLAY_MODE = "overlay"
OWNER_MODE = "owner"

OVERLAY_PRIVATE_PATHS = [
    "AGENTS.md",
    "AGENTS.dfs.md",
    "CLAUDE.md",
    "GEMINI.md",
    "WORKMEMORY/",
    "scripts/check_repo_hygiene.py",
    "scripts/check_repo_structure.py",
    ".agent-rules.md",
    ".cursorrules",
]

# The hook lives inside .git so it is neither tracked nor diffed, and survives checkout/reset.
OVERLAY_HOOK_DIR = pathlib.Path(".git") / "dfs-hooks"

EXCLUDE_HEADER = "# DFS overlay: private scaffolding, never committed to upstream"
ATTRIBUTES_HEADER = "# DFS overlay: LF pins for private scaffolding (local, highest precedence)"

# Where the value we replaced came from, so `--take-hooks-path` is reversible.
HOOKS_PATH_BACKUP_KEY = "dfs.bootstrap.hooksPathBackup"
