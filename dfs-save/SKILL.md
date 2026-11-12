---
name: dfs-save
description: "Use when harvesting a reusable insight into the vault."
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - knowledge-harvesting
    - inbox
    - a-mac
    - dedup-gate
    related_skills:
    - dfs-inbox-consolidate
    - dfs-handoff
    - dfs-debug
    mcp_tools:
    - save_inbox_draft
    - search_vault
---

# DFS-SAVE — 沉淀闸门

一道闸门定生死：过了就落盘，过不了就扔掉。本 skill 只做一件事——把会话里非直觉的收获压成一张 `99-Inbox/` 草稿。
## [MUST] 两条闸门

> **去重闸门**：没跑 `find_similar_drafts(...)` 拿到裁决，不得落盘。
> **结构闸门**：四节缺一不得落盘；typo、单行语法修复、一次性调试记录一律不落盘。

## Step 1 — 分流：这次做对了什么？

先定分支，再动笔：

| 分支 | 判据 | tags | 归档目标写法 |
|---|---|---|---|
| **pattern**（做对了什么） | 可复用的做法/模式，下次还想照做 | `category/pattern` | `新增 <规则> §n` |
| **troubleshooting**（踩了什么坑） | 事故复盘、失败根因 | `category/troubleshooting` | `并入 <规则> §n（补实例，勿另立新规）` |

每会话至少自问一次「哪一步**做对了**」。只收事故 = 做法永远失传。

**完成判据**：分支已定，且写出「归档目标」一句话——没有归属的草稿是悬空知识。

## Step 2 — 去重闸门：`find_similar_drafts`

```text
find_similar_drafts(title="<拟用标题>", content="<拟用正文>")
```

返回二元裁决 + 相似度（0.6×标题覆盖 + 0.4×正文 Jaccard）。按裁决走：

| verdict | 动作 |
|---|---|
| `DUPLICATE`（≥0.70） | 合并进已有笔记，**不新建**。确需独立卡时，把用户同意的原话记进草稿正文。 |
| `NEAR_DUPLICATE`（0.45~0.70） | 读那篇笔记：同一问题则合并；不同则在正文写明与它的**边界差异**。 |
| `NOVEL`（<0.45） | 新建。 |

要同时看库里已有结论文本，再补一次 `search_vault(query="<主题词>")`——它答的是「已有结论是什么」，不是「是否重复」。

**边界（别把闸门当作全库保证）**：比对粒度是**文档级**（文档 frontmatter 标题 + 正文 Jaccard）。已被并入某条大规则 §n 的内容，查不到标题级重复——那一段的重复由 `/dfs-inbox-consolidate` 在归档时判。本闸门守的是"再写一张重复草稿"。

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


## Step 3 — 结构闸门：四节 + 触发句

正文四节，缺一即退回（结构见 `templates/draft-template.md`）：

1. **现象与成因分析** — 症状、误导性归因（含被排除的错误假设）、真根因。
2. **终极解决方案** — 最小可复现代码/命令。
3. **防御性工程规范** — 一条能迁移到其他项目的规则，附判据。
4. **确定性评估信号** — 工具调用次数、错误回执原文、环境状态。

`description` 是**触发句**，回答「什么场景该读这条」，不是标题复述：
- 好：`当正文每句都被强制另起一行、或行内流被莫名断开时读这条。`
- 坏：`HTML5 Phrasing Content 陷阱` —— 这是主题，检索不到场景。

**完成判据**：四节齐全、无未填占位符、`description` 写的是场景而非主题。


## Step 4 — 落盘并取回执

```text
save_inbox_draft(
  title="...", content="...", tags=["category/pattern", "topic/..."],
  source="Session Discovery (<项目/PR 线索>)",
  description="<场景触发句>", verified="YYYY-MM-DD"
)
```

- `content` **不带** YAML frontmatter：工具负责生成，以 `---` 开头会被直接拒写。
- `description` / `verified` 是**参数**，不写进正文。工具把它们写进 frontmatter，写入前用 `yaml.safe_load` 自检必备键，失败则拒写。

**完成判据**（物理回读，不信工具自报）：`read_file` 前 12 行，`yaml.safe_load` 后 `{title, created, type, status, tags, source, description, verified}` 齐全。
通过后向用户报：`[PASS] Knowledge harvested and persisted to 99-Inbox/ (passed A-MAC gate).`


## [ANTI]

| 借口 | 危害 | 守卫 |
|---|---|---|
| 「改了个 typo，建个卡吧」 | Inbox 噪声稀释库价值 | 过不了结构闸门；只收非直觉、可迁移的收获 |
| 「我确信这是新的，跳过去重」 | 重复笔记各自漂移 | 去重闸门先于动笔，verdict 是硬证据 |
| 「标题够说明一切，description 随便填」 | 检索靠碰运气 | `description` 必须是场景触发句；标题复述被拒写 |
| 「只记 bug 就行，做对的部分是常识」 | 做法失传，每次都从事故重学 | 每会话至少产出一张 `category/pattern` |
| 「放哪等晋级时再想」 | 草稿长期滞留 Inbox | 正文 MUST 写归档目标 `并入 X §n` / `新增 X §n` |
| 「工具没写 description，保存后再 patch 回去」 | 补丁漏一次就永久缺字段 | 字段走参数，拒写而非事后修补 |
