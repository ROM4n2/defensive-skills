---
name: dfs-bootstrap
description: Initialize a repository with security git hooks and DFS rule anchors. Use when starting a new repo or adding DFS guardrails to an existing one.
disable-model-invocation: true
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bootstrap, git-hooks, security, pre-commit, repo-init]
    related_skills: [dfs-onboard, dfs-save, dfs-pipeline]
---

# DFS-BOOTSTRAP: Repository Security & Knowledge Anchoring

> **Invocation — explicit only.** `disable-model-invocation: true` is honored by Claude Code and ignored
> elsewhere, so the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Initialize any new or existing repository (`<your projects root>/{project}`) with zero-leak secret detection git hooks and 3-line Defensive Skills knowledge anchors.

## The 4-Phase Bootstrap Protocol

### Phase 1: Security Git Hooks & .gitignore Protection (MUST)
1. Verify `.gitignore` contains all sensitive patterns (the list MUST stay in sync with `REQUIRED_IGNORES` in `scripts/bootstrap.py` — that script is the single source of truth, and `tests/test_bootstrap_script.py` fails if this repo's own `.gitignore` drifts from it):
   ```gitignore
   # Sensitive credentials & secrets
   config.yaml
   config.yml
   config.local.yaml
   .env
   .env.*
   *.env
   *.secret
   *.pem
   *.key
   *.local.json
   credentials.json
   ```
2. Configure `.githooks/pre-commit` from template `templates/githooks-pre-commit.sh`:
   ```bash
   mkdir -p .githooks
   cp templates/githooks-pre-commit.sh .githooks/pre-commit
   chmod +x .githooks/pre-commit
   git config core.hooksPath .githooks
   ```
3. Secret scanning regex pattern (zero-leak barrier embedded in `templates/githooks-pre-commit.sh`):
   ```bash
   grep -nE '(sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|AIza[A-Za-z0-9_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'
   ```

---

### Phase 2: Knowledge Vault Anchor Injection (MUST)
Create/Update project-level `CLAUDE.md` and `.agent-rules.md` in repository root with the standardized 3-line anchor:

```markdown
## 工程规范与避坑检索
- 核心规范源：`{vault_root}/AGENTS.md`（`{vault_root}` 按 `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → 向上查找 `AGENTS.md` 解析，契约见 `dfs/references/vault-root-resolution.md`）
- 检索避坑规范：调用 `search_vault` MCP（本仓库服务：`mcp/knowledge_server.py`）；无 MCP 时按 `mcp/README.md` 的降级表用 `search_files` 检索
  （DFS-PORT：原先的 `{vault_root}/` + `search-vault.py` CLI 是私有知识库侧实现，未随本仓库发布）
- 发现新踩坑自动沉淀：写草稿至 `{vault_root}/99-Inbox/YYYY-MM-DD-{topic}.md`
```

---

### Phase 3.5: WORKMEMORY Scaffold & Agent Distillation (MUST)
Run the mechanical scaffold, then distill the primer:

1. Run `python scripts/bootstrap.py --target .` (cross-platform, stdlib only; resolves its templates relative to this skill directory). Idempotent, and it does Phases 1, 2 and 3.5 in one pass: appends the required `.gitignore` patterns, installs `templates/githooks-pre-commit.sh` (never overwriting an existing hook) and sets `core.hooksPath`, injects the rule anchor, then scaffolds the `WORKMEMORY/` 4-piece set from `templates/workmemory/` and injects the WORKMEMORY anchor. Use `--dry-run` to preview, `--vault-root PATH` to override `$WIKI_PATH`.
   <!-- DFS-PORT: the private vault's Windows-only PowerShell bootstrap (which reads a private
        Templates/ tree) does not ship; this script is the port, and it resolves no absolute
        knowledge-base path unless one is actually configured. -->
   (Doing it by hand is still valid — Phases 1 and 2 above are the manual equivalent.)
2. **Agent distillation step (script cannot do this)**: read the project codebase and fill `WORKMEMORY/PROJECT_OVERVIEW.md` from its template skeleton — 一段话项目定位（目标/技术栈/运行方式）、当前状态（进行中工作与待办）、高频坑（现象→根因→解法）。Replace the placeholder comments with real content distilled from README/AGENTS.md/git log/ADR.
3. Append a bootstrap `NOTE` event to `work.log` recording what was distilled (identity: ask user for model-id if unsure).
4. Event discipline (SHOULD): `WORK_START` 附「不做范围」一行（明确排除的功能/重构/顺手修改）；`WORK_END` 收尾时做回写检查——稳定结论回写（dfs/模块文档/INDEX）、临时产物（日志/真实数据/凭据/截图）不入库。
5. Protocol reference: `{vault_root}/01-Rules/CROSS-AGENT-MEMORY.md`; canonical instance: the DeLector repo's `WORKMEMORY/PROTOCOL.md`.

---

### Phase 4: Binary Verification & Mechanical Test (HARD GATE)
Verify the pre-commit barrier actually works before claiming success:
1. Run pre-commit hook directly: `bash .githooks/pre-commit` (or `python scripts/bootstrap.py --dry-run --target .` to confirm the script's own plan first).
2. Verify exit code is 0.
3. Announce: `✅ Repository bootstrapped with zero-leakage pre-commit guard and Vault anchors.`
