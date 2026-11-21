# Dead-Gate Traps: Gates That Cannot Fire (`references/dead-gate-traps.md`)

Load this when authoring a gate that reads an artifact another tool owns — git index blobs, normalized
files, formatted output, or anything a formatter/serializer has already rewritten. These gates pass
review, pass their own smoke test, and can never fail on the defect they name.

---

## 1. The Normalization Trap (MUST)

**A gate must read the representation in which the defect can still exist.**

Git is the canonical case. With `*.sh text eol=lf` in `.gitattributes`, `git add` normalizes CRLF to LF
**in the index blob**. A pre-commit gate that runs `git show :$path | grep -c $'\r'` is therefore dead:
the bytes it inspects are already clean, and the CRLF it was written to catch lives only in the working
tree.

Measured on this host (`core.autocrlf=true`):

| Representation | Bytes |
|---|---|
| working tree, after an editor wrote CRLF | `b'#!/usr/bin/env bash\r\necho hi\r\n'` |
| index blob, `git show :file` after `git add` | `b'#!/usr/bin/env bash\necho hi\n'` |
| index blob after `git add -f` (force) | `b'#!/usr/bin/env bash\necho hi\n'` (still normalized, only a warning) |

So the gate reports `0` forever. Worse, it is *plausible*: the check reads a real blob, has a real
regex, and fails on nothing because nothing reaches it.

### The two checks that CAN fire

Replace the dead check with the invariants that survive normalization:

1. **Gate the declaration, not the derived bytes.** Assert the pin itself is present — the loss of
   `.githooks/** text eol=lf` from `.gitattributes` is the actual precondition for the failure
   (`cannot spawn .githooks/pre-commit` after the next checkout). This is checkable and it can be lost.
2. **Gate the narrow case where worktree bytes are load-bearing.** Only the files whose *execution*
   depends on their bytes — `.githooks/*` — need a working-tree CRLF scan, because bash refuses a
   CRLF script regardless of what git stores.

```python
# CORRECT: the declaration is the invariant
REQUIRED_GITATTRIBUTES_PINS = (".githooks/** text eol=lf", "WORKMEMORY/** text eol=lf")

def check_gitattributes_pins(root):
    lines = {l.strip() for l in (root / ".gitattributes").read_text(encoding="utf-8").splitlines()}
    return [f"[EOL_PIN] .gitattributes is missing pin: {p}" for p in REQUIRED_GITATTRIBUTES_PINS if p not in lines]
```

```bash
# CORRECT: scan the worktree, and only where it changes whether the file can run
case "$path" in
    .githooks/*)
        [ "$(tr -cd '\r' < "$path" | wc -c)" -gt 0 ] && printf 'EOL\t%s\tCRLF，bash 无法执行\n' "$path"
        ;;
esac
```

### Generalization

Before writing a gate on any derived representation, ask: **"what pipeline stage produced these bytes,
and does it already erase the defect?"** Common instances:

| Gate intent | Representation a naive gate reads | Why it is dead | Read instead |
|---|---|---|---|
| CRLF in `eol=lf` files | index blob | `git add` normalized it | the pin declaration + worktree for executable files |
| Trailing whitespace | pre-commit `git show` after an editor hook | the formatter already stripped it | the formatter's config, or the worktree before formatting |
| Missing newline at EOF | serialized JSON | the serializer appended it | the source template |
| Duplicate keys in YAML | parsed dict | the parser already collapsed them | the raw text, before parsing |

---

## 2. The Unreachable-Wiring Trap (MUST)

**Testing a gate function directly proves the function works, not that anything calls it.**

A gate wired into a hook is two artifacts: the gate module, and the call site. Tests that invoke
`check_x.py`（示例门禁脚本） directly leave the call site uncovered — the wiring can be deleted while every
test stays green.

This is not hypothetical: in a 31-test suite, 12 tests exercised the hygiene gate directly and **zero**
went through the hook. A mutation that replaced the hook's invocation with `if false; then` left the
whole suite green. Only a mutation-testing pass found it.

**Rule**: for every gate, ship one test that triggers the defect through the *outermost* entry point a
user actually hits (the hook, the CI target, the CLI default) and asserts the gate's own output tag:

```python
def test_hook_invokes_the_hygiene_gate(self):
    """End-to-end: the gate must be reached *through the hook*, not only when invoked directly."""
    stage("src/demo.py", b'p = "D:/Code/other-repo/file.py"\n')
    proc = run_hook()                       # bash .githooks/pre-commit
    self.assertEqual(proc.returncode, 1)
    self.assertIn("[ABS_PATH]", proc.stderr)   # the gate's tag, not a generic failure
```

Assert the **tag**, not merely a non-zero exit: a non-zero exit can come from an unrelated early
failure (a CRLF hook, a missing interpreter) and would report the gate as wired when it is not.

---

## 3. Self-Rejection Trap (MUST)

**A gate must pass on the artifacts its own installer produces.**

A repository-hygiene gate that forbids hardcoded host paths will reject a bootstrap-generated
`AGENTS.md` that embeds `{vault_root}/AGENTS.md` — the scaffold fails its own gate on the first
commit. This class is invisible to gate unit tests (they feed hand-written fixtures) and appears only
when the two features meet.

Guard: one test that runs the installer, then runs the gate over the installed tree, and requires exit 0.

```python
def test_scaffolded_repo_passes_its_own_hygiene_gate(self):
    self.assertEqual(bootstrap().returncode, 0)
    git(["add", "-A"])
    proc = run_gate("--staged")
    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
```

The fix is usually not to weaken the gate but to remove the machine-local value from the generated
file: write the portable token (`$WIKI_PATH/AGENTS.md`) and validate the environment variable at
install time instead of baking the resolved path into a committed artifact.

---

## 4. Exit-Code Collapse Trap (MUST)

`2` (gate could not run) MUST NOT be reported as `0` (pass) or `1` (violation). A config loader that
falls back to defaults on a malformed config turns "my gate is misconfigured" into "the repo is clean".

```python
try:
    loaded = json.loads(path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    print(f"[FAIL] {path} is not valid JSON: {exc}", file=sys.stderr)
    raise SystemExit(2)          # NOT: return {}
```

Test it explicitly: stage a malformed config and assert `returncode == 2`, never `0`.

### 4.1 The wrapper-exit trap (a gate's own proof can be forged)

The same collapse happens one level up, in whatever **launches** the gate. A wrapper that ends with
`echo "done"` exits `0` regardless of what the gate returned:

```bash
python -m unittest tests/  ; echo "EXIT=$?"    # WRONG: prints the exit of `echo`
python -m unittest tests/  ; rc=$?; echo "EXIT=$rc"; exit $rc   # RIGHT
```

Measured: a mutation-testing run failed with `PYEXIT=1` in its log while the launching process reported
`exit code 0`. Four successive runs of the same script were reported as four successes; only the log
body revealed three failures. **A background-process notification's exit code is the wrapper's, not the
subject's.**

Two consequences:

- When a CI step, a background job, or a shell one-liner wraps a gate, the wrapper MUST capture `$?`
  into a variable and `exit` it. `echo`/`printf`/`cat` after the gate silently rebase the status.
- When reading a result, trust the **log body** (`PYEXIT=`, `exit=`, `Ran N tests`) over the process
  exit code. A green process carrying a red log is the common shape of this bug.

Test it: make the gate exit 1, run the wrapper, assert the wrapper's status is also 1.

---

## 5. Checklist before claiming a gate works

- [ ] Mutation proof: one injected defect produces `exit 1` naming `file:line`; revert produces `exit 0`.
- [ ] **The mutation was applied exactly once** (`assert raw.count(old) == 1`) — a drifted anchor that
      replaces zero times reports a false green.
- [ ] **Wiring proof**: the defect is caught through the outermost entry point, asserting the gate's tag.
- [ ] **Self-acceptance proof**: the installer's own output passes the gate.
- [ ] **Normalization review**: name the pipeline stage that produced the bytes the gate reads, and
      state why the defect can still exist there.
- [ ] **Exit-code proof**: `2` is distinct from `0` and `1`, with a test for the un-runnable case.
- [ ] **Wrapper proof**: whatever launches the gate (CI step, background job, shell one-liner) captures
      `$?` and exits it — an `echo` after the gate silently reports success (§4.1).
