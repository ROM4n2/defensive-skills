# Dual-Version CHEATSHEET 同步机制 (VAULT-STRUCTURE §5)

当草稿归档路由到 `dual-version` 时，脚本自动触发 CHEATSHEET 同步检测。

## 1. 状态判断行为
- STANDARDS 追加后，脚本检查对应 CHEATSHEET 是否已包含新章节标题。
- `cheatsheet_action = "synced"`: CHEATSHEET 已包含该章节，无需额外操作。
- `cheatsheet_action = "stale"`: CHEATSHEET 缺少该章节，必须执行浓缩同步。
- `cheatsheet_action = "missing"`: CHEATSHEET 文件不存在，提示从 STANDARDS 生成。

## 2. Agent 收到 stale 后的 MUST 执行协议
1. 读取 `{LANG}-STANDARDS.md` 中新增章节。
2. 在 `{LANG}-CHEATSHEET.md` 对应位置追加浓缩版（一句话核心法则 + <= 5 行精炼代码示例）。
3. 确保章节序号 1:1 严格对齐。

## 3. 输出示例与格式
```
  [1] Python 异步并发模式
      Tags: lang/python, topic/concurrency
      Target: dual -> 03-Languages/Python/PYTHON-STANDARDS.md
      Action: dual-append - 已追加至 STANDARDS
      [NOTE] CHEATSHEET 同步: PYTHON-CHEATSHEET.md 中未找到「PYTHON-ASYNC-CONCURRENCY-MODES」章节
  ------------------------------------------------------------
  [NOTE] CHEATSHEET 同步待办 (VAULT-STRUCTURE §5):
      [NOTE] 03-Languages/Python/PYTHON-CHEATSHEET.md <- 需从 STANDARDS 浓缩
```
