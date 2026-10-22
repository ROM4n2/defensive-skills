---
name: dfs-incident
description: Triage a production incident and draft a blameless postmortem. Use when a service is down, degraded, or the user asks for an incident review.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  disable-model-invocation: 'true'
  hermes:
    tags: [incident-response, postmortem, sre, blameless, 5-whys, root-cause]
    related_skills: [dfs-debug, dfs-save, dfs-team]
---
# DFS-INCIDENT: Production Incident Response & Blameless Postmortem

> **Invocation — explicit only.** This skill carries `disable-model-invocation: "true"` under
> `metadata`, the Agent Skills extension slot, which no harness enforces as a hard switch
> (Claude Code honored it only at the old top-level location; Hermes never implemented it), so
> the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. When you need to know which harness actually honors a given frontmatter key — and what
> to use in its place where one is ignored — read `dfs/references/harness-field-mapping.md`.

Coordinate rapid incident containment (mitigation before analysis), build forensic event timelines, uncover systemic root causes with 5-Whys, and archive blameless postmortems to prevent repeat failures.

## [MUST] The Containment-First Iron Rule (RFC 2119 MUST)
> **In an active production outage, STOP debugging and prioritize IMMEDIATE CONTAINMENT.**
> Rollback, shed load, toggle feature flags, or cut traffic first. Perform deep forensic root-cause analysis ONLY after user service is restored.

---

## The 4-Phase Incident Lifecycle

```
  [Phase 1: Rapid Triage & Blast Radius Assessment]
                         │
                         ▼
  [Phase 2: Immediate Containment (Stop the Bleeding)]
                         │
                         ▼
  [Phase 3: Forensic Timeline & 5-Whys Deep Root Cause]
                         │
                         ▼
  [Phase 4: Blameless Postmortem & Action Item Lock (/dfs-save)]
```

### Phase 1: Rapid Triage
1. Identify severity tier:
   - **P0**: Core service down, data corruption risk, total outage.
   - **P1**: Significant feature degraded, latency spike > 5x baseline.
   - **P2**: Non-critical subsystem failing, internal admin tool outage.
2. Freeze deployments and non-essential background jobs immediately.
3. **Checkable Completion Criterion**:
   - Severity tier tagged (P0/P1/P2); incident channel opened; freeze order issued.

### Phase 2: Immediate Containment
1. Apply the fastest mitigation tactic:
   - Rollback recent deployment: `git revert` or deploy prior container tag.
   - Circuit breaker / feature flag toggle to disable faulty codepath.
   - Rate limiting / shed load on upstream gateway.
2. Confirm metric recovery (latency, error rate, saturation return to SLO baseline).
3. **Checkable Completion Criterion**:
   - Error budget drain stopped; user traffic restored to healthy baseline SLO.

### Phase 3: Forensic Timeline Reconstruction
1. Capture all relevant error snapshots, telemetry traces, and database logs before log retention windows expire.
2. Construct minute-by-minute timeline linking deployment actions to anomaly curves.
3. **Checkable Completion Criterion**:
   - Timeline assembled with concrete timestamp citations ($T_0, T_{detect}, T_{mitigate}$); log receipts preserved.

### Phase 4: Blameless Postmortem Archival
1. Load `templates/postmortem-template.md` via `read_file(path='templates/postmortem-template.md')`.
2. Conduct 5-Whys causal analysis (focus on systemic flaws and missing guardrails, never on human blame).
3. Record preventative Action Items with owners and deadlines.
4. Convert systemic failure modes into permanent automated CI / pre-commit blockers via `/dfs-gate` (enforcing mutation test verification).
5. Auto-ingest defensive takeaways into `01-Rules/` or draft to `99-Inbox/` via `dfs-save`.
5. **Checkable Completion Criterion**:
   - Postmortem markdown file written to `docs/postmortems/YYYY-MM-DD-<incident>.md`; at least 1 preventative rule draft generated via `dfs-save`.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Let me attach a debugger or inspect stack traces while users see 500 errors."* | **Prolonged MTTR & Error Budget Drain**: Root-cause hunting during outages wastes precious recovery minutes. | Containment first: rollback or flip feature flags immediately before any forensic code analysis. |
| *"The incident was caused by developer X forgetting a parameter, so we'll remind the team."* | **Blame Trap & Repeat Outages**: Blaming individuals ignores systemic absence of CI linting/type checks. | Blameless rule: 5-Whys must trace to missing automated tests, gates, or architectural guardrails. |
| *"Service metrics look okay now, so we can skip the written postmortem."* | **Knowledge Evaporation**: Unrecorded incidents repeat identically in future sprints. | Postmortem archival in `docs/postmortems/` is strictly mandatory for all P0 and P1 events. |
| *"We will prevent this by being more careful in the future."* | **Zero Defense Invariant**: Good intentions are not engineering controls. | Action items MUST consist of code gates, automated tests, or monitoring alerts with owners. |
