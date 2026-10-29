# dfs-handoff — extended playbook (tier 3)

Loaded on demand by `dfs-handoff/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

### Phase 3b: WORKMEMORY 卫生（仅当 Phase 0.5 探测到项目约定；2026-10-17 补入）

交接不只是"给下一个 agent 一张卡"，还要把**共享记忆层**留在可继续工作的状态：

1. **轮转（HOT → WARM）**：若事件数 > 项目配置的保留阈值 × 1.5 ⇒ **下一个开始工作的 agent 顺手执行**（不要等有人想起来）：
   - 最老事件按**事件日期**移入 `archive/work-YYYY-MM-DD.log`（已存在的分片追加在其后，保持时间序）；
   - 热层只留最新 N 条；**只移动、不改字节**（禁止顺手改写/美化/去重/重排任何事件正文）；
   - **MUST 执行并发守卫**：轮转前**立即重读**事件日志（**禁止**用会话早期快照当基准）；轮转后复核 ① 末条事件头不变 ② **事件集合守恒**（`grep -h '^### ' work.log archive/*.log | sort | uniq -c` 的 before/after `diff` **无输出**）。
2. **COLD digest**：**仅在用户显式要求**（如"把上月总结成 digest"）时生成 `cold/digest-YYYY-MM.md`，并**同步刷新项目 primer**（如 `PROJECT_OVERVIEW.md`）。未要求 ⇒ 不做。
3. **目录与索引（按项目协议，别硬编码）**：
   - 超限事件正文放 `notes/`（若项目有该目录）；
   - **closed 的 handoff MUST 移入 `archive/`**，并从 Active handoffs 节改挂到「已归档」段；
   - **热层索引 MUST 保持极小**：若项目已拆出 `INDEX-topics.md`，则主题索引与蒸馏登记写**那里**（WARM，按需加载），`INDEX.md` 只留配置 + 文件清单 + Active/已归档 handoffs + 一行指针。

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
