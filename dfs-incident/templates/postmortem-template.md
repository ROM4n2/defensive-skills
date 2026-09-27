# Blameless Postmortem Template (`templates/postmortem-template.md`)

Use this document template to conduct systematic, blameless root-cause analysis and action item tracking following any production outage or degradation.

```markdown
# 🚨 Postmortem: [Incident Summary Title]

> **Date of Incident**: YYYY-MM-DD
> **Severity Tier**: [P0 - Outage / P1 - Major Degradation / P2 - Minor Impact]
> **Total Outage Duration**: [e.g. 42 minutes]
> **Incident Commander / Lead**: [Name / Subagent]
> **Status**: [Action Items In Progress / Resolved / Verified]

---

## 1. 业务与用户影响 (User & Business Impact)
- **Impacted Systems**: [e.g. Payment Gateway, User Authentication]
- **User Impact Ratio**: [e.g. 15% of checkout requests failed with HTTP 504]
- **Financial / Operational Loss**: [e.g. ~350 orders delayed]

---

## 2. 故障时间线 (Chronological Timeline)
*(All timestamps in UTC+8 / Local Time)*
- **14:02** - Deploy commit `abc1234` containing new connection pool settings.
- **14:07** - Monitoring alerts trigger: p99 latency spikes from 45ms to 3,200ms.
- **14:12** - Incident declared (P1). Incident commander pauses all deployments.
- **14:18** - Containment applied: Traffic rerouted via canary bypass / feature flag disabled.
- **14:26** - Service metrics recover to baseline.
- **14:44** - Post-incident stability verified.

---

## 3. 根因 5-Whys 分析 (Root Cause Analysis - 5 Whys)
1. *Why did checkout fail?* Database connection pool exhausted.
2. *Why was it exhausted?* Goroutines leaked on unhandled HTTP context cancellations.
3. *Why did context leak?* Missing `defer cancel()` and timeout propagation in downstream RPC client.
4. *Why wasn't this caught in staging?* Load test scripts did not simulate abrupt client disconnects.
5. *Why was there no defensive guard?* Missing bounded worker pool and circuit breaker on upstream gateway.

---

## 4. 经验教训与防错规则 (Lessons Learned & Anti-Recurrence)
### What Went Well
- Fast detection: Prometheus alert fired within 5 minutes of latency degradation.
- Clean rollback: Feature flag toggled immediately without full cluster redeployment.

### Where We Got Lucky
- Occurred during mid-day monitoring window rather than off-peak overnight hours.

---

## 5. 改进防线与 Action Items (Preventative Action Items)
| Item | Description | Type | Owner | Target Date | Status |
|---|---|---|---|---|---|
| 1 | Add connection pool exhaustion alert at 80% saturation | Detection | SRE | YYYY-MM-DD | Open |
| 2 | Enforce mandatory `context.WithTimeout` on all outbound RPCs | Prevention | Backend | YYYY-MM-DD | Open |
| 3 | Ingest defensive rule into `01-Rules/CONCURRENCY-PATTERNS.md` | Knowledge | Vault | YYYY-MM-DD | Open |
```
