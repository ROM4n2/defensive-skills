---
name: dfs-incident
description: Triage production incidents and draft blameless postmortems.
disable-model-invocation: true
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [incident-response, postmortem, sre, blameless, 5-whys, root-cause]
    related_skills: [dfs-debug, dfs-save, dfs-team]
---

# DFS-INCIDENT: Production Incident Response & Blameless Postmortem

> **Invocation — explicit only.** `disable-model-invocation: true` is honored by Claude Code and ignored
> elsewhere, so the same rule is stated here in the file itself: do not auto-select this skill
> on your own — wait until the user asks for it, or until an already-running DFS skill routes
> here. (See `dfs/references/harness-field-mapping.md`.)

Coordinate rapid incident containment (mitigation before analysis), build forensic event timelines, uncover systemic root causes with 5-Whys, and archive blameless postmortems to prevent repeat failures.

## 🚨 The Containment-First Iron Rule (HARD GATE)
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

### Phase 2: Immediate Containment
1. Apply the fastest mitigation tactic:
   - Rollback recent deployment: `git revert` or deploy prior container tag.
   - Circuit breaker / feature flag toggle to disable faulty codepath.
   - Rate limiting / shed load on upstream gateway.
2. Confirm metric recovery (latency, error rate, saturation return to SLO baseline).

### Phase 3: Forensic Timeline Reconstruction
1. Capture all relevant error snapshots, telemetry traces, and database logs before log retention windows expire.
2. Construct minute-by-minute timeline linking deployment actions to anomaly curves.

### Phase 4: Blameless Postmortem Archival
1. Load `templates/postmortem-template.md` via `read_file(path='templates/postmortem-template.md')`.
2. Conduct 5-Whys causal analysis (focus on systemic flaws and missing guardrails, never on human blame).
3. Record preventative Action Items with owners and deadlines.
4. Auto-ingest defensive takeaways into `01-Rules/` or draft to `99-Inbox/` via `dfs-save`.
