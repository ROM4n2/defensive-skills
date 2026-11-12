# Verifying a Context Anchor (re-onboard as a verification pass)

Use when a repo already carries `.agent-context.md` / `AGENTS.md` invariants / an onboarding brief and you are re-entering it. The deliverable is a **corrected anchor + a list of the drift you found**, not a rewritten document.

## 0. Establish the baseline the anchor claims

Run the anchor's test command **verbatim** — flags are load-bearing (`GOWORK=off` keeps a worktree from resolving into the parent workspace; `-race`; `-count=1` defeats the test cache). Substitute nothing "cleaner".

```bash
git branch --show-current && git status --short   # before
<anchor's exact test command>
git branch --show-current                          # after — a sibling session's checkout -b invalidates the run
```

Record the receipt: packages green, `func Test` count, `=== RUN`/subtest count, race verdict, plus build and vet.

## 1. The four drift classes, and the probe for each

| Class | Why reading misses it | Probe |
|---|---|---|
| `file:line` hop | a moved ref still lands on plausible code (neighbouring struct, a `RunOptions` type where `Run` was meant) | grep the **symbol**, take the real line: `grep -n 'func (h \*Handler) HandleRun\|func (p \*Pool) process\|func Run('` |
| hardcoded literal → config | no line number moves; the argument's *source* changed | read the actual call site: anchor says `NewPool(3, …)`, main passes `conf.WorkerConcurrency` |
| per-package file inventory | new files are invisible until you list the directory | `search_files (target='files')` on the package, diff against the anchor's list |
| enumerated range / version | the range is a claim, not a scan | re-list and re-count: `docs/adr/0001..0018` → count the directory; config key count; prompt version |

## 2. Recompute every derived number

```bash
git ls-files '*.go' | grep -vc '_test.go'          # prod file count
git ls-files '*.go' | grep -c '_test.go'           # test file count
git ls-files '*.go' | grep -v '_test.go' | xargs wc -l | tail -1   # prod LOC
git ls-files '*.go' | grep '_test.go' | xargs wc -l | tail -1      # test LOC
grep -rn '^func Test' --include='*_test.go' . | wc -l              # func Test
```

Rewrite each entry with the fresh value and today's date. Totals can stay stable while the prod/test split drifts underneath, so recompute the split, not just the total.

## 3. Headroom report

If the repo enforces a per-file line budget, report the file nearest the ceiling in the handoff (e.g. 395/400). The next agent's one-line addition is what breaks the gate; the margin changes where they put the code.

## 4. Close out

- Patch the anchor in place (targeted edits), never regenerate it.
- Append one append-only event to the repo's shared work log naming the baseline as **re-verified** and listing the drift corrected.
- Report foreign working-tree changes as "not mine, untouched".
