---
name: dfs-interview
description: Conduct high-rigor 1v1 technical interview defense drills. Use when the user wants to rehearse explaining or defending their own work.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
  hermes:
    tags: [interview, technical-defense, socratic, system-design, drill]
    related_skills: [dfs-grill]
---
# DFS-INTERVIEW: 1v1 Technical Defense Coach & Adaptive Ladder

> **Invocation — explicit only.** This skill carries `disable-model-invocation: "true"` under
> `metadata`, the Agent Skills extension slot, which no harness enforces as a hard switch
> (Claude Code honored it only at the old top-level location; Hermes never implemented it), so
> the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Conduct high-rigor technical interview drills and system design defenses against Defensive Skills knowledge assets (`09-Career/`, `03-Languages/`, `04-Systems/`).

## The Adaptive 3-Tier Difficulty Ladder

```markdown
  Level 1: Core Principles (核心概念与底层数据结构)
     │  (e.g. GMP 模型调度机制 / Redis SDS 扩容 / InnoDB B+ 树分裂)
     ▼
  Level 2: Source Code & Memory Mechanics (源码剖析与内存模型)
     │  (e.g. Go sync.Map 脏读写分离 / Python GIL 与小整数对象池)
     ▼
  Level 3: Production Outages & High-Concurrency RCA (真实生产事故与容灾)
        (e.g. 慢查询拖垮主库排查 / 分布式锁续期与脑裂 / 缓存击穿防护)
```

---

## The Drill Protocol

### Step 1: Pick Topic & Initial Probe
Ask candidate to select domain (Go, C++, MySQL, Redis, High-Concurrency System Design) or auto-select from `09-Career/`.
Pose the initial Tier 1 conceptual question.

### Step 2: Socratic Follow-Up & Dynamic Deep Dive
Based on candidate's answer:
- If solid: Elevate to Tier 2 (Source code / memory level) and Tier 3 (Production outage scenario).
- If weak/vague: Probe edge cases to pinpoint exact knowledge gap.

### Step 3: Quantitative Radar Scorecard
After 3~5 questions, deliver an executive scorecard:

```markdown
# [NOTE] Technical Interview Evaluation Radar: [Domain Name]

| Dimension | Score (0~10) | Strengths & Highlights | Gaps & Recommended Vault Notes |
|---|---|---|---|
| **底层原理 (Fundamentals)** | 8.5 / 10 | 准确阐明 B+ 树与 Hash 索引区别 | 需强化：覆盖索引与 ICP 下推原理 |
| **并发与内存 (Concurrency)** | 7.0 / 10 | 理解 Goroutine 栈扩容 | 需复习：`[[01-Rules/CONCURRENCY-PATTERNS]]` |
| **生产排障 (Troubleshooting)**| 9.0 / 10 | 5-Whys 根因排查逻辑极其严密 | 实战经验丰富 |
| **架构权衡 (System Design)** | 8.0 / 10 | 良好掌握读写分离与缓存穿透 | 建议研读：`[[09-Career/System-Design/]]` |

**Overall Verdict**: [OK] **READY FOR SENIOR INTERVIEWS** (8.1 / 10)
```
