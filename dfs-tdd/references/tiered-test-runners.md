# Tiered, Change-Aware Test Runners (`references/tiered-test-runners.md`)

Load this when a test suite's wall-clock time starts pushing contributors toward `--no-verify`, or when
CI spends most of its budget re-running suites unrelated to the diff.

The reference implementation is `run_tests.py` (repo root) in the author's `mcm-2027` repo (340 lines,
stdlib only). This document records the design decisions worth copying and the traps that cost a
rewrite.

---

## 1. The three properties that make a runner worth having

| Property | Why it matters | How it is achieved |
|---|---|---|
| **Zero silent skips** | A hardcoded module list silently stops running new tests. The suite looks green and covers less each week. | Discover `tests/**/test_*.py` from disk every run. Never maintain a list. |
| **Tier split by declaration, not by directory** | Directory layout forces a choice between "all fast" and "all slow" at file creation time, which is the wrong moment. | A module is `heavy` iff it declares `TEST_TIER = "heavy"` at top level, or is registered in `data/test_tiers.json`. Everything else is `fast`. |
| **Budget as a gate, not a report** | A slow test is invisible until it is 90 s and everyone runs `--no-verify`. | `--enforce-budget` fails the run when a `fast` module exceeds `fast_budget_seconds` (default 15 s), forcing promotion to `heavy` + `WATCHED_PATHS`. |

## 2. Read markers with AST, never by importing

Importing a test module to read its `TEST_TIER` executes it — side effects, slow imports, and failures
during discovery. Parse the file and take only top-level literals:

```python
def _inspect_module_markers(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tier, watched = None, []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            try:
                val = ast.literal_eval(node.value)     # literals only; a call raises and is skipped
            except Exception:
                continue
            if name == "TEST_TIER" and isinstance(val, str):
                tier = val.strip().lower()
            elif name == "WATCHED_PATHS" and isinstance(val, (list, tuple)):
                watched = [str(x) for x in val if isinstance(x, str)]
    return tier, watched
```

`ast.literal_eval` is the guard: a module computing its tier (`TEST_TIER = "heavy" if os.getenv(...) else "fast"`)
is silently treated as `fast` rather than crashing discovery. Document that, so nobody debugs a phantom.

## 3. Change-aware selection: fast always, heavy by dependency

`--changed` runs the whole fast tier (it is cheap by construction) plus only the heavy modules whose
watched paths were touched:

```python
if any(_path_matches_prefix(p, prefix) for p in changed for prefix in shared_prefixes):
    return sorted(heavy_map)          # a shared-core edit invalidates every heavy suite
for mod, watched in sorted(heavy_map.items()):
    targets = [*watched, mod.replace(".", "/") + ".py"]
    if any(_path_matches_prefix(p, t) for p in changed for t in targets):
        selected.append(mod)
```

Two decisions worth copying:

- **`shared_core_prefixes` is an over-approximation by design.** Editing `src/config.py` or a raw-data
  directory selects *every* heavy module. Under-selecting produces a green run that proves nothing;
  over-selecting costs time. Choose the safe side.
- **Prefix matching, not glob.** `_path_matches_prefix` treats a trailing `/` as a directory prefix and
  otherwise requires exact match or `path + "/"`, so `src/config.py` does not accidentally select
  `src/config_helpers.py`.

## 4. Feed CI a matrix, do not duplicate the split

`--list-json` emits `{mode, fast, heavy, selected}` so the CI config builds its heavy matrix from the
runner's own classification. Duplicating the tier list in YAML guarantees the two drift.

```yaml
- run: python run_tests.py --tier heavy --list-json > heavy.json
- run: python run_tests.py --tier fast
# matrix strategy reads heavy.json → one job per heavy module
```

## 5. Keep intentional failures out of the success log

Negative-path tests print their expected `[FAIL]` / `[BUDGET]` lines on purpose. Piped into a green log,
those lines are indistinguishable from real failures, and the next person greps `FAIL` and panics.

Capture the step's output and replay it **only on failure**:

```python
def run_step(cmd, desc, *, capture=False):
    result = subprocess.run(cmd, cwd=ROOT, text=True, env=child_env(),
                            capture_output= capture)
    if result.returncode != 0:
        if capture:
            body = (result.stdout or "") + (result.stderr or "")
            if body.strip():
                print(body.rstrip())        # replay the real output now that it matters
        sys.exit(result.returncode)
    if capture:
        summary = next((l.strip() for l in reversed(result.stdout.splitlines())
                        if l.strip().startswith("Ran ")), "all tests passed")
        print(f"[OK] {desc} completed successfully ({summary}).")
```

The success line quotes the `Ran N tests` summary, so a captured step still proves it executed — a
silent `[OK]` with no counts is the presence-only assertion trap in another costume.

## 6. Traps that cost a rewrite

| Trap | Symptom | Guard |
|---|---|---|
| Importing modules to read markers | Discovery hangs or runs tests twice | `ast.parse` + `ast.literal_eval` |
| Budget checked after the whole run | You learn about the 90 s module after waiting 90 s | Measure per module; report `(dt)` inline every line |
| `--changed` skipping the fast tier | A fast regression ships because only heavy modules matched | Fast tier always runs in `--changed` |
| Failure log written to a fixed repo path | Diffs and `.gitignore` churn | Write to `TMPDIR`, print the absolute path |
| `SOURCE_DATE_EPOCH` set with `setdefault` mid-process | Child processes already inherited the old value | Set it at the top of the entry script, before any import that could spawn a child |
| Budget as `[WARN]` only | Nobody acts; every run warns | `--enforce-budget` makes it exit 1 |

## 7. Minimal adoption order

Do not port the whole runner at once. In order of payoff:

1. Disk discovery (kills silent skips) — small, immediate.
2. Per-module timing printed inline — makes the problem visible before it hurts.
3. `TEST_TIER` marker + `--tier fast|heavy` — the split itself.
4. `--enforce-budget` in CI only, never pre-commit — a budget failure in a commit hook teaches people to bypass hooks.
5. `--changed` + `shared_core_prefixes` — needs a few weeks of data on what is actually shared.
6. `--list-json` + CI matrix — last, and only if the heavy tier genuinely exceeds one runner's budget.
