# [NOTE] Multi-Expert Swarm Audit Report: [Target Component]

**Date**: [YYYY-MM-DD]  
**Target Scope / PR**: [Component / Diff Path]  
**Seats Dispatched**: <list of active specialist seats>  
**Seats Skipped (MUST — artifact evidence, not "not relevant")**: <seat>: <artifact class absent from the target>
**Findings**: <M> after collapsing <N> raw seat findings — M must be < N
**Read scope**: <per seat: files opened + line ranges; mark outside-target reads and give the reason>

---

### [NOTE] Critical Findings (P0 / P1)
- **[Seat/Lens]** [CONFIRMED | PLAUSIBLE]: [Finding description with file:line reference and failure scenario]
  - *Impact*: [Data loss, deadlock, race condition, security risk, or broken flow]
  - *Verification Status*: [CONFIRMED via skeptic read | PLAUSIBLE]

### [NOTE] Improvements & Suggestions (P2)
- **[Seat/Lens]** [UNVERIFIED]: [Refactoring, guard clause, readability, or minor performance optimization]

### [NOTE] Consensus Action Plan & Patches
1. [Action 1: Immediate fix or migration script]
2. [Action 2: Code patch or error handling improvement]
3. [Action 3: Test addition covering the failure scenario]

### [NOTE] Reuse Ladder Check
*(Required for every finding proposing new code or adding external dependencies)*
- **[Proposal]**: [Proposed addition]
  - *Ladder Assessment*: Already covered by [stdlib / in-repo module]? -> [Prefer reuse / New dependency justified because ...]
