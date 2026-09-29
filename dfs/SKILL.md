---
name: dfs
description: Route developer intent to the right Defensive Skills workflow. Use when the user asks for a coding task and you must decide which dfs skill to load, or when it is unclear where to start.
disable-model-invocation: true
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [router, navigation, workflow, dfs]
    related_skills: [dfs-plan, dfs-exec, dfs-save, dfs-handoff]
---

# Defensive Skills Master Router & Environment Detector

> **Invocation — explicit only.** `disable-model-invocation: true` is honored by Claude Code and ignored
> elsewhere, so the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Intelligently detect workspace environment state and route developer intent to the optimal Defensive Skill.

## 🧭 Environment-Aware Auto-Detection (Step 0)
Before routing, perform non-invasive environment inspection:
1. **Empty / Fresh Directory**: No `.git` or no `.githooks` ➔ Recommend `/dfs-bootstrap`
2. **Existing Codebase (Unonboarded)**: No `.agent-context.md` ➔ Recommend `/dfs-onboard`
3. **Active Implementation Plan**: `implementation_plan.md` or `.vault-exec-ledger.json` present ➔ Recommend `/dfs-exec` or `/dfs-pipeline`
4. **Fuzzy Idea, No Design Yet**: Vague user prompt ➔ Recommend `/dfs-spark`（生成方案），需要压边界时再接 `/dfs-grill`
5. **Bug / Outage / Test Failure**: Stack trace or error log ➔ Recommend `/dfs-debug` (dev) or `/dfs-incident` (prod outage)
6. **Database Schema Evolution**: Altering columns or tables ➔ Recommend `/dfs-migrate`
7. **Production Release / Tagging**: Version bump or changelog generation ➔ Recommend `/dfs-release`

---

## 🗺️ 23-Skill Lifecycle Navigation Matrix

| Engineering Stage | Trigger Skill | Core Capability & Deliverable |
|---|---|---|
| **0. 入口与接手** | `/dfs`<br>`/dfs-bootstrap`<br>`/dfs-onboard` | • 意图路由与环境探测（本表入口）<br>• 仓库安全与防泄露钩子筑基<br>• 代码库极速接手与 Ground Truth 单测基线捕获 |
| **1. 需求与架构** | `/dfs-spark`<br>`/dfs-grill`<br>`/dfs-adr`<br>`/dfs-research` | • 模糊需求定档与规格书生成<br>• 双镜头 (用户/技术) 极限审讯与前沿决策树<br>• MADR 架构决策自增归档<br>• 外部证据分级调研并沉淀入库 |
| **2. 规划与执行** | `/dfs-plan`<br>`/dfs-exec`<br>`/dfs-pipeline`<br>`/dfs-migrate` | • 细粒度任务拆解与子代理 Prompt 脚手架生成<br>• 多子代理 TDD 派发 + Maker-Checker 状态机 (Zero-Edit)<br>• 端到端 Git Worktree 隔离开发流水线<br>• 零停机数据库迁移 (Expand/Contract 五步阶梯) |
| **3. 质量与排障** | `/dfs-tdd`<br>`/dfs-refactor`<br>`/dfs-debug`<br>`/dfs-incident` | • 契约 TDD 与伪绿变异防线<br>• 极简主义重构 (卫语句展平、YAGNI)<br>• 4步强制根因排障 (复现断言前置与自愈反哺)<br>• 生产事故止血、5-Whys 溯源与无指责复盘 |
| **4. 审计与基准** | `/dfs-perf`<br>`/dfs-review`<br>`/dfs-team` | • 多语言基准压测 CLI (-benchmem, -race, EXPLAIN)<br>• 7语言 RFC 2119 规范与红黄牌门禁<br>• 6大专家全栈 Swarm 并发会审 |
| **5. 交付与沉淀** | `/dfs-release`<br>`/dfs-save`<br>`/dfs-inbox-consolidate`<br>`/dfs-handoff`<br>`/dfs-interview` | • 语义化发布、变更日志自动化与回滚预案<br>• Karpathy 对话即沉淀 (前置查重入库 99-Inbox)<br>• 99-Inbox 草稿分流归档至 DFS 归宿<br>• 会话收尾与 1-Click 续接交接卡<br>• 1v1 高压技术答辩与自适应难度阶梯 |

---

## ⚡ Quick Intent Dispatch Examples
- User: *"帮我看看这个新项目"* ➔ Run `/dfs-onboard`
- User: *"我想做一个新功能，但还不确定怎么设计"* ➔ Run `/dfs-spark`
- User: *"这个报错怎么解决？"* ➔ Run `/dfs-debug`
- User: *"准备开始写代码执行计划"* ➔ Run `/dfs-exec`
- User: *"我们要结束今天的开发"* ➔ Run `/dfs-handoff`

## 🧪 Worked example — detection to route

Observed workspace (Step 0): `.git` yes · `.githooks` yes · `.agent-context.md` yes · no `implementation_plan.md`

```
$ user: CI 打包崩了，报 CFBundleIdentifier missing
$ <pasted build log>

[dfs] Step 0 case 5 — stack trace / error log
      bootstrapped (.githooks) and onboarded (.agent-context.md) -> cases 1 and 2 skip
      a build-time failure, not a live outage                    -> not /dfs-incident
=> route: /dfs-debug
```
