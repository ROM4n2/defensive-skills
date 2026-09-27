---
name: dfs-pipeline
description: Execute end-to-end Git Worktree multi-skill pipeline.
disable-model-invocation: true
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pipeline, git-worktree, multi-skill, orchestrator, autonomous]
    related_skills: [dfs-spark, dfs-grill, dfs-adr, dfs-plan, dfs-exec, dfs-perf, dfs-team, dfs-save]
---

# DFS-PIPELINE: End-to-End Autonomous Engineering Pipeline

Orchestrate the full development lifecycle with Git Worktree branch isolation, multi-subagent task dispatching (`/dfs-exec`), performance profiling, multi-expert review, and automated knowledge harvesting.

## The 8-Stage Pipeline Ledger

```markdown
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Vault End-to-End Delivery Pipeline                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Stage 1: /dfs-spark    ➔ 0-to-1 需求发散与规格书定型 (Design Spec)                  │
│ Stage 2: /dfs-grill    ➔ 双镜头极限架构压测与前沿决策树推进                         │
│ Stage 3: /dfs-adr      ➔ 自动编号与 MADR 标准架构决策记录归档                       │
│ Stage 4: /dfs-plan     ➔ 任务细粒度拆解与 Subagent Prompt 脚手架生成                │
│ Stage 5: Git Worktree    ➔ 自动创建独立分支工作区 (.worktrees/feat-{name})            │
│ Stage 6: /dfs-exec     ➔ 多子智能体 TDD 开发 + Maker-Checker 双人复核流水线         │
│ Stage 7: /dfs-perf     ➔ 基准压测 (-benchmem)、竞态检测 (-race) 与性能卡片生成      │
│ Stage 8: /dfs-team     ➔ 6 专家全栈 Swarm 并发终审与 PR 合并门禁                    │
│ Stage 9: /dfs-save     ➔ Karpathy 对话即沉淀，经验入库 99-Inbox/                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Execution Protocol

### Step 1: Worktree Setup
When starting feature execution, create an isolated git worktree:
```bash
git worktree add -b feat-{feature_name} .worktrees/feat-{feature_name} master
```

### Step 2: Autonomous Execution Loop
Dispatch `/dfs-exec` inside the isolated worktree directory, tracking tasks via `.vault-exec-ledger.json`.

### Step 3: Verification & Multi-Expert Gate
1. Run test suite and benchmarks via `/dfs-perf`.
2. Run multi-expert audit via `/dfs-team`.
3. If all P0/P1 issues resolved: Merge worktree branch to master and remove worktree.
4. Call `/dfs-save` to harvest session learnings.
