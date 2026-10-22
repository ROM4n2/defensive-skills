---
name: dfs
description: Route developer intent to the right Defensive Skills workflow. Use when the user asks for a coding task and you must decide which dfs skill to load, or when it is unclear where to start.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
  hermes:
    tags: [router, navigation, workflow, dfs]
    related_skills: [dfs-plan, dfs-exec, dfs-save, dfs-handoff, dfs-bootstrap, dfs-onboard, dfs-maintain, dfs-spark, dfs-debug]
---
# Defensive Skills Master Router & Environment Detector

> **Invocation — explicit only.** This skill carries `disable-model-invocation: "true"` under
> `metadata`, the Agent Skills extension slot, which no harness enforces as a hard switch
> (Claude Code honored it only at the old top-level location; Hermes never implemented it), so
> the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Intelligently detect workspace environment state and route developer intent to the optimal Defensive Skill.

## Environment-Aware Auto-Detection (Step 0)
Before routing, perform non-invasive environment inspection:
1. **Empty / Fresh Directory**: No `.git` or no `.githooks` -> Recommend `/dfs-bootstrap`
2. **Existing Codebase (Unonboarded)**: No `.agent-context.md` -> Recommend `/dfs-onboard`
2b. **Onboarded but no repo invariants anchor** (`.agent-context.md` exists, but no `AGENTS.md` / `CLAUDE.md` / `docs/agents/INVARIANTS.md` carrying the red lines and known traps) -> Recommend a `/dfs-onboard` Phase-3 refresh: every later subagent brief must otherwise restate the invariants in full, which is the largest avoidable token cost in a multi-dispatch run.
3. **Active Implementation Plan**: `implementation_plan.md` or `.vault-exec-ledger.json` present -> Recommend `/dfs-exec` or `/dfs-pipeline`
4. **Fuzzy Idea, No Design Yet**: Vague user prompt -> Recommend `/dfs-spark` (spec definition), follow with `/dfs-grill` if boundaries are fuzzy
5. **Bug / Outage / Test Failure**: Stack trace or error log -> Recommend `/dfs-debug` (dev) or `/dfs-incident` (prod outage)
6. **Database Schema Evolution**: Altering columns or tables -> Recommend `/dfs-migrate`
7. **Production Release / Tagging**: Version bump or changelog generation -> Recommend `/dfs-release`
8. **Lingering Worktrees / Dirty Workspace**: Residual worktree branches or stale locks -> Recommend `/dfs-maintain`
9. **Unverified Audit Findings / Review Disputes**: Dangling UNVERIFIED claims -> Recommend `/dfs-verify`
10. **Recurring Defect Patterns / Missing Gates**: Repeated bug classes -> Recommend `/dfs-gate`

---

## 29-Skill Lifecycle Navigation Matrix (1 Master Router + 28 Sub-Skills)

| Engineering Stage | Trigger Skill | Core Capability & Deliverable |
|---|---|---|
| **0. 入口与维护** | `/dfs`<br>`/dfs-bootstrap`<br>`/dfs-onboard`<br>`/dfs-maintain` | • 意图路由与环境探测（本表入口）<br>• 仓库安全与防泄露钩子筑基<br>• 代码库极速接手与 Ground Truth 单测基线捕获<br>• 例行仓库卫生维护、Worktree 垃圾修剪与基准上下文物理刷新 |
| **1. 需求与架构** | `/dfs-spark`<br>`/dfs-grill`<br>`/dfs-adr`<br>`/dfs-research` | • 模糊需求定档与规格书生成<br>• 双镜头 (用户/技术) 极限审讯与前沿决策树<br>• MADR 架构决策自增归档<br>• 外部证据分级调研并沉淀入库 |
| **2. 规划与执行** | `/dfs-plan`<br>`/dfs-exec`<br>`/dfs-orchestrate`<br>`/dfs-pipeline`<br>`/dfs-migrate`<br>`/dfs-upgrade` | • 细粒度任务拆解与子代理 Prompt 脚手架生成<br>• 多子代理 TDD 派发 + Maker-Checker 状态机 (Zero-Edit)<br>• 多智能体独占文件分区、对抗性 Brief 构造与串行防竞争调度<br>• 端到端 Git Worktree 隔离开发流水线<br>• 零停机数据库迁移 (Expand/Contract 五步阶梯)<br>• 依赖升级破坏性评估与分级演进 |
| **3. 质量与排障** | `/dfs-tdd`<br>`/dfs-refactor`<br>`/dfs-debug`<br>`/dfs-incident`<br>`/dfs-gate` | • 契约 TDD 与伪绿变异防线<br>• 极简主义重构 (卫语句展平、YAGNI)<br>• 4步强制根因排障 (复现断言前置与自愈反哺)<br>• 生产事故止血、5-Whys 溯源与无指责复盘<br>• 缺陷模式物理门禁化 (CI/pre-commit 脚本化与变异自证) |
| **4. 审计与基准** | `/dfs-perf`<br>`/dfs-review`<br>`/dfs-team`<br>`/dfs-verify` | • 多语言基准压测 CLI (-benchmem, -race, EXPLAIN)<br>• 7语言 RFC 2119 规范与红黄牌门禁<br>• 6大专家全栈 Swarm 并发会审<br>• UNVERIFIED 疑似缺陷与审计指控核实 (否定式检索证明缺失) |
| **5. 交付与沉淀** | `/dfs-release`<br>`/dfs-save`<br>`/dfs-inbox-consolidate`<br>`/dfs-handoff`<br>`/dfs-interview`<br>`/dfs-agent-sdk` | • 语义化发布、变更日志自动化与回滚预案<br>• Karpathy 对话即沉淀 (前置查重入库 99-Inbox)<br>• 99-Inbox 草稿分流归档至 DFS 归宿<br>• 会话收尾与 1-Click 续接交接卡<br>• 1v1 高压技术答辩与自适应难度阶梯<br>• pi-agent SDK 与企业级 LLM 接口接入 |

---

## [NOTE] Quick Intent Dispatch Examples
- User: *"帮我看看这个新项目"* -> Run `/dfs-onboard`
- User: *"我想做一个新功能，但还不确定怎么设计"* -> Run `/dfs-spark`
- User: *"这个报错怎么解决？"* -> Run `/dfs-debug`
- User: *"准备开始写代码执行计划"* -> Run `/dfs-exec`
- User: *"我们要结束今天的开发"* -> Run `/dfs-handoff`

## [NOTE] Worked example — detection to route

Observed workspace (Step 0): `.git` yes · `.githooks` yes · `.agent-context.md` yes · no `implementation_plan.md`

```
$ user: CI 打包崩了，报 CFBundleIdentifier missing
$ <pasted build log>

[dfs] Step 0 case 5 — stack trace / error log
      bootstrapped (.githooks) and onboarded (.agent-context.md) -> cases 1 and 2 skip
      a build-time failure, not a live outage                    -> not /dfs-incident
=> route: /dfs-debug
```
