---
name: dfs-handoff
description: "Generate session wrap-up and 1-click continuation cards."
disable-model-invocation: true
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [handoff, session-end, continuation-card, workmemory]
    related_skills: [dfs-save, dfs-exec]
---

# DFS-HANDOFF: Session Wrap-up & 1-Click Agent Handoff (v2)

Capture working state at the end of a session, land user corrections before they evaporate, harvest uncommitted learnings to `99-Inbox/`, verify clean git status, and generate a token-budgeted continuation card for the next agent session.

> 协议依据：`CROSS-AGENT-MEMORY.md` §2.5（CORRECTION 事件 + corrections.md 账本）。Phase 0 与 Phase 1 的产出都进 `WORKMEMORY/corrections.md` 与 `work.log`（dfs 宿主 = `11-Agents/corrections.md`）。

## The 5-Phase Handoff Protocol (v2)

### Phase 0: Corrections Check（必问，先于一切收尾）
Ask the user, verbatim intent: *「这次会话里，你有没有纠正过我的做法、结论或方向？」*
- **有纠正 → MUST 三步**：
  1. 逐条把纠正写入交接卡 `## Corrections` 节（原话 1 行 + 已做/未做）；
  2. 项目 `WORKMEMORY/corrections.md` 账本追加一行（状态 `open`）+ `work.log` 追加 `CORRECTION` 事件（事件头规范见协议 §2.3）；
  3. 已在会话中落实的纠正 → 状态 `resolved`；**禁止**为"好看"把未验证的纠正标成 `closed`。
- **成熟纠正**（非项目特例、可泛化为规则/规范）：导流 `/dfs-save` 或 `save_inbox_draft`，账本「蒸馏去向」回填 `dfs://<路径>` 后置 `closed`。
- 用户明确说没有 → 记录 "no corrections" 一行即可，不跳过提问本身。

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
- **3. Unresolved Corrections**: User feedback, open rows in `WORKMEMORY/corrections.md` (or "none").
- **4. Pointers**: Path pointers to daily logs, agent audit trails, and corrections ledger.
- **5. 1-Click Continuation Prompt**: Copy-pasteable shell/agent resumption prompt.

### Phase 4: Output & Exit
Deliver handoff card to user, confirm every Phase 0 correction has a ledger row, and conclude session gracefully.
