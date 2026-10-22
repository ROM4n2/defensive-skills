---
name: dfs-pipeline
description: Execute an end-to-end Git Worktree multi-skill pipeline. Use when a task spans several DFS skills and each stage needs an isolated worktree.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
  hermes:
    tags: [pipeline, git-worktree, multi-skill, orchestrator, autonomous]
    related_skills: [dfs-spark, dfs-grill, dfs-adr, dfs-plan, dfs-exec, dfs-perf, dfs-team, dfs-save, dfs-orchestrate, dfs-maintain, dfs-verify]
---
# DFS-PIPELINE: End-to-End Autonomous Engineering Pipeline

> **Invocation — explicit only.** This skill carries `disable-model-invocation: "true"` under
> `metadata`, the Agent Skills extension slot, which no harness enforces as a hard switch
> (Claude Code honored it only at the old top-level location; Hermes never implemented it), so
> the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Orchestrate the full development lifecycle with Git Worktree branch isolation, multi-subagent task dispatching (`/dfs-exec`), performance profiling, multi-expert review, and automated knowledge harvesting.

## [MUST] The Worktree Isolation Invariant (RFC 2119 MUST)
> **Never execute multi-stage pipeline delivery directly on the main working tree.**
> All multi-skill feature implementations MUST take place within an isolated Git Worktree (`.worktrees/feat-{name}`) to ensure zero side-effects on primary work until all quality gates pass.

---

## The 9-Stage Pipeline Ledger

```markdown
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Vault End-to-End Delivery Pipeline                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Stage 1: /dfs-spark    -> 需求发散与规格书定型 (Design Spec)                            │
│ Stage 2: /dfs-grill    -> 双镜头极限架构压测与前沿决策树推进                            │
│ Stage 3: /dfs-adr      -> 自动编号与 MADR 标准架构决策记录归档                          │
│ Stage 4: /dfs-plan     -> 任务细粒度拆解与 Subagent Prompt 脚手架生成                   │
│ Stage 5: Git Worktree  -> 自动创建独立分支工作区 (.worktrees/feat-{name})               │
│ Stage 6: /dfs-exec     -> 多子智能体 TDD 开发 + Maker-Checker 双人复核流水线            │
│ Stage 7: /dfs-perf     -> 基准压测 (-benchmem)、竞态检测 (-race) 与性能卡片生成         │
│ Stage 8: /dfs-team     -> 6 专家全栈 Swarm 并发终审与 PR 合并门禁                       │
│ Stage 9: /dfs-save     -> Karpathy 对话即沉淀，经验入库 99-Inbox/                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Execution Protocol

### Step 1: Worktree Setup
When starting feature execution, create an isolated git worktree:
```bash
git worktree add -b feat-{feature_name} .worktrees/feat-{feature_name} master
```
- **Checkable Completion Criterion**:
  - Git worktree created in `.worktrees/`; verified branch pointer isolated from master.

### Step 2: Autonomous Execution Loop
Dispatch `/dfs-exec` inside the isolated worktree directory, tracking tasks via `.vault-exec-ledger.json`. Follow `/dfs-orchestrate` for multi-agent dispatch boundaries and file-occupancy partitioning.
- **Checkable Completion Criterion**:
  - `.vault-exec-ledger.json` reports all tasks `COMPLETED`; test suite verified 100% green within worktree.

### Step 3: Verification & Multi-Expert Gate
1. Run test suite and benchmarks via `/dfs-perf`.
2. Run multi-expert audit via `/dfs-team`.
3. If `/dfs-team` outputs UNVERIFIED findings or disputed claims: Route to `/dfs-verify` to obtain physical negative-search proof and verify reachability before accepting or rejecting findings.
4. If the pipeline uncovers a recurring defect pattern: Invoke `/dfs-gate` to convert the rule into an automated pre-commit or CI mechanical gate with mutation proof.
5. If all P0/P1 issues resolved: Merge worktree branch to master and invoke `/dfs-maintain` to prune worktrees (inner-first), unregister git metadata, and clean repository loose objects.
6. Call `/dfs-save` to harvest session learnings.
- **Checkable Completion Criterion**:
  - Consensus report from `/dfs-team` free of unresolved P0/P1 blockers (all UNVERIFIED claims resolved via `/dfs-verify`); worktree merged and pruned via `/dfs-maintain`.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Setting up a worktree takes time, so I'll run the pipeline directly on master."* | **Tainted Workspace & Unsafe States**: Pipeline failures leave dirty uncommitted files on the main working tree. | Mandatory Isolation: Always execute pipeline within `.worktrees/feat-{name}`. |
| *"Subagents reported green, so I can skip the /dfs-team swarm review."* | **Blind Spot Accumulation**: Maker-Checker per task misses cross-cutting architecture and database flaws. | Swarm Verification: Full pipeline requires multi-expert consensus before merging to master. |
| *"Merge completed cleanly, so we don't need to harvest learnings via /dfs-save."* | **Sediment Loss**: Non-obvious implementation traps discovered during the run are lost forever. | Mandatory Harvest: Call `/dfs-save` upon pipeline completion to record technical discoveries. |
| *"I'll leave the worktree around in case we need it later."* | **Disk Bloat & Lock Contention**: Lingering worktrees hold branch locks and confuse git operations. | Always clean up with `git worktree remove` after branch merge. |
