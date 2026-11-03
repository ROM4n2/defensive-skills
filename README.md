# Defensive Skills

[English](README.en.md)

28 个面向编码代理的 Markdown 技能，附脚本化门禁。

## 安装与验证

前置条件：Git、Python 3.11+。

```bash
git clone https://github.com/ROM4n2/defensive-skills.git
cd defensive-skills
python install.py --target <你的技能目录>
python -m pytest tests/ -q
```

安装器参数：`--tier A`、`--mode copy|link`、`--force`、`--dry-run`。

## 可选：知识库 MCP

```jsonc
{
  "mcpServers": {
    "coding-vault-search": {
      "command": "python",
      "args": ["<repo>/mcp/knowledge_server.py", "--root", "<知识库根目录>"]
    }
  }
}
```

无 MCP 时使用文件级等价操作，见 [`mcp/README.md`](mcp/README.md)。

## 技能清单（28 个）

仅 `dfs-bootstrap`、`dfs-inbox-consolidate`、`dfs-incident`、`dfs-pipeline` 保留顶层 `disable-model-invocation`。`dfs`、`dfs-interview`、`dfs-handoff` 均可由模型调用。

| Skill | 用途 | 仅显式调用 |
|---|---|---|
| `dfs` | Route developer intent to the right Defensive Skills workflow. Use only when the user explicitly asks which DFS workflow to use, how this DFS process works, or asks for help choosing a DFS skill; do not use for general coding tasks. | 否 |
| `dfs-plan` | Draft bite-sized TDD implementation plans from specs. Use when the user asks for an implementation plan, or before writing code for a multi-step feature. | 否 |
| `dfs-exec` | Execute TDD plans via adaptive gear-shifting (Tier 1 Solo-Light, Tier 2 Maker-Checker, Tier 3 Critical-Swarm). Use when an implementation plan exists and the user asks to execute or implement it. | 否 |
| `dfs-debug` | Execute 4-step systematic root-cause debugging with a reproduction. Use when the user reports a bug, a failing test, or says something is broken. | 否 |
| `dfs-save` | Harvest non-obvious engineering solutions into 99-Inbox drafts. Use when a debugging session or task just produced a reusable insight worth saving. | 否 |
| `dfs-handoff` | Generate a session wrap-up and a 1-click continuation card. Use when the user wants to pause, hand off, or resume later in a fresh session. | 否 |
| `dfs-team` | Audit code, a design, or a plan with a multi-domain subagent swarm, then collapse the findings into a single consensus report. Use when the target spans two or more specialist domains and needs several independent expert reviews. | 否 |
| `dfs-adr` | Draft and archive numbered Architecture Decision Records. Use when the user makes an architecture decision or asks to record one. | 否 |
| `dfs-bootstrap` | Initialize a repository with security git hooks and DFS rule anchors. Use when starting a new repo or adding DFS guardrails to an existing one. | **是** |
| `dfs-gate` | Author mechanical gates for recurring defect classes. Use when a defect class has recurred, or an audit finding needs a permanent mechanical check instead of a note. | 否 |
| `dfs-maintain` | Maintain repo hygiene, prune worktrees, and sync context. Use when a repo has stale worktrees, drifted context files, or needs a scheduled hygiene pass. | 否 |
| `dfs-orchestrate` | Dispatch and verify subagents with file-occupancy guards. Use when several subagents must work in one repo without colliding, or a batch needs a granularity call. | 否 |
| `dfs-verify` | Verify unverified audit claims with physical evidence. Use when a report or audit asserts something no probe has confirmed, before anyone acts on it. | 否 |
| `dfs-grill` | Interrogate a proposal's boundaries and undecided points through Dual-Lens Socratic inquiry, ending in an architecture decision record. Use when the user wants an idea, design, or plan challenged or pressure-tested before building. | 否 |
| `dfs-inbox-consolidate` | Classify and archive 99-Inbox drafts into DFS destinations. Use when the inbox has accumulated drafts and the user asks to file or clean them up. | **是** |
| `dfs-incident` | Triage a production incident and draft a blameless postmortem. Use when a service is down, degraded, or the user asks for an incident review. | **是** |
| `dfs-interview` | Conduct high-rigor 1v1 technical interview defense drills. Use when the user wants to rehearse explaining or defending their own work. | 否 |
| `dfs-migrate` | Plan zero-downtime database schema migrations safely. Use when a schema change must ship without taking the service offline. | 否 |
| `dfs-onboard` | Rapidly orient an AI agent to develop on an existing codebase. Use when entering an unfamiliar repo and you need to map how it works before editing. | 否 |
| `dfs-perf` | Profile multi-language benchmarks, races, and query plans. Use when the user reports slowness, a performance regression, or asks for a benchmark. | 否 |
| `dfs-pipeline` | Execute an end-to-end Git Worktree multi-skill pipeline. Use when a task spans several DFS skills and each stage needs an isolated worktree. | **是** |
| `dfs-refactor` | Execute senior-level refactoring with guard-clause flattening. Use when the user asks to clean up, simplify, or restructure existing code. | 否 |
| `dfs-release` | Draft semantic releases, changelogs, rollback plans, and verify published releases. Use when the user asks to cut a release, tag a version, write a changelog, or check whether a release actually shipped. | 否 |
| `dfs-research` | Research external sources and sink findings into the Vault. Use when the user asks to investigate a topic and record what was learned. | 否 |
| `dfs-review` | Review a code diff against 7-language RFC 2119 DFS rules. Use when the user asks for a code review, or before merging a change. | 否 |
| `dfs-spark` | Generate a design specification from a fuzzy need through Dual-Lens dialogue, at a size the idea earns. Use when the user has an idea with no design yet and wants it shaped into a spec, a short design note, or a feasibility answer. | 否 |
| `dfs-tdd` | Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards. Use when implementing a feature test-first, or when a green test suite is suspect. | 否 |
| `dfs-upgrade` | Assess breaking changes and upgrade risk for a dependency. Use when upgrading a package version and you need to know what will break and in which files. | 否 |

## 当前行为

| 项目 | 约定 |
|---|---|
| Ledger 位置 | `dfs-exec/scripts/vault_exec_state.py`，随包提供。 |
| 从 `dfs-exec` 调用 | 在该 Skill 目录运行 `python scripts/vault_exec_state.py <command>`。 |
| 从 `dfs-plan` 调用 | 在该 Skill 目录运行 `python ../dfs-exec/scripts/vault_exec_state.py <command>`。 |
| Bootstrap | 缺少 `.git` 时先执行 `git init`，确认分支后安装 `.githooks/pre-commit` 并设置 `core.hooksPath`；不再静默跳过。 |
| 文件占用 | `dfs-orchestrate` 唯一定义占用规则；`dfs-maintain` 只在清理前核验既有分配。 |

## 验证与已知取舍

| 检查 | 实测结果 |
|---|---|
| 完整测试 | `114 passed, 1 skipped, 74 subtests passed` |
| 变异门禁 | 27 个注入缺陷全部被捕获 |
| Frontmatter | 28/28 可解析；4 个顶层禁用字段，`metadata` 下残留 0 |
| 主文件预算 | v0.4.0 技能 ≤120 行且 ≤8,500 字节；全局技能 ≤180 行 |

通用 `agentskills validate` **不宣称全部通过**。`dfs-incident` 和 `dfs-pipeline` 的顶层禁用字段会报告 `Unexpected fields`，这是保留当前 Trae 禁用行为的跨 harness 取舍。其它 flow-list 格式问题与这一行为取舍分开处理。

## 文档

- [`mcp/README.md`](mcp/README.md)：MCP 注册、根目录与文件级等价操作。
- [`scripts/README.md`](scripts/README.md)：脚本位置、调用和未随包项。
- [`dfs/references/harness-field-mapping.md`](dfs/references/harness-field-mapping.md)：frontmatter 行为与跨 harness 取舍。

## License

MIT，见 [`LICENSE`](LICENSE)。
