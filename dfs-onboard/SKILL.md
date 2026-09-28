---
name: dfs-onboard
description: Rapidly orient an AI agent to develop on an existing codebase. Use when entering an unfamiliar repo and you need to map how it works before editing.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [onboarding, codebase-discovery, architecture-mapping, baseline-testing]
    related_skills: [dfs-bootstrap, dfs-tdd, dfs-plan]
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
   - Record exact passing test count (e.g. `✅ 124 passed in 2.3s`).
   - If pre-existing failures occur: Record them as **Pre-Existing Broken Baselines** to prevent blaming subsequent changes.

---

### Phase 2: Symbol Topology & Key Path Mapping
Inspect directory structure and build symbol index:
1. Locate core entrypoints (`main.go`, `app.py`, `src/index.ts`).
2. Map data flow: Request ➔ Route ➔ Controller ➔ Service ➔ Repository ➔ DB.
3. Identify existing wheels (The Ladder of Reuse level 1).

---

### Phase 3: Invariants & Local Gotchas Extraction
Extract critical gotchas:
- Secret management patterns (`.env`, `config.yaml`).
- Concurrency patterns (Mutex, Worker Pools, Context propagation).
- Windows/cross-platform path handling (`Path.resolve()`, `MSYS=winsymlinks:nativestrict`).

---

### Phase 4: Machine-Readable `.agent-context.md` Generation
Write `.agent-context.md` in project root:

```markdown
# 🤖 Agent Context: {Project Name}

### 1. 🛠️ Ground Truth Verification Baseline
- **Primary Test Command**: `{test_cmd}`
- **Baseline Test Result**: ✅ {pass_count} passed, 0 failed (Captured on {date})
- **Build / Lint Command**: `{build_cmd}`

### 2. 🗺️ Core Symbol & Architecture Map
- Entrypoint: `{entrypoint_file}`
- Core Services: `{service_files}`
- Data Models: `{model_files}`

### 3. 🚨 Local Engineering Red Lines & Gotchas
- {Gotcha 1: e.g. Never hold mutex during network calls}
- {Gotcha 2: e.g. All SQL queries must use prepared statements}

### 4. 📚 Defensive Skills Linkage
- Global Standards: `{vault_root}/AGENTS.md` (resolve via `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → upward search)
- Vault Search: `search_vault` MCP tool (server: `mcp/knowledge_server.py`; without MCP use the `mcp/README.md` fallback table)
  (DFS-PORT: the private vault-side `search-vault.py` CLI is not shipped with this repo)
```

Prompt human partner: `Codebase onboarded. Test baseline verified ({pass_count} passed). Ready to develop?`
