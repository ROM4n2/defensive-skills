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
- **Before dispatching two or more workstreams in parallel against the same repository** — the file-occupancy partition is planned here (see the Concurrent Workstream File-Occupancy Partitioning Rule), because measuring it before dispatch is what prevents same-file collisions and merge-time surprises.
- When automated candidate PRs or abandoned branches stall scheduled discovery pipelines.
- When synchronizing `.agent-context.md` or repository baselines after a large milestone.

> **Full playbook**: every rule below has a detailed entry — commands, Windows/MSYS traps, and the reasoning behind each guard — in [`references/maintenance-playbook.md`](references/maintenance-playbook.md). Load it before executing a step you have not run recently.

---

## The 5-Step Maintenance Protocol

### Step 1: CI/CD Pipeline Health Audit
Audit recent automated pipeline runs before touching files.
```bash
gh run list --limit 10
gh run view <run-id> --log-failed
```
Four traps decide whether this step produces a diagnosis or a guess: the missing-`jq` failure on MSYS, transient transport EOFs during polling, mixing local validation with network probes in one CI step, and letting third-party downtime block a static deploy. Each is spelled out in the playbook.

### Step 2: PR & Remote Branch Backlog Drainage
Drain automated candidate PRs and abandoned feature branches that accumulate and stall scheduled pipelines.
```bash
gh pr list
gh pr close <pr-number> --delete-branch --comment "Closing stale candidate PR during routine maintenance"
git fetch --prune origin
```
- **Checkable Completion Criterion**: `gh pr list` contains zero abandoned/stale automated drafts; `git ls-remote --heads origin` shows no orphaned feature branches.

### Step 3: Worktree Pruning & Unmerged Artifact Salvage (MUST)
Subagents running in isolated git worktrees (`.worktrees/subagent-*`) often leave accumulated directories and unmerged branches. **Salvage before prune** — the order is the whole rule, and reversing it destroys deliverables permanently.

**Concurrent Workstream File-Occupancy Partitioning Rule (do this BEFORE dispatch)**: independence of *intent* is not independence of *files*. Measure each workstream's per-file spread and assign **exclusive ownership per FILE**, never per task name; serialize the two when they genuinely need one file. A partition decided at merge time is not a partition.

```bash
git branch --no-merged master      # 1. salvage check FIRST
git log master..<branch> --stat
git worktree list | grep '/.worktrees/' | awk '{print $1}' | while read -r wt; do
  [ -n "$wt" ] && git worktree remove --force "$wt" 2>/dev/null || true
done
git worktree prune -v               # 3. unlink metadata
for b in $(git branch --list 'hermes-subagent/*' | tr -d ' *+'); do
  git branch -D "$b" 2>/dev/null || true
done                                # 4. then delete branches
```
Fourteen named traps govern this step — uncommitted child changes invisible to `git branch --no-merged`, leaf-first removal on Windows, exit 255 tolerance, the stale-CWD exit 126 recovery, the `git -C` parent-repo fallback false negative, contention-contaminated baselines, and more. All are in the playbook; skipping them is how a "clean" prune silently deletes someone's only copy.

### Step 4: Machine Context & Baseline Synchronization
When the codebase has evolved across multiple sessions, project-level context files become stale.
1. Re-run primary test and build commands to capture physical numbers — **from the repo's sanctioned baseline, not your language default**.
2. Update `.agent-context.md` (or equivalent context anchor) with recomputed figures and newly established red lines.
3. Track project-specific gotchas in `.agents/skills/<project>-gotchas/SKILL.md` rather than polluting global cross-session memory.

The local/CI split rule, the removed-anchor rule, and why provenance must sit next to every number are in the playbook.

### Step 5: Full Clean Baseline Verification
Ensure the master working tree is clean and 100% green.
```bash
git status
pnpm test  # or pytest / cargo test / go test ./...
git push origin master
gh run watch <run-id>
```
- **Checkable Completion Criterion**: `git status` reports working tree clean; local test suite exits 0; remote GitHub Actions CI run completes with `success`.
- **Line-Ending Contract Check**: re-verify after every programmatic edit when the repo pins an explicit CRLF contract — the exact assertion is in the playbook.

---

## [ANTI] Common Rationalizations & Anti-Patterns

Eleven rationalizations are catalogued with their hazard and guard in the playbook's anti-pattern table. The three that cause irreversible damage:

| Agent Rationalization | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"I'll force-delete all subagent branches with `git branch -D`."* | **Silent Deliverable Loss**: unmerged audit reports and findings are permanently destroyed. | Always run `git branch --no-merged master` before deleting branches. |
| *"I'll just run `rm -rf .worktrees` without removing worktrees via git."* | **Git Index Corruption**: stale lockfiles and phantom references remain. | `git worktree remove --force` then `git worktree prune -v`. |
| *"These workstreams are independent, so they can run in parallel as-is."* | **Same-File Collision**: logical independence says nothing about file overlap. | Measure per-file spread and assign exclusive file ownership before dispatch. |
