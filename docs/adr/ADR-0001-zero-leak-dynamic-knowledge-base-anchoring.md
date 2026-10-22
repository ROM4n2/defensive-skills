---
title: "ADR-0001: Zero-Leak Dynamic Knowledge-Base Anchoring and Tier-3 Degradation"
created: 2026-10-22
updated: 2026-10-22
type: project
tags:
  - category/project
  - topic/adr
  - topic/architecture
  - topic/security
  - topic/portability
status: stable
audience: both
---

# ADR-0001: Zero-Leak Dynamic Knowledge-Base Anchoring and Tier-3 Degradation

## 1. Context and Problem Statement
When scaffolding a new or existing repository via `dfs-bootstrap`, the generator injects knowledge-base anchors into `AGENTS.md`, `CLAUDE.md`, and `WORKMEMORY/PROTOCOL.md`.

Previously, `dfs-bootstrap/scripts/bootstrap.py` resolved `$WIKI_PATH` or `$OBSIDIAN_VAULT_PATH` at **scaffolding time** and baked the resolved absolute path (e.g. `D:/Obsidian/Coding/...`) directly into git-tracked files.

This introduced critical architectural issues:
1. **PII and Host Leakage**: Local filesystem structures, drive letters, and usernames are committed into git, violating zero-PII policies for open-source and collaborative repositories.
2. **One Rule, Two Implementations (Defect Class 4)**: The specification (`dfs/references/vault-root-resolution.md`) mandates dynamic 3-tier runtime resolution (`$WIKI_PATH` -> upward walk -> `./.agent/`), but the scaffold hardcoded a static one-time binding.
3. **Cross-Machine Breakage**: Cloned by another developer, run in CI, or placed in an environment without an Obsidian vault, the agent attempts to read non-existent absolute host paths, leading to errors or hallucinations.

## 2. Decision Drivers
- **Zero-PII & Open-Source Portability**: Git-tracked files must never require local drive letters, absolute host paths, or personal directory structures.
- **Dynamic Runtime Contract**: The agent must resolve external knowledge roots at session runtime, not static scaffolding time.
- **Graceful Tier-3 Degradation**: Repositories without an external knowledge base must remain 100% functional in standalone mode (project self-contained), without crashing, warning loops, or user friction.
- **Zero-Friction for Vault-Equipped Environments**: Developers with an active Knowledge Vault (`$WIKI_PATH` or MCP `search_vault`) must retain direct, seamless access to enterprise/personal rules without manual per-project path configuration.

## 3. Considered Options
- **Option A (Chosen)**: Dynamic Runtime Contract with Explicit Tier-3 Degradation
  - Git-tracked anchors declare dynamic resolution contracts (`search_vault` MCP or `$WIKI_PATH`), never concrete drive letters.
  - If no vault is present, the project operates in standalone self-contained mode (rules anchored in local `AGENTS.md`/`docs/`, draft findings stored in local `WORKMEMORY/notes/`).
  - [OK] Pros: 100% clean git diffs, portable across OSes and machines, zero leakage upon public push.
  - [NOTE] Cons: Agents running in environments without MCP or exported environment variables will not discover external vaults automatically (falls back to local rules).
- **Option B**: Tracked Standard Protocol + Ignored Local Override (`.agent/local.env`)
  - Track generic anchors in git; scaffold a `.gitignored` local configuration file storing the local machine's absolute vault path.
  - [NOTE] Pros: Allows machine-specific path binding without git contamination.
  - [NOTE] Cons: Additional file surface, redundant when `$WIKI_PATH` is already exported in the shell environment.
- **Option C**: Static Placeholder Manual Fill (`<YOUR_VAULT_ROOT>`)
  - Scaffold unresolved text markers for users to find-and-replace manually.
  - [NOTE] Pros: Simple template logic.
  - [NOTE] Cons: Prone to accidental commits of replaced paths, high human friction.

## 4. Decision Outcome
Chosen option: **Option A (Dynamic Runtime Contract with Explicit Tier-3 Degradation)**.

### Concrete Implementation Rules (RFC 2119)
1. **[MUST] No Absolute Paths in Tracked Artifacts**: `bootstrap.py` and all `templates/` MUST NOT bake host-specific drive letters or paths into generated files.
2. **[MUST] Standardized 3-Line Dynamic Anchor**:
   The injected rule anchor in `AGENTS.md` and `CLAUDE.md` MUST follow the portable dynamic format:
   ```markdown
   ## [NOTE] 工程规范与避坑检索
   - 核心规范源：优先通过 `search_vault` MCP 或环境变量 `$WIKI_PATH`/`$OBSIDIAN_VAULT_PATH` 解析；无外部知识库时以本仓 `AGENTS.md` 及 `docs/` 为自闭环规范源
   - 检索避坑规范：调用 `search_vault` MCP；无 MCP 时检索本地工程文档与测试套件
   - 发现新踩坑自动沉淀：优先调用 `save_inbox_draft`；无外部知识库时写草稿至 `WORKMEMORY/notes/YYYY-MM-DD-{topic}.md`
   ```
3. **[MUST] Dynamic Protocol Reference**:
   `WORKMEMORY/PROTOCOL.md` MUST refer to the abstract contract:
   `> 协议铁律规范层：优先解析 $WIKI_PATH/01-Rules/CROSS-AGENT-MEMORY.md；无外部知识库时以本文件为自包含真源。`
4. **[MUST] Scaffolder Decoupling**:
   `bootstrap.py` parameter `--vault-root` remains supported for local standalone initialization if explicitly passed, but the default behavior MUST generate portable dynamic anchors instead of inlining the executing host's environment variables.

## 5. Consequences and Trade-offs
- [OK] **Positive**: Any project bootstrapped with DFS can be published immediately to GitHub without path scrubbing or credential-exposure risks.
- [OK] **Positive**: Collaborators and CI runners on Linux/macOS work out-of-the-box without path mismatch errors.
- [OK] **Positive**: In local environments with `$WIKI_PATH` or MCP configured, agents continue to access the Obsidian Knowledge Vault with zero difference in behavior.
- [NOTE] **Negative**: Repositories without MCP or `$WIKI_PATH` cannot link to an external vault; they will strictly operate in project-local mode. This is the desired safe default.
- [MUST] **Compliance Guardrail**: Add a mechanical test to `tests/test_bootstrap_script.py` asserting that output files from `bootstrap.py` never contain drive-letter prefixes (`^[A-Za-z]:[\\/]`) or host usernames, regardless of local environment variables.
