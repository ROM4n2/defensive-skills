# 🏛️ Multi-Expert Swarm Audit Report: [Target Component]

**Date**: [YYYY-MM-DD]  
**Target Scope / PR**: [Component / Diff Path]  
**Seats Dispatched**: <list of active specialist seats>  
**Seats Skipped (why)**: <list of skipped seats and rationale>

---

### 🚨 Critical Findings (P0 / P1)
- **[Seat/Lens]** [CONFIRMED | PLAUSIBLE]: [Finding description with file:line reference and failure scenario]
  - *Impact*: [Data loss, deadlock, race condition, security risk, or broken flow]
  - *Verification Status*: [CONFIRMED via skeptic read | PLAUSIBLE]

### ⚠️ Improvements & Suggestions (P2)
- **[Seat/Lens]** [UNVERIFIED]: [Refactoring, guard clause, readability, or minor performance optimization]

### 💡 Consensus Action Plan & Patches
1. [Action 1: Immediate fix or migration script]
2. [Action 2: Code patch or error handling improvement]
3. [Action 3: Test addition covering the failure scenario]

### ♻️ Reuse Ladder Check
*(Required for every finding proposing new code or adding external dependencies)*
- **[Proposal]**: [Proposed addition]
  - *Ladder Assessment*: Already covered by [stdlib / in-repo module]? -> [Prefer reuse / New dependency justified because ...]
