---
name: dfs-inbox-consolidate
description: Classify and archive 99-Inbox drafts into DFS destinations. Use when the inbox has accumulated drafts and the user asks to file or clean them up.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  disable-model-invocation: "true"
  hermes:
    tags:
      - inbox-processing
      - archival
      - knowledge-management
      - triage
    related_skills:
      - dfs-save
    mcp_tools:
      - promote_inbox_draft
---

# DFS-INBOX-CONSOLIDATE: Inbox Draft Archival Pipeline

> **Invocation — explicit only.** This skill carries `disable-model-invocation: "true"` under
> `metadata`, the Agent Skills extension slot, which no harness enforces as a hard switch
> (Claude Code honored it only at the old top-level location; Hermes never implemented it), so
> the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

## 🚨 The Transactional Archival Invariant (RFC 2119 MUST)
> **NO draft shall be deleted from `99-Inbox/` until its target note write is committed and verified.**
> Always run `--dry-run` before `--execute`. Never guess destinations for ambiguous drafts.

---

## ⚡ Scope Detection (MUST — 执行前第一步)

**在任何操作前，MUST 先检测当前 Vault 根目录**：

```python
import os
def detect_vault_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "AGENTS.md")) or os.path.exists(os.path.join(d, "CLAUDE.md")):
            return d
        d = os.path.dirname(d)
    return None
```

- **检测到 Vault**：脚本路径为 `{vault_root}/scripts/vault-inbox-consolidate.py`
- **未检测到 Vault**：报错退出，不执行归档

---

## 1. 功能概述

将 `99-Inbox/` 中的草稿笔记按 frontmatter tags 自动分类并归档到 Vault 正式目录。

**路由规则**：

| Tag 匹配 | 目标类型 | 目标路径 |
|----------|---------|---------|
| `lang/python`, `lang/go`, ... | dual-version | `03-Languages/{LANG}/{LANG}-STANDARDS.md` + CHEATSHEET 同步检测 |
| `topic/git`, `topic/error-handling`, ... | rule-append | `01-Rules/{TARGET}.md` |
| `topic/architecture`, `topic/refactoring`, ... | source-article | `06-Sources/Articles/{TITLE}.md` |
| `topic/linguistics` + `project/delector` | project | `08-Projects/DeLector/{TITLE}.md` |
| 无匹配 + source-notes | source-article | `06-Sources/Articles/{TITLE}.md` |
| `category/pattern` | **pattern-card** | `01-Rules/{NAME}.md`（独立卡，命名不带日期；与 `category/rules` 并列） |

> **pattern vs troubleshooting**：`category/pattern` = 可复用的**成功做法**（"做对了什么"）⇒ 独立成卡；`category/troubleshooting` = 事故复盘 ⇒ **合并进对应规则的 §n**（不新建卡）。两类都晋级，别只处理事故类，否则"做法"永远失传。

---

## 1b. 「归档目标」优先与路由对账 (MUST)

脚本判定是**建议**不是真值：`analyze_draft()` 按 `tags` **列表顺序取首个命中**（同一 tag 序列、不同归属的草稿只有一个出口），未注册 tag 则静默落 fallback 目标，**不报错**。

- **逐篇对账 (MUST)**：`--dry-run` 后 MUST 把每篇的脚本判定与**草稿正文自述的「归档目标」**对照；不一致即走 §2c 人工落位，MUST NOT 接受脚本判定。
- **多段 frontmatter (MUST)**：只取 canonical 段（外层），MUST NOT 把正文内重复的 YAML 段追加进规则文件。
- **补盲区 (MUST)**：发现未注册 tag ⇒ 补路由配置（`scripts/routing.example.json`）并在其基线测试中登记，补完做变异自证（删条目 ⇒ 必红）。

## 2. 使用方式

```bash
# 预览模式（默认）— 不修改任何文件
python scripts/vault-inbox-consolidate.py --dry-run

# 预览单个文件
python scripts/vault-inbox-consolidate.py --dry-run --file "2026-09-06-xxx.md"

# 执行归档 — 创建目标文件 + 删除原件
python scripts/vault-inbox-consolidate.py --execute

# 执行单个文件
python scripts/vault-inbox-consolidate.py --execute --file "2026-09-06-xxx.md"

# JSON 输出
python scripts/vault-inbox-consolidate.py --dry-run --json
```

---

## 2b. 单篇晋级路径 (MCP)

批量归档走上面的脚本；**单篇晋级**或需要在归档前由 Agent 判断目标时，走 MCP：

- `promote_inbox_draft(draft, destination)` — 将指定草稿晋级到目标目录，由服务端完成搬运与状态改写。

Agent 判断目标时可参考上方 `TARGET_ROUTING_MAP`；目标仍有歧义时，向用户确认后再晋级，
**MUST NOT** 凭猜测写入正式目录。

---

## 2c. 人工落位路径（脚本判定不适用时）

1. **定位**：目标为已有规则文件 ⇒ 走**附录块**（不新建文件、不改章节编号）。
2. **附录块形态**：yaml 分隔线 + `#### <标题>` + `> 来源: 99-Inbox/<原名> | 日期: <YYYY-MM-DD>` + 一句**已执行态**说明 + 正文（去掉与外层重复的 `# H1`）。**行尾 MUST 与目标文件一致**（CRLF / LF 不可混）。
3. **补字段**：目标 frontmatter 的 `updated` / `verified` 刷为今天，并补关联索引条目。
4. **验证后移除原件 (MUST)**：先做**逐行覆盖比对**（「标题存在」≠「内容落盘」）并备份副本 —— 投放箱目录常为 untracked，**无 git 兜底**；通过后才删。
5. **收口**：跑该知识库的质检与巡检命令（Inbox MUST CLEAN）。

## 3. 执行流程与完成判据

```
  [1. 扫描 99-Inbox/*.md（排除 tpl- 前缀）]
                     │
                     ▼
  [2. 解析 YAML frontmatter (tags, status, type)]
                     │
                     ▼
  [3. 匹配 TARGET_ROUTING_MAP 确定目标路径]
                     │
                     ▼
  [4. 运行 --dry-run 预览计划并确认]
                     │
                     ▼
  [5. 运行 --execute 提交原子事务并清理原件]
```

- **Checkable Completion Criterion**: 
  - 运行 `python scripts/vault-inbox-consolidate.py --execute` 输出 `0 errors`，归档目标物理生成且原件已安全移除。

---

## 4. Dual-Version CHEATSHEET 同步 (VAULT-STRUCTURE §5)

当路由到 `dual-version` 时，脚本自动处理 CHEATSHEET 同步检测：

**行为**：
- STANDARDS 追加后，脚本检查对应 CHEATSHEET 是否已包含新章节标题
- `cheatsheet_action = "synced"`：CHEATSHEET 已有该章节，无需操作
- `cheatsheet_action = "stale"`：CHEATSHEET 缺少该章节，返回浓缩指令
- `cheatsheet_action = "missing"`：CHEATSHEET 文件不存在，提示从 STANDARDS 生成

**Agent 收到 `stale` 后 MUST 执行**：
1. 读取 `{LANG}-STANDARDS.md` 中新增章节
2. 在 `{LANG}-CHEATSHEET.md` 对应位置追加浓缩版（一句话核心法则 + ≤5 行代码示例）
3. 确保章节序号 1:1 对齐

**输出示例**：
```
  [1] Python 异步并发模式
      Tags: lang/python, topic/concurrency
      Target: dual → 03-Languages/Python/PYTHON-STANDARDS.md
      Action: dual-append — 已追加至 STANDARDS
      ⚠️  CHEATSHEET 同步: PYTHON-CHEATSHEET.md 中未找到「PYTHON-ASYNC-CONCURRENCY-MODES」章节
  ────────────────────────────────────────────────────────────
  📋 CHEATSHEET 同步待办 (VAULT-STRUCTURE §5):
    ⚠️  03-Languages/Python/PYTHON-CHEATSHEET.md ← 需从 STANDARDS 浓缩
```

---

## 4b. 晋级后 MUST 补字段 / 标取代关系

1. **`description`（触发句）**：一句话写明"什么场景该读本条"，MUST NOT 写成标题复述。
2. **`verified`（复核日期）**：MUST 更新为今天（`updated` 不等于复核）。
3. **被取代的旧结论**：使旧条目失效 ⇒ 标 `status: superseded-by: <path>`；不静默删除，也不静默保留。
4. **时效闸**：跑规则时效检查，超期未复核的规范会被点名；随各规则被引用时补 `verified` 逐步收敛。

## 5. 归档后 MUST 验证

执行完毕后 **MUST** 运行健康巡检确认：

```bash
python scripts/vault-healthcheck.py
```

确认 Inbox Ingestion Hygiene 为 ✅ CLEAN。

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I'll run `--execute` directly without `--dry-run` to be faster."* | **Silent Data Deletion**: uninspected bulk moves or rule appends into wrong destinations. | Mandatory `--dry-run` preview before `--execute`. |
| *"The draft has ambiguous tags, but I'll guess an archival path."* | **Knowledge Base Fragmentation**: insights buried under wrong topics or deleted prematurely. | If routing has ambiguity, prompt user for confirmation before promotion. |
| *"I appended to STANDARDS, so I don't need to check CHEATSHEET."* | **Dual-Version Drift**: human quick-reference cheatsheet diverges from standards. | If `cheatsheet_action == "stale"`, immediately append the condensed section. |
| *"I'll modify notes in `99-Inbox/` directly without committing the transaction."* | **Broken Ingestion State**: leaving partial writes or unmanaged orphans. | Use transactional tools (`vault-inbox-consolidate.py` or `promote_inbox_draft`). |

---

## 6. 关联工具

- Inbox 超龄扫描：`python scripts/vault-inbox-triage.py`
- 全库健康巡检：`python scripts/vault-healthcheck.py`
- Vault 结构规范：[[01-Rules/VAULT-STRUCTURE]]
- CC Switch 管理规范：[[05-Tools/CC-SWITCH-GUIDE]]
