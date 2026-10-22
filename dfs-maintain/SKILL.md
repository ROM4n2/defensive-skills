---
name: dfs-maintain
description: Maintain repo hygiene, prune worktrees, and sync context. Use when a repo has stale worktrees, drifted context files, or needs a scheduled hygiene pass.
license: MIT
metadata:
  version: 0.1.0
  platforms: linux, macos, windows
  hermes:
    tags: [maintenance, git-worktree, ci-cd, hygiene, context-sync]
    related_skills: [dfs-pipeline, dfs-bootstrap, dfs-orchestrate, dfs-handoff, dfs-gate]
---
# DFS-MAINTAIN: Hygiene, Pruning & Context Sync

Standard operating procedure for periodic repository maintenance, subagent worktree cleanup, CI/CD pipeline stabilization, and machine context synchronization.

## When to Use
- When asked to perform routine or periodic codebase maintenance (`常规维护`, `清理仓库`).
- When CI/CD runs repeatedly fail due to pipeline coupling, 404 external links, or runner blocks.
- When cleaning up accumulated `.worktrees/` and subagent branches after multi-agent workflows.
- **Before dispatching two or more workstreams in parallel against the same repository** — the file-occupancy partition is planned here (see the Concurrent Workstream File-Occupancy Partitioning Rule in Step 3), because measuring it before dispatch is what prevents same-file collisions and merge-time surprises.
- When automated candidate PRs or abandoned branches stall scheduled discovery pipelines.
- When synchronizing `.agent-context.md` or repository baselines after a large milestone.

---

## The 5-Step Maintenance Protocol

### Step 1: CI/CD Pipeline Health Audit
Audit recent automated pipeline runs before touching files:
```bash
gh run list --limit 10
gh run view <run-id> --log-failed
```
- **Windows CI Inspection Without `jq` Rule**: On Windows/MSYS environments, `jq` is frequently missing from PATH (exit 127 `command not found`). When querying multi-job pipeline details via `gh run view <id> --json jobs`, avoid piping to `jq`; parse the JSON output using standard-library Python (`python3 -c "import subprocess, json; data=json.loads(subprocess.check_output(['gh', 'run', 'view', '<id>', '--json', 'jobs'])); ..."`).
- **CI Polling Transient Transport Fault Tolerance Rule**: When polling remote pipeline or PR status via `gh run view <id>` or `gh pr view <pr> --json statusCheckRollup`, transient network drops (such as `failed to get run: Get "...": EOF` or TLS handshake resets) occur intermittently on cloud endpoints. Never treat a transient transport EOF as a pipeline failure or abort the monitoring loop; back off for 15~30s and retry the query.
- **Step Separation Rule**: Never combine local validation (`lint`, `typecheck`, `test`) and external network probing into a single multiline script step in CI. Separate them into distinct steps so failures instantly identify whether the root cause is local code drift or remote server downtime.
- **External Dependency Decoupling**: Remote network probes (e.g. link checks, third-party API availability) in production deployment workflows must fail soft (`continue-on-error: true`). Never let third-party downtime block static deployments.

### Step 2: PR & Remote Branch Backlog Drainage
Drain automated candidate PRs and abandoned feature branches that accumulate and stall scheduled pipelines:
```bash
gh pr list
# Close stale PR and prune remote branch atomically
gh pr close <pr-number> --delete-branch --comment "Closing stale candidate PR during routine maintenance"
git fetch --prune origin
```
- **Checkable Completion Criterion**: `gh pr list` contains zero abandoned/stale automated drafts; `git ls-remote --heads origin` shows no orphaned feature branches.

### Step 3: Worktree Pruning & Unmerged Artifact Salvage (MUST)
Subagents running in isolated git worktrees (`.worktrees/subagent-*`) often leave accumulated directories and unmerged branches.

- **Concurrent Workstream File-Occupancy Partitioning Rule (do this BEFORE dispatch)**: independence of *intent* is not independence of *files*. Two logically unrelated workstreams routinely both need the same shared module — a giant test file, a monolith's probe suite, a shared conftest — and two worktrees editing one file produce an unmergeable branch no matter how clean each side is on its own. Before dispatching parallel workstreams, measure each one's file spread (per candidate file: `grep -rc '<token>' <dir>/ | sort -t: -k2 -rn`, plus the workstream's own declared test list) and assign **exclusive ownership per FILE**, never per task name. Then publish an explicit own/forbidden file table in every plan and in every handoff, because the subagents cannot see each other and will happily walk into each other's files. When two workstreams genuinely need one file, **serialize** them — the second dispatches only after the first is merged and its commits are present in the tree — rather than letting both edit it.
- **Partition, do not just plan to resolve**: a partition decided at merge time is not a partition. The measurement is cheap (a few greps) and the cost of skipping it is a rebase-and-re-review cycle on work that was already signed off.

```bash
# 1. MUST check for unmerged work BEFORE deleting any branch
git branch --no-merged master

# 2. Inspect and cherry-pick deliverables if found
git log master..<unmerged-branch> --stat
git cherry-pick <commit-hash>

# 3. Batch unregister all subagent worktrees via git authoritative table, then prune metadata
git worktree list | grep '/.worktrees/' | awk '{print $1}' | while read -r wt; do
  [ -n "$wt" ] && git worktree remove --force "$wt" 2>/dev/null || true
done
git worktree prune -v

# 4. Delete verified merged subagent branches (or force delete transient subagent branches)
for b in $(git branch --list 'hermes-subagent/*' | tr -d ' *+'); do
  git branch -D "$b" 2>/dev/null || true
done

# 5. Remove leftover untracked worktree CHILD directories. Keep the .worktrees/ root when the
#    repo convention uses it as the parallel-isolation dir (gitignored, recreated in one mkdir);
#    nuke the root only when it is pure debris.
rm -rf .worktrees/<stale-child> 2>/dev/null || true
```
- **Unmerged Salvage Rule**: Always run `git branch --no-merged master` before pruning branches. Subagents frequently commit valuable reports (audits, benchmarks, architectural findings) on their branches that were not included in the feature PR; force-deleting with `git branch -D` permanently destroys them.
- **Uncommitted Child Worktree Changes Trap**: Subagents often leave deliverables as uncommitted working tree modifications inside `.worktrees/subagent-*`. Neither parent `git status` nor `git branch --no-merged` reveals them. Always inspect `git -C <worktree> status --short` before pruning; commit inside the child worktree (`git -C <worktree> add -A && git -C <worktree> commit -m "..."`) before merging into the integration branch.
- **Worktree Unlink Before Branch Delete Rule**: `git branch -d` or `-D` fails with `cannot delete branch ... used by worktree` if the branch is still checked out in an active worktree. Always run `git worktree remove --force <worktree-path>` and `git worktree prune -v` before deleting branches.
- **Leaf-First Pruning Rule**: Remove nested child worktrees before parent worktree directories. Removing a parent while children exist triggers `Filename too long` or `fatal: not a working tree` on Windows. **The nesting is usually unintentional**: dispatching two children in parallel creates the second worktree *inside* the first (`.worktrees/A/.worktrees/B`) because the session cwd drifts between dispatches. Run `git worktree list` immediately after any multi-child dispatch, and never remove the outer worktree while a nested child is still running — `remove --force` takes the live child's files with it.
- **Concurrent Child Test Contention Rule**: parallel subagent test runs share the same data dir, db and caches, so a suite that passes under contention can still be hiding interference. Treat a concurrent child's "all green" as **provisional**: re-run the affected suites serially in the parent before merging its branch, and time any independent review so it does not overlap another test-running child.
- **Contaminated-Baseline Rule**: the same contention fabricates results in the opposite direction, and that direction is more expensive. If a child's *baseline* (pre-change) run fails or errors only in tests unrelated to its change — typically with storage/connection errors — that is contamination, not a regression: never let the child adopt that figure, because its "count must not decrease" criterion and every number in its report become anchored to it. Steer it to re-run serially, confirm the expected count, and require it to name the discarded run as a contention artifact in its final report; an unexplained baseline delta reads later as a regression that was waved through. When steering mid-run, prefer a message over a re-dispatch: the child keeps its context and the fix costs one step instead of a cold start.
- **Windows File Lock & Exit 255 Tolerance Rule**: On Windows, background processes or file indexers frequently lock worktree directories, causing `git worktree remove --force` to print `error: failed to delete ... Permission denied` and exit 255. Do not treat exit 255 as a failure to unregister: git still successfully deletes `.git/worktrees/<id>` administrative metadata. Confirm with `git worktree list`; if absent from the list, proceed to `git branch -d`, then clean up leftover empty directories when released.
- **Terminal CWD Tracker & Dead Directory Recovery Rule**: If the session's internal working directory was set inside a subagent worktree (or child dir) that gets deleted or unlinked, all subsequent shell commands will fail during shell pre-cd with `line N: cd: <deleted-dir>: No such file or directory` (exit 126). Never panic or abandon the session: recover deterministically by running a terminal call with explicit `workdir="<repo-root>"` that executes `mkdir -p <deleted-dir>`, followed immediately by a clean `cd <repo-root> && echo "CWD_RESET_OK"` to snap the harness CWD tracker back to the parent repository.
- **Workspace Isolation in Child Worktrees**: When child worktrees sit below a monorepo or workspace manifest (e.g. Go `go.work`, pnpm workspace), build/test commands inside child worktrees can silently resolve dependencies to the main repository. Explicitly disable workspace mode (e.g. `GOWORK=off go test ...`) to ensure test execution stays strictly isolated to the worktree.
- **Deduplicate `.gitignore` Rule**: Multi-subagent delegations frequently append duplicate `.worktrees/` entries to the root `.gitignore`. Verify and deduplicate `.gitignore` after pruning worktrees before committing repository state.
- **Debris vs Live Worktree Identification Rule**: when `git worktree list` shows nothing under `.worktrees/` but directories remain, they are unregistered debris, not live worktrees. Identify with `ls -a <dir>`: no `.git` file plus only stray subdirectories (an emptied cache skeleton, one copied child dir) — inert debris. Check `git branch --no-merged master` for salvage, then remove the child dirs directly; there is no live checkout to `git worktree remove`.
- **`git -C` Parent-Repo Fallback Trap**: `git -C <leftover-dir> status|log` on a directory with no git metadata does **not** fail — git walks up to the enclosing repository and prints the PARENT's branch, HEAD and status. That output is evidence about the parent, never about the leftover dir; reading it as "the stale worktree is clean and on master" is a false negative that green-lights deleting someone's only copy. Confirm the registry with `git worktree list` and the contents with `ls -a` before concluding anything.
- **Ignore-Pattern Suffix Re-Check Rule**: ignore patterns are usually suffix-specific (`*.db.bak-*`, `*.db`), so renaming or adding local residue under a NEW suffix silently turns it untracked and one `git add -A` commits it — frequently real user data. After any rename run `git check-ignore -v <new-path>`; when uncovered and a tracked `.gitignore` edit would need a PR, add the pattern to `.git/info/exclude` with a dated comment, then confirm `git status` is clean again. Note that `git status` hides directories whose contents are all ignored — silence is not proof the debris is gone.
- **In-Flight Rebase Over Remote Master with Local Worklogs Rule**: when synchronizing an active feature branch with `origin/master` after upstream merges (e.g. peer PRs landed), local append-only progress logs or notes (such as `WORKMEMORY/work.log`) will block `git rebase` with `cannot rebase: you have unstaged changes`. Never discard or force-reset them: run `git stash && git rebase origin/master && git stash pop` so ongoing audit trails are preserved continuously across rebased commits without dirty aborts.
- **Direct-Push Scope Gate Pre-Check Syntax Rule**: when pre-push hooks gate direct commits to `master` via scope linters (e.g. `check_master_commit_scope.py`), verify manually before pushing with the explicit range flag: `python3 tools/check_master_commit_scope.py --range origin/master..master`. Omitting `--range` fails with exit code 2 and masks whether the staged commit list actually satisfies the allowlist.
- **Loose Object Accumulation & `gc.auto` Dormancy Rule**: repos with extensive branch switching, rebasing, or subagent lifecycles regularly accumulate loose objects (`git count-objects -v`). On Windows/MSYS, `gc.auto` often stays dormant even when loose objects exceed the 6,700 default threshold because background detachment fails silently or `gc.auto` is unconfigured (`git config --get gc.auto` returns empty). Periodically inspect `git count-objects -v`; execute plain `git gc` (never pass `--prune=now`, which permanently removes unreachable objects that might belong to concurrent in-flight worktrees) and confirm integrity with `git fsck --no-progress`.
- **Database/Storage Residue Appraisal Before Deletion Rule**: when discovering test residue directories or snapshot copies (e.g. `.test-db-residue-*`, `*.db.bak-*`), never `rm -rf` based on naming or directory heuristics alone. Perform read-only schema and row-count appraisal (e.g. compare table schemas, row counts, and record timestamps against canonical backups using sqlite3 read-only mode). Record the comparison in maintenance notes and require operator confirmation before deletion unless an identical canonical backup is verified to exist.

### Step 4: Machine Context & Baseline Synchronization
When the codebase has evolved across multiple sessions, project-level context files become stale:
1. Re-run primary test and build commands to capture physical numbers — **from the repo's sanctioned baseline, not your language default**. When the repo states a local/CI split ("local runs targeted tests only, the full suite lives in CI"), the figures come from the latest CI run's receipt (`gh run list` / `gh run view <id> --json jobs`) plus a narrow local subset; running the full suite locally against that stated discipline freezes the host when other agents share the machine. Record provenance (CI run id vs local run) next to every number — a figure nobody can re-derive is not a baseline.
   - File count, test suite count, route count, passing assertions.
2. Update `.agent-context.md` (or equivalent context anchor):
   - Replace outdated test counts and file lists with recomputed figures.
   - Record newly established local engineering red lines and gotchas.
   - **If the anchor was deliberately removed** (common: it duplicated an `AGENTS.md` / shared-memory directory the repo now keeps), do NOT recreate it — follow the repo's existing anchor, note the substitution in the handoff, and record the fresh figures there instead.
3. Track project-specific gotchas in `.agents/skills/<project>-gotchas/SKILL.md` rather than polluting global cross-session memory.

### Step 5: Full Clean Baseline Verification
Ensure the master working tree is clean and 100% green:
```bash
git status
pnpm test  # or pytest / cargo test / go test ./...
git push origin master
gh run watch <run-id>
```
- **Checkable Completion Criterion**: `git status` reports working tree clean; local test suite exits 0; remote GitHub Actions CI run completes with `success`.
- **Line-Ending Contract Check**: in repos that pin `text=auto eol=crlf` (or any explicit CRLF contract for logs/protocol files), re-verify after every programmatic edit: build the new text with explicit `\r\n` (e.g. `"\r\n".join(lines)`) or normalize with `re.sub(rb'(?<!\r)\n', b'\r\n', data)`, then assert the lone-LF count is 0 — `len([1 for i,b in enumerate(d) if b==0x0A and (i==0 or d[i-1]!=0x0D)])`. Python triple-quoted literals and shell heredocs inject LF-only newlines, so an append that looks clean silently breaks the contract; re-check, never assume.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I'll force-delete all subagent branches with `git branch -D`."* | **Silent Deliverable Loss**: Unmerged audit reports, spike notes, or subagent findings are permanently destroyed. | Always run `git branch --no-merged master` to inspect and salvage deliverables before deleting branches. |
| *"I'll just run `rm -rf .worktrees` without removing worktrees via git."* | **Git Index Corruption**: Git's administrative database (`.git/worktrees/`) retains stale lockfiles and phantom references. | Always run `git worktree remove --force` followed by `git worktree prune -v`. |
| *"I'll delete subagent branches before pruning worktrees."* | **Git Blocked Deletion**: Git refuses to delete a branch checked out in an active worktree (`used by worktree at ...`). | Always unlink worktrees via `git worktree remove --force` before deleting branches. |
| *"A locked worktree folder on Windows means cleanup failed."* | **Premature Abort**: Assuming transient OS directory lock blocks git cleanup. | Git unlinks worktree metadata regardless of folder locks; prune metadata, delete the branch, then retry directory cleanup. |
| *"Worktree folder deletion caused terminal exit 126, session is corrupted."* | **Stale CWD Pre-CD Trap**: The harness shell persists the deleted worktree path as its current working directory. | Re-create the missing path via `mkdir -p` with explicit `workdir`, then `cd` cleanly to the project root. |
| *"CI failed, so I'll rerun the job until it passes."* | **Flaky Pipeline Blindness**: Obscures real upstream slug migrations or 404 links that require source updates. | Inspect raw failed step logs (`gh run view --log-failed`) to address the deterministic root cause. |
| *"I'll pipe `gh run view --json jobs` into `jq` to parse CI step progress."* | **Windows Exit 127 Pipe Failure**: `jq` is typically missing from Git-Bash/MSYS PATH. | Use Python's stdlib `json` module to parse and extract step status deterministically. |
| *"We merged all features, no need to update context docs."* | **Context Drift**: Future agents read stale test commands, wrong file counts, and outdated architectural constraints. | Refresh `.agent-context.md` with physical test counts captured on the current date. |
| *"It's in a test-residue or `.bak` directory, so it's disposable junk."* | **Irreversible Data Loss**: Residue directories often hold recent development iterations or single copies of schema experiments that have not been backfilled. | Perform read-only schema and row-count comparison against canonical backups before deletion. |
| *"Git will automatically run gc in the background when loose objects exceed the limit."* | **Unchecked Disk & Git Bloat**: On Windows/MSYS, `gc.auto` background detachment routinely fails silently or stays unconfigured, allowing loose objects to bloat unchecked. | Check `git count-objects -v` and run plain `git gc` without `--prune=now`. |
| *"These workstreams are independent, so they can run in parallel as-is."* | **Same-File Collision**: logical independence says nothing about file overlap; two worktrees editing one shared module cannot be merged. | Measure each workstream's per-file hit spread and assign exclusive file ownership before dispatch; publish an own/forbidden table in every plan and handoff. |
