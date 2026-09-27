# Defensive Skills (DFS) — Handoff to `skill-dev`

**Generated**: 2026-09-27
**Live source of truth**: `<home>\.cc-switch\skills\` (24 skills)
**This directory**: staging tree for the standalone open-source release. **Not yet a git repo.**
**Copies here**: 24/24 in parity with source (verified hashes at generation time)

This document is the entry point for whoever (agent or human) continues in this directory.
It records the verified state, the two-subset distinction, the blockers that must be solved
before publishing, and the interface that a standalone companion MCP has to implement.

---

## 0. Corrections from the session that produced this handoff

Recorded verbatim-intent, because these shaped the state below and must not be re-litigated:

| # | Correction | Status |
|---|---|---|
| 1 | *"不要迎合我，要实话实说，我们是来做事情的，就要做到最好"* — a previous "8/8 all-green" report was **fake-green**; the conformance suite was not validating `scripts/` references or `related_skills` at all. | `resolved` — suite extended to 12 rules and mutation-tested |
| 2 | Suite renamed `vault-*` → `dfs-*` (Defensive Skills). | `resolved` |
| 3 | The Hermes-only `dfs-code-review` was a duplicate of `dfs-review`; merge and delete rather than ship 24+1. | `resolved` |
| 4 | `vault-*.py` scripts stay **unrenamed** (blast radius across `01-Rules/` `05-Tools/` `08-Projects/` `.claude/skills/` too large). Skills reference real script names. | `resolved` — decision recorded, do not reopen casually |
| 5 | Local tree stays as-is; **open-source development happens in this directory**. | `open` — this document starts it |

> No `WORKMEMORY/corrections.md` ledger exists in this directory, so the dfs-handoff Phase 0
> ledger write is N/A here. The table above is the ledger until one is created.

---

## 1. What exists right now (verified, not remembered)

- **24 skills** in `~/.cc-switch/skills/`, mirrored here.
- **12 shipped subset** in `D:\Obsidian\Coding\skills\` + `package\skills\` (template vendored snapshot).
- **Conformance gate**: `D:\Obsidian\Coding\scripts\tests\test_dfs_skills_conformance.py` — 14 test methods enforcing 12 rules.
- **Shipped-subset gate**: `D:\Obsidian\Coding\scripts\tests\test_shipped_skills.py` — 3 tests.
- **Vault health gate**: `D:\Obsidian\Coding\scripts\vault-healthcheck.py` — 10 checks.

Last verified run:

```
test_dfs_skills_conformance.py   Ran 14 tests   OK
test_shipped_skills.py           Ran  3 tests   OK
vault-healthcheck.py             L2 4/4, L1 34/34   ALL CRITICAL CHECKS PASSED
```

**Mutation-tested.** Every rule was verified to go RED when its defect is injected (dangling
`related_skills`, nonexistent `scripts/` path, bogus declared tool, hardcoded absolute path,
undeclared tool call, typo'd tool call). A green run only means something because of this.
Re-run the mutation harness before trusting any future green.

---

## 2. The 12 vs 24 distinction

These are **not** two versions of the same thing. Three independent axes get conflated; keep them
apart or you will make wrong decisions about what goes in the public repo.

### Axis A — Source vs snapshot (packaging)

| | Path | Role | Count |
|---|---|---|---|
| **Live truth** | `~/.cc-switch/skills/` | Author-side working copy. Edit here. | **24** |
| **Vendored subset** | `D:\Obsidian\Coding\skills\` + `package\skills\` | Read-only snapshot shipped with the Obsidian template. | **12** |
| **Adjacent (not DFS)** | `~/.cc-switch/skills/` non-`dfs-*` | Third-party skills (caveman, ponytail, ppt-master…). Never touch as part of DFS. | ~41 |

The 12 is a **subset of** the 24, chosen by Axis B. It is a distribution artifact, not a fork —
if you fix a bug in a shipped skill you must fix it in the live tree and re-copy.

### Axis B — Domain-neutral vs domain-bound (the selection rule)

This is the actual criterion. Read the allowlist in `test_shipped_skills.py`:

- **Ships (12)** — usable by a recipient who may not be writing software. They operate on the
  *knowledge-base workflow itself*: route, plan, execute, debug, distill, hand off, research.
- **Does not ship (12)** — requires the recipient to be writing code in a specific language/runtime
  stack (`dfs-tdd`, `dfs-refactor`, `dfs-perf`, `dfs-review`, `dfs-onboard`, `dfs-bootstrap`,
  `dfs-pipeline`, `dfs-migrate`, `dfs-release`, `dfs-incident`, `dfs-agent-sdk`), or serves career
  drills (`dfs-interview`).

**Honest caveat:** the line is not razor-clean. `dfs-exec` (TDD subagent dispatch) and `dfs-debug`
(root-cause with a repro harness) are programmer-flavoured yet do ship. They were kept because
their *method* (isolated context, RED-then-GREEN, repro-before-fix) transfers to any file-editing
task. If you want a defensible public story, either justify that explicitly in the README or move
them to the non-shipped side. Do not silently leave the inconsistency.

### Axis C — Coupling to *your* Vault and MCP (the one that blocks publication)

Axis B decides what ships. **Axis C decides what actually works when it ships.** This is the
real problem and the reason this staging directory exists.

Coupling audit (measured, not estimated):

| Coupling | Full 24 | Shipped 12 | Meaning for a stranger |
|---|---|---|---|
| Calls `coding-vault-search` MCP | **10** | **7** | Broken without your MCP server |
| Uses `{vault_root}` | **5** | **3** | Needs a resolvable knowledge base |
| References `99-Inbox/` | **11** | **8** | Needs your ingestion queue to exist |
| Calls vault-resident `vault-*.py` | **21 sites / 6 skills / 7 targets** | **16 sites / 3 skills / 4 targets** | **Fixed 2026-09-27** (B4): engines ship in `scripts/`, 3 private tools declared optional. The original `1 / 1` estimate was wrong; Rule 8 measured it |

**8 of the 12 shipped skills touch `99-Inbox/`, 7 require your MCP.** Out of the box, a stranger
who copies `skills/` gets a router that points at skills which then fail at their first step.
Axis B alone is not a publishable subset — Axis C has to be solved.

Per-skill detail (full 24):

| Skill | In shipped 12 | MCP tools | `{vault_root}` | `99-Inbox` | Own templates / refs / scripts |
|---|---|---|---|---|---|
| `dfs` | ✅ | — | — | yes | 0 / 2 shared contracts / 0 |
| `dfs-adr` | ✅ | — | — | yes | 1 / 0 / 0 |
| `dfs-agent-sdk` | — | search_vault | — | — | 0 / **65** / 0 |
| `dfs-bootstrap` | — | — | yes | yes | 1 / 0 / 0 |
| `dfs-debug` | ✅ | search_vault, save_inbox_draft | — | yes | 1 / 0 / 0 |
| `dfs-exec` | ✅ | — | — | — | 2 / 0 / 0 |
| `dfs-grill` | ✅ | omni_search | — | yes | 0 / 0 / 0 |
| `dfs-handoff` | ✅ | — | — | yes | 1 / 0 / 0 |
| `dfs-inbox-consolidate` | ✅ | promote_inbox_draft | yes | yes | 0 / 0 / 0 (+3 vault scripts) |
| `dfs-incident` | — | — | — | yes | 1 / 0 / 0 |
| `dfs-interview` | — | — | — | — | 0 / 0 / 0 |
| `dfs-migrate` | — | — | — | — | 1 / 0 / 1 (`ddl_lint.py`) |
| `dfs-onboard` | — | — | yes | — | 0 / 0 / 0 |
| `dfs-perf` | — | — | — | — | 1 / 0 / 1 (`benchmark_runner.py`) |
| `dfs-pipeline` | — | — | — | yes | 0 / 0 / 0 |
| `dfs-plan` | ✅ | omni_search, get_code_template | — | — | 1 / 0 / 0 |
| `dfs-refactor` | — | — | — | — | 0 / 0 / 0 |
| `dfs-release` | — | — | — | — | 2 / 0 / 1 (`changelog_gen.py`) |
| `dfs-research` | ✅ | search_vault, omni_search, get_note, get_rule_snippet, save_inbox_draft | yes | yes | 1 / 0 / 0 |
| `dfs-review` | — | get_rule_snippet, list_standards | — | — | 1 / 0 / 0 |
| `dfs-save` | ✅ | search_vault, save_inbox_draft | yes | yes | 1 / 0 / 0 |
| `dfs-spark` | ✅ | omni_search | — | — | 1 / 0 / 0 |
| `dfs-tdd` | — | get_code_template | — | — | 0 / 0 / 0 |
| `dfs-team` | ✅ | — | — | — | 1 / 0 / 0 |

Shipped (12): `dfs`, `dfs-adr`, `dfs-debug`, `dfs-exec`, `dfs-grill`, `dfs-handoff`,
`dfs-inbox-consolidate`, `dfs-plan`, `dfs-research`, `dfs-save`, `dfs-spark`, `dfs-team`.

Not shipped (12): `dfs-agent-sdk`, `dfs-bootstrap`, `dfs-incident`, `dfs-interview`,
`dfs-migrate`, `dfs-onboard`, `dfs-perf`, `dfs-pipeline`, `dfs-refactor`, `dfs-release`,
`dfs-review`, `dfs-tdd`.

---

## 3. Standalone blockers (what must change before publishing)

Ordered by how hard they are to dodge.

### B1 — The MCP server is yours and is not in this repo

The 10 MCP-dependent skills (7 of them shipped) call `coding-vault-search`, currently implemented
at `D:\Obsidian\Coding\scripts\vault_search_mcp.py` (849 lines, stdio JSON-RPC, 9 tools).
**Nothing here ships that server.** Two viable directions — decide before writing code:

- **(a) Ship a companion MCP.** Port the 9-tool server into this repo, backed by a pluggable
  "knowledge store" (a directory of markdown files). Skills stay unchanged; the server becomes the
  installable artifact. This is what "单独 skill + 配套 MCP" implies.
- **(b) Make MCP optional.** Each skill already declares `metadata.hermes.mcp_tools`. Define a
  documented fallback to plain `read_file`/`write_file` over a resolved root, so skills degrade
  when no MCP is present. Cheaper, weaker retrieval.

(a) is the stronger product; (b) is the stronger fallback. Doing both — server when present,
file-level fallback when absent — is the defensible answer, and the `mcp_tools` declaration is
already the switch to build on.

**RESOLVED 2026-09-27 — both, built.** User decision: ship the server *and* document the fallback.

- `mcp/knowledge_server.py` — ported stdio JSON-RPC server, stdlib only, 9 canonical tool names
  unchanged (Conformance Rule 9 depends on them). Backends reimplemented against a configurable
  root instead of shelling out to the author's 1108-line `search-vault.py` / 663-line
  `vault-proactive-scan.py`: copying those into a public repo would import a personal taxonomy.
  Ceilings (keyword scorer not BM25; harness-agnostic L0 rung; regex not AST debt scan) are
  marked in the module docstring.
- `mcp/README.md` — registration, root contract (no third tier: no hardcoded fallback path),
  the `knowledge.json` layout override (**this is B2's answer**), and the per-tool file-level
  fallback table (**the (b) half**).
- `tests/test_knowledge_server.py` — 15 tests driving the real server over stdio against a temp
  knowledge root, incl. traversal refusal, the A-MAC gate, and a `tools/list` == `KNOWN_MCP_TOOLS`
  drift assertion. Receipt: `Ran 15 tests ... OK`, exit 0.
- Language note for review: the ported tool descriptions are English (the private original's are
  Chinese). Nothing depends on description text — Rule 9/11 check names — so this is a
  presentation choice, not a contract change. Flip it in one pass if Chinese-first is preferred.

### B2 — `{vault_root}` means *your* Vault

Five skills resolve a root and then expect your directory layout. The resolution contract is
already written and portable (`dfs/references/vault-root-resolution.md`, three tiers:
`$WIKI_PATH`/`$OBSIDIAN_VAULT_PATH` → upward search → degrade). What is **not** portable is the
layout assumption: `01-Rules/`, `03-Languages/`, `05-Tools/`, `08-Projects/`, `09-Career/`,
`99-Inbox/`. Publish a minimal layout spec, or make the directory names configurable.

**RESOLVED 2026-09-27** — configurable, via an optional `knowledge.json` at the knowledge root
merged over documented defaults (unknown keys rejected, not ignored). See `mcp/README.md § Layout`.
The defaults still mirror this Vault's names, so nothing that already works changes.

### B3 — `99-Inbox/` is your ingestion queue

8 shipped skills read or write it. For a stranger this directory does not exist. Either the
companion MCP creates it on first use, or the skills state the one-line precondition.

### B4 — Script naming is inconsistent with the brand

Skills are `dfs-*`; the scripts they call are `vault-*.py`. **This is a known, accepted inconsistency
locally** (see correction #4). In a public repo it will be read as an oversight.

**RE-DIAGNOSED AND RESOLVED 2026-09-27.** The original entry said "the one script they call" — that
was a miscount. The ported Rule 8 gate measured **21 dangling `scripts/...` references across 6
skills, pointing at 7 scripts that exist only in the author's Vault** (shipped subset: 16 sites /
3 skills / 4 targets). Naming was never the real problem: five skills assume the author's CLI
toolchain is on disk.

Fix, per the "engines ship, private infrastructure is declared" decision:

- **Shipped** at `<repo>/scripts/`: `vault_exec_state.py` (engine of `dfs-exec` / `dfs-handoff`),
  `vault-inbox-consolidate.py` (engine of `dfs-inbox-consolidate`), `vault_transaction.py` (its
  transaction primitive). Names deliberately NOT renamed — the skill text references those paths,
  so a rename would churn skill content for no functional gain.
- **Declared optional** in `scripts/README.md` and exempted in the gate through
  `OPTIONAL_SCRIPT_POINTERS`: `vault-healthcheck.py`, `vault-inbox-triage.py`, `bootstrap.ps1`.
  Each inspects a knowledge base's own structure, so shipping it would be wrong-by-default for
  anyone else. **Declared gap: `dfs-bootstrap` Phase 3.5 needs a cross-platform port of
  `bootstrap.ps1` before that skill can ship.**
- **Text fixed** where a real in-repo equivalent exists: `dfs-agent-sdk` now points at
  `tests/test_skills_conformance.py`; `dfs-bootstrap` / `dfs-onboard` point at the `search_vault`
  MCP tool plus the `mcp/README.md` fallback table instead of the private `search-vault.py` CLI.
- Gate changes: `<repo>/scripts` added to `get_script_roots()` (matching the skills' own
  `{vault_root}/scripts/<file>` shape; the author-Vault fallback root stays dropped), and the
  exemption list **fails when it goes stale**, so it cannot rot into a blanket mute.
- Result: Rule 8 GREEN, `KNOWN_RED_BASELINE` now empty, and — since an expected-red rule proves
  nothing about the check itself — a **new mutation was added for Rule 8** (inject
  `scripts/ghost-helper.py`, deliberately outside the exemption list). 14/14 mutations caught.
- Tree divergence: exactly **3 files** differ from `~/.cc-switch/skills/` (all deliberate, all
  greppable via `DFS-PORT`); `diff -rq` over all 24 skill dirs reports no other drift.

### B5 — Frontmatter carries Hermes-specific fields

`disable-model-invocation: true` (7 skills) and `metadata.hermes.*` are Hermes conventions. For
portability, document the mapping to other harnesses (Claude Code `allowed-tools`, etc.) or move
harness-neutral metadata to the top level. `dfs-exec`/`dfs-review` already carry a
`delegate_task` (Hermes) / `invoke_subagent` (Claude Code) neutral dispatch note — extend it.

---

## 4. The MCP contract to reimplement

Source of truth: `dfs/references/mcp-contract.md`. Implementation reference (read-only, do not
copy the vault coupling): `D:\Obsidian\Coding\scripts\vault_search_mcp.py`.

Nine tools. Signatures as currently implemented:

```python
search_vault(query, tag=None, top=5, output_format="detailed")
omni_search(query, scope="ladder", top=5)
get_note(rel_path)
get_rule_snippet(rule_name, section=None)
list_standards()
get_code_template(template_name, lang=None)
save_inbox_draft(title, content, tags=None, source=None)
promote_inbox_draft(draft_filename, target_dir)
vault_proactive_scan(project_path=None, limit=15)
```

Semantics that matter for a reimplementation:

- **`omni_search(scope="ladder")`** — the escalation gateway. It is the "broad/cross-cutting"
  entry point; `search_vault` is the narrow keyword one. Skills rely on that split; keep both.
- **`get_rule_snippet`** — returns *one section* of a rules file, not the whole file. This is a
  deliberate token-economy contract; skills call it per-language during review.
- **`save_inbox_draft`** — the A-MAC admission gate into `99-Inbox/`. `dfs-save` and `dfs-debug`
  both sink through it.
- **`promote_inbox_draft`** — single-draft promotion; the batch path is the CLI script.
- **`vault_proactive_scan`** — scans a *project* for unresolved debt, not the knowledge base.

Conformance is machine-checked: Rules 9/11/12 validate that declared tools are canonical, that
usage ⊆ declaration, and that call sites are not typos of canonical names. Port the test alongside
the server or the contract silently rots.

---

## 5. The conformance gate to port

`test_dfs_skills_conformance.py` — 14 methods, 12 rules. Port this **with** the skills; without it
the suite decays into prose within weeks (this is not hypothetical — the previous 6-rule version
reported green while 71 dangling references sat in the tree).

| Rule | Assertion |
|---|---|
| 1 | Every skill dir has a non-empty `SKILL.md` |
| 2 | Frontmatter parses as YAML; `name` matches dir name; `description` non-empty |
| 3a/3b/3c | `description` ≤ 60 chars, ends with `.`, no banned marketing phrases |
| 4 | Router `dfs` has `disable-model-invocation: true` |
| 5 | `templates/…` / `references/…` pointers resolve, including qualified `dfs-<name>/references/…` |
| 6 | No `~/.claude/agents` hardcoding without a neutral fallback |
| 7 | Every `related_skills` entry names a real skill |
| 8 | Every `scripts/…` reference exists (skill dir or vault scripts root); `upstream`-marked lines exempt |
| 9 | Declared `mcp_tools` are canonical |
| 10 | No hardcoded absolute Vault path |
| 11 | MCP usage ⊆ declared `mcp_tools` |
| 12 | Vault/MCP-shaped call sites and near-miss typos are canonical |

**Rule 12's scope is deliberately narrow** — it checks the vault/MCP naming family plus
edit-distance-≤2 typos, *not* every call site, because docs legitimately discuss third-party APIs
(`prompt()`, `join()`). A generic `bogus_tool()` is **not** caught. That is an engineering
trade-off, not an oversight; do not "fix" it into a false-positive machine.

Two more suites exist alongside it: `test_shipped_skills.py` (allowlist) and
`vault-healthcheck.py` (10 checks, includes registry sync). The shipped-allowlist test is the one
to port first — it is what keeps the public subset honest.

---

## 6. Suggested next steps

1. ~~`git init` here; add `LICENSE`, `.gitignore`, and a README~~ **DONE 2026-09-27** —
   MIT (`LICENSE`, matching every other repo in `D:\Code`); `.gitignore` superset of
   `bootstrap.ps1`'s 11 required patterns (verified 0 missing) plus a port-local state block;
   `README.md` leads with the three failure modes and carries only numbers that were measured
   (24 skills / 12 rules / 38 tests / 14 mutations / two interpreters).
2. ~~Decide B1~~ **DONE 2026-09-27** — both: server in-repo + documented file-level fallback.
   `mcp/knowledge_server.py`, `mcp/README.md`, `tests/test_knowledge_server.py` (15 tests, exit 0).
3. Separate the truly domain-neutral set from `dfs-exec`/`dfs-debug` — justify or move them (Axis B caveat).
4. ~~Publish the minimal Vault layout spec (§B2)~~ **DONE 2026-09-27** — `knowledge.json` override.

Still open, in order: `LICENSE` + a README that leads with the problem; B3 (`99-Inbox/` must exist
or be created — the shipped consolidator now exits 2 with instructions rather than reporting an
empty queue); B5 (map the Hermes-specific frontmatter fields for other harnesses); the `dfs-bootstrap`
cross-platform port of `bootstrap.ps1` (the one declared gap left by B4); the shipped-subset allowlist
gate once Axis B's `dfs-exec`/`dfs-debug` decision lands; then `install.py`.
5. Port `test_dfs_skills_conformance.py` + `test_shipped_skills.py` first, then the skills.
   Gate-then-content, never content-then-gate.
6. Write a single-file, zero-dependency `install.py` that detects Claude Code / Hermes / Codex /
   Cursor skill dirs and links or copies accordingly.
7. Rename `vault-inbox-consolidate.py` inside this repo only (B4), and document the harness
   field mapping (B5).

---

## 7. Continuation prompt (copy-paste)

> Continue the Defensive Skills standalone release in `D:\Code\skill-dev`.
> Read `HANDOFF.md` first — it holds the verified state, the 12-vs-24 distinction, and five
> publication blockers. Do not re-derive them.
> Next action: Axis B — curate the public subset (justify or move `dfs-exec` / `dfs-debug`), then
> B3/B5, then `install.py`, then the FIRST COMMIT (nothing is committed yet).
> DONE: LICENSE + README + .gitignore (step 1), B1, B2, B4 — see their sections; do not re-litigate.
> Constraint: `~/.cc-switch/skills/` stays the live truth; `vault-*.py` scripts keep their names
> locally; every new claim must come with a raw command receipt, not a self-report.
> Gate has teeth only if `python tests/mutation_check.py` still exits 0 (14 mutations, empty baseline).
> Numbers in `README.md` were measured; re-measure before changing them.
