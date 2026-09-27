# PROJECT_OVERVIEW — skill-dev

> 60 秒项目 primer。新 agent 的第二读（读完 work.log 事件流之前先建立全局认知）。
> 维护规则：bootstrap 时由 agent 从代码库提炼生成初稿；此后每次 WORK_END / 交接后刷新。

## 这是什么项目

Defensive Skills（DFS）的**独立开源发布仓库**。内容是一套供 AI coding agent 使用的工程化
harness：24 个 `dfs-*` skill（1 个 router `dfs` + 23 个域技能），纯 Markdown + Python 标准库，
无构建步骤、无运行时依赖。主链路：路由(`dfs`) → 规划(`dfs-plan`) → TDD 执行(`dfs-exec`) →
根因调试(`dfs-debug`) → 知识沉淀(`dfs-save`) → 交接(`dfs-handoff`)。

- 形态：`<skill>/SKILL.md`（YAML frontmatter + 正文）+ `templates/` / `references/` / `scripts/`。
- 规模：24 个 skill 目录 / 24 个 SKILL.md / 122 个文件（不含 `.git`）；`dfs-agent-sdk` 独占 65 个 references。
- 运行方式：无。交付物是文本；未来由待写的 `install.py` 复制或链接到各 harness 的 skills 目录。
- 发布阻塞（未解）：B1 配套 MCP server 不在本仓库；B2/B3 `{vault_root}` 与 `99-Inbox/` 仍是作者
  Vault 的布局假设；B4 `vault-inbox-consolidate.py` 命名与品牌不一致；B5 frontmatter 携带 Hermes
  专有字段。详见 `HANDOFF.md` §3。

## 当前状态

- `HANDOFF.md` 是当前唯一权威入口：12-vs-24 子集判据、5 个发布阻塞项、MCP 契约、conformance 规则表。
- 24/24 与 live tree `~/.cc-switch/skills/` 逐文件一致（`diff -rq` 全绿）；其中 12 个是 shipped 子集。
- 已 bootstrap（2026-09-27）：`git init` + `.githooks/pre-commit` 密钥扫描 + Vault 锚点 + WORKMEMORY 四件套。
- conformance 门禁已移植到本仓库（`tests/test_skills_conformance.py`，12 规则 / 14 测试，stdlib 零依赖），
  并带变异测试夹具 `tests/mutation_check.py`（13 个注入缺陷全部被捕获）。
- 配套 MCP 已建（B1 决策 = 两者都做）：`mcp/knowledge_server.py`（stdio JSON-RPC，stdlib 零依赖，9 个规范工具名
  不变）+ `mcp/README.md`（注册方式、根解析契约、`knowledge.json` 布局覆盖、逐工具的文件级降级表）。
  `tests/test_knowledge_server.py` 15 个测试全绿（临时知识库 + 真实 stdio 协议，含越界拒读与 A-MAC 闸门）。
- **门禁全绿（2026-09-27）**：`tests/test_skills_conformance.py` Ran 14 OK / exit 0；
  `tests/mutation_check.py` 14/14 CAUGHT / exit 0，基线 = 空集；`tests/test_knowledge_server.py` Ran 15 OK；
  `tests/test_vendored_scripts.py` Ran 9 OK。Rule 8 悬空引用 = 0。
- B4 已闭环，形态 = 「引擎随包，私人工具显式声明」：`scripts/` 内置 vault_exec_state.py（dfs-exec/dfs-handoff 引擎）、
  vault-inbox-consolidate.py（dfs-inbox-consolidate 引擎）、vault_transaction.py（事务原语）、routing.example.json（中性 starter）；
  vault-healthcheck.py / vault-inbox-triage.py / bootstrap.ps1 三个私人工具进门禁 `OPTIONAL_SCRIPT_POINTERS` 豁免表
  （自失效：不再被引用的豁免会使 Rule 8 判红），并在 `scripts/README.md` 声明。
- B2 解决方式：目录名可配置（`knowledge.json`），默认值仍等于本 Vault 布局，所以现有行为不变。
- LICENSE + 顶层 README 已落地（2026-09-27）：MIT（与 `D:\Code` 下其他仓库一致，除 vendored 的 Apache 那个）；
  `README.md` 以三个失败模式开场、只写实测数字（24 技能 / 12 规则 / 38 测试 / 14 变异 / 双解释器一致），
  含技能全览、门禁自验方式、12 条规则表、布局契约、声明缺口、目录导航。
- 下一步：① Axis B（公开子集收敛：论证或移出 dfs-exec / dfs-debug）；② B3（`99-Inbox/` 必须存在或自动创建）；
  ③ B5（Hermes 专有 frontmatter 字段的其他 harness 映射）；④ dfs-bootstrap 的 bootstrap.ps1 跨平台移植（B4 留下的显式缺口）；
  ⑤ shipped 子集白名单门禁；⑥ `install.py`。
- **首个 commit 已落地**（2026-09-27，`0e021c0`，136 文件，工作区干净；无 remote，未推送）。
  提交前修掉两个「对陌生人无价值」的坑：`.gitattributes` 钉 `eol=lf`（CRLF shebang 会让 Linux 上的
  `.githooks/pre-commit` 直接失效，而所有技能都声明 `platforms: [linux, macos, windows]`）；
  `git update-index --chmod=+x` 钉执行位（Windows 下 `core.filemode=false`，钩子与引擎脚本的执行位
  被静默记成 100644，Linux clone 会拿到一个跑不起来的钩子）。
  验证方式：把仓库 clone 到临时目录，**在 clone 内**检查钩子的 shebang/行尾/权限、跑 `bash .githooks/pre-commit`
  与四个门禁（双解释器）→ 全部 exit 0。

## 高频坑（踩过的雷区）

- **假绿 conformance**：6 规则版 suite 报全绿，树里实际有 71 个悬空引用 → 断言只覆盖"声明"不覆盖
  "调用点" → 每条规则必须做 mutation test（注入缺陷必须转红），绿才有意义。
- **模板预置事件被继承**：`bootstrap.ps1` 复制的 `Templates/workmemory/work.log` 内含一条预置示例事件
  （伪造的 agent-id 与"bootstrap 完成"结论）→ 根因是模板带样本正文 → 新仓库会凭空多出一条不属于自己的
  历史 → bootstrap 后必须替换为真实事件（本仓库已在首次 commit 前清除）。
- **锚点路径硬编码分隔符**：`"$vaultRoot\AGENTS.md"` 在 POSIX PowerShell 下产出混合分隔符串，既无法解析
  又让 Linux CI 变红 → 一律用 `Join-Path`。
- **pre-commit 带 BOM 即失效**：UTF-8 BOM 会污染 shebang，bash 直接报错 → 必须以
  `UTF8Encoding($false)` 无 BOM 写入（`bootstrap.ps1` 已处理，勿手改 hook 编码）。
- **文档计数不可尽信**：`HANDOFF.md` §1 称 `dfs-agent-sdk` 有 67 个 references，实测 65（源码树与本树同为 65）
  → 计数一律用命令复核，不抄文档。同理 §3 表记"只有 1 个 skill 调用 vault 脚本"，实测 5 个 skill / 7 个脚本 / 21 处。
- **门禁的"绿"会取决于解释器**：原版 `import yaml`，默认 `python` 3.14 无 PyYAML 直接 ModuleNotFoundError，只有
  `python3` 3.11.8 能跑 → 门槛脚本必须 stdlib 零依赖，否则同一棵树在不同解释器下结论不同。
- **给门禁挂 Vault 兜底根 = 把缺陷重新埋掉**：原版 Rule 8 允许 `scripts/...` 解析到作者 Vault 的 `scripts/`，
  于是"只有作者机器跑得通"的引用永远绿。移植版必须砍掉这个根（21 处悬挂引用就是这么被逼出来的）。
- **`except Exception: continue` 会挪走归因**：frontmatter 解析失败时 Rule 9/11 静默跳过，靠 Rule 2 兜底——
  套件仍是红的（不是静默洞），但报错指向 Rule 2。写变异测试期望值要按这个来，否则会误判某条规则没生效。
- **数据脏点（Rule 7 不查）**：`dfs-exec/SKILL.md` 的 `related_skills` 里 `dfs-review` 出现两次。
  Rule 7 只验证能否解析、不验证重复，所以门禁不会报；修的话要改 live tree 再回拷，否则破坏 24/24 奇偶性。
- **移植根解析时被自己的仓库骗到**：`resolve_vault_root` 的兜底 `<script>/../..` 在本仓库恰好命中仓库自己的
  `AGENTS.md`，于是工具把代码检出目录当知识库、报「99-Inbox 不存在」并**退出码 0** —— 典型静默错答案。
  修法：兜底必须要求脚本同级存在**本工具的服务对象**（如 `99-Inbox/`），否则 exit 2 打印配置指引。
  这条是 `tests/test_vendored_scripts.py` 抓出来的，不是推演出来的。
- **门禁的解析根不能跟着移植一起丢**：`get_script_roots()` 漏了 `<root>/scripts` 会让 21 处合法引用变悬空；
  正确做法是补回**本仓库自己的** `scripts/`，而不是把刻意砍掉的「作者机器绝对路径兜底根」再加回去。
- **"预期为红"的规则等于没有变异覆盖**：Rule 8 转绿那一刻变异夹具报 `BASELINE MOVED` —— 它此前只被
  `KNOWN_RED_BASELINE` 覆盖，从无用例证明过它真能判红。规则由红转绿时必须同时补它的变异用例，
  且注入的缺陷要**刻意避开豁免名单**，才能同时证明豁免表吞不掉新缺陷。
- **`--tasks` 的 task id 是原样标签**：`init --tasks "Task 1"` 生成的 id 就是 `Task 1`（带空格），
  只有 `--plan-file` 才合成 `Task-N`；用错形态会让 `--task-id Task-1` 报「未找到任务」。测试期望值按此写。
