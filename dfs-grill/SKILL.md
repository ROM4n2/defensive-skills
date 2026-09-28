---
name: dfs-grill
description: Stress-test an architecture through Dual-Lens Socratic inquiry. Use when the user wants their design challenged or pressure-tested before building.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, socratic-grill, dual-lens, adr, stress-testing]
    related_skills: [dfs-spark, dfs-adr, dfs-plan, dfs-team]
    mcp_tools: [omni_search]
---

# DFS-GRILL: Socratic Architecture Stress-Testing & Dual-Lens Panel

## ⚡ Scope Detection (MUST — 执行前第一步)

**在任何操作前，MUST 先检测当前 Vault 根目录**：

```python
# 检测逻辑：从 cwd 向上查找 AGENTS.md 或 CLAUDE.md
import os
def detect_vault_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "AGENTS.md")) or os.path.exists(os.path.join(d, "CLAUDE.md")):
            return d
        d = os.path.dirname(d)
    return None
```

- **检测到 Vault**：使用该 Vault 的目录结构（`01-Rules/`、`08-Projects/{project}/01-ADR/`、`99-Inbox/` 等）。
- **未检测到 Vault**：在当前项目根目录创建 `docs/adr/` 存放 ADR，不写入任何 Vault 路径。
- **跨 Vault 调用**：如果 skill 存储在全局目录但当前工作目录是另一个项目，**MUST NOT** 硬编码作者本机的 Vault 绝对路径——MUST 按 `dfs/references/vault-root-resolution.md` 的三级解析契约取值（`$WIKI_PATH` → 向上查找 `AGENTS.md`/`.obsidian` → 降级到当前项目 `./.agent/`），或退回当前项目根目录。

Interview and stress-test the developer's proposed plan, architecture, or design relentlessly across **Dual Lenses: User & Product Experience (用户体验层) + Technical & Systems Rigor (技术实现层)** against First Principles and The Ladder of Reuse until reaching a bulletproof consensus.

## Core Philosophy (Dual-Lens Socratic First Principles)
- **Dual-Lens Evaluation**: Every design must be validated on both **User Value (用户体验与刚需闭环)** and **Technical Resilience (技术高可用与健壮性)**.
- **The Frontier Protocol**: Work the tree in **tight numbered rounds** (1~2 high-leverage questions per round). Never overwhelm the human.
- **Decisions Belong to the Human**: Formulate clear trade-offs, state your recommended option (`➡️ <recommended>`), and wait for user decision.

---

## The Dual-Lens Multi-Perspective Grill Workflow

```markdown
                     用户提出方案 / 架构想法
                               │
                       [/dfs-grill 启动]
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
  【用户与产品体验层】                             【技术与工程实现层】
  🎯 产品经理与用户体验架构师                      🤖 后端并发 / 🎨 前端交互 / 🗄️ 数据库 / 🛡️ SRE
  - 拷问真实痛点 vs 伪需求                        - 拷问并发死锁、状态机竞态
  - 拷问操作旅程与认知摩擦                        - 拷问慢查询、弱网重连与熔断
       │                                               │
       └───────────────────────┬───────────────────────┘
                               ▼
                 主审官 (Lead Socratic Inquisitor)
                 - 汇总用户体验 + 技术架构的核心盲区
                 - 提炼 1~2 个最关键的前沿选择题
                 - 给出推荐方案 (➡️ Recommended)
                               ▼
                        用户拍板 (1句话)
                               ▼
                   自动归档正式 ADR-000x 架构决策
```

### Stage 1: Dual-Lens Background Inquest (Parallel Fan-out)
When the proposal is complex enough that background research pays for itself, dispatch the relevant seats concurrently across specialists.
- **Runtime-neutral dispatch**: In Hermes or standard agent environments, dispatch subagents via `delegate_task` with targeted role goals, scope, and instructions corresponding to the seat.
- **Claude Code fallback**: In Claude Code environments, dispatch the corresponding subagent seats (`~/.claude/agents/` as optional Claude-specific fallback) using the `subagent_type` values below.

| Lens | Subagent Role (`subagent_type`) | Grills on |
|---|---|---|
| Product & UX | `product-ux` | Real pain vs imagined need, journey friction, mental model, human-readable failure |
| Frontend & State | `frontend-architect` | State machine consistency, async races, offline/reconnect, render cost |
| Backend & Concurrency | `code-reviewer` | Thread/goroutine lifecycle, lock scope, transaction boundaries, silent errors |
| Storage & DBA | `dba-optimizer` | Schema shape, index coverage, query cost, lock ordering |
| SRE & Resilience | `sre-resilience` | Downstream timeouts, retries, failure modes, resource bounds |

**Only dispatch the lenses the proposal actually touches.** For a small or purely local design decision, skip Stage 1 entirely and go straight to Stage 3 — a five-agent panel on a two-file change is theatre, and the specialists will manufacture findings to justify their seat.

Never block the human on the fan-out: if a seat returns nothing substantive, drop it from the synthesis rather than padding a round with it.

### Stage 2: Context Ingestion & The Ladder of Reuse
Query `omni_search(proposal, scope='ladder')` to challenge against **The Ladder of Reuse (RFC 2119 MUST)**:
- **Level 0 (YAGNI / User Value)**: Does this feature actually solve a real user problem?
- **Level 1 (Stdlib/Existing Code)**: Does standard library or existing codebase already have a 3-line solution?
- **Level 2 (Existing Dependencies)**: Can existing libraries satisfy this without adding new dependencies?

### Stage 3: Frontier Round Protocol (Tight Socratic Rounds)
Synthesize the specialists' findings into tight, numbered questions:

```markdown
❓ **Q1 - <Product & User Experience Decision>**: <Socratic question body exposing user journey friction or value assumptions>
  - Option A: [Minimalist/High-Value approach]
  - Option B: [Feature-rich approach]

➡️ **Recommended**: Option A — [Concise justification on user value & simplicity]

---

❓ **Q2 - <Technical Architecture Decision>**: <Question about failure recovery, concurrency, or data consistency>

➡️ **Recommended**: [Concrete defense strategy]
```

Recompute the frontier on each user reply. Move outward until the frontier is completely resolved.

---

### Stage 4: Consensus & ADR Archiving
Summarize consensus into a formal **Architecture Decision Record (ADR-000x)**:
- Context, Decision Drivers (both User & Tech), Considered Options, Pros/Cons, Decision Outcome, and Consequences.
- Dual-Track Ingestion Gate:
  - Option 1: Draft in `08-Inbox/`
  - Option 2: Direct promotion to `05-Projects/{project}/01-ADR/` or `01-Rules/`.

---

## Downstream Relay
Prompt user: `Dual-lens consensus locked and ADR archived. Proceed to /dfs-plan (task breakdown) or /dfs-exec (autonomous multi-agent delivery)?`
