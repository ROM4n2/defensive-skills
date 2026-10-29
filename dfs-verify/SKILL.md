---
name: dfs-verify
description: Verify unverified audit claims with physical evidence. Use when a report or audit asserts something no probe has confirmed, before anyone acts on it.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  author: Haoyu, Hermes Agent
  hermes:
    tags:
    - verification
    - audit
    - static-analysis
    - triage
    - evidence-first
    related_skills:
    - dfs-review
    - dfs-team
    - dfs-debug
    - dfs-gate
    - dfs-orchestrate
    mcp_tools: []
---



# DFS-VERIFY: Evidence-Backed Verdicts for UNVERIFIED Findings

A multi-expert audit, a linter sweep, or a reviewer's report routinely ships findings marked CONFIRMED / UNVERIFIED / "suspected". Nobody may act on an UNVERIFIED claim, yet leaving it dangling is just as bad: it gets re-litigated every session and blocks the work behind it. This skill is the verification leg — one claim at a time, a verdict with citeable evidence, and a backfilled registry so the claim never has to be re-derived.

## When to use
- A backlog/registry row or audit section marks findings UNVERIFIED / 待补证 / "needs confirmation before grading".
- Someone proposes a fix based on a static-analysis claim that was never adversarially checked.
- Before grading severity, sequencing work, or escalating a finding to the owner.
- **A whole registered batch is about to be scheduled** — re-verify every row on the current baseline first, not only the rows already marked UNVERIFIED. Rows marked "to fix" are claims about a past state; bounded patches land in between and silently close them.

## Procedure
1. **Restate claim as a checkable predicate**: State exact condition before reading code; split compound claims.
2. **Trace the whole hop and callers**: Cite `path:line` across config default -> helper -> call site -> entrypoint.
3. **Prove absence with negative search**: Back negative claims with exact `search_files` / regex queries returning 0 hits.
4. **Prefer executed receipts over quotes**: Run the narrowest test command and report what the suite does NOT cover.
5. **Check the CONDITION of self-healing paths**: Verify `if` branch triggers on subsequent runs, not just clean initial state.
6. **Separate verdict from severity**: Verdicts: 成立 / 不成立 / 改判 / 结案 (holds / refuted / re-graded / closed).
7. **Write verdict where claim lives**: Update review report and backfill registry row with evidence pointers.
8. **Do not repair in the same pass**: Verification is strictly read-only; product code changes require separate PR.
9. **Falsify the measurement harness before accepting a counter-intuitive benchmark verdict**: When an evaluation reports 0% lift or total wipeout, run zero-cost probes across the **Three Evaluation Gates (Corpus / Observation / Span Coverage)** in [references/verification-pitfalls-and-eval-gates.md](references/verification-pitfalls-and-eval-gates.md) §1–§2 before grading capability.

## Pitfalls
- **Doc comment vs implementation**: Read counter lexical scope; loop-local counters reset every iteration.
- **Same shape != same content**: Equal row counts across DB snapshots do not prove byte identity; run hash comparison.
- **Byte caps are not time limits**: Size bounds memory, never duration; per-hop timeouts multiplied by retries are worst-case bounds.
- **Unset config keys**: Verify `config --get <key>` is set before blaming eviction code.
- **Hypothetical I/O vs present reality**: Refute P1 claims when all registered implementations are in-memory sub-millisecond ops.
- **Weak-test claims require comparative mutation proof**: Apply one mutation where old assertion stays green and new goes red.
For the full 9-item audit pitfall catalog and evaluation harness falsification rules, load [references/verification-pitfalls-and-eval-gates.md](references/verification-pitfalls-and-eval-gates.md) §3.

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
