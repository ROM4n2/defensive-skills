---
name: dfs-handoff
description: Generate a session wrap-up and a 1-click continuation card. Use when the user wants to pause, hand off, or resume later in a fresh session.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  disable-model-invocation: "true"
  hermes:
    tags:
      - handoff
      - session-end
      - continuation-card
      - workmemory
    related_skills:
      - dfs-save
      - dfs-exec
---

# DFS-HANDOFF: Session Wrap-up & 1-Click Agent Handoff (v2)

> **Invocation — explicit only.** `disable-model-invocation: true` is honored by Claude Code and ignored
> elsewhere, so the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Capture working state at the end of a session, land user corrections before they evaporate, harvest uncommitted learnings to `99-Inbox/`, verify clean git status, and generate a token-budgeted continuation card for the next agent session.

> 捕获依据：ADR-0004 §4.1-7（纠正随 `WORK_END` 可选一行捕获，零额外步骤）；成熟纠正导流 `99-Inbox/`。

## The 5-Phase Handoff Protocol (v2)

### Phase 0: Corrections Scan（agent MUST 自扫，先于一切收尾）

agent 自扫本次会话记录，列出候选纠正（做法/结论/方向被用户改过的节点），交用户**确认/否决**——不要求用户回忆。
- **有纠正 →**：
  1. `WORK_END` 事件可选附一行 `本次被纠正: <1 行>`（与同事件既有的「推荐做回写检查」同款语气，可选/推荐，非 MUST，零额外步骤）；
  2. 本会话落不了地的纠正 → 交接卡 `## Corrections` 节逐条 1 行（原话 + 已做/未做）。
- **成熟纠正**（非项目特例、可泛化为规则/规范）：导流 `/dfs-save` 或 `save_inbox_draft` 沉淀至 `99-Inbox/`。
- 用户否决全部候选 → 不附该行即可，**不跳过自扫本身**。

### Phase 1: Karpathy Ingestion Check (Harvest Before Exit)
Ask: *Did this session discover any non-obvious bugs, workarounds, or reusable patterns?*
- If yes: Call `save_inbox_draft` MCP or run `/dfs-save` to persist draft in `99-Inbox/`.
- If no: Proceed to Phase 2.

### Phase 2: Ground-Truth State Capture
1. Git Status: `git status --short` & `git log -n 1 --oneline`
2. Test Evidence: Run test suite (`pytest`, `go test ./...`) and record passing count.
3. Ledger Status: Inspect `.vault-exec-ledger.json` for remaining tasks.

### Phase 3: 1-Click Continuation Card Generation（v2 预算分节）
交接卡 MUST 遵守 token 预算：**≈75 词 ≈ 100 token**。必带节压缩到事实句；一切长内容用指针节导流，不内联。

Load the continuation card template via `read_file(path='templates/continuation-card.md')` to format the handoff card.

**预算表**：

| 节 | 上限 | 纪律 |
|---|---|---|
| 1. Breakpoint & Git State | ≤5 行 | 分支/commit/测试基线三事实 |
| 2. Completed vs Remaining | ≤10 行 | 一行一项，动词开头 |
| 3. Unresolved Corrections | ≤5 行 | 原话 1 行 + 未做原因；无纠正写 "none" |
| 指针节 | ≤3 条 | 细节/测试输出/长清单 → `10-Daily`、`11-Agents/logs`、文件路径指针 |

Key required sections in `continuation-card.md`:
- **1. Breakpoint & Git State**: Branch, commit hash/message, test passing baseline.
- **2. Completed vs Remaining**: One-line evidence for done items, one-line next action for pending.
- **3. Unresolved Corrections**: Corrections confirmed in Phase 0 but not yet landed in `WORK_END` (or "none").
- **4. Pointers**: Path pointers to daily logs and agent audit trails.
- **5. 1-Click Continuation Prompt**: Copy-pasteable shell/agent resumption prompt.

### Phase 4: Output & Exit
Deliver handoff card to user, confirm every Phase 0 correction has landed (`WORK_END` 一行 or 交接卡 `## Corrections`), and conclude session gracefully.
