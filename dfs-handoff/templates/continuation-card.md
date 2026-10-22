# [NOTE] Agent Handoff & Continuation Card (v2)

### 1. [STEP] Breakpoint & Git State
- **Branch / Last Commit**: `{git_branch}` @ `{commit_hash} {commit_message}`
- **Test Baseline**: [PASS] {pass_count} passing

### [NOTE] Verified Execution Receipts (No Fake Green)
- **Test Command**: `{raw_test_cmd}`
- **Exit Code**: 0 (Physical green confirmed)
- **Stdout Proof**: `{pass_count} passed, 0 failed in {duration}s`
- **Diff Stats**: `{files_changed} files changed, +{insertions}/-{deletions}`

### 2. [PASS] Completed vs [STEP] Remaining
- [PASS] {task}: {one-line evidence}
- [NOTE] {next_task}: {one-line next action}

### 3. [STEP] Unresolved Corrections
- {用户原话} → 已做: {…} / 未做: {原因}
- none

### 4. [STEP] Pointers（细节不内联，只给指针）
- 测试输出: `10-Daily/{YYYY-MM-DD}.md#L{n}`
- 审计明细: `11-Agents/logs/{YYYY-MM}.md`
- 纠正记录: `WORKMEMORY/work.log` 尾 50 行（`WORK_END` 的「本次被纠正」行）
- 交接包: `WORKMEMORY/handoff_<topic>.md`（**仅当 Phase 0.5 探测到项目约定时**；卡的其余节只给指针，不复制包内容）

### 5. [STEP] 1-Click Continuation Prompt
> "Resume `{project_name}` at `{next_task}`. Read `WORKMEMORY/INDEX.md` (HOT: 文件清单 + Active handoffs),
> `work.log` tail 50; for prior work on a topic `grep -i '<关键词>' WORKMEMORY/INDEX-topics.md` (WARM,
> 主题索引 + 蒸馏登记); then `python scripts/vault_exec_state.py resume`."
