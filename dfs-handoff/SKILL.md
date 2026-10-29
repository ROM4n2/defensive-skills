---
name: dfs-handoff
description: Generate a session wrap-up and a 1-click continuation card. Use when the user wants to pause, hand off, or resume later in a fresh session.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
  author: Defensive Skills contributors
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

> **Detailed playbook**: this skill's long-form sections were moved to [`references/handoff-phases.md`](references/handoff-phases.md). Load it when you need the full procedure, the worked example, or the field evidence — the constraints above are self-sufficient without it.

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
1. Git Status & Maintenance: Run `/dfs-maintain` to prune lingering subagent worktrees, clear git locks, and re-sync repository baselines; capture `git status --short` & `git log -n 1 --oneline`.
2. Test Evidence: Run test suite (`pytest`, `go test ./...`) and record passing count.
3. Ledger Status: Inspect `.vault-exec-ledger.json` for remaining tasks.

### Phase 3: Handoff Package（**仅当 Phase 0.5 探测到项目约定；否则跳过**）

按项目协议**写盘**，不是只在对话里说。以 DeLector `WORKMEMORY/PROTOCOL.md` §4 为例，发送方 MUST 做三件事：
1. **写包** `<约定的目录>/handoff_<topic>.md`：前置元数据（`to` / `from` / `created` / `role` / `status: open`）+ 四节正文（任务上下文 · 已完成含证据 · 未完成与下一步 · 风险与坑）；
2. **记交接事件**：在项目的事件日志追加该约定规定的事件类型（例 `HANDOFF`），**事件头 MUST 合规**（协议要求的 schema：日期 + 时间 + **裸类型 token**）；
3. **更新索引**：把包挂进约定指定的索引节（例 `INDEX.md` 的 `## Active handoffs`），把「（无）」替换为指向该包的一行。

**反模式（实测踩过）**：只把状态写进对话；只记 `WORK_END` 而不写包；写了包却不更新索引。三者任缺其一，下一个 agent / 下一次会话**都拿不到**，交接等于没做。包写好后，Phase 4 的交接卡**只给指针，不复制包内容**。

### Phase 3b: WORKMEMORY 卫生（仅当 Phase 0.5 探测到项目约定；2026-10-17 补入）

Rotate the append-only log at its threshold, verify the rotation conserved every event, refresh
the topic index and distillation registry, and archive closed handoffs. The rotation commands,
the conservation check, and the digest/primer rules are in
[`references/handoff-phases.md`](references/handoff-phases.md).

### Phase 4: 1-Click Continuation Card Generation（预算分节）

Generate the continuation card from `templates/continuation-card.md` within the 100-token budget:
factual bullets only, pointers to disk artifacts for detail. The budget split by section and the
template's required sections are in
[`references/handoff-phases.md`](references/handoff-phases.md).

### Phase 5: Output & Exit
Deliver the handoff card to the user, then **verify the 收尾三件套 actually landed**（仅当 Phase 0.5 探测到项目约定时）：包文件存在、交接事件已追加且**事件头合规**、索引节已从「（无）」更新为指向该包 —— 用一行 `ls` / `grep` **取证**，不要凭记忆宣称「写了」。再确认：① 若触发轮转阈值 ⇒ **已轮转**且守恒对账 `diff` 无输出；② 若用户要求了 digest ⇒ `cold/digest-YYYY-MM.md` 已生成且 primer 已刷新；③ closed 的 handoff 已入 `archive/` 且索引段已改挂。
最后确认 every Phase 0 correction has landed（`WORK_END` 一行 or 交接卡 `## Corrections`），最后优雅收尾。
---

## Checkable Completion Criterion
- Continuation card generated strictly within 100-token budget.
- If project protocol exists: handoff package written to disk, event logged, and active index updated with verified exit 0.

---

## Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I described what was done in the conversation, so the handoff is complete."* | **Context Amnesia**: Conversation text is lost upon fresh session startup. | When repository protocol specifies workmemory, MUST write the handoff package to disk, log the event, and update the index. |
| *"I will inline full test logs and complete diffs inside the continuation card."* | **Token Budget Exhaustion**: Large continuation cards overflow fresh session token budgets and degrade attention. | Enforce the 100-token budget: continuation cards contain brief factual bullets and point to disk artifacts for details. |
| *"I'll update the index without checking if the package was physically created."* | **Dangling Index Pointer**: Subsequent agents encounter broken links when attempting to load handoff packages. | Physically verify package file existence with `ls` or `read_file` before updating index markers. |
