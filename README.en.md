# Defensive Skills (DFS) · give an AI coding agent's gates real teeth

<p align="center">
  <a href="README.md">中文</a> · <b>English</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-23-4B5563?style=flat-square" alt="Skills" />
  <img src="https://img.shields.io/badge/Conformance-12%20rules-0969DA?style=flat-square" alt="Conformance rules" />
  <img src="https://img.shields.io/badge/Tests-92%20passed-2EA44F?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/Mutation-14%2F14%20caught-2EA44F?style=flat-square" alt="Mutation harness" />
  <img src="https://img.shields.io/badge/Dependencies-0%20(stdlib)-gray?style=flat-square" alt="Zero dependencies" />
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?style=flat-square" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-gray?style=flat-square" alt="License MIT" />
</p>

<p align="center">
  <b>An engineering-constraint framework for AI coding agents: pure-Markdown skills plus zero-dependency gates, aimed at one failure mode — "everything looks green and nobody actually checked".</b>
</p>

---

## 🎯 The three things it pushes back on

Not a feature list — three specific failure modes, each with a receipt from this repository's own history.

**1. Fake-green gates — "the tests pass" and "it is actually fine" are two different claims.**
This repo's conformance gate started with 6 rules and reported all green. Adding **mutation testing** (inject a defect for every declarative check, assert it must go red) and deleting the "a `scripts/...` reference may resolve onto the author's own machine" escape hatch grew it to 12 rules — and it immediately reported **21 script references that only resolve on the author's machine**, spread across 6 skills. The green set never changed; what changed was whether anything was being checked.

**2. Planning hallucination — writing a detailed plan for code you never read.**
`dfs-plan` emits only the next steps that are **knowable right now** (staged planning), each with its verification method. `dfs-exec` enforces "repro or failing test first, implementation second". `dfs-tdd` watches specifically for TDD's fake-green shortcuts. Assertions without evidence are not allowed in a plan.

**3. Silent failures — something went wrong and the exit code was still 0.**
When `vault-inbox-consolidate.py` was ported, its `<script>/../..` fallback happened to land on the checkout's own `AGENTS.md`, so the tool treated the working directory as a knowledge base, reported "inbox does not exist", and **exited 0** — a silent wrong answer, end to end. Now an unresolvable root means `exit 2` plus instructions for configuring it. The same rule runs through the whole repo: **fail loudly, never swallow an exception, never invent a default.**

---

## 🚀 Quick start

### 1) Install the skills

A skill is just a directory containing `SKILL.md`. Copy (or symlink) them into your harness's skills directory. The paths below were verified to exist on a real machine:

| Harness | Skills directory |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Hermes | `<hermes profile dir>/skills/` |

```bash
# all 23, or only the 5 with no prerequisites; links by default, copies on Windows
python install.py --target ~/.codex/skills
python install.py --target ~/.codex/skills --tier A
```

`install.py` reads the tiers straight from the catalogue table below (which a gate keeps honest), and also takes `--mode copy|link`, `--force`, `--dry-run`. Not interested? `cp -r dfs dfs-* ~/.codex/skills/` still works.

### 2) Install the knowledge layer (optional, but recommended)

The skills retrieve from *your own* Markdown knowledge base through the `coding-vault-search` MCP server. This repo ships a **stdio JSON-RPC, zero-dependency** implementation:

```jsonc
{
  "mcpServers": {
    "coding-vault-search": {
      "command": "python",
      "args": ["<repo>/mcp/knowledge_server.py", "--root", "<your knowledge base root>"]
    }
  }
}
```

**It also works without MCP**: every capability has a file-level equivalent (`search_files` / `read_file` / `write_file`) — the fallback table is in [`mcp/README.md`](mcp/README.md). Tool names like `search_vault`, `get_rule_snippet` and `save_inbox_draft` are a **contract**: skills declare which ones they call in their frontmatter, and the gate rejects any name outside the canonical set.

### 3) The engine scripts

`dfs-exec`, `dfs-handoff` and `dfs-inbox-consolidate` rely on real programs under `scripts/` (execution ledger, transactional archival):

```bash
python scripts/vault_exec_state.py init --plan-file implementation_plan.md
python scripts/vault-inbox-consolidate.py --vault-path <knowledge root> --dry-run
```

What ships and what deliberately does not: [`scripts/README.md`](scripts/README.md).

---

## 🧭 Skill catalogue (23 skills · 7 on the main chain)

The main chain is `dfs` (route) → `dfs-plan` (plan) → `dfs-exec` (TDD execution) → `dfs-debug` (root-cause debugging) → `dfs-save` (harvest) → `dfs-handoff` (handoff), plus `dfs-team` (multi-expert consensus review).

The "prerequisite" column is **measured**, not decorative — `tests/test_readme_skill_table.py` re-derives every row and fails if the table disagrees. **—** works out of the box; **knowledge base** wants your own knowledge base wired up (MCP, or the file-level fallback); **extra assets** references deliberately unshipped private tooling, so bring an equivalent (see [`scripts/README.md`](scripts/README.md)).

> `dfs-agent-sdk` (the author's own pi-agent SDK documentation corpus — 90% of this repo's bytes, and unrelated to the DFS argument) **is not published here**; it ships separately.

| Skill | Purpose | Prerequisite | MCP | Bundled |
|---|---|---|---|---|
| **chain** `dfs` | Route developer intent to optimal Defensive Skills. | knowledge base | — | refs×3 |
| **chain** `dfs-plan` | Draft bite-sized TDD implementation plans from specs. | knowledge base | omni_search, get_code_template | tpl×1 |
| **chain** `dfs-exec` | Execute TDD plans via isolated subagents with maker-checker. | knowledge base | — | tpl×2 |
| **chain** `dfs-debug` | Execute 4-step systematic root-cause debugging with repro. | knowledge base | search_vault, save_inbox_draft | tpl×1 |
| **chain** `dfs-save` | Harvest non-obvious engineering solutions to 99-Inbox. | knowledge base | search_vault, save_inbox_draft | tpl×1 |
| **chain** `dfs-handoff` | Generate session wrap-up and 1-click continuation cards. | knowledge base | — | tpl×1 |
| **chain** `dfs-team` | Orchestrate multi-expert subagent reviews with consensus. | — | — | tpl×1 |
| `dfs-adr` | Draft and archive numbered Architecture Decision Records. | knowledge base | — | tpl×1 |
| `dfs-bootstrap` | Initialize repos with security git hooks and DFS anchors. | knowledge base | — | tpl×2 scripts×1 |
| `dfs-grill` | Stress-test architecture via Dual-Lens Socratic inquiry. | knowledge base | omni_search | — |
| `dfs-inbox-consolidate` | Classify and archive 99-Inbox drafts to DFS destinations. | extra assets | promote_inbox_draft | — |
| `dfs-incident` | Triage production incidents and draft blameless postmortems. | knowledge base | — | tpl×1 |
| `dfs-interview` | Conduct high-rigor 1v1 technical interview defense drills. | knowledge base | — | — |
| `dfs-migrate` | Plan zero-downtime database schema migrations safely. | — | — | tpl×1 scripts×1 |
| `dfs-onboard` | Rapidly orient AI agent to develop on existing codebases. | knowledge base | — | — |
| `dfs-perf` | Profile multi-language benchmarks, races, and query plans. | — | — | tpl×1 scripts×1 |
| `dfs-pipeline` | Execute end-to-end Git Worktree multi-skill pipeline. | knowledge base | — | — |
| `dfs-refactor` | Execute senior-level refactoring & guard clause flattening. | — | — | — |
| `dfs-release` | Draft semantic releases, changelogs, and rollback plans. | — | — | tpl×2 scripts×1 |
| `dfs-research` | Research external sources and sink findings into the Vault. | knowledge base | search_vault, omni_search, get_note, get_rule_snippet, save_inbox_draft | tpl×1 |
| `dfs-review` | Review code diffs against 7-language RFC 2119 DFS rules. | knowledge base | get_rule_snippet, list_standards | tpl×1 |
| `dfs-spark` | Turn 0-to-1 ideas into specs via Dual-Lens dialogue. | knowledge base | omni_search | tpl×1 |
| `dfs-tdd` | Enforce strict RED-GREEN-REFACTOR TDD and fake-green guards. | knowledge base | get_code_template | — |

---

## 🛡️ How these gates are verified

**Don't take this section's word for it — run them.** All four are zero-dependency; no pytest needed:

```bash
python tests/test_skills_conformance.py    # 12 rules × 23 skills                → exit 0
python tests/mutation_check.py             # inject a defect per rule; all must land → exit 0
python tests/test_knowledge_server.py      # MCP server over real stdio JSON-RPC → exit 0
python tests/test_vendored_scripts.py      # ledger / transactional archival / rollback → exit 0
python tests/test_docs_links.py            # docs links resolve; never to untracked state → exit 0
python tests/test_bootstrap_script.py      # bootstrap.py: idempotent / never clobbers / never leaks → exit 0
python tests/test_readme_skill_table.py    # the skill table is re-derivable from the tree → exit 0
python tests/test_install.py               # installer: tier filter / never clobbers / dry-run → exit 0
python tests/test_harness_field_mapping.py # the harness field map matches the tree → exit 0
```

All nine produce **identical results under Python 3.11.8 and 3.14.7**. That is a design goal, not a coincidence: a gate's verdict must not depend on which interpreter you happen to invoke it with. An early version did `import yaml` and simply could not run on an interpreter without PyYAML.

Four deliberate design choices worth calling out:

* **The docs are inside the gate's jurisdiction too.** `test_docs_links.py` rejects dangling links and links to deliberately-untracked state; while preparing this repo's first public commit it caught two real ones (the README still linked `HANDOFF.md` and `WORKMEMORY/`). The gate is mutation-probed itself: 5 injected defects, all caught.

* **A green run without mutation testing is not green.** `mutation_check.py` injects 14 defects into a temporary copy (delete a file, edit frontmatter, plant a dangling pointer, plant an absolute path, plant a near-miss typo, …), asserts each one is caught **by its corresponding rule**, and asserts the clean tree reports zero failures. A rule going from red to green must ship its own mutation case in the same change — this repo just did exactly that: the moment Rule 8 went green, the harness reported `BASELINE MOVED`, because the rule had only ever been covered by "expected to be red" and nothing had ever proven it could actually fail.
* **Exemptions are declarations, not silencers.** A few references point at private tools that deliberately do not ship; they are registered in `OPTIONAL_SCRIPT_POINTERS`. An exemption that stops matching any reference makes Rule 8 fail immediately — the table cannot rot into a collective mute button.
* **Referencing something that only resolves on your machine is banned.** Rules 8 and 10 refuse to let `scripts/...` point outside the repo, and refuse hardcoded absolute knowledge-base paths.

### The 12 conformance rules

| # | Assertion |
|---|---|
| 1 | Every skill directory exists and holds a non-empty `SKILL.md` |
| 2 | Frontmatter parses; `name` / `description` are non-empty |
| 3 | `description` ≤ 60 chars, ends with a period, no marketing words |
| 4 | The router skill `dfs` must set `disable-model-invocation: true` |
| 5 | Pointers inside `templates/` and `references/` resolve on disk |
| 6 | No hardcoded `~/.claude/agents/`-style paths without a neutral fallback |
| 7 | Every `related_skills` entry resolves to a real skill or an allowlisted external one |
| 8 | Every `scripts/<file>` reference actually ships; **never borrowed from outside** |
| 9 | Declared `mcp_tools` must be canonical tool names |
| 10 | No hardcoded absolute knowledge-base paths; use `{vault_root}` / env vars |
| 11 | Calling `tool(...)` in the body requires declaring it in `mcp_tools` |
| 12 | MCP-shaped call sites must be canonical; near-miss typos (`serch_vault`) are rejected |

---

## 🗂️ Knowledge-base layout and root contract

Neither the skills nor the scripts assume your directory names. Root resolution (`--root` / `--vault-path` → `$WIKI_PATH` → `$OBSIDIAN_VAULT_PATH` → walk up for `AGENTS.md` / `.obsidian/` → **error out**, never fall back to some hardcoded path):

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

Save that as `knowledge.json` in your knowledge-base root to override the defaults; unknown keys are an **error**, not ignored. The defaults match the directory names DFS has always used (`01-Rules/`, `03-Languages/`, `99-Inbox/`…), so doing nothing is fine.

---

## ⚠️ Known limits (nothing hidden)

* **`dfs-bootstrap` Phase 3.5 is ported and cross-platform now.** `dfs-bootstrap/scripts/bootstrap.py` (stdlib) does the whole pass in one shot: verify/extend `.gitignore`, install the secret-scanning hook (**never overwriting** an existing one) and set `core.hooksPath`, inject the rule anchor, scaffold the 4-piece `WORKMEMORY/` set. Idempotent, `--dry-run` previews, and a missing template is **exit 2** rather than a skip. The old Windows-only PowerShell version does not ship (comparison in [`scripts/README.md`](scripts/README.md)).
* **`vault-healthcheck.py` / `vault-inbox-triage.py` do not ship.** They audit the structure of one specific knowledge base; pointed at anyone else's, they are wrong by construction. They affect `dfs-inbox-consolidate`, the one skill labelled "extra assets" in the table above.
* **Retrieval is weighted keyword/tag scoring, not BM25 + a graph.** Fine for a knowledge base at note scale; past tens of thousands of notes you want a real ranker (the upgrade point is documented in `mcp/knowledge_server.py`'s module docstring).
* **`disable-model-invocation` / `metadata.hermes.*` in frontmatter is Hermes dialect.** The map to
  other harnesses is [`dfs/references/harness-field-mapping.md`](dfs/references/harness-field-mapping.md):
  which harness honors which key, and — for the keys it does not — the lever that enforces the same
  intent. `metadata.hermes.mcp_tools` is **not** a harness feature at all: it is this suite's own
  declaration, checked by the conformance gate.
* The repo contains **23 skills** (`dfs-agent-sdk` was moved out and ships separately); the "prerequisite" column measures what each skill actually depends on, and the 5 with no prerequisite work the moment they are installed.

---

## 📁 Repository map

| You want | Go to |
|---|---|
| Knowledge-layer MCP: registration, root contract, no-MCP fallback table | [`mcp/README.md`](mcp/README.md) |
| Bundled engine scripts / what does not ship / port divergences | [`scripts/README.md`](scripts/README.md) |
| Which harness honors which frontmatter field | [`dfs/references/harness-field-mapping.md`](dfs/references/harness-field-mapping.md) |
| Conformance gate and mutation harness | [`tests/`](tests/) |
| Install into a harness by tier | [`install.py`](install.py) |
| Repo security guard (secret-scanning hook) | [`.githooks/pre-commit`](.githooks/) |

Harness anchors (`AGENTS.md`, `CLAUDE.md`, `.agent-rules.md`, `.cursorrules`), the `WORKMEMORY/` working log and the session handoff doc are **generated locally by `dfs-bootstrap` and intentionally not tracked** — they resolve `{vault_root}` to machine-specific absolute paths, so committing them would ship one machine's layout as if it were everyone's. See `.gitignore`.

The repo ships a zero-leak pre-commit hook (secret / keystore / sensitive-file scanning); enable it with `git config core.hooksPath .githooks`.

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).
