# dfs-inbox-consolidate — extended playbook (tier 3)

Loaded on demand by `dfs-inbox-consolidate/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

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
| `category/pattern` | **pattern-card** | `01-Rules/{NAME}.md`（独立卡，命名不带日期；与 `category/rules` 并列） |
| 无匹配 + source-notes | source-article | `06-Sources/Articles/{TITLE}.md` |

> **pattern vs troubleshooting（2026-10-17 补入）**：`category/pattern` = 可复用的**成功做法**（"做对了什么"）⇒ 独立成卡；`category/troubleshooting` = 事故复盘 ⇒ **合并进对应规则的 §n**（不新建卡）。两类都晋级，别只处理事故类，否则"做法"永远失传。首张实例：`01-Rules/REFACTOR-SAFETY-NET.md`。

---

## 2. 使用方式
```bash
python scripts/vault-inbox-consolidate.py --dry-run                # 预览模式 (默认)
python scripts/vault-inbox-consolidate.py --dry-run --file <name>  # 预览单文件
python scripts/vault-inbox-consolidate.py --execute               # 执行归档 (原子写入+原件移除)
python scripts/vault-inbox-consolidate.py --execute --file <name>  # 执行单文件
python scripts/vault-inbox-consolidate.py --dry-run --json        # JSON 格式输出
```

---

## 6. 关联工具

- Inbox 超龄扫描：`python scripts/vault-inbox-triage.py`
- 全库健康巡检：`python scripts/vault-healthcheck.py`
- 规则时效闸：作者版 `vault-rule-freshness --strict`，需自备等价物（见 `scripts/README.md`）
- Vault 结构规范：[[01-Rules/VAULT-STRUCTURE]]
- CC Switch 管理规范：[[05-Tools/CC-SWITCH-GUIDE]]
