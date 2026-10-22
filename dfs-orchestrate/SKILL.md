---
name: dfs-orchestrate
description: Dispatch and verify subagents with file-occupancy guards. Use when several subagents must work in one repo without colliding, or a batch needs a granularity call.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags: [delegation, subagents, verification, multi-agent, orchestration]
    related_skills: [dfs-exec, dfs-pipeline, dfs-maintain, dfs-gate, dfs-verify, dfs-plan]
---
# DFS-ORCHESTRATE: Multi-Agent Dispatch, Verify, Merge

> **Invariant (MUST)**: a child's report is a **self-report, not evidence**. Nothing a subagent asserts about its own work — "tests pass", "verified", "uploaded", "reviewed" — counts until the orchestrator reproduces the claim in the parent tree.

## When to use
- Dispatching one or more subagents to implement, review, or verify work.
- Running parallel workstreams against one repository.
- Acting on a completion report: merging a child branch, triaging a child-reported finding.
- Maker-checker separation is required but no tiering skill applies.

Sibling skills: worktree pruning / file-occupancy partitioning live in `dfs-maintain`; when the output should be a permanent check rather than a fix, use `dfs-gate`.

---

## The loop

### 1. Partition by FILE before dispatch
Independence of intent is not independence of files. Two logically unrelated workstreams routinely need the same shared module, and two branches editing one file never merge cleanly. Measure per-file spread, assign **exclusive ownership per FILE**, publish an own/forbidden table in every plan and every handoff — children cannot see each other and will walk into each other's files. Two workstreams needing one file are **serialized**: the second dispatches only after the first is merged. Full procedure: `dfs-maintain`.

**Re-check the contract when scope grows.** A follow-up fix can silently collide with a file you granted another workstream — amend the published table the moment you hand out a new file, and log the amendment where both sides will read it.

### 2. Brief construction
A child starts with **no conversation, no memory, no repo context files**. Everything it needs goes in the brief.
- **Point at the repo's invariants file; restate only the delta.** Repository-wide rules (privacy red lines, forbidden commit paths, format/lint false positives, timeout rules) belong in the repo's anchor file — cite it by path and let the child read it once. Repeating the full invariant set in every brief is the single largest avoidable token cost in a multi-dispatch run: it is paid in full on every dispatch and changes never.
- **Pass evidence, not conclusions.** For every claim about existing code, give `file:line` and a short quote. "The endpoint lacks an origin gate" is unusable; the line and the missing call is actionable.
- **Name the exact files it owns and the exact files it must not touch.**
- **Prescribe the receipt shape**: command + exit code + counts + diff stat, plus a mutation self-proof where you want the work proven rather than asserted.
- **Derive the gate list from the change's BLAST RADIUS, not from the files touched.** When a change alters how a symbol is *called* — a signature, a return shape, a transport swap, a fixture's interface — every hand-rolled mock of the old shape stops intercepting, and those mocks live in test files nobody listed. Before writing the commands, grep the whole test tree for each changed symbol and put those files in the gate list for the builder, for the reviewer, and for your own re-run. Getting this wrong reads as *local green, then the full-suite job fails on a shard you never ran* — the touched file is the wrong unit of "affected".
- **Ask it to declare what it could NOT validate on this host.** That list is the honest boundary of the change, and it is the part a reviewer most needs.
- **Also ask for what it found OUTSIDE its ownership.** A child boxed into a file set still reads around the edges, and it is the only one positioned to notice that the change just made something *else* untrue — a docstring citing a now-stale path, a comment naming a guard that moved, a second call site of the shape you changed, a plan line that contradicts the brief. None of it is in its mandate, so unnamed it is simply dropped. Make "anything you found that is outside your ownership" an explicit field and expect a list: it has repeatedly returned the findings the orchestrator could not cheaply reconstruct, and it costs one line in the brief.
- **Impose the Frozen Surface Rule on relocation briefs.** When moving or splitting code covering recently stabilized, frozen, or sensitive contracts (e.g. auth, payment, evaluation schemas), instruct the child explicitly: change zero assertion text, report suspected defects instead of fixing them, and require byte-level identity verification (byte-exact splice or block hash comparison) against pre-move source. Without this explicit barrier, subagents reflexively "clean up" or loosen assertions that look unusual, destroying regression coverage during pure relocation.
- **Require a residual inventory handback in multi-batch migrations.** In phased extractions across large files, line coordinates drift after the first commit. Instruct each child to return an empirical inventory of what remains in the source file (section headers, line ranges, and test/symbol counts). This gives the orchestrator a verified map for subsequent dispatches without repeated ground-up re-exploration.
- **Tempting-but-wrong instructions get obeyed.** If you name a specific tool version, config key, or API in the brief, the child will use it verbatim even when it cannot work. Either verify it first, or state it as a hypothesis and require the child to confirm it exists and to record a sourced deviation if not. The same holds for a **rule whose premise is a claim about the codebase**: when an instruction says "do X because Y holds", Y is a factual claim the child can check. Require it to verify Y and report a contradiction rather than comply, and phrase instructions as the *intent* — a wrong premise then yields a reported contradiction instead of a wrong rule faithfully applied.
- **Sequence same-file batches.** When two batches must edit one file, hold the second until the first is merged; do not launch both and hope.
- **Size the dispatch unit by domain, not by item count.** A cluster of small, independent, same-domain fixes belongs in ONE builder dispatch with ONE reviewer for the batch — not one dispatch per item. On a resource-constrained host every extra concurrent agent costs more than it saves, and maker-checker separation survives because the batch still gets an independent reviewer. What must NOT be batched: items in different domains (a reviewer can no longer judge the diff coherently), and items where one's failure would invalidate another's proof (e.g. two items touching the same test file, where the second's baseline is the first's output). Record the granularity decision in the plan so the deviation from one-task-per-dispatch is visible rather than silent.
- **Automatic escalation of lightweight tasks.** When delegating a task initially scoped as lightweight, chore, or config (Solo path), if its execution touches production code or core test assertions, escalate immediately to Maker-Checker (TDD Builder + independent Reviewer). Never bypass independent review for production code edits just because the task was pre-labeled as light.
- **Children commit on their own branch and do not push or merge; the orchestrator owns integration.**

### 3. Serialize the unshareable resource
**One test-running process at a time.** Parallel test runs against a shared data dir / database / cache fabricate results in *both* directions:
- **False green** hides real interference — treat a concurrent child's "all green" as provisional.
- **False red** contaminates the child's *baseline*, which poisons its "count must not decrease" criterion and every number in its report. A baseline red confined to tests unrelated to the change is contamination, not regression: steer the child to discard it and re-run serially.

Before dispatching a test-running child, confirm nothing else is running tests; before dispatching a reviewer, check whether another test-running child is still alive. When you must run several, run them serially — it is slower and correct.

### 4. Verify before merge
1. Read the diff yourself; do not skim the child's summary of it.
2. Re-run the affected suites **serially**, from the parent tree — and size "affected" by blast radius, not by the files in the diff. A change that swaps a call's transport, alters a shared fixture's interface, or edits a test helper the rest of the suite imports has the **whole suite** as its affected set. Run the full suite locally for those, even when repo convention defers the full run to CI: deferring is exactly what lets the local-green / full-suite-red gap ship. The child's own gate list will have had the same blind spot, so this is the step that catches it.
3. Cross-check the child's numbers against yours. A count that differs is a finding until explained (a skipped network test, a different collection root).
4. Check for an **ordering dependency between batches** before merging: a check introduced by batch X may be unable to pass until batch Y's fix lands (X's gate flags the very shape Y repairs). Merge X after Y, and declare X's expected standalone red up front so it is not debugged as a defect.
5. **Re-verify that earlier batches' fixes survived this batch's restructuring.** After a move, split or mechanical rewrite, assertions someone else landed earlier now sit inside the moved ranges. A collected-count check is blind to a fix that a faithful-looking splice overwrote, and a line-number citation is worse than useless because the line moved. Grep the parent tree for the distinct *text or identity* of each prior fix — the capture made before the call, the explicit `encoding=` argument, the non-vacuous comparison — and prove it still exists **and still sits inside the test that owns it**. Brief the child to return that before/after evidence rather than the sentence "the fix is intact".
6. Only then merge, delete the branch, and prune the worktree.

### 5. Review adversarially or not at all
A reviewer that only reproduces the builder's commands adds almost nothing. Require the brief to make the reviewer *try to break* the change — see `templates/adversarial-reviewer-brief.md` for the copyable shape. The load-bearing asks: redo mutation proofs verbatim; falsify every allowance/suppression by arguing from the code rather than its prose reason; construct a counterexample the safety mechanism misses; verify the riskiest construct empirically (class relationships, control flow on every branch) instead of reading it; state residual unknowns; and prove the tree is clean after mutations.

**Point the reviewer at the riskiest hop.** You usually know which construct smells; naming it converts a shallow review into a decisive one.

### 6. Merge, then clean
Worktree removal is **inner-first**: parallel dispatches nest worktrees (`.worktrees/A/.worktrees/B`, and deeper), so removing an outer one destroys live nested work. On Windows a removal may deregister the worktree while failing to delete the directory (file locks) — the git state is already correct; retry the directory later. Details and salvage rules: `dfs-maintain`.

**Prune by exact subagent ID, never via wildcard glob.** Running blanket `rm -rf .worktrees/subagent-*` or bulk deleting `hermes-subagent/*` branches destroys the active worktrees and branches of sibling subagents still running in the background. Target only the finished child: `rm -rf .worktrees/subagent-<id>`, `git worktree prune`, and `git branch -D hermes-subagent/<child-branch>`.

---

## Acting on what a child reports
- **Reproduce before registering.** A finding — including one produced by a tool you built — becomes a backlog item only after it reproduces on the baseline. Unreproduced stays an observation, and a one-off you cannot reproduce must be reported as *not reproduced*, never written up as pending work.
- **A child's correction of YOUR premise is a different kind of report — adopt it on its artifact, not on its confidence.** "Self-report is not evidence" applies to claims about the child's *own* work; it does not license dismissing a child that contradicts you. When a brief rests on a factual claim about the code and the child reports the claim is false, it normally arrives with something independently checkable — a source location, an AST result, a test that pins the boundary. Adopt the correction when that artifact holds up, and prefer the child's version when it is the one that keeps the motivating case failing. Your adjudication is a hypothesis; the child is the one holding the code, and a rule applied literally against a wrong premise is the exact failure the "phrase it as intent" instruction exists to catch.
- **Re-check "pre-existing flake" classifications.** Re-run the named test in isolation. A flaky classification can hide a real regression, and a real regression can hide behind a flake label.
- **Your own command error masquerading as a finding.** Before interpreting a red, verify the invocation: a linter handed a file type it does not parse reports thousands of errors that mean nothing. Verify the command, then the code.
- **A harness warning about the child's own writes invalidates the evidence drawn from them.** If the run reports that a file write failed while the narrative proceeds as though it landed, every receipt sourced from that file is unverified — re-derive those numbers yourself instead of reading past the warning.
- **Long delegations can add skills.** Children may write to the skill library. After a long run, re-read what is there before relying on it.

## HITL authorization gates
When a task needs explicit user authorization before touching files, present: the change surface, the irreversible risks, and **what cannot be validated on this machine** — as a compact table (surface | current state | proposed change | why it is unverifiable here), with one recommendation. **Include the "mechanize the class" option among the choices**: this user reliably takes the most comprehensive option and separately asks for recurring defect classes to be gated rather than fixed one at a time.

## Pitfalls
- **Silent escalation bypass on production code touches.** Labeling a task 'Tier 1' or 'lightweight' does not excuse skipping independent review when the diff touches production code. If a supposedly light task modifies application source files, an independent reviewer subagent must be dispatched before merging.
- **Parent workspace files misroute subagent worktrees.** When a child runs inside `.worktrees/subagent-<id>`, its relative path from a parent workspace file (e.g. `go.work` defining `use ./pkg`, `pnpm-workspace.yaml`, or a Cargo virtual workspace) differs from the declared member path. The toolchain then either fails to resolve packages or silently compiles and runs tests against the *parent* directory instead of the isolated worktree. Instruct the child to disable parent workspace resolution in every toolchain command (e.g. `GOWORK=off go test ...` for Go) or explicitly set the isolated working directory root.
- **Emitting an empty turn on dispatch or re-entry.** Both when dispatching a background subagent and when a child re-enters, the orchestrator turn must NEVER end with zero text. When dispatching, always output a one-line status line naming the dispatched subagent and target before stopping; emitting an empty response triggers client-side warnings that interrupt execution. On a Checker (Reviewer) `PASS` verdict, execute the complete closing cascade in that same turn: inspect verdict, merge the reviewed branch (`git merge --no-ff`), run regression tests, update ledger/state machine (`complete-task`), prune the child worktree, and immediately start the next task or deliver the milestone summary. Stopping before this cascade completes or emitting an empty response leaves the workspace half-transitioned and forces a user re-prompt.
- **Wildcard cleanup during parallel runs.** Running blanket `rm -rf .worktrees/*` or bulk deleting all subagent branches while sibling children are in flight deletes their active working trees mid-execution, causing silent subprocess failures and lost work. Target only the finished child's specific worktree and branch.
- **Editing a child's output in the orchestrator thread.** When the harness requires independent review, a defect goes back to the implementer as a defect list — the orchestrator patching it directly voids the separation that was the point.
- **Accepting a partial-validation account as complete.** A child that could not exercise a branch (platform-specific, network-specific) must say so unprompted; if the report is silent on validation limits, ask before merging.
- **Trusting a green suite as proof the criteria work.** A suite passes on a tree where the check matches nothing. Mutation self-proofs are what separate "passing" from "working".
- **Dispatching the next batch before the previous one lands.** Merges queue, worktrees nest, and the file-ownership table drifts out of date. Land, then dispatch.
- **A plan's coordinates go stale as its own tasks run.** Line numbers, section offsets and "the fixture lives at X:62" recorded while planning task 1 are wrong by the time task 3 runs — an earlier task will have deleted or moved lines. Instruct every later child to locate by **content** (comment/header text, symbol names) and to report the real ranges it found *before* it moves anything. Say in the brief that the recorded numbers are expected to be wrong.
- **Duplication introduced to satisfy an ownership boundary compounds.** When splitting forces a verbatim copy because the dependency is owned by another workflow — a shared fixture, a helper that must not be imported across the seam — hoist it into the shared layer before the NEXT batch lands. By the third batch there are three copies and they start to drift. Have the child verify **empirically, not by assumption**, that the hoisted form still registers where it must (e.g. a fixture imported into a module's namespace keeps module-local autouse scope) and keep the forced-copy workaround only if that verification fails — in which case it reports the contradiction instead of forcing it.
---

## Checkable Completion Criterion
- Subagent deliverables merged only after the serial verification test suite exits 0.
- All child worktrees pruned without residual locks (`git worktree list` shows only primary branches).

---

## Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"The subagent reported tests passed, so I can trust its output without checking."* | **Unverified Self-Reporting**: Subagents can hallucinate green test outcomes or omit failing integration tests. | Caller MUST independently execute and verify the physical test suite and diff before accepting child deliverables. |
| *"Two subagents modifying the same file can resolve git conflicts later."* | **Concurrent Mutation Conflict**: Parallel edits to overlapping lines create irrecoverable merge collisions and overwritten work. | Enforce strict File-Occupancy Tables: exactly one subagent is granted write ownership per file. |
| *"Running tests in parallel across all subagents speeds up the build."* | **Test Environment & Port/DB Contention**: Parallel suites collide on test databases, mock servers, and socket locks. | Execute verification test suites serially; never run contending integration suites concurrently. |
