---
name: dfs-inbox-consolidate
description: "Classify and archive 99-Inbox drafts to DFS destinations."
disable-model-invocation: true
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [inbox-processing, archival, knowledge-management, triage]
    related_skills: [dfs-save]
    mcp_tools: [promote_inbox_draft]
---

# DFS-INBOX-CONSOLIDATE: Inbox Draft Archival Pipeline

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

## 2b. 单篇晋级路径 (MCP)

批量归档走上面的脚本；**单篇晋级**或需要在归档前由 Agent 判断目标时，走 MCP：

- `promote_inbox_draft(draft, destination)` — 将指定草稿晋级到目标目录，由服务端完成搬运与状态改写。

Agent 判断目标时可参考上方 `TARGET_ROUTING_MAP`；目标仍有歧义时，向用户确认后再晋级，
**MUST NOT** 凭猜测写入正式目录。

## 3. 执行流程

```
1. 扫描 99-Inbox/*.md（排除 tpl- 前缀）
2. 解析每个草稿的 YAML frontmatter（tags, status, type）
3. 按 tags 匹配 TARGET_ROUTING_MAP → 确定目标路径
4. --dry-run：输出推荐目标 + 执行计划，不修改文件
5. --execute：
   a. dual/rule-append 类型 → 追加内容到目标文件
   b. source-article/project 类型 → 创建新文件（status → stable）
   c. 删除 99-Inbox/ 中的原件
```

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

## 5. 归档后 MUST 验证

执行完毕后 **MUST** 运行健康巡检确认：

```bash
python scripts/vault-healthcheck.py
```

确认 Inbox Ingestion Hygiene 为 ✅ CLEAN。

## 6. 关联工具

- Inbox 超龄扫描：`python scripts/vault-inbox-triage.py`
- 全库健康巡检：`python scripts/vault-healthcheck.py`
- Vault 结构规范：[[01-Rules/VAULT-STRUCTURE]]
- CC Switch 管理规范：[[05-Tools/CC-SWITCH-GUIDE]]
