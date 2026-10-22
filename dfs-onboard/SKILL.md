---
name: dfs-onboard
description: Rapidly orient an AI agent to develop on an existing codebase. Use when entering an unfamiliar repo and you need to map how it works before editing.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags: [onboarding, codebase-discovery, architecture-mapping, baseline-testing]
    related_skills: [dfs-bootstrap, dfs-tdd]
---
# DFS-ONBOARD: Codebase Takeover & Context Anchor

Quickly orient an AI Agent on an unfamiliar or existing repository (`<your projects root>/{project}`) to establish immediate development readiness with verified test baselines and architecture invariants.

## The 4-Phase Onboarding Protocol

### Phase 1: Ground Truth Baseline & Verification Commands (MUST)
1. **Identify Build & Test Tooling**:
   - Go: `go test ./...`
   - Python: `pytest`
   - Rust: `cargo test`
   - TypeScript/Node: `npm test` or `pnpm test`
   - C/C++: `ctest` or `make test`
2. **Execute Baseline Test Suite**:
   Run the test command immediately in terminal:
   - Record exact passing test count (e.g. `[PASS] 124 passed in 2.3s`).
   - If pre-existing failures occur: Record them as **Pre-Existing Broken Baselines** to prevent blaming subsequent changes.
   - **Shared-workdir guard (multi-agent repos)**: run `git branch --show-current` right before and after the baseline; another session's `checkout -b` can switch the tree mid-run and silently invalidate the baseline.

---

### Phase 2: Symbol Topology & Key Path Mapping
Inspect directory structure and build symbol index:
1. Locate core entrypoints (`main.go`, `app.py`, `src/index.ts`).
2. Map data flow: Request -> Route -> Controller -> Service -> Repository -> DB. Done when every hop in that chain carries a real `file:line` — a hop you cannot locate is an unmapped layer, not an absent one.
3. Identify existing wheels (The Ladder of Reuse level 1).

---

### Phase 3: Invariants & Local Gotchas Extraction
Extract critical gotchas:
- Secret management patterns (`.env`, `config.yaml`).
- Concurrency patterns (Mutex, Worker Pools, Context propagation).
- Windows/cross-platform path handling (`Path.resolve()`, `MSYS=winsymlinks:nativestrict`).
- **Always record these three classes** — each one has burned a full debugging cycle by looking like a real defect:
  1. **Format/lint false positives**: a checked-out tree with CRLF on disk and LF in the index makes `gofmt -l` / formatters report files that are not misformatted. Verify with `git ls-files --eol` before "fixing" anything, and never mass-reformat them.
  2. **Terminal encoding on the wire**: sending non-ASCII JSON from a Unix-like shell can arrive as a body-parse error at the server. That is the terminal, not the service — verify HTTP contracts with a real client library, not shell `curl`.
  3. **"Exit 0 is not correct"**: every silent-failure mode in this repo (blank charts, doubled counters, refused slots, dropped labels) passed a green suite first. Record the self-report checks the repo uses, so the next agent reaches for them instead of trusting exit codes.

**Persist gotchas to the repo's invariants file (MUST).** Gotchas that live only in this conversation are lost at session end; gotchas in the repo are read by every future subagent brief at zero marginal cost. Write them to the repo's existing anchor (`AGENTS.md` / `CLAUDE.md` / `docs/agents/INVARIANTS.md` — follow the repo's convention, do not invent a second one).

---

### Phase 4: Machine-Readable `.agent-context.md` Generation
Write `.agent-context.md` in project root:

```markdown
# [NOTE] Agent Context: {Project Name}

### 1. [STEP] Ground Truth Verification Baseline
- **Primary Test Command**: `{test_cmd}`
- **Baseline Test Result**: [PASS] {pass_count} passed, 0 failed (Captured on {date})
- **Build / Lint Command**: `{build_cmd}`

### 2. [STEP] Core Symbol & Architecture Map
- Entrypoint: `{entrypoint_file}`
- Core Services: `{service_files}`
- Data Models: `{model_files}`

### 3. [STEP] Local Engineering Red Lines & Gotchas
- {Gotcha 1: e.g. Never hold mutex during network calls}
- {Gotcha 2: e.g. All SQL queries must use prepared statements}

### 4. [STEP] Defensive Skills Linkage
- Global Standards: `{vault_root}/AGENTS.md` (resolve via `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → upward search)
- Vault Search: `search_vault` MCP tool (server: `mcp/knowledge_server.py`; without MCP use the `mcp/README.md` fallback table)
  (DFS-PORT: the private vault-side `search-vault.py` CLI is not shipped with this repo)
```

**Pre-generation guard (MUST)**: check the repo first — if `.agent-context.md` was deliberately removed before (e.g. it duplicated `AGENTS.md` / a shared-memory directory), or the repo documents an equivalent machine-readable anchor, **do NOT recreate it**; follow the repo's existing convention and note the substitution in your handoff.

Prompt human partner: `Codebase onboarded. Test baseline verified ({pass_count} passed). Ready to develop?`
---

## Checkable Completion Criterion
- `.agent-context.md` created (or existing convention acknowledged) with verified build/test commands, LOC baseline, and passing test count.
- Physical execution receipt of existing test suite captured (Exit code 0 or baseline failure count).
- Repo invariants file refreshed with this session's gotchas (three mandatory classes above) — diff-verified, not rewritten from scratch.

---

## [NOTE] Returning to an already-onboarded repo (re-onboard = verify, do not re-derive)

When an invariants/anchor file already exists, the second onboarding is a **diff-verify**, not a rebuild:

1. Re-run the test baseline (it is the only thing that can have drifted silently).
2. Spot-check 3 `file:line` references from the anchor against the current tree; a moved hop means the map is stale — patch that line, do not re-trace the whole chain.
3. Read the ledger / work log tail for open gaps and their triggers; carry them forward.
4. Re-deriving an architecture map that already exists costs a full context window and produces the same document.

## Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I will infer the project architecture from memory without running tests."* | **Ground-Truth Drift**: Assumptions about outdated dependencies or broken build environments lead to broken plans. | Run existing build and test commands immediately; capture authentic baseline passing counts before writing code. |
| *"I'll explore the whole repository deeply before answering the user."* | **Context Bloat & Token Depletion**: Indiscriminate deep reads consume context without producing actionable value. | Follow the 3-phase rapid onboarding ladder: identify framework, read entry points, run test suite, and record in `.agent-context.md`. |
| *"If .agent-context.md was deleted before, I should recreate it anyway."* | **Repository Convention Violation**: Recreating intentionally pruned or substituted files creates duplicate drift. | Follow the Pre-generation Guard: if `.agent-context.md` was deliberately removed or substituted, follow existing conventions. |
