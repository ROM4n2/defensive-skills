---
name: dfs-bootstrap
description: Initialize a repository with security git hooks and DFS rule anchors. Use when starting a new repo or adding DFS guardrails to an existing one.
license: MIT
metadata:
  version: 0.2.1
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
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

Initialize any new or existing repository (`D:/Code/{project}`) with zero-leak secret detection git hooks and 3-line Defensive Skills knowledge anchors.

## The 4-Phase Bootstrap Protocol

### Phase 1: Security Git Hooks & .gitignore Protection (MUST)
1. Verify `.gitignore` contains all sensitive patterns (list MUST stay in sync with `bootstrap.ps1` `$requiredIgnores` — it is the single source of truth):
   ```gitignore
   # Secrets & Local Configs
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
2. Install `.githooks/pre-commit` from `templates/githooks-pre-commit.sh` with **Unix (LF) line
   endings and no UTF-8 BOM** — a CRLF or BOM shebang stops git from spawning the hook
   (`cannot spawn .githooks/pre-commit`). Normalize the copied file to LF/no-BOM before committing:
   ```bash
   mkdir -p .githooks
   cp templates/githooks-pre-commit.sh .githooks/pre-commit   # first line MUST be exactly: #!/usr/bin/env bash
   chmod +x .githooks/pre-commit
   git config core.hooksPath .githooks
   ```
3. **Pin LF in `.gitattributes` — otherwise the hook re-breaks on fresh checkout.** On Windows
   `core.autocrlf=true` silently rewrites `pre-commit` to CRLF when git materializes it, undoing the
   normalization above. The repo must pin the endings, not just write LF once:
   ```gitattributes
   .githooks/** text eol=lf
   WORKMEMORY/** text eol=lf   # append-only UTF-8 log; keeps git diffs sane
   *.sh text eol=lf
   ```
   After adding `.gitattributes`, run `git add --renormalize .` so the stored blobs are LF.
4. The secret-scan regex set (OpenAI/AWS/GitHub/Google/Slack keys, JWT, PEM private-key blocks,
   keystore magic bytes) lives inside `templates/githooks-pre-commit.sh`; keep the installed hook and
   the template in sync.

---

### Phase 2: Knowledge Vault Anchor Injection (MUST)
Create/Update project-level `CLAUDE.md` and `.agent-rules.md` in repository root with the standardized 3-line anchor:

```markdown
## 📖 工程规范与避坑检索
- 核心规范源：`{vault_root}/AGENTS.md`（`{vault_root}` 按 `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → 向上查找 `AGENTS.md` 解析，契约见 `dfs/references/vault-root-resolution.md`）
- 检索避坑规范：调用 `search_vault` MCP 或 `python {vault_root}/scripts/search-vault.py "<关键词>"`
- 发现新踩坑自动沉淀：写草稿至 `{vault_root}/99-Inbox/YYYY-MM-DD-{topic}.md`
```

---

### Phase 3.5: WORKMEMORY Scaffold & Agent Distillation (MUST)
Run the mechanical scaffold, then distill the primer:

1. Run `pwsh {vault_root}/scripts/bootstrap.ps1` (idempotent — it scaffolds `WORKMEMORY/` 4-piece set from `Templates/workmemory/`, injects anchors, and skips existing state).
2. **Agent distillation step (script cannot do this)**: read the project codebase and fill `WORKMEMORY/PROJECT_OVERVIEW.md` from its template skeleton — 一段话项目定位（目标/技术栈/运行方式）、当前状态（进行中工作与待办）、高频坑（现象→根因→解法）。Replace the placeholder comments with real content distilled from README/AGENTS.md/git log/ADR.
3. Append a bootstrap `NOTE` event to `work.log` recording what was distilled (identity: ask user for model-id if unsure).
4. Event discipline (SHOULD): `WORK_START` 附「不做范围」一行（明确排除的功能/重构/顺手修改）；`WORK_END` 收尾时做回写检查——稳定结论回写（dfs/模块文档/INDEX）、临时产物（日志/真实数据/凭据/截图）不入库。
5. Protocol reference: `{vault_root}/01-Rules/CROSS-AGENT-MEMORY.md`; canonical instance: the DeLector repo's `WORKMEMORY/PROTOCOL.md`.

---

### Phase 4: Binary Verification & Mechanical Test (HARD GATE)
A green `bash .githooks/pre-commit` on a clean tree proves only that the hook does not crash — it
does NOT prove it blocks anything. Verify the barrier with these probes before claiming success:

1. **Clean tree** — `bash .githooks/pre-commit` must exit 0 (no false positive on repo content).
2. **Adversarial (content)** — stage a throwaway file holding a synthetic key, e.g.
   `python -c "open('__probe__.txt','w').write('k = sk-' + '0'*32)" && git add __probe__.txt`
   （探针内容用**运行时拼接**，不把 `sk-` 字面量写进本文件：本仓是**公开**仓，字面量既会命中本仓 hook，也可能命中 GitHub 的 secret scanning —— 拼接出的内容仍能触发 hook，探针效力不变。）
   Then run `git commit` — it MUST exit 1 with a `[LINE]` attribution, and `git rev-parse HEAD` MUST
   be unchanged (the commit was truly aborted, not merely warned).
3. **Adversarial (filename)** — `printf 'x=1' > .env && git add -f .env`; the hook MUST exit 1 with `[NAME]`.
4. **Checkout durability (Windows)** — `rm .githooks/pre-commit && git checkout -- .githooks/pre-commit`,
   then confirm `file .githooks/pre-commit` reports plain `ASCII text`, not `with CRLF line terminators`
   (catches a missing `.gitattributes` LF pin).
5. Clean up every probe (`git reset -q HEAD ...` + `rm -f`), confirm the worktree is back to the intended state.
6. Announce: `✅ Repository bootstrapped with zero-leakage pre-commit guard and Vault anchors.`
