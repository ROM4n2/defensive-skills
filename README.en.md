# Defensive Skills

[中文](README.md)

28 Markdown skills for coding agents, with scripted gates.

## Install and verify

Prerequisites: Git and Python 3.11+.

```bash
git clone https://github.com/ROM4n2/defensive-skills.git
cd defensive-skills
python install.py --target <your-skills-dir>
python -m pytest tests/ -q
```

Installer options: `--tier A`, `--mode copy|link`, `--force`, `--dry-run`.

## Optional: knowledge-base MCP

```jsonc
{
  "mcpServers": {
    "coding-vault-search": {
      "command": "python",
      "args": ["<repo>/mcp/knowledge_server.py", "--root", "<knowledge-root>"]
    }
  }
}
```

Without MCP, use the file-level equivalents in [`mcp/README.md`](mcp/README.md).

## Skill catalogue (28)

Only `dfs-bootstrap`, `dfs-inbox-consolidate`, `dfs-incident`, and `dfs-pipeline` keep top-level `disable-model-invocation`. `dfs`, `dfs-interview`, and `dfs-handoff` are model-invocable.

| Skill | Purpose | Explicit only |
|---|---|---|
| `dfs` | Use when choosing which DFS workflow or skill to run. | No |
| `dfs-plan` | Use when drafting a bite-sized TDD implementation plan. | No |
| `dfs-exec` | Use when executing a TDD plan with subagents. | No |
| `dfs-debug` | Use when debugging a reproducible failure or stack trace. | No |
| `dfs-save` | Use when harvesting a reusable insight into the vault. | No |
| `dfs-handoff` | Use when ending a session with a continuation card. | No |
| `dfs-team` | Use when auditing with a multi-domain expert panel. | No |
| `dfs-adr` | Use when recording an architecture decision as a MADR. | No |
| `dfs-bootstrap` | Use when bootstrapping a repo with security hooks. | Yes |
| `dfs-gate` | Use when turning a recurring defect into a mechanical gate. | No |
| `dfs-maintain` | Use when pruning worktrees and syncing agent context. | No |
| `dfs-orchestrate` | Use when dispatching subagents with file ownership. | No |
| `dfs-verify` | Use when verifying audit claims with physical evidence. | No |
| `dfs-grill` | Use when interrogating a fuzzy design or proposal. | No |
| `dfs-inbox-consolidate` | Use when routing 99-Inbox drafts to their homes. | Yes |
| `dfs-incident` | Triage a production incident and draft a blameless postmortem. Use when a service is down, degraded, or the user asks for an incident review. | Yes |
| `dfs-interview` | Use when drilling a candidate in a technical interview. | No |
| `dfs-migrate` | Use when planning a zero-downtime schema migration. | No |
| `dfs-onboard` | Use when onboarding an agent to an unfamiliar codebase. | No |
| `dfs-perf` | Use when profiling benchmarks, races, or query plans. | No |
| `dfs-pipeline` | Use when running the worktree multi-skill pipeline. | Yes |
| `dfs-refactor` | Use when refactoring behind guard clauses. | No |
| `dfs-release` | Use when cutting a semantic release and changelog. | No |
| `dfs-research` | Use when surveying external sources for a spec. | No |
| `dfs-review` | Use when reviewing a diff against RFC 2119 rules. | No |
| `dfs-spark` | Use when turning a fuzzy idea into a design spec. | No |
| `dfs-tdd` | Use when enforcing RED-GREEN-REFACTOR discipline. | No |
| `dfs-upgrade` | Use when assessing a dependency upgrade risk. | No |

## Current behavior

| Area | Contract |
|---|---|
| Ledger location | `dfs-exec/scripts/vault_exec_state.py`, bundled with the Skill. |
| Call from `dfs-exec` | Run `python scripts/vault_exec_state.py <command>` from that Skill directory. |
| Call from `dfs-plan` | Run `python ../dfs-exec/scripts/vault_exec_state.py <command>` from that Skill directory. |
| Bootstrap | If `.git` is missing, run `git init`, confirm the branch, then install `.githooks/pre-commit` and set `core.hooksPath`. No silent skip. |
| File occupancy | `dfs-orchestrate` is the sole authority; `dfs-maintain` only verifies the existing allocation before cleanup. |

## Validation and trade-offs

| Check | Measured result |
|---|---|
| Full test suite | `114 passed, 1 skipped, 74 subtests passed` |
| Mutation harness | All 27 injected defects caught |
| Frontmatter | 28/28 parsed; four top-level disable fields; zero under `metadata` |
| Body budget | v0.4.0 skills: ≤120 lines and ≤8,500 bytes; global skills: ≤180 lines |

Generic `agentskills validate` is **not claimed to pass everywhere**. `dfs-incident` and `dfs-pipeline` report `Unexpected fields` for their top-level disable fields. This is an intentional cross-harness trade-off that preserves current Trae behavior. Flow-list YAML issues are separate from this choice.

## Documentation

- [`mcp/README.md`](mcp/README.md): MCP registration, root handling, and file-level equivalents.
- [`scripts/README.md`](scripts/README.md): script locations, invocation, and unshipped items.
- [`dfs/references/harness-field-mapping.md`](dfs/references/harness-field-mapping.md): frontmatter behavior and the cross-harness trade-off.

## License

MIT; see [`LICENSE`](LICENSE).
