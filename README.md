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
| `dfs` | Use when choosing which DFS workflow or skill to run. | 否 |
| `dfs-plan` | Use when drafting a bite-sized TDD implementation plan. | 否 |
| `dfs-exec` | Use when executing a TDD plan with subagents. | 否 |
| `dfs-debug` | Use when debugging a reproducible failure or stack trace. | 否 |
| `dfs-save` | Use when harvesting a reusable insight into the vault. | 否 |
| `dfs-handoff` | Use when ending a session with a continuation card. | 否 |
| `dfs-team` | Use when auditing with a multi-domain expert panel. | 否 |
| `dfs-adr` | Use when recording an architecture decision as a MADR. | 否 |
| `dfs-bootstrap` | Use when bootstrapping a repo with security hooks. | 是 |
| `dfs-gate` | Use when turning a recurring defect into a mechanical gate. | 否 |
| `dfs-maintain` | Use when pruning worktrees and syncing agent context. | 否 |
| `dfs-orchestrate` | Use when dispatching subagents with file ownership. | 否 |
| `dfs-verify` | Use when verifying audit claims with physical evidence. | 否 |
| `dfs-grill` | Use when interrogating a fuzzy design or proposal. | 否 |
| `dfs-inbox-consolidate` | Use when routing 99-Inbox drafts to their homes. | 是 |
| `dfs-incident` | Triage a production incident and draft a blameless postmortem. Use when a service is down, degraded, or the user asks for an incident review. | 是 |
| `dfs-interview` | Use when drilling a candidate in a technical interview. | 否 |
| `dfs-migrate` | Use when planning a zero-downtime schema migration. | 否 |
| `dfs-onboard` | Use when onboarding an agent to an unfamiliar codebase. | 否 |
| `dfs-perf` | Use when profiling benchmarks, races, or query plans. | 否 |
| `dfs-pipeline` | Use when running the worktree multi-skill pipeline. | 是 |
| `dfs-refactor` | Use when refactoring behind guard clauses. | 否 |
| `dfs-release` | Use when cutting a semantic release and changelog. | 否 |
| `dfs-research` | Use when surveying external sources for a spec. | 否 |
| `dfs-review` | Use when reviewing a diff against RFC 2119 rules. | 否 |
| `dfs-spark` | Use when turning a fuzzy idea into a design spec. | 否 |
| `dfs-tdd` | Use when enforcing RED-GREEN-REFACTOR discipline. | 否 |
| `dfs-upgrade` | Use when assessing a dependency upgrade risk. | 否 |

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
