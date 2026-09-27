# 🤝 Agent Handoff & Continuation Card (v2)

### 1. 📍 Breakpoint & Git State
- **Branch / Last Commit**: `{git_branch}` @ `{commit_hash} {commit_message}`
- **Test Baseline**: ✅ {pass_count} passing

### 🧾 Verified Execution Receipts (No Fake Green)
- **Test Command**: `{raw_test_cmd}`
- **Exit Code**: 0 (Physical green confirmed)
- **Stdout Proof**: `{pass_count} passed, 0 failed in {duration}s`
- **Diff Stats**: `{files_changed} files changed, +{insertions}/-{deletions}`

### 2. ✅ Completed vs ⏳ Remaining
- ✅ {task}: {one-line evidence}
- ⏳ {next_task}: {one-line next action}

### 3. 🔁 Unresolved Corrections
- {用户原话} → 已做: {…} / 未做: {原因}（账本行已 open）
- none

### 4. 🔗 Pointers（细节不内联，只给指针）
- 测试输出: `10-Daily/{YYYY-MM-DD}.md#L{n}`
- 审计明细: `11-Agents/logs/{YYYY-MM}.md`
- 账本: `WORKMEMORY/corrections.md`（open 条目 MUST 先读）

### 5. 🚀 1-Click Continuation Prompt
> "Resume `{project_name}` at `{next_task}`. Read `WORKMEMORY/INDEX.md`,
> `corrections.md` (open rows first), then `python scripts/vault_exec_state.py resume`."
