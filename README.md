# Defensive Skills (DFS) · 让 AI 编码代理的门禁真正有牙齿

<p align="center">
  <b>中文</b> · <a href="README.en.md">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-23-4B5563?style=flat-square" alt="Skills" />
  <img src="https://img.shields.io/badge/Conformance-13%20rules-0969DA?style=flat-square" alt="Conformance rules" />
  <img src="https://img.shields.io/badge/Tests-104%20passed-2EA44F?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/Mutation-20%2F20%20caught-2EA44F?style=flat-square" alt="Mutation harness" />
  <img src="https://img.shields.io/badge/Dependencies-0%20(stdlib)-gray?style=flat-square" alt="Zero dependencies" />
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?style=flat-square" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-gray?style=flat-square" alt="License MIT" />
</p>

<p align="center">
  <b>一套给 AI 编码代理用的工程约束框架：纯 Markdown 技能 + 零依赖配置的门禁，专治「看起来全绿、其实没人验过」。</b>
</p>

---

## 🎯 它反对的三件事

不是功能清单，是三种具体的失败模式。每条都附上本仓库自己的收据。

**1. 假绿门禁 —— 「测试通过」和「真的没问题」是两件事。**
本仓库的一致性门禁最早只有 6 条规则，报全绿。补上**变异测试**（对每一项声明式检查注入缺陷，断言它必须转红）并砍掉「`scripts/...` 允许解析到作者自己机器上的目录」这类兜底之后，规则扩到 12 条，立刻报出 **21 处只有作者机器解析得通的脚本引用**，分布在 6 个技能里。绿的集合从来没变过——变的只是它到底有没有在检查。

**2. 计划幻觉 —— 对着没读过的代码写详细方案。**
`dfs-plan` 只产出**当下能确定**的下一步（分段式计划），每步带验证方式；`dfs-exec` 强制「先有复现/先有失败的测试，再动实现」；`dfs-tdd` 专门盯 RED-GREEN-REFACTOR 的偷跑假绿。计划里不许出现没证据的断言。

**3. 静默失败 —— 出了错却退出码 0。**
移植 `vault-inbox-consolidate.py` 时，它的原型兜底 `<script>/../..` 恰好命中代码检出目录里自己的 `AGENTS.md`，于是工具把工作区当成知识库、报「Inbox 不存在」并**退出码 0**——完全是一次静默错答案。现在无根可解析就 `exit 2` 并打印该怎么配。同一原则贯穿全仓：**能响就响，不吞异常，不给假默认值。**

---

## 🚀 快速开始

### 1) 装技能

技能就是含 `SKILL.md` 的普通目录，拷进（或软链到）你的 harness 的技能目录即可。以下路径已在本机实测存在：

| Harness | 技能目录 |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Hermes | `<hermes 配置目录>/skills/` |

```bash
# 整包 23 个，或只装「零前置」的 5 个；默认软链，Windows 上自动退回复制
python install.py --target ~/.codex/skills
python install.py --target ~/.codex/skills --tier A
```

`install.py` 的分档直接从下面的技能表读（那张表有门禁保证与树一致），另有 `--mode copy|link`、`--force`、`--dry-run`。不想用它就直接 `cp -r dfs dfs-* ~/.codex/skills/`。

### 2) 装知识层（可选但强烈建议）

技能靠 `coding-vault-search` MCP 检索你自己的 Markdown 知识库。仓库自带一个 **stdio JSON-RPC、零依赖**的服务：

```jsonc
{
  "mcpServers": {
    "coding-vault-search": {
      "command": "python",
      "args": ["<repo>/mcp/knowledge_server.py", "--root", "<你的知识库根目录>"]
    }
  }
}
```

**没有 MCP 也能跑**：每个能力都有文件级等价物（`search_files` / `read_file` / `write_file`），降级表见 [`mcp/README.md`](mcp/README.md)。工具名 `search_vault`、`get_rule_snippet`、`save_inbox_draft` 等是**契约**，技能在 frontmatter 里声明自己会调哪些，门禁拒绝任何不在规范集合里的名字。

### 3) 引擎脚本

`dfs-exec`、`dfs-handoff`、`dfs-inbox-consolidate` 靠 `scripts/` 下的实际程序工作（执行台账、事务化归档）：

```bash
python scripts/vault_exec_state.py init --plan-file implementation_plan.md
python scripts/vault-inbox-consolidate.py --vault-path <知识库根> --dry-run
```

细节与「哪些没随包」见 [`scripts/README.md`](scripts/README.md)。

---

## 🧭 技能全览（23 个 · 主链 7 个）

主链是 `dfs`（路由）→ `dfs-plan`（计划）→ `dfs-exec`（TDD 执行）→ `dfs-debug`（根因调试）→ `dfs-save`（沉淀）→ `dfs-handoff`（交接），加 `dfs-team`（多专家共识评审）。

「前置」这一列是**实测**的，不是分类癖好——`tests/test_readme_skill_table.py` 会重新推导每一行，手改对不上就判红。**—** 装完即用；**需知识库** 要先接上自己的知识库（MCP 或文件级降级）；**需额外资产** 引用了刻意不随包的私有工具，需要自备等价物（见 [`scripts/README.md`](scripts/README.md)）。

> `dfs-agent-sdk`（一份 **pi-agent SDK 的第三方文档语料**：来自 [`buchidonggua/dg-ai-notes`](https://github.com/buchidonggua/dg-ai-notes) 的 `dg-piagent` skill，**非本仓库作者作品**；曾占本仓库 90% 字节、与 DFS 的工程约束论点无关）**不随本仓库发布**。

| 技能 | 作用 | 前置 | MCP | 附带资产 |
|---|---|---|---|---|
| **主链** `dfs` | Route developer intent to the right Defensive Skills workflow. Use when the user asks for a coding task and you must decide which dfs skill to load, or when it is unclear where to start. | 需知识库 | — | refs×5 |
| **主链** `dfs-plan` | Draft bite-sized TDD implementation plans from specs. Use when the user asks for an implementation plan, or before writing code for a multi-step feature. | 需知识库 | omni_search, get_code_template | tpl×1 |
| **主链** `dfs-exec` | Execute TDD plans via isolated subagents with maker-checker. Use when an implementation plan exists and the user asks to execute or implement it. | 需知识库 | — | tpl×2 |
| **主链** `dfs-debug` | Execute 4-step systematic root-cause debugging with a reproduction. Use when the user reports a bug, a failing test, or says something is broken. | 需知识库 | search_vault, save_inbox_draft | tpl×1 |
| **主链** `dfs-save` | Harvest non-obvious engineering solutions into 99-Inbox drafts. Use when a debugging session or task just produced a reusable insight worth saving. | 需知识库 | search_vault, save_inbox_draft | tpl×1 |
| **主链** `dfs-handoff` | Generate a session wrap-up and a 1-click continuation card. Use when the user wants to pause, hand off, or resume later in a fresh session. | 需知识库 | — | tpl×1 |
| **主链** `dfs-team` | Audit code, a design, or a plan with a multi-domain subagent swarm, then collapse the findings into a single consensus report. Use when the target spans two or more specialist domains and needs several independent expert reviews. | — | — | tpl×1 |
| `dfs-adr` | Draft and archive numbered Architecture Decision Records. Use when the user makes an architecture decision or asks to record one. | 需知识库 | — | tpl×1 |
| `dfs-bootstrap` | Initialize a repository with security git hooks and DFS rule anchors. Use when starting a new repo or adding DFS guardrails to an existing one. | 需知识库 | — | tpl×2 scripts×1 |
| `dfs-grill` | Interrogate a proposal's boundaries and undecided points through Dual-Lens Socratic inquiry, ending in an architecture decision record. Use when the user wants an idea, design, or plan challenged or pressure-tested before building. | 需知识库 | omni_search | — |
| `dfs-inbox-consolidate` | Classify and archive 99-Inbox drafts into DFS destinations. Use when the inbox has accumulated drafts and the user asks to file or clean them up. | 需额外资产 | promote_inbox_draft | — |
| `dfs-incident` | Triage a production incident and draft a blameless postmortem. Use when a service is down, degraded, or the user asks for an incident review. | 需知识库 | — | tpl×1 |
| `dfs-interview` | Conduct high-rigor 1v1 technical interview defense drills. Use when the user wants to rehearse explaining or defending their own work. | 需知识库 | — | — |
| `dfs-migrate` | Plan zero-downtime database schema migrations safely. Use when a schema change must ship without taking the service offline. | — | — | tpl×1 scripts×1 |
| `dfs-onboard` | Rapidly orient an AI agent to develop on an existing codebase. Use when entering an unfamiliar repo and you need to map how it works before editing. | 需知识库 | — | — |
| `dfs-perf` | Profile multi-language benchmarks, races, and query plans. Use when the user reports slowness, a performance regression, or asks for a benchmark. | — | — | tpl×1 scripts×1 |
| `dfs-pipeline` | Execute an end-to-end Git Worktree multi-skill pipeline. Use when a task spans several DFS skills and each stage needs an isolated worktree. | 需知识库 | — | — |
| `dfs-refactor` | Execute senior-level refactoring with guard-clause flattening. Use when the user asks to clean up, simplify, or restructure existing code. | — | — | — |
| `dfs-release` | Draft semantic releases, changelogs, and rollback plans. Use when the user asks to cut a release, tag a version, or write a changelog. | — | — | tpl×2 scripts×1 |
| `dfs-research` | Research external sources and sink findings into the Vault. Use when the user asks to investigate a topic and record what was learned. | 需知识库 | search_vault, omni_search, get_note, get_rule_snippet, save_inbox_draft | tpl×1 |
| `dfs-review` | Review a code diff against 7-language RFC 2119 DFS rules. Use when the user asks for a code review, or before merging a change. | 需知识库 | get_rule_snippet, list_standards | tpl×1 |
| `dfs-spark` | Generate a design specification from a fuzzy need through Dual-Lens dialogue, at a size the idea earns. Use when the user has an idea with no design yet and wants it shaped into a spec, a short design note, or a feasibility answer. | 需知识库 | omni_search | tpl×1 |
| `dfs-tdd` | Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards. Use when implementing a feature test-first, or when a green test suite is suspect. | 需知识库 | get_code_template | — |

---

## 🛡️ 这套门禁自己怎么被验证

**别读这段，直接跑**——全部零依赖，不需要 pytest：

```bash
python tests/test_skills_conformance.py    # 13 条规则 × 23 个技能        → exit 0
python tests/mutation_check.py             # 给每条规则注入缺陷，必须被抓 → exit 0
python tests/test_knowledge_server.py      # MCP 服务真实 stdio 协议      → exit 0
python tests/test_vendored_scripts.py      # 台账 / 事务化归档 / 回滚     → exit 0
python tests/test_docs_links.py            # 文档链接不悬空、不指向未随包文件 → exit 0
python tests/test_bootstrap_script.py      # bootstrap.py：幂等 / 不覆写钩子 / 不泄路径 / 不预置伪造历史 → exit 0
python tests/test_readme_skill_table.py    # README 技能表可被树重新导出（含前置分档）→ exit 0
python tests/test_install.py               # 安装器：分档筛选 / 不覆盖已有 / dry-run → exit 0
python tests/test_harness_field_mapping.py # frontmatter 字段映射表与树一致 → exit 0
python tests/test_shipped_assets_tracked.py # 随包资产真被 git 跟踪（否则 clone 跑不起来）→ exit 0
```

十个门禁在 **Python 3.11.8 与 3.14.7 下结果完全一致**（这条是设计目标：门禁的结论不该取决于你碰巧用哪个解释器调用它——早期版本 `import yaml`，在没有 PyYAML 的解释器下直接跑不起来）。

几条刻意的设计，值得单独说：

* **文档也在门禁管辖内。** `test_docs_links.py` 拒绝悬空链接，也拒绝指向「刻意不入库」状态的链接；本仓库准备首个公开发布时它当场抓到两处真链接（README 当时还在链 `HANDOFF.md` 与 `WORKMEMORY/`）。这道门禁自己也做了变异验证：注入 5 个缺陷，全部被抓。

* **没有变异测试的绿不算绿。** `mutation_check.py` 往一棵临时拷贝里注入 20 个缺陷（删文件、改 frontmatter、塞悬空指针、塞绝对路径、塞近似拼错……），断言每个都被**对应的那条规则**抓住，同时断言干净树**零失败**。规则从红转绿时必须同时补它自己的变异用例——本仓库刚刚就是这么做的：Rule 8 修好那一刻，夹具立刻报 `BASELINE MOVED`，因为它此前只靠"预期为红"覆盖，从没用例证明过它真能判红。
* **豁免是声明，不是消音器。** 少数引用指向**故意不随包**的私有工具，它们登记在 `OPTIONAL_SCRIPT_POINTERS` 里；某条豁免一旦不再被任何技能引用，Rule 8 立刻判红——防止豁免表烂成集体消音器。
* **同一条关系，反过来问也是门禁。** 规则 1–12 都在检查技能「说了什么」，没有一条会发现反面缺陷：一个随包、占着 clone 的字节、却没有任何正文把读者引过去的文件。Rule 5 管的是这条关系的一半——指针找得到文件；**谁也不管文件是否被指针找到**。实测：往 `dfs/references/` 放一个没人引用的文件、把 README 的 `refs×N` 计数改对、再 `git add`，12 条规则可以全绿。Rule 13 补上另一半。它能被满足的方式有两种：正文指过去，或在 `CODE_ROUTED_ASSETS` 里声明读它的那个程序——而声明同样自失效（资产变成正文可达、或程序不再提及它，声明即失效判红）。`bootstrap.py` 读取的 4 个 `WORKMEMORY/` 模板就是这样声明的：正文路由到脚本、脚本再读模板，这条链是真的，硬要求正文逐个指过去只会制造假阳性。
* **不许引用只在自己机器上解析得通的东西。** 规则 8/10 明确禁止把 `scripts/...` 借给仓库外的路径、禁止硬编码知识库绝对路径。
* **本机全绿 ≠ 陌生人 clone 能用。** `test_shipped_assets_tracked.py` 不测磁盘，测**「clone 下来会拿到什么」**：随包路径下不允许有被 `.gitignore` 吞掉的文件（构建缓存除外），也不允许有忘了入库的文件。这道门禁是**补票**——`.gitignore` 里一条没加锚的 `WORKMEMORY/` 在**任意深度**匹配，而 git 在 Windows 上忽略匹配**不区分大小写**，于是静默吞掉了 `dfs-bootstrap/templates/workmemory/` 那 4 个模板，它们**从未进过任何一次 commit**；本机十套门禁全绿（文件就躺在磁盘上），而别人的 clone 里 `dfs-bootstrap` 直接 `exit 2: template(s) missing`。

### 13 条一致性规则

| # | 断言 |
|---|---|
| 1 | 每个技能目录存在且含非空 `SKILL.md` |
| 2 | frontmatter 可解析，`name` / `description` 非空 |
| 3 | `description` 含显式触发子句（`Use when …`）、≤ 320 字符、以句点结尾、不含营销词 |
| 4 | 路由技能 `dfs` 必须 `disable-model-invocation: true` |
| 5 | `templates/` 与 `references/` 里的指针必须在磁盘上解析得到 |
| 6 | 不得硬编码 `~/.claude/agents/` 这类路径而不给中性回退；扫描范围含正文 + `templates/` + `references/`，**逐文件**配对 |
| 7 | `related_skills` 每项都指向真实技能或白名单内的外部技能，且不得重复列出 |
| 8 | 每个 `scripts/<file>` 引用必须真实随包；**永不外借** |
| 9 | 声明的 `mcp_tools` 只能是规范工具名 |
| 10 | 禁止硬编码知识库绝对路径，改用 `{vault_root}` / 环境变量 |
| 11 | 正文里调用过 `tool(...)` 就必须在 `mcp_tools` 里声明 |
| 12 | 形似 MCP 的调用点必须规范；近似拼错（如 `serch_vault`）直接拒绝 |
| 13 | 随包的 `references/` / `templates/` 资产必须能从某个正文到达；只能被程序读取的，把消费者声明出来（声明会自失效） |

---

## 🗂️ 知识库布局与根目录契约

技能与脚本都不假定你的目录名。根目录解析契约（`--root` / `--vault-path` → `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → 向上找 `AGENTS.md` / `.obsidian/` → **没有知识库时进入「只存档」模式**，绝不回退到某个硬编码路径）：

```json
{
  "content_dirs": ["notes", "rules", "inbox"],
  "rules_dir": "rules",
  "languages_dir": "standards",
  "career_dir": "career",
  "inbox_dir": "inbox",
  "code_template_dir": "templates/code",
  "prompts_dir": "tools/subagents"
}
```

把这段存成知识库根目录的 `knowledge.json` 即可覆盖默认布局；未知键会被**报错**而不是忽略。默认值对应 DFS 一贯使用的目录名（`01-Rules/`、`03-Languages/`、`99-Inbox/`…），所以不改也没问题。

**还没有知识库？** 也能用：`save_inbox_draft` 会把草稿落到投放箱（`$DFS_INBOX`，否则 `<cwd>/.dfs-inbox/`），首次写入时自动生成一个自我说明的 `README.md`，并把**绝对路径**打进输出；检索类工具此时一律拒绝，并说明原因（"没找到" 与 "没接知识库" 必须长得不一样）。`--root` 指错则直接 exit 2，不会悄悄变成投放箱；之后配好知识库，用 `vault-inbox-consolidate.py --inbox <投放箱> --vault-path <你的根> --execute` 一次性归档。

---

## ⚠️ 已知边界（不藏）

* **`dfs-bootstrap` Phase 3.5 已完成跨平台移植。** `dfs-bootstrap/scripts/bootstrap.py`（stdlib）一次跑完：校验并补齐 `.gitignore`、安装密钥扫描钩子（**绝不覆写**已有钩子）并设置 `core.hooksPath`、注入规则锚点、下发 `WORKMEMORY/` 四件套；幂等，`--dry-run` 可预览，模板缺失即 **exit 2** 而不是跳过。原先那版 Windows-only PowerShell 不随包（对照见 [`scripts/README.md`](scripts/README.md)）。
* **`vault-healthcheck.py` / `vault-inbox-triage.py` 不随包。** 它们体检的是特定知识库的结构，换成别人的库天生就是错的——受影响的是 `dfs-inbox-consolidate`（即表格里唯一标为「需额外资产」的技能）。
* **检索是加权关键词/标签打分，不是 BM25 + 图谱。** 对笔记量级的知识库足够；上万篇就该换真正的排序器（升级点写在 `mcp/knowledge_server.py` 的模块注释里）。
* **frontmatter 里的 `disable-model-invocation` / `metadata.hermes.*` 是 Hermes 方言。** 映射表已落地于 [`dfs/references/harness-field-mapping.md`](dfs/references/harness-field-mapping.md)：逐条说明哪个 harness 认哪个键，以及不认的键该用哪个等效杠杆来强制同一意图。注意 `metadata.hermes.mcp_tools` **不是任何 harness 的功能**——它是本套件自己的声明，由一致性门禁校验。
* **投放箱不是知识库。** 完全没有知识库时草稿能存能列，但**归档（晋级）必须有一个知识库根**——`--execute` 在没有根时会 exit 2，而不是猜一个目标目录。这是刻意的：归档是"删原件 + 写正式目录"，目标都不能猜。
* 仓库内含 **23 个技能**（`dfs-agent-sdk` 已移出——它是第三方语料，不随本仓库发布）；表格的「前置」列把每个技能的依赖实测标出，最轻的 5 个零前置技能装完即用。
* **渐进式披露实际是两级，不是三级。** Skill 规范推荐「`description`（始终在索引里）→ SKILL.md 正文 → `references/`＋`scripts/` 详细资料」的三级披露。本套件落实的是**前两级**：23 个技能的 `description` 全部携带显式触发子句（第一级），正文承载完整流程（第二级）。第三级只有 `dfs` 用到了——它带 `references/`×3；其余 22 个技能没有 `references/` 子目录，也没有任何技能用到嵌套主题层级。这是刻意的：这里的每个技能都是**一条稳定工作流**，把正文压到 500 行以内比造层级更划算；等某个技能真的需要纵深再拆第三级。
* **语言策略：英文机器面、双语 README、正文英文优先。** agent 路由时必然加载的 frontmatter（`name` / `description` / `mcp_tools`）已全英文；`SKILL.md` 正文 14/23 为纯英文，残余 **1,865 个汉字**分布在 9 个技能里（最大三处：`dfs-inbox-consolidate` 473 / `dfs` 342 / `dfs-grill` 307，其余为零星片段）——**刻意保留，不是未完工**：面板数据不参与指令，对模型理解无影响，翻译的收益远小于它带来的维护成本。提 issue / PR 用英文即可。

---

## 📁 目录导航

| 需要什么 | 去哪 |
|---|---|
| 知识层 MCP：注册、根契约、无 MCP 降级表 | [`mcp/README.md`](mcp/README.md) |
| 随包引擎脚本 / 未随包清单 / 移植分歧 | [`scripts/README.md`](scripts/README.md) |
| 各 harness 认哪些 frontmatter 字段 | [`dfs/references/harness-field-mapping.md`](dfs/references/harness-field-mapping.md) |
| 一致性门禁与变异夹具 | [`tests/`](tests/) |
| 按分档安装到目标 harness | [`install.py`](install.py) |
| 仓库安全守卫（密钥扫描钩子） | [`.githooks/pre-commit`](.githooks/) |
| 英文版 README | [`README.en.md`](README.en.md) |

**刻意不入库的本机生成物**：harness 锚点（`AGENTS.md` / `CLAUDE.md` / `.agent-rules.md` / `.cursorrules`）、`WORKMEMORY/` 工作记忆、会话交接文档 —— 由 `dfs-bootstrap` 在本机生成，且会把 `{vault_root}` 解析成绝对路径；提交它们等于把一台机器的目录布局当成所有人的。见 `.gitignore`。

仓库自带零泄漏 pre-commit 钩子（密钥/keystore/敏感文件扫描），`git config core.hooksPath .githooks` 即可启用。

---

## 📄 License

MIT — 见 [`LICENSE`](LICENSE)。
