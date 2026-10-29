---
name: dfs-inbox-consolidate
description: Classify and archive 99-Inbox drafts into DFS destinations. Use when the inbox has accumulated drafts and the user asks to file or clean them up.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
  hermes:
    mcp_tools: [promote_inbox_draft]
    tags: [inbox-processing, archival, knowledge-management, triage]
    related_skills: [dfs-save]
---
# DFS-INBOX-CONSOLIDATE: Inbox Draft Archival Pipeline

> **Invocation — explicit only.** This skill carries `disable-model-invocation: "true"` under
> `metadata`, the Agent Skills extension slot, which no harness enforces as a hard switch
> (Claude Code honored it only at the old top-level location; Hermes never implemented it), so
> the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

> **Detailed playbook**: this skill's long-form sections were moved to [`references/archival-workflow.md`](references/archival-workflow.md). Load it when you need the full procedure, the worked example, or the field evidence — the constraints above are self-sufficient without it.

## [MUST] The Transactional Archival Invariant (RFC 2119 MUST)
> **NO draft shall be deleted from `99-Inbox/` until its target note write is committed and verified.**
> Always run `--dry-run` before `--execute`. Never guess destinations for ambiguous drafts.

---

## Scope Detection (MUST - 执行前第一步)
在任何操作前，先解析当前 Vault 根目录（遵循 Tier 1 环境变量 `$WIKI_PATH` / `$OBSIDIAN_VAULT_PATH` 或向父目录上溯探测 `AGENTS.md`）。
- **检测到 Vault**: 执行脚本为 `{vault_root}/scripts/vault-inbox-consolidate.py`
- **未检测到 Vault**: 报错退出，严禁盲目执行归档

---

## 1b. 「归档目标」优先与路由对账 (MUST)
脚本判定是**建议**不是真值：`analyze_draft()` 按 `tags` **列表顺序取首个命中**（同 tag 序列、不同归属的草稿只有一个出口），未注册 tag 则静默落 `fallback.default`（`01-Rules/CODING-UNIVERSAL.md`），**不报错**。
- **逐篇对账 (MUST)**：`--dry-run` 后 MUST 把每篇的脚本判定与**草稿正文自述的「归档目标」**对照；不一致即走 §2c 人工落位，MUST NOT 接受脚本判定。
- **多段 frontmatter (MUST)**：只取 canonical 段（外层），MUST NOT 把正文内重复的 YAML 段追加进规则文件。
- **补盲区 (MUST)**：发现未注册 tag ⇒ 补 `scripts/routing.example.json`（本仓随包的示例路由表；派生你自己的 `routing.json`），再把新条目登记进你的路由加载测试（§5 冻结集合防线），补完做变异自证（删条目 ⇒ 必红）。

## 2b. 单篇晋级路径 (MCP)

批量归档走上面的脚本；**单篇晋级**或需要在归档前由 Agent 判断目标时，走 MCP：

- `promote_inbox_draft(draft, destination)` — 将指定草稿晋级到目标目录，由服务端完成搬运与状态改写。

Agent 判断目标时可参考上方 `TARGET_ROUTING_MAP`；目标仍有歧义时，向用户确认后再晋级，
**MUST NOT** 凭猜测写入正式目录。

---

## 2c. 人工落位路径（脚本判定不适用时）
1. **定位**：目标为已有规则文件 ⇒ 走**附录块**（不新建文件、不改章节编号）；目标需新建 ⇒ 只在此处新建。
2. **附录块形态**：yaml 分隔线 + `#### <标题>` + `> 来源: 99-Inbox/<原名> | 日期: <YYYY-MM-DD>` + 一句**已执行态**说明 + 正文（去掉与外层重复的 `# H1`）。**行尾 MUST 与目标文件一致**（CRLF / LF 不可混）。
3. **补字段**：目标 frontmatter 的 `updated` / `verified` 刷为今天，并补关联索引条目（§4b）。
4. **验证后移除原件 (MUST)**：先做**逐行覆盖比对**（「标题存在」≠「内容落盘」）并备份副本 —— `99-Inbox/` untracked，**无 git 兜底**；通过后才 `rm`。
5. **收口**：`vault-quality-check.py`（本次改动文件零告警） + `vault-healthcheck.py`（[4] Inbox MUST CLEAN）。

## 3. 执行流程与完成判据

```
  [1. 扫描 99-Inbox/] -> [2. 解析 YAML 元数据] -> [3. 匹配目标路由]
                                                       │
  [5. --execute 原子写入+原件移除] <--- [4. --dry-run 预览确认] <┘
```

- **Checkable Completion Criterion**: 
  - 运行 `python scripts/vault-inbox-consolidate.py --execute` 输出 `0 errors`，归档目标物理生成且原件已安全移除。

---

## 4. Dual-Version CHEATSHEET 同步 (VAULT-STRUCTURE §5)
当路由到 `dual-version` 时，脚本自动处理 CHEATSHEET 同步检测。若输出状态为 `stale`，Agent MUST 遵循 [references/cheatsheet-sync.md](references/cheatsheet-sync.md) 协议在 `{LANG}-CHEATSHEET.md` 对应位置同步追加浓缩版并对齐章节编号。

---

## 4b. 晋级后 MUST 补字段 / 标取代关系（2026-10-17 补入）

晋级（脚本或 MCP）完成后，Agent MUST 检查目标文件的 frontmatter 与正文：

1. **`description`（触发句）**：一句话写明"什么场景该读本条"，**MUST NOT** 写成标题复述——后续检索靠它做相关性过滤。
2. **`verified`（复核日期）**：MUST 更新为今天。`updated` 不等于复核（改错别字不算）。
3. **被取代的旧结论**：若本次晋级使某条旧规则/旧条目失效 ⇒ 在该处标 `status: superseded-by: <path>`，**不静默删除、也不静默保留**（保持历史可追溯，但检索时必须看得出它已过期）。
4. **时效闸**：用你自己的规则时效检查（作者版是 `vault-rule-freshness`，看 `verified` 日期与 `--days N` 阈值；**不随包**，因为它读的是特定知识库的规范目录结构）报告超期未复核的规范；迁移期内严格模式会红，属预期，随各规则被引用时补 `verified` 逐步收敛。

**Checkable Completion Criterion**：目标文件含 `description` + `verified`；若存在被取代项，其 `superseded-by` 已标注。

---

## 5. 归档后 MUST 验证

执行完毕后 **MUST** 运行健康巡检确认：

```bash
python scripts/vault-healthcheck.py
```

确认 Inbox Ingestion Hygiene 为 [PASS] CLEAN。

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I'll run `--execute` directly without `--dry-run` to be faster."* | **Silent Data Deletion**: uninspected bulk moves or rule appends into wrong destinations. | Mandatory `--dry-run` preview before `--execute`. |
| *"The draft has ambiguous tags, but I'll guess an archival path."* | **Knowledge Base Fragmentation**: insights buried under wrong topics or deleted prematurely. | If routing has ambiguity, prompt user for confirmation before promotion. |
| *"I appended to STANDARDS, so I don't need to check CHEATSHEET."* | **Dual-Version Drift**: human quick-reference cheatsheet diverges from standards. | If `cheatsheet_action == "stale"`, immediately append the condensed section. |
| *"I'll modify notes in `99-Inbox/` directly without committing the transaction."* | **Broken Ingestion State**: leaving partial writes or unmanaged orphans. | Use transactional tools (`vault-inbox-consolidate.py` or `promote_inbox_draft`). |

---
