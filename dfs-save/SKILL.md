---
name: dfs-save
description: Harvest non-obvious engineering solutions into 99-Inbox drafts. Use when a debugging session or task just produced a reusable insight worth saving.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags: [knowledge-harvesting, inbox, a-mac, karpathy-mode, learnings]
    related_skills: [dfs-inbox-consolidate, dfs-handoff]
    mcp_tools: [search_vault, save_inbox_draft]
---
# DFS-SAVE: Karpathy-Mode Knowledge Harvester & Ingestion Gate

Harvest non-obvious engineering solutions, environment gotchas, and architectural patterns discovered during coding sessions into `99-Inbox/` with **pre-save deduplication check** and **A-MAC quality validation**.

## [MUST] The A-MAC Ingestion Invariant (RFC 2119 MUST)
> **NO draft shall be persisted to `99-Inbox/` without passing the pre-save similarity check and the A-MAC Quality Gate.**
> Trivial one-off fixes (e.g. typos, single-line syntax fixes) fail A-MAC and MUST NOT be saved.

---

## [NOTE] This skill, or `/dfs-inbox-consolidate` / `/dfs-handoff`?

| | this skill | `/dfs-inbox-consolidate` | `/dfs-handoff` |
|---|---|---|---|
| The ask | **harvest** — capture a single discovered insight | **consolidate** — batch-classify inbox drafts into Vault | **handoff** — wrap up active session state |
| Output | a new `99-Inbox/` draft note | filed notes in `01-Rules/`, `03-Languages/`, etc. | a continuation card |
| Feeds | `99-Inbox/` | knowledge vault destinations | next session |

---

## The 3-Step Harvesting Workflow

```
  [Step 1: Novelty Check & Similarity Search (search_vault)]
                               │
                               ▼
  [Step 2: A-MAC Quality Gate & Structured Draft Composition]
                               │
                               ▼
  [Step 3: Call MCP Tool & Persist Physical Receipt]
```

### Step 1: Novelty & Similarity Check
1. **Pre-Save Deduplication Check**:
   - Query `search_vault(query="<topic_keywords>")` before composing a draft.
   - If an existing note addresses the identical problem with >70% similarity, propose appending to or updating the existing note instead of creating a duplicate draft.
2. **Checkable Completion Criterion**:
   - `search_vault` has executed and returned results; similarity is verified <70%, or explicit user agreement to update existing note is recorded.

### Step 2: Compose Draft File
1. **A-MAC Quality Gate Evaluation**:
   - The field schema lives in `dfs/references/a-mac-gate.md`. Reject trivial one-off bug fixes.
   - Load the draft structure specification via `read_file(path='templates/draft-template.md')`.
2. **Required Document Structure**:
   - **Frontmatter**: Valid YAML with `created: YYYY-MM-DD`, `type: source-notes`, `status: draft`, `tags: [...]`, and `source: "..."`.
   - **1. 现象与成因分析 (Symptom & Root Cause)**: Deceptive symptoms, broken state, and true root cause.
   - **2. 终极解决方案 (Permanent Solution & Code)**: Minimal, clean, reproducible code fix.
   - **3. 防御性工程规范 (Defensive Rule)**: Universal rule to prevent recurrence in other projects.
   - **4. 确定性评估信号 (Deterministic Evaluation Signals)**: Tool results count, error receipts, and environment state checks.
3. **Checkable Completion Criterion**:
   - Draft content adheres to `templates/draft-template.md`, includes all 4 mandatory sections, and has zero unpopulated placeholders.

### Step 2b: 草稿类型判定 — **成功做法也要沉淀**（2026-10-17 补入）

1. **判定这是 pattern 还是 troubleshooting**：
   - **pattern（做对了什么）**：可复用的**做法/模式**（如"重构前先立双向对账安全网 + 逐切片扫查"）⇒ tags 加 `category/pattern`，`type: pattern`，路由 `01-Rules/`（独立卡，命名不带日期）。
   - **troubleshooting（踩了什么坑）**：事故复盘/失败根因 ⇒ `category/troubleshooting`，通常**合并进对应规则的 §n** 而非新建卡。
   - [NOTE] **只沉淀事故是缺口**：多数会话的草稿全是事故驱动，导致"做法"永远失传。Ask 自己："这次有哪一步**做对了**、下次还想照做？"有 ⇒ 立 pattern 卡。
2. **Frontmatter 必带（在既有字段之外）**：
   - `description: "<一句话触发条件：什么场景该读本条>"` —— 用于相关性过滤，**MUST NOT** 写成标题复述。
   - `verified: YYYY-MM-DD` —— 最近一次人工复核日期（与 `updated` 不同：改错别字不算复核）。
   - 正文**必须写明「归档目标」**：`并入 <规则> §n（补实例，勿另立新规）` 或 `新增 <规则> §n`。没有归档目标的草稿是悬空知识。
3. **Checkable Completion Criterion**：
   - 已判定 pattern/troubleshooting、frontmatter 含 `description` + `verified`、正文含归档目标。

### Step 3: Call MCP Tool & Persist Physical Receipt
1. **Persist Draft**:
   - Call `save_inbox_draft(title=..., content=..., tags=...)` to write to `99-Inbox/` (or `.dfs-inbox/` fallback).
   - **`content` 里 MUST NOT 写 YAML frontmatter 块**：该工具自行生成 frontmatter（title/created/type/status/tags/source，并自动追加 `category/notes`）。你在 content 顶部写的 `description:` / `verified:` 会**原样落在闭合 `---` 之后变成正文**，Step 2b 的 frontmatter 要求因此静默落空（2026-10-22 实测两篇均中招）。
2. **Post-write frontmatter 修补 (MUST)**:
   - 保存后 `read_file` 前 20 行确认 `description` / `verified` 的物理位置；若在正文，用 `patch` 把它们移到闭合 `---` **之前**。
   - 修补后断言：把前两段 `---` 之间的文本喂 `yaml.safe_load`，必含 `{title, created, type, status, tags, source, description, verified}`，缺任一即失败。
3. **Verify Receipt**:
   - Verify the MCP response returns a successful path confirmation.
   - Announce to user: `[PASS] Knowledge harvested and persisted to 99-Inbox/ (passed A-MAC gate).`
4. **Checkable Completion Criterion**:
   - MCP call returns success with absolute path printed in terminal output.
   - 落盘文件的 frontmatter YAML 可解析且 8 个必备键齐全（物理回读，非工具自报）。

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Fixed a typo in line 12, let me create an inbox draft."* | **Inbox Noise Pollution**: diluting vault value with trivial churn. | Reject trivial fixes at the A-MAC gate; only harvest non-obvious, reusable learnings. |
| *"I already know this is a novel solution, so I can skip search_vault."* | **Fragmented Duplication**: duplicate notes drift out of sync across the vault. | Mandatory pre-save `search_vault` execution before drafting. |
| *"I'll write free-form text without YAML frontmatter."* | **Ingestion Failure**: `dfs-inbox-consolidate` fails to parse or route unstructured notes. | Frontmatter MUST include `created`, `type: source-notes`, `status: draft`, and taxonomy `tags`. |
| *"I'll invent new ad-hoc tags."* | **Taxonomy Drift**: orphaned tags that match no consolidation routing rules. | Align tags with existing vault taxonomy (`category/*`, `topic/*`, `tool/*`). |
| *"Only the bug/failure is worth saving; the thing that went right is obvious."* | **Practice Amnesia**: 可复用的成功做法从不入库，每次都从事故重新学。 | 每会话至少自问一次"哪一步做对了"；是 ⇒ 立 `category/pattern` 卡。 |
| *"归档时再想放哪，草稿里先不写。"* | **Stranded Knowledge**: 草稿没有归属，晋级时被猜路由或长期滞留 Inbox。 | 正文 MUST 写「归档目标」：并入 `X §n`（补实例）或新增 `X §n`。 |
| *"I'll skip description/verified; the title is enough."* | **Retrieval Miss & Silent Staleness**: 后续检索靠标题碰运气；旧结论没有失效机制（曾出现"登记表挂着待修、其实早已落地"把两个 agent 带偏一整轮的 A4 类事故）。 | Frontmatter MUST 带 `description`（触发句）与 `verified`（复核日期）。 |
