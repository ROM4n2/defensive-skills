---
name: dfs-gate
description: Author mechanical gates for recurring defect classes. Use when a defect class has recurred, or an audit finding needs a permanent mechanical check instead of a note.
license: MIT
metadata:
  version: 0.1.0
  platforms: linux, macos, windows
  hermes:
    tags: [ci, gates, prevention, defensive-engineering, static-analysis]
    related_skills: [dfs-maintain, dfs-verify, dfs-debug, dfs-bootstrap, dfs-incident, dfs-orchestrate]
---
# DFS-GATE: Make the Rule Fail Loudly, or It Does Not Exist

> **Invariant (MUST)**: a rule that lives only in prose does not exist. A rule on the executed path — a CI job, a pre-commit / pre-push hook, a linter — does exist.

When the same *shape* of defect recurs, fixing the instance is not the fix. The durable fix is a gate that makes the shape fail loudly on every future contributor's path. This skill is how to build one that people keep instead of one they route around.

## When to use
- A second (or Nth) defect of the same shape was just fixed and you can name the shape in one sentence.
- The user asks to "prevent this class", "add a guard", "make it mechanical", "we should not have to catch this again".
- You are about to add a rule to a conventions document or AGENTS.md — stop and check first whether it can be a gate instead.

Not every rule can be mechanized. When it genuinely cannot, say so explicitly and name who must check it and at which moment — an honest "a human checks this at review" beats a gate nobody can build and a paragraph nobody reads.

## Step 1 — Establish the design preconditions
1. **Name the failure shape in one sentence, and list the concrete incidents that share it.** If you cannot name the shape, you are not ready to gate it; a criterion built on a vibe produces false positives, and false positives are what get a gate suppressed wholesale.
2. **State which layer it belongs on.** A local hook is bypassable (`--no-verify`) and absent on a fresh clone; CI is the backstop and the only authoritative layer. If the repo already has a hook for this shape, the gate's job is the *second* layer and its rationale must say so — do not build a CI job that merely duplicates an unbypassable hook, and do not rely on a hook alone where bypass is the actual hazard.
3. **Choose the enforcement point deliberately**: pre-commit for fast feedback on the author's own path; pre-push when the check needs a commit *range*; CI when it must be impossible to bypass. Mature repos often want a hook for speed plus CI for authority.
4. **Mirror the repo's existing gate tool.** Read a sibling gate first and copy its argv conventions and its exit-code contract rather than inventing one.

## Step 2 — Exit-code contract (MUST)
`0` = pass, `1` = violation found, `2` = the gate could not run (environment unusable). Keeping "found something" distinct from "could not run" is what stops a broken environment from being read as a pass. A gate that collapses these two is worse than absent: it reports safety it never checked.

## Step 3 — The rules that make a gate trustworthy
1. **One criterion per real incident.** Every check must map to a failure that actually happened. If you cannot say which incident a criterion catches, drop it. Thoroughness is not a virtue here — precision is.
2. **Match the mechanism, not the symptom.** Prefer criteria describing a mechanism (an exception clause whose body is only `pass`; a TLS-verification disable with no logging call in the enclosing function) over criteria matching a string from one incident. Mechanism criteria survive refactors; string criteria silently stop matching and become decoration.
3. **Never red on day one.** Ship with the current tree passing: give every pre-existing legitimate site an inline suppression carrying a *specific* reason. A gate that is red the moment it lands gets disabled, ignored, or explained away — and it also supplies false assurance afterwards.
4. **Suppression must carry a reason; an empty reason is itself a violation — and the reason is a CLAIM ABOUT THE CODE, which has to be true of it.** What keeps a suppression list honest is not the presence of prose but its accuracy: a plausible-sounding reason that misdescribes the code buys a lasting exemption on a false premise, which is worse than no reason at all. Every reason is therefore re-checkable, not write-once. When a reason and a code comment disagree, the arbitrating fact is what the code *does* — read the call path; never resolve it by which comment reads more authoritative or was written later. A reason that cannot be made true is the signal that the exemption itself is wrong.
5. **Anti-dilution stop rule.** If the first scan returns a large number of hits, STOP and report the list instead of bulk-suppressing. Past some count the gate has stopped encoding a rule and started encoding a snapshot of the codebase; the move is to narrow to the highest-signal subset (or fix the offenders) first, then re-scan.
6. **Prove it can go red (mutation self-proof).** Inject one instance of the defect shape into a throwaway file, run the gate, show a non-zero exit naming that `file:line`; remove it, show `0`. A gate that has never been observed failing has not been tested for its job.
7. **Unit-test the gate against synthetic samples, not the real tree.** One positive sample per criterion, plus a negative sample that must NOT match, plus an empty-reason rejection. Test fixtures belong in `tmp_path`, so the gate's own suite never depends on repo state.
8. **Fail loud at the enforcement layer.** A tolerance key on the gate job or step (`continue-on-error` and friends) converts it into decoration. The gate exists precisely to be able to fail; do not give it an off switch.
9. **Never rename existing CI jobs to accommodate the new one.** Job names are branch-protection keys; a rename silently un-enforces the protection while looking untouched. Add the new job, then verify the pre-existing job names byte-for-byte before and after.
10. **Write the "why this gate exists" rationale as a comment on the gate itself**, not only in the PR: the comment must state the shape it catches and why the cheaper layer was insufficient. The next maintainer decides whether to keep it from that comment.

## Step 4 — Landing a gate that tripped the anti-dilution stop
The stop rule (Step 3.5) is the easy half. When the reported list comes back, adjudicate in this order — never by suppressing first:
1. **Bifurcate every hit into genuine incident vs legitimate site.** The discriminating question is: *if this fails, does the caller still receive a success-shaped result?* A swallowed best-effort cleanup is legitimate; a swallowed failure whose absence changes what the caller believes happened is an incident.
2. **Justify any narrowing by mechanism, and register the limit it introduces.** The wording must name the difference between the kept and dropped forms (e.g. "a `pass` body extinguishes an error path entirely; a `continue` is a per-item policy in a loop whose remaining iterations still execute"), never the hit count. Then record, in the gate's own comment, the class of defect the narrowed criterion will no longer catch. A narrowing with no registered limit is an unacknowledged hole. **Re-run the mutation self-proof afterwards**: a criterion change invalidates every proof taken before it, and a refinement that stops the gate biting the incident that motivated it is a failed refinement, not a landed one.
3. **Fix the incidents; do not suppress them.** Make the failure observable (log/warn) so the body no longer matches the criterion — the count drops by construction and no suppression is spent on it. Each fix carries its own RED test asserting the failure was previously invisible. A fix that makes an existing exemption obsolete MUST delete that exemption as part of the same change: leaving it behind preserves a comment asserting a state the code no longer has (the same defect class as a reason that is not true of the code), and it silently re-arms if the criterion ever matches that site again.
4. **A site that falls out of scope because of the narrowing MUST still be fixed if it is a genuine incident.** Narrowing a criterion is not licence to stop caring about a known failure; land the fix and say so explicitly, or the narrowing reads as concealment.
5. **Report the arithmetic so suppression cannot hide work**: `original = narrowed-away N + fixed M + suppressed K`, with all three terms enumerated. A reader must be able to verify that K absorbed only what was genuinely legitimate.
6. **A cluster of hits sharing one legitimate mechanism indicts the CRITERION, not the codebase.** When many candidates are legitimate for the *same* reason — above all when the repo documents that reason as a deliberate convention (a call style, an export surface, a loading order) — suppressing the cluster converts the gate into a snapshot of one codebase. Find the shape the criterion failed to model and teach it that shape instead. Success looks like a visible drop in the candidate count **with no loss of bite**, and it costs no suppressions. Reach for per-site suppression only after you have asked whether one mechanism explains the cluster.
7. **The refined criterion MUST NOT clear the finding that motivated the gate — check it against that exact case before landing.** State the boundary mechanistically: what the rule protects, and what it deliberately does not, with the reason that distinction exists. Then test-lock it by adding a unit sample built from the motivating finding's *shape* that MUST still fire — a rule you cannot fail on the case that spawned it is decoration. If the rule as you wrote it clears that case, the rule is wrong, not the case. **For an "export surface" refinement — an `__all__`, a public header, a barrel file — protect only symbols the module provides as its own member.** A bare foreign re-export kept in an export list for compatibility is not an owned member, and that padding is exactly where dead references hide; a criterion that honours the export list wholesale will clear the very sites it was built to find.
8. **A genuine incident kept under a transitional suppression needs an owner and a plan entry, not just a comment.** When the offending site cannot be fixed in this change (its file belongs to another workstream, or the fix needs a decision you do not own), the suppression reason MUST name it as a genuine defect — never blur it into the legitimate ones — and the fix MUST be registered where the owning workstream will read it. A comment alone is where findings go to be forgotten.

## Pitfalls
- **Security-gate config can fail OPEN, and fail-open looks exactly like a pass.** Scanner and linter configs are routinely read by a loader that silently ignores unknown keys: one misspelled key means no rules load, the scan matches nothing, and the job stays green while the hazard ships. Before trusting a security gate, confirm each config key is a real schema key (source, release notes, or a deliberate negative control), and state in the rationale whether an unsupported key would fail open or fail closed. Assume fail-open until proven otherwise.
- **"Not red" has more than one cause.** An unrunnable job, a job whose trigger never matches, and a job that genuinely passes all present identically as "not red". Confirm the new job actually executed on the intended event before concluding the gate works — a gate that never runs is decoration with a green light.
- **Widening a criterion "while we are here".** Every added pattern is a new false-positive surface. Land the narrow gate; let a real miss justify the next criterion, with its own incident behind it.
- **A gate with no documented escape hatch gets routed around.** Provide the suppression path *and* the reason requirement, so the pressure valve is visible instead of being `--no-verify`, a disabled job, or an excluded path.
- **Gating a symptom because the mechanism is hard to detect.** A gate that fires on a specific string from one incident catches that string forever and nothing else. If only the symptom is detectable, name that limit in the rationale comment.
- **Assuming a passing run means the criterion works.** A green result on a clean tree is consistent with a criterion that matches nothing at all. The mutation self-proof and the negative/positive unit samples are what separate "passing" from "working".
- **Convention documents absorbing prevention duty.** When asked to prevent a class, a paragraph in a conventions file feels cheaper than a gate and is skipped at review time. Check whether a mechanical check is possible before writing prose; prose is the fallback, not the default.
---

## Checkable Completion Criterion
- Gate script committed to `.githooks/` or repository CI configuration.
- Mutation probe executed demonstrating non-zero exit on injected defect and exit 0 on clean code.

---

## Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Writing a prose document in 01-Rules is enough to prevent recurrence."* | **Knowledge Evaporation**: Text documentation without automated execution is ignored by future agents. | Invariant: a rule that lives only in prose does not exist. All recurring defects MUST be converted into CI or pre-commit mechanical gates. |
| *"The gate script exited 0, so the check works."* | **False Green / No-Op Gate**: A buggy gate script that never fails lets regressions through silently. | Mutation Testing Invariant: MUST inject a deliberate defect and physically verify the gate turns RED (non-zero exit) before committing. |
| *"We can widen the gate pattern to catch other hypothetical bugs."* | **False Positive Explosion**: Overly broad regexes block valid engineering changes and get disabled by frustrated teams. | Land the narrow gate addressing the concrete reproduced incident; justify future widening only with new physical incidents. |
