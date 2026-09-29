# Subagent dispatch — one contract, three runtimes

Every DFS skill that fans work out to subagents dispatches through this contract. It lives here, once,
because three skills used to carry their own copy and the copies drifted — `standard multi-agent
environments` in one, `standard agent environments` in another.

## The contract

1. **Runtime-neutral first.** `delegate_task` (Hermes, and any standard multi-agent runtime) carrying
   the seat's goal, scope and instructions. This path always works; it is never the optional one.
2. **Claude Code fallback.** Claude Code dispatches via `invoke_subagent`, and may pick a *base agent*
   with `subagent_type`. Those agents live in `~/.claude/agents/` — a Claude-specific directory, so
   treat the whole path as an optional fallback, never as the only route.
3. **A `subagent_type` must resolve.** If the named agent is not present in `~/.claude/agents/`, do not
   pass it anyway: fall back to `delegate_task` with the same prompt. A `subagent_type` that resolves
   to nothing fails silently, which is exactly the failure this contract exists to prevent.

## `subagent_type` picks the base agent, not the job

The Claude Code agent list is fixed and short, so one base agent legitimately serves different jobs in
different skills. `code-reviewer` is the base agent for `dfs-team`'s **Code Quality & Standards** seat
(the Red/Yellow protocol) *and* for `dfs-grill`'s **Backend & Concurrency** seat (lock scope, goroutine
lifecycle, silent errors). That is reuse, not drift.

**The job comes from the seat's own row and from the prompt you write — never from the agent's name.**
Before dispatching, read that row's `Owns` / `Grills on` column and put that scope in the prompt. Two
seats sharing a base agent must not receive the same prompt.

## Read scope — declare it, don't bound it

**Measure first, because the intuitive fix is the wrong one.** The rule below came from one measured
run: a 1,196-line target audited by three seats. All three read the **entire** target (4,063 lines
total, a 3.4x amplification), and yet **14 of the 15 findings were distinct** — so the amplification
bought real coverage. Two of the three also read a file outside the target, and both outside reads
were load-bearing: one seat confirmed a dead-green test card only by reading the test file, the other
confirmed a coverage gap the same way. Bounding a seat's input to its own domain would have removed
both.

So the rule is **disclosure, not restriction**:

- **Before dispatching**, state the target scope — the files the seats are auditing.
- **In its report, a seat lists every file it opened with the line ranges**, and marks which lie
  outside the target scope. Each outside read carries a one-line reason: the finding it produced or
  verified.
- **A finding with no read behind it is suspect.** A conclusion that cost no read came from the
  code's own comments or from nowhere, not from an inspection. The read list is how you tell those
  apart before the finding reaches the synthesis.

Full reads are the price of independent readings — that price is agreed. An unlisted read is the
price nobody agreed to.

## Who dispatches, and from what roster

| Skill | Pattern | Roster |
|---|---|---|
| `dfs-team` | one subagent per seat, in parallel | its `Owns` / `Cross-checks` table |
| `dfs-grill` | one subagent per lens, in parallel | its `Grills on` table |
| `dfs-review` | one isolated reviewer, no fan-out | no roster — one reviewer against one diff |
