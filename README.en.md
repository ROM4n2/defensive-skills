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
| `dfs` | Route developer intent to the right Defensive Skills workflow. Use only when the user explicitly asks which DFS workflow to use, how this DFS process works, or asks for help choosing a DFS skill; do not use for general coding tasks. | No |
| `dfs-plan` | Draft bite-sized TDD implementation plans from specs. Use when the user asks for an implementation plan, or before writing code for a multi-step feature. | No |
| `dfs-exec` | Execute TDD plans via adaptive gear-shifting (Tier 1 Solo-Light, Tier 2 Maker-Checker, Tier 3 Critical-Swarm). Use when an implementation plan exists and the user asks to execute or implement it. | No |
| `dfs-debug` | Execute 4-step systematic root-cause debugging with a reproduction. Use when the user reports a bug, a failing test, or says something is broken. | No |
| `dfs-save` | Harvest non-obvious engineering solutions into 99-Inbox drafts. Use when a debugging session or task just produced a reusable insight worth saving. | No |
| `dfs-handoff` | Generate a session wrap-up and a 1-click continuation card. Use when the user wants to pause, hand off, or resume later in a fresh session. | No |
| `dfs-team` | Audit code, a design, or a plan with a multi-domain subagent swarm, then collapse the findings into a single consensus report. Use when the target spans two or more specialist domains and needs several independent expert reviews. | No |
| `dfs-adr` | Draft and archive numbered Architecture Decision Records. Use when the user makes an architecture decision or asks to record one. | No |
| `dfs-bootstrap` | Initialize a repository with security git hooks and DFS rule anchors. Use when starting a new repo or adding DFS guardrails to an existing one. | **Yes** |
| `dfs-gate` | Author mechanical gates for recurring defect classes. Use when a defect class has recurred, or an audit finding needs a permanent mechanical check instead of a note. | No |
| `dfs-maintain` | Maintain repo hygiene, prune worktrees, and sync context. Use when a repo has stale worktrees, drifted context files, or needs a scheduled hygiene pass. | No |
| `dfs-orchestrate` | Dispatch and verify subagents with file-occupancy guards. Use when several subagents must work in one repo without colliding, or a batch needs a granularity call. | No |
| `dfs-verify` | Verify unverified audit claims with physical evidence. Use when a report or audit asserts something no probe has confirmed, before anyone acts on it. | No |
| `dfs-grill` | Interrogate a proposal's boundaries and undecided points through Dual-Lens Socratic inquiry, ending in an architecture decision record. Use when the user wants an idea, design, or plan challenged or pressure-tested before building. | No |
| `dfs-inbox-consolidate` | Classify and archive 99-Inbox drafts into DFS destinations. Use when the inbox has accumulated drafts and the user asks to file or clean them up. | **Yes** |
| `dfs-incident` | Triage a production incident and draft a blameless postmortem. Use when a service is down, degraded, or the user asks for an incident review. | **Yes** |
| `dfs-interview` | Conduct high-rigor 1v1 technical interview defense drills. Use when the user wants to rehearse explaining or defending their own work. | No |
| `dfs-migrate` | Plan zero-downtime database schema migrations safely. Use when a schema change must ship without taking the service offline. | No |
| `dfs-onboard` | Rapidly orient an AI agent to develop on an existing codebase. Use when entering an unfamiliar repo and you need to map how it works before editing. | No |
| `dfs-perf` | Profile multi-language benchmarks, races, and query plans. Use when the user reports slowness, a performance regression, or asks for a benchmark. | No |
| `dfs-pipeline` | Execute an end-to-end Git Worktree multi-skill pipeline. Use when a task spans several DFS skills and each stage needs an isolated worktree. | **Yes** |
| `dfs-refactor` | Execute senior-level refactoring with guard-clause flattening. Use when the user asks to clean up, simplify, or restructure existing code. | No |
| `dfs-release` | Draft semantic releases, changelogs, rollback plans, and verify published releases. Use when the user asks to cut a release, tag a version, write a changelog, or check whether a release actually shipped. | No |
| `dfs-research` | Research external sources and sink findings into the Vault. Use when the user asks to investigate a topic and record what was learned. | No |
| `dfs-review` | Review a code diff against 7-language RFC 2119 DFS rules. Use when the user asks for a code review, or before merging a change. | No |
| `dfs-spark` | Generate a design specification from a fuzzy need through Dual-Lens dialogue, at a size the idea earns. Use when the user has an idea with no design yet and wants it shaped into a spec, a short design note, or a feasibility answer. | No |
| `dfs-tdd` | Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards. Use when implementing a feature test-first, or when a green test suite is suspect. | No |
| `dfs-upgrade` | Assess breaking changes and upgrade risk for a dependency. Use when upgrading a package version and you need to know what will break and in which files. | No |

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
