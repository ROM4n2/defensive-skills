# Bootstrap Anti-Patterns (`references/anti-patterns.md`)

Load this when reviewing a bootstrapped repository, auditing an agent's bootstrap claim, or when
someone proposes skipping a phase "just this once".

---

## 1. The Rationalization Table

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I'll skip pre-commit secret hooks during initial scaffolding to move faster."* | **Credential Leakage**: unprotected commits leak API keys or local configs permanently into git history. | Install and activate the hook before the first commit in any repository. |
| *"I'll configure git hooks without normalizing line endings."* | **CRLF Shebang Failure**: Windows CRLF breaks bash execution (`cannot spawn .githooks/pre-commit`). | Force LF on the hook **and** pin it in `.gitattributes`; the hook rejects CRLF under `.githooks/`. |
| *"Testing with a live secret literal verifies the hook works."* | **Secret Scanner Invalidation**: committing a real token trips remote scanners and revokes credentials. | Use runtime-concatenated synthetic probes (`'sk-' + '0'*32`) that exercise the regex without tripping scanners. |
| *"Write the full rules into AGENTS.md, CLAUDE.md, .agent-rules.md and .cursorrules so every runtime sees them."* | **Rule Duplication Drift**: every rule edit must land in N files; they diverge, and runtimes reading several inject the same text multiple times per session. | `AGENTS.md` is the single truth; other files are pointers or absent. Generate aliases only under `--legacy-aliases`. |
| *"Point the anchor at the knowledge base (`$WIKI_PATH/AGENTS.md`) so the agent can find the rules."* | **Inert Pointer**: no harness expands a shell variable inside markdown and no code reads that line, so the rules are never actually reached — the agent reaches them through the MCP tool, which resolves the root itself. A literal host path is worse: wrong on every other machine and it trips the repo's own `[ABS_PATH]` rule. | Name the tool and the skill, not an external path: an MCP tool call is resolvable, a path under an unexpanded variable is decoration. Validate the env var at bootstrap time and **fail closed** when it has no `AGENTS.md`. |
| *"An existing hook means the repo is already protected — leave it alone."* | **Stale Gate**: a hook from an older version silently lacks the EOL/hygiene gates forever. | Version-marker the hook; upgrade on mismatch with a `.dfsbak` backup, and preserve hooks carrying no marker (project-owned). |
| *"The gates lint the repo, so the shipped gate scripts must be clean."* | **Shoe-maker's Children**: the two gate TEMPLATES carried Ruff I001/B009/PLW1510 from day one; every bootstrapped repo went CI-red while the skill's own tests were green — and `install_gates` never overwrote a copy, so the fix could not propagate. | `tests/test_template_quality.py` lints every shipped Python template (stdlib import-order check always, real Ruff when available); gate templates carry `# dfs-bootstrap-gate-version:` and marked copies auto-upgrade with `.dfsbak`. |
| *"Baseline the hygiene gate with one global count so CI goes green."* | **Debt-Camouflaged Leak**: 292 historical `docs/` host paths make a global `allowed_abs_path=292` green; a new machine path leaked into production `delector/` is indistinguishable and ships. A single number cannot separate legacy debt from a fresh defect. | Ratchet by `(category, first-path-scope)` bucket; **unlisted bucket = zero tolerance**, correctness classes (`CONFLICT`/`SYMLINK`/`SYNTAX`/`EOL_PIN`) never ratchetable; `--emit-baseline` self-measures so numbers are never hand-copied. |
| *"Bootstrap the fork normally — I'll just remember not to commit AGENTS.md."* | **Fork Pollution**: every review opens with a page of private files the maintainer must reject; one `git add -A` makes it permanent history. | Use `--mode overlay`: exclusions in `.git/info/exclude`, pins in `.git/info/attributes`, hook inside `.git`. Measured clean `git status` / `diff` / `add -A`. |
| *"The code compiles and the file is under 1000 lines, so the structure is fine."* | **Silent Bloat**: stub bodies, elision comments, and import cycles pass a size check and a syntax check; they are the actual leading indicator of a rewrite. | Ship `check_repo_structure.py` with the hygiene gate; it rejects `[CYCLE]` / `[FANOUT]` / `[STUB]` / `[NEST]` / `[FUNC_LEN]` / `[CLASS]`. |
| *"Overlay mode means I can write AGENTS.md freely — it's excluded."* | **Upstream Pollution**: on a fork, `AGENTS.md` is already **tracked**; appending to it shows as `M AGENTS.md` and lands in the next PR. `.git/info/exclude` does not hide tracked files. | Overlay checks `git ls-files --error-unmatch` first; a tracked rules file is never written and the private layer goes to `AGENTS.dfs.md`. |
| *"Setting `core.hooksPath` to my hook directory installs my gate."* | **Disabled Upstream Gates**: it *replaces* the repository's hook — `make test`, lint, license checks stop running, and commits keep succeeding so nobody notices. | The installed hook chains to `.githooks/pre-commit` (or `.git/hooks/pre-commit`) first and exits 1 on its failure. `DFS_UPSTREAM_HOOKS` overrides the search. |

---

## 2. Why Each Guard Is Mechanical

A guard that depends on the reviewer's attention fails on the first busy week. Each row maps to
something a script can check:

1. **Credential leakage** → the hook exists and rejects a synthetic probe (Phase 4, probe 2).
2. **CRLF** → the `.gitattributes` pin is present, and a CRLF file under `.githooks/` is rejected.
3. **Live secret probe** → the probe file's content is assembled at runtime; the source contains no
   literal that could itself be scanned as a finding.
4. **Rule duplication** → `CLAUDE.md` byte-equals the 2-line pointer; no alias files are generated.
5. **Inert anchor** → the anchor names at least one MCP tool token and contains no host path (neither the expanded root nor an unexpanded `$WIKI_PATH/...` form).
6. **Stale gate** → the installed hook carries `# dfs-bootstrap-hook-version: N` and `N` matches.
7. **Fork pollution** → `git status --porcelain` / `diff` / `diff --cached` are empty after overlay.
8. **Silent bloat** → `check_repo_structure.py` exits 0 on the repo.

---

## 3. Bootstrap-Specific Traps That Are Not Rationalizations

| Trap | Signature | Guard |
|---|---|---|
| **Self-rejection** | The scaffold's own output fails the gate the scaffold installed (e.g. an absolute anchor vs `[ABS_PATH]`). | One test that runs bootstrap, then runs the gate over the result, expecting exit 0. |
| **Unreachable wiring** | Gate unit tests pass; the hook never calls the gate. | One test that triggers the defect *through the hook* and asserts the gate's tag. |
| **Idempotency drift** | A second run rewrites a file or rescaffolds `WORKMEMORY/`, destroying real history. | Byte-compare the tree across two runs; assert `work.log` content survives. |
| **Silent template skip** | A missing template is a warning, so the scaffold "succeeds" having written nothing. | A missing template is `exit 2`, never a warning. |
| **Exit-code collapse** | A malformed config falls back to defaults and reports clean. | `exit 2` for "gate could not run", with a test for it. |

Full mechanism for the first two: `dfs-gate/references/dead-gate-traps.md` §2 and §3.
