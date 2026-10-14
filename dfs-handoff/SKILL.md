---
name: dfs-handoff
description: Generate a session wrap-up and a 1-click continuation card. Use when the user wants to pause, hand off, or resume later in a fresh session.
disable-model-invocation: true
version: 0.3.0
author: Haoyu
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [handoff, session-end, continuation-card, workmemory]
    related_skills: [dfs-save, dfs-exec]
---

# DFS-HANDOFF: Session Wrap-up & 1-Click Agent Handoff (v3)

> **Invocation — explicit only.** `disable-model-invocation: true` is honored by Claude Code and ignored
> elsewhere, so the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Capture working state at the end of a session, land user corrections before they evaporate, harvest uncommitted learnings to `99-Inbox/`, verify clean git status, and generate a token-budgeted continuation card for the next agent session.

> 捕获依据：ADR-0004 §4.1-7（纠正随 `WORK_END` 可选一行捕获，零额外步骤）；成熟纠正导流 `99-Inbox/`。

## The 7-Phase Handoff Protocol (v3)

> **v3 变更（2026-10-14，实测事故）**：补上「**项目有约定时必须写盘**」这一步。此前本 skill 只交付**对话内的交接卡**，全文不提 `handoff_*.md` / `WORKMEMORY`；而仓库协议（例：DeLector `WORKMEMORY/PROTOCOL.md` §4）要求发送方做三件事 —— **写包 + 记交接事件 + 更新索引的 Active handoffs 节**。后果实测：6 个项目 handoff 文件数全为 0、索引长期为「（无）」⇒ 这步**从未真正执行过**。同族教训：**仓库协议已规定、而 skill 没接上的步，属于 skill 的缺口**（与 `/dfs-exec` HARD GATE 4 的"不在执行路径上的规则等于不存在"同一根因）。

### Phase 0: Corrections Scan（agent MUST 自扫，先于一切收尾）

agent 自扫本次会话记录，列出候选纠正（做法/结论/方向被用户改过的节点），交用户**确认/否决**——不要求用户回忆。
- **有纠正 →**：
  1. `WORK_END` 事件可选附一行 `本次被纠正: <1 行>`（与同事件既有的「推荐做回写检查」同款语气，可选/推荐，非 MUST，零额外步骤）；
  2. 本会话落不了地的纠正 → 交接卡 `## Corrections` 节逐条 1 行（原话 + 已做/未做）。
- **成熟纠正**（非项目特例、可泛化为规则/规范）：导流 `/dfs-save` 或 `save_inbox_draft` 沉淀至 `99-Inbox/`。
- 用户否决全部候选 → 不附该行即可，**不跳过自扫本身**。

### Phase 0.5: Convention Detection（MUST：先问项目，别把默认形态当通用形态）

写任何收尾产物之前先探测**项目自己的约定**，并按它执行：
1. 项目里是否存在跨 agent 工作记忆约定？典型标记：`WORKMEMORY/PROTOCOL.md`（或 `AGENTS.md` 指向的等价物）。
2. **存在 → 读它**：handoff 包的字段与存放路径、交接事件类型名、索引节名，**一律以该文件为准，不要硬编码某一种 schema**。
3. **不存在 → Card-only 模式**：跳过 Phase 3，只交付 Phase 4 的交接卡（这是本 skill 原先的形态，仍适用于无约定的项目）。
4. 记下该约定的交接事件类型（例：`HANDOFF`）供 Phase 3 使用。

### Phase 1: Karpathy Ingestion Check (Harvest Before Exit)
Ask: *Did this session discover any non-obvious bugs, workarounds, or reusable patterns?*
- If yes: Call `save_inbox_draft` MCP or run `/dfs-save` to persist draft in `99-Inbox/`.
- If no: Proceed to Phase 2.

### Phase 2: Ground-Truth State Capture
1. Git Status: `git status --short` & `git log -n 1 --oneline`
2. Test Evidence: Run test suite (`pytest`, `go test ./...`) and record passing count.
3. Ledger Status: Inspect `.vault-exec-ledger.json` for remaining tasks.

### Phase 3: Handoff Package（**仅当 Phase 0.5 探测到项目约定；否则跳过**）

按项目协议**写盘**，不是只在对话里说。以 DeLector `WORKMEMORY/PROTOCOL.md` §4 为例，发送方 MUST 做三件事：
1. **写包** `<约定的目录>/handoff_<topic>.md`：前置元数据（`to` / `from` / `created` / `role` / `status: open`）+ 四节正文（任务上下文 · 已完成含证据 · 未完成与下一步 · 风险与坑）；
2. **记交接事件**：在项目的事件日志追加该约定规定的事件类型（例 `HANDOFF`），**事件头 MUST 合规**（协议要求的 schema：日期 + 时间 + **裸类型 token**）；
3. **更新索引**：把包挂进约定指定的索引节（例 `INDEX.md` 的 `## Active handoffs`），把「（无）」替换为指向该包的一行。

**反模式（实测踩过）**：只把状态写进对话；只记 `WORK_END` 而不写包；写了包却不更新索引。三者任缺其一，下一个 agent / 下一次会话**都拿不到**，交接等于没做。包写好后，Phase 4 的交接卡**只给指针，不复制包内容**。

### Phase 4: 1-Click Continuation Card Generation（预算分节）
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

### Phase 5: Output & Exit
Deliver the handoff card to the user, then **verify the 收尾三件套 actually landed**（仅当 Phase 0.5 探测到项目约定时）：包文件存在、交接事件已追加且**事件头合规**、索引节已从「（无）」更新为指向该包 —— 用一行 `ls` / `grep` **取证**，不要凭记忆宣称「写了」。再确认 every Phase 0 correction has landed（`WORK_END` 一行 or 交接卡 `## Corrections`），最后优雅收尾。
