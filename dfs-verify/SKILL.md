---
name: dfs-verify
description: Verify unverified audit claims with physical evidence. Use when a report or audit asserts something no probe has confirmed, before anyone acts on it.
license: MIT
metadata:
  version: 0.1.0
  platforms: linux, macos, windows
  hermes:
    tags: [verification, audit, static-analysis, triage, evidence-first]
    related_skills: [dfs-review, dfs-team, dfs-debug, dfs-gate, dfs-orchestrate]
---
# DFS-VERIFY: Evidence-Backed Verdicts for UNVERIFIED Findings

A multi-expert audit, a linter sweep, or a reviewer's report routinely ships findings marked CONFIRMED / UNVERIFIED / "suspected". Nobody may act on an UNVERIFIED claim, yet leaving it dangling is just as bad: it gets re-litigated every session and blocks the work behind it. This skill is the verification leg — one claim at a time, a verdict with citeable evidence, and a backfilled registry so the claim never has to be re-derived.

## When to use
- A backlog/registry row or audit section marks findings UNVERIFIED / 待补证 / "needs confirmation before grading".
- Someone proposes a fix based on a static-analysis claim that was never adversarially checked.
- Before grading severity, sequencing work, or escalating a finding to the owner.
- **A whole registered batch is about to be scheduled** — re-verify every row on the current baseline first, not only the rows already marked UNVERIFIED. Rows marked "to fix" are claims about a past state; bounded patches land in between and silently close them.

## Procedure
1. **Restate the claim as a checkable predicate before reading code.** "The fetch loop has no total deadline"; "restarts have no cumulative cap"; "the backoff is deterministic". A claim you cannot restate is not yet verifiable — split it until each half is.
2. **Read the whole hop, then the callers.** Cite `path:line` for every hop (config default → helper → call site → entrypoint). A missing guard at one site proves nothing: the helper may be wrapped by one caller and not another — search the call sites (`search_files`) and read each one.
3. **Prove absence with a negative search, not prose.** "No jitter / no cap / no handler" are negative claims: back each with the exact negative search that returns nothing — run it with the native search tool (`search_files`), and cite the re-runnable shell equivalent (e.g. `grep -rnE "rand\.|jitter" <pkg>/` → 0 hits) in the report itself, plus a const/config dump showing the value that *should* have varied. Put the command in the report so a reader can re-run it.
4. **Prefer one executed receipt over many quotes.** Where a test seam exists, run the narrowest package/test that exercises the path (`go test ./pkg/ -count=1`, `pytest tests/test_x.py -k case`). Then name what the suite does **not** cover — "8 cases cover the per-episode budget, none cover the crash-loop" is a stronger finding than a green run alone.
5. **Check the CONDITION of any self-healing path, not just its existence.** A migration/backfill/retry/fallback only counts if it re-runs when you need it — read the enclosing `if`. A branch gated on "column absent"/"already migrated" will NOT heal later damage, so "there is a backfill" flips to "damage persists" the moment you read the gate. This is the most common source of a wrong verdict in this class of work.
6. **Keep the verdict and the severity separate, and label severity as a recommendation.** Verdict vocabulary: 成立 / 不成立 / 改判 / 结案 (holds / does not hold / re-graded / closed). Add the natural bound ("each cycle includes a process cold start, so it is not a tight CPU spin") so the owner can grade without redoing your work, and say explicitly that the grade is yours to recommend, theirs to set.
7. **Write the verdict where the claim lives.** A dated report in the repo's review/audit directory **plus** backfill of the registry row (status + pointer to the report). State re-graded claims explicitly ("original: X → now: Y, because …"); silently flipping a status destroys the audit trail.
8. **Do not repair in the same pass.** Verification and repair are different change classes with different gates — registry/doc edits ride the booklet path, code fixes need a branch + PR + tests. Touching code while verifying breaks the "no product code was modified" guarantee the owner approved the pass on.

## Pitfalls
- **Doc comment vs implementation.** Config comments routinely promise more than the code delivers ("total restart budget" implemented as a per-episode counter). Read the counter's scope — a loop-local variable resets every iteration. Report the mismatch itself; the fix may be one word of comment or a real guard.
- **"Same shape" is not "same content".** Identical table/row counts across two snapshots do not mean identical files — timestamp columns and non-table bytes differ. Run `cmp`, then characterise the difference before concluding "duplicate, safe to delete".
- **Byte caps are not time limits.** A size guard on a stream bounds memory, never duration; a per-operation timeout multiplied by a hop count is a worst case, not a deadline. State which one the code actually has.
- **Threshold mechanisms that "should have" fired.** If auto-gc / TTL cleanup / eviction did not fire despite the condition being met, first check the config key is even set (`git config --get <key>` printing nothing = unset) before blaming the mechanism.
- **Never delete residue without identity evidence.** Quarantine and leftover directories (test DBs, snapshot copies) may hold the only copy of something. Compare against any preserved backup, characterise read-only, and leave the delete decision to the owner unless the remaining copies are provably identical.
- **Hypothetical future extensions vs present codebase reality.** Reviewers frequently escalate missing interface arguments (e.g. missing `context.Context`) to P1/Blocker by imagining "what if an I/O-bound implementation is added later". Check the actual registered implementations: if all current implementations are sub-millisecond in-memory operations (pure AST evaluation, local clock reads), the blocking hang scenario is unreachable in the current system — refute or downgrade to P2/enhancement.
- **Microsecond mutex hold time vs macroscopic lock contention.** Reviewers often label "heap allocation or slice copy inside a mutex" as a critical contention bottleneck. Calculate the actual hold time and arrival rate: copying a bounded 32-element slice takes <1µs; behind an upstream rate limiter and small concurrency pool, collision probability is near zero — refute lock contention claims that lack arrival-rate and hold-time triangulation.
- **The registered remedy can be wrong even when the defect is real.** Wording written from a skim routinely mislabels the mechanism: "field X is not masked" can be false (X *is* masked, first-4-plus-last-4) while the true defect is the missing origin gate — and the two demand opposite fixes (add a gate, which locks out legitimate remote clients, vs. redact by origin, which does not). Derive the fix shape from the code you just read, never from the registered sentence, and correct the registry wording as part of the verdict.
- **A delegate's deviation rationale is itself an unverified claim.** When a subagent departs from its task spec and justifies it ("that version can no longer run", "that API is gone", "that flag is mandatory now"), adjudicate the rationale against the **primary artifact** — upstream release notes, changelog, the dependency's own source, the tool's actual output — not against the spec text. Accept-and-record when it holds: a task spec written from a plan is not evidence about the world, and a plan that names a now-unusable version would otherwise force a broken build. Demand REVISE when it does not. Never accept on "the rationale sounds plausible", and never reject on "it differs from the plan" — spec-fidelity is not a correctness criterion.
- **A test that exists is not a test that guards.** A claim of the form "this assertion can never fail" needs the *mechanism* named before it earns a verdict — the framework guarantee (a capture plugin always installing a non-None stream), the comparison that is true by construction, or the branch that cannot be reached. "It looks weak" is not a verdict, and neither is a green run. When the repair follows, its acceptance proof is **comparative, under one mutation**: apply a single mutation to the guarded code path and show the OLD assertion stays green while the replacement goes red. A green replacement on its own proves nothing — it may be green for exactly the reason the old one was. Note also that the registered line number is often off by one or two (blank lines, wrapped messages): go to the named line, read it, and report the assertion's real location rather than confirming the claim against a comment.
- **Re-verify per item, then report which rows are stale.** Expect a nonempty fraction to be already-closed by intervening work; those verdicts are 结案 with the proof, not plan inputs. Scheduling a stale row spends a branch and a review cycle on a defect that no longer exists.

## Output shape
A dated `<review-dir>/<YYYY-MM-DD>-<topic>-verification.md` in the repo's documentation language, containing: a verdict table (claim | original grade | this pass's verdict | recommended severity); one section per claim with `file:line`, the runnable command, and its result; an explicit re-graded/refined list; a "not covered this pass" list; and an appendix of the exact commands so the whole pass is re-runnable.
---

## Checkable Completion Criterion
- Every evaluated claim carries binary proof (CONFIRMED with reproduction / REFUTED with reachability proof).
- Zero production source files modified during the verification audit pass.

---

## Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"The review finding sounds plausible, so I will rewrite the code immediately."* | **Ghost Defect Chasing**: Model hallucinations and out-of-context review comments prompt destructive, unneeded code rewrites. | Read code first and obtain physical negative-search proof; if the failure scenario is unreachable, label REFUTED. |
| *"I can verify this claim while editing the function to be cleaner."* | **Observer Effect & Confounded Baselines**: Modifying code during verification alters execution context and invalidates proof. | Verification is strictly read-only; ZERO production code edits shall be made while verifying a finding. |
| *"I don't need a negative search command; prose explanation is enough."* | **Unverifiable Subjective Assertion**: Future reviewers cannot mechanically reproduce a prose claim of absence. | Prove absence with a concrete, re-runnable negative search command returning zero hits. |
