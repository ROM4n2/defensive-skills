# Gate Reference: Thresholds, Pragmas, Opt-Ins (`references/gate-reference.md`)

The single place that defines what the two gates check. `SKILL.md` names the classes; this file owns
the numbers, the escape hatches, and the measured behaviour.

---

## 1. `check_repo_hygiene.py` — per-file, reads the git index

Runs on every commit. `--staged` reads the index in **one** `git cat-file --batch` process; `--all`
reads the worktree (CI mode).

| Class | Default | Escape hatch | Source of the number |
|---|---|---|---|
| `[LARGE]` blob | 500 KB | `git:allow-large-file` | `pre-commit-hooks` `check-added-large-files` |
| `[BLOAT]` source module | 1000 lines | `git:allow-bloat` | `pylint` C0302 `max-module-lines` |
| `[BUDGET]` context file | `AGENTS.md` 80 lines / 8 KB; `work.log` 150 lines / 24 KB | — (rotate instead) | measured cost of the two files every session reads |
| `[ABS_PATH]` host path | `C:/…`, `D:/…`, `/home/…`, `file:///C:/…` | `git:allow-abs-path` | portability |
| `[CONFLICT]` marker | `<<<<<<<` / `=======` / `>>>>>>>` | `git:allow-conflict-marker` | — |
| `[EOL_PIN]` missing pin | pins absent from **both** `.gitattributes` and `.git/info/attributes` | — | hook executability |
| `[SYMLINK]` / `[SYNTAX]` | broken symlink; unparseable Python | — | — |

The context budgets are not industry standards — they are the measured price of the two files **every**
new session reads. They grow one reasonable-looking line at a time, and the cost is paid forever.

**`[EOL_PIN]` accepts two sources.** `.gitattributes` (owner mode) or `.git/info/attributes` (overlay
mode). Accepting only the tracked file made overlay mode fail its own gate on every commit.

---

## 2. `check_repo_structure.py` — whole-graph, AST-based

Runs only when the commit touches Python. Always analyses the **whole** import graph: a cycle spans
modules that may not be staged, so a partial graph would silently report "no cycles".

| Class | Default | Why |
|---|---|---|
| `[CYCLE]` | any SCC > 1 module | Tarjan SCC; a cycle is never acceptable |
| `[FANOUT]` | > 12 internal imports | hub module — split it or add a seam |
| `[FUNC_LEN]` | > 60 lines | stops fitting on one screen with its docstring |
| `[NEST]` | > 4 levels | guard-clause discipline (`dfs-refactor`) |
| `[CLASS]` | > 20 methods | god object |
| `[STUB]` | any | placeholder body |

### 2.1 What `[STUB]` catches

| Signature | Example |
|---|---|
| `pass`-only body | `def f(): pass` |
| `...`-only body | `def f(): ...` |
| docstring-only body | `def f(): """Does it."""` |
| bare `NotImplementedError` | unless `@abstractmethod` |
| elision comment | `# ... rest of implementation unchanged` |
| placeholder marker | `# TODO`, `# FIXME`, `# XXX`, `# HACK` |

**Elision markers must be phrases, not bare words.** An earlier regex matched the single word
`unchanged` and flagged a normal English sentence in a real repo ("three masked columns is unchanged,
and a −1e6 padding logit cannot leak"). Every alternative now requires the elision sense:
`rest of the body omitted`, `remaining methods unchanged`, `same as above`, `implementation here`.

---

## 3. Opt-in checks (off by default)

Enable per repo in `data/repo_structure.json`. **Never land a gate red on day one** — a gate installed
into an existing repo that immediately reports 400 violations gets deleted, and the whole gate file
goes with it.

| Key | Enables | `-1` / `0` |
|---|---|---|
| `max_dead_exports` | `[DEAD]` unreferenced public symbols | `-1` off, `0` zero tolerance |
| `require_test_for_src` | `[TEST_GAP]` `src/` module with no test file | `0` off, `1` on |
| `max_dup_lines` | `[DUP]` identical function bodies | `0` off, `>0` minimum block size |

### 3.1 Measured hit counts (two real repos)

`mcm-2027` — 65 modules, ~15k lines. `DeLector` — 300+ modules including a mirrored Android copy.

| Check | mcm-2027 | DeLector |
|---|---|---|
| `[DEAD]` | 29 | 2 |
| `[TEST_GAP]` | 3 | 0 |
| `[DUP]` | 1 | 92 |
| baseline (default checks only) | `FUNC_LEN` 15 · `NEST` 14 | `CYCLE` 2 · `FANOUT` 4 · `FUNC_LEN` 194 · `NEST` 94 · `STUB` 39 |

`[FUNC_LEN]` and `[NEST]` dominate a red baseline. If a repo is red, fix those first — cheapest and
most reliable signal.

### 3.1.1 Default-class ratchet — land green on a repo with debt

The opt-in tolerance above only covers `[DEAD]`. For the **default** classes, set `allowed_*` counts
in `data/repo_structure.json`:

```json
{ "allowed_cycle": 2, "allowed_fanout": 4, "allowed_func_len": 194,
  "allowed_nest": 94, "allowed_class": 0, "allowed_stub": 37 }
```

| Key | Class absorbed |
| --- | --- |
| `allowed_cycle` | `[CYCLE]` |
| `allowed_fanout` | `[FANOUT]` |
| `allowed_func_len` | `[FUNC_LEN]` |
| `allowed_nest` | `[NEST]` |
| `allowed_class` | `[CLASS]` |
| `allowed_stub` | `[STUB]` |

Semantics (all four are load-bearing — each has a test):

- **Default `0` = enforce everything.** A fresh bootstrap behaves exactly as before ratchet existed.
- **A count, not an allow-list.** Fixing one old finding and adding a new one stays green; the number
  is the contract. Lower it as debt is paid — a ratchet that only ever goes up is not a ratchet.
- **Per class.** Tolerating `[STUB]` must never absorb a `[FUNC_LEN]` finding.
- **Never silent.** The verdict line names every absorbed class with `n/total` (e.g.
  `(baseline tolerated: [FUNC_LEN] 194/194, [NEST] 94/94)`), including on FAIL. Suppression that
  cannot be seen is indistinguishable from a deleted gate.
- **Beyond the count, only the excess findings are reported** — the first `allowed_*` findings are
  absorbed and anything past them surfaces. A new violation therefore appears on its own instead of
  being buried in the tolerated baseline, and the `n/total` ratio in the verdict keeps the absorbed
  share auditable. This differs from `max_dead_exports`, which reports the full set once its limit is
  breached.

Unlike the opt-in checks, `allowed_*` never disables a check — the analysis still runs over every
module; only the verdict is filtered. Capture the counts from a real run of
`python -B check_repo_structure.py --all`（落盘位置：目标仓库 `scripts/`） rather than copying them from this doc (numbers
drift as the repo changes).

### 3.2 `[DEAD]` — what counts as a reference

Counts textual occurrences across all **non-test** modules; one occurrence is the definition, so
`count > 1` means referenced. Exemptions: leading-underscore names, `main`, `setup`, `teardown_*`, and
the `pytest_` / `test_` / `visit_` prefixes (pytest calls those by name, never by import).

Deliberate limitation: a symbol reached only through `getattr(obj, "name")` is reported. That is the
case worth a human look.

### 3.3 `[TEST_GAP]` — file-level, not coverage

A percentage tool tells you 71% of lines are covered; it does not tell you `src/billing.py` has **zero**
tests. Both naming conventions count: `tests/test_widget.py` or `tests/widget_test.py`. `__init__.py`
is exempt. Roots configurable via `SOURCE_ROOTS` / `TEST_ROOTS`.

### 3.4 `[DUP]` — three design failures found by measurement

**Node-type sequences are far too coarse.** Keying on the sequence of AST node type names gave **580
hits** on DeLector, essentially all false: every function with an `if` inside a `for` produces the same
sequence. The working key is a full `ast.dump` of the function with identifiers and literals erased.

**Dump the body, not the `FunctionDef`.** Dumping the whole node keeps `name='handler_one'` in the key,
so two identical bodies with different names never match — the exact duplicate the check exists to find.
The name is normalised in two places (the wrapper and `Erase.visit_FunctionDef`); removing only one is a
no-op, which is why the mutation test asserts the pair.

**Keep the signature in the key.** Comparing bodies only reported `def a(x)` and `def b(x, y)` as clones
— different interfaces, not copy-paste. Arity and annotations participate; parameter *names* do not.

**Mirrored build trees are not clones.** DeLector keeps `delector/` and a copy under
`android/app/src/main/python/delector/`; **421 of 421** remaining hits were this pattern. Skip a pair
when one path is a suffix of the other.

### 3.5 Enabling them — the tolerance is a ratchet

```json
// data/repo_structure.json
{ "max_dead_exports": 29, "require_test_for_src": 1, "max_dup_lines": 8 }
```

Set `max_dead_exports` to the repo's **current** count first, then lower it as symbols are removed.
Verify the ratchet actually moves: with the tolerance set the gate exits 0; delete one dead export and
lower the tolerance by one — still 0; set it to `0` — exit 1 naming the remainder.

---

## 4. Cost

| Repo | default checks | +`[DEAD]` | +`[TEST_GAP]` | +`[DUP]` |
|---|---|---|---|---|
| mcm-2027 (65 modules) | 1.19 s | 2.01 s | 1.94 s | 1.36 s |
| DeLector (490 modules) | 7.96 s | 18.00 s | 12.66 s | 10.74 s |

`[DEAD]` roughly doubles the runtime because it concatenates every module's text. On a repo that size,
run the structure gate in CI rather than pre-commit — the hook already limits it to commits touching
Python, but a 19 s pre-commit gets bypassed with `--no-verify`.

---

## 5. Exit contract

`0` clean · `1` violation · `2` the gate could not run (malformed config, not a git repository).
Never collapse `1` and `2`: a config that silently falls back to defaults turns "misconfigured" into
"clean". Design rationale: `dfs-gate/references/dead-gate-traps.md`.

## 6. CLI surface — ratchet, adapters, doctor

Both gates run from the target repo's `scripts/`; the shipped copies are `templates/repo/check_repo_hygiene.py`
and `templates/repo/check_repo_structure.py`.

- `check_repo_structure.py --emit-baseline` self-measures per-class counts into `data/repo_structure.json`
  with commit provenance. `allowed_*` may only decrease — enforce in CI with `--ratchet-guard` (fails if
  any tolerance rose vs HEAD). Never hand-copy numbers from docs.
- `check_repo_hygiene.py --no-git --all` audits a **non-git tree** (a skill's own source, an unpacked
  archive) by walking the filesystem — same findings as `git ls-files`, no temp repo needed. EOL_PIN (a
  git-checkout invariant) is skipped in this mode; hook templates are checked by the LF/no-BOM portability
  test instead. `--staged` / `--ratchet-guard` require git and are rejected with `--no-git` rather than
  silently ignored.
- `check_repo_hygiene.py --emit-baseline` self-measures **scope-granular** buckets into
  `data/repo_hygiene.json`'s `ratchet` map, keyed `"CATEGORY|scope"` (`scope` = first path segment or
  `<root>`). Only the four debt classes (`ABS_PATH`/`BLOAT`/`LARGE`/`BUDGET`) are ratchetable; correctness
  classes stay fatal. An **unlisted bucket allows zero** — so a new host path in production code is caught
  even while `docs/` carries a large legacy baseline. `--ratchet-guard` forbids raising any bucket
  (including newly added ones); both gates carry the same four flags.
- `--json` emits machine-readable findings (total / tolerated / reported / by-class / by-bucket) for trend
  data; `--explain` prints effective config, source path and provenance.
- `--emit-ci github` prints (read-only) two CI steps and a guard-test template — wiring that a test asserts
  exists, so "gate deleted but tests green" cannot happen.
- `bootstrap.py --doctor [--target T] [--doctor-mode auto|owner|overlay] [--verify]` reports which
  capabilities an existing hook has/lacks **read-only**. It looks where the hook actually is (overlay
  installs into `.git/dfs-hooks/`), and its exit code means something: `0` clean, `1` gaps (including a
  stale gate or an unset `core.hooksPath`), `2` cannot run. Capability detection is textual and says so;
  `--verify` executes the installed hook against a synthetic secret in a scratch repo to prove the scan
  blocks. `--emit-checks` prints a sourceable `dfs-checks.sh` so a project-owned hook can gain the gates
  without being overwritten or losing its custom scans.
- A project's `core.hooksPath` is **never repointed** away from a directory its hook chain does not cover —
  local chains (e.g. a pre-push fingerprint gate) stay intact unless `--take-hooks-path` is given.
- A **0-byte** gate is treated as an interrupted upgrade and repaired, not as someone's own copy; gate
  version markers are read from the whole file, and a *newer* gate is left alone rather than downgraded.

## 7. Local-only gate install (bootstrap, private `.git/` state)

`install_local_gate(target, dry_run)` runs as part of bootstrap initialization (skipped by
`--no-gates`, honors `--dry-run`). It copies `templates/local-gates/fingerprint-gate.sh` into
`<target>/.git/local-gates/fingerprint-gate.sh` — **private `.git/` state only, never a tracked repo
path**. A tracked copy would carry the very identifiers the gate exists to hide and would change
behaviour for every clone, so `git ls-files` must never contain it.

- **Version marker**: `LOCAL_GATE_VERSION` / marker line in `constants.py`; an installed older version
  is upgraded with a backup; a newer/foreign copy is left alone (never downgraded) — same范式 as repo gates.
- **Idempotent & non-destructive**: running bootstrap twice leaves the gate hash unchanged. The
  machine-private `fingerprints.txt` and `fingerprint-allow.txt` are user-owned and NEVER overwritten
  by reinstall/upgrade — only the gate script itself is managed by bootstrap.
- **Trigger point**: project initialization (bootstrap). Not AGENTS.md (read every session = noise),
  not `--doctor` (manual, no fixed trigger), not CI (cloud runners cannot see a local `.git/`).
- **Patterns**: see SKILL.md Local-only gates section — identity-bearing absolute paths only; generic
  tool dir names are not fingerprints (2026-11-21 false positive).
