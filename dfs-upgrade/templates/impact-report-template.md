# Dependency Upgrade Impact Report Template (`templates/impact-report-template.md`)

Use this document template to record breaking changes, call-site impacts, migration hops, and verification baselines before executing a dependency upgrade.

```markdown
# 📦 Dependency Upgrade Impact Report: [Package Name] ([Current Version] ➔ [Target Version])

> **Target Package**: `package-name`
> **Upgrade Range**: `v1.2.0` ➔ `v2.0.0`
> **Ecosystem / Language**: [Go / Python / Node / Rust / Java]
> **Assessed Risk Level**: [HIGH - Breaking API / MEDIUM - Deprecations & Behavior Change / LOW - Patch/Minor]
> **Date Assessed**: YYYY-MM-DD
> **Status**: [DRAFT / APPROVED / READY_FOR_PLAN]

---

## 1. 变更全貌与风险总结 (Executive Summary & Risk Level)
- **Primary Motivation**: [Security patch / Performance improvement / Feature enablement / EOL deprecation]
- **Major Breaking Shifts**:
  - [Shift 1: e.g. Configuration schema migrated from flat flags to nested struct]
  - [Shift 2: e.g. Async callback API replaced with async/await Promises]
- **Cost of Skipping Hop**: [Why direct jump is dangerous, or confirmation that direct jump is safe]

---

## 2. 上游破坏性变更清单 (Breaking Delta Catalog)
*(Enumerate all intermediate breaking changes between current and target version)*

| ID | Version | Upstream Breaking Change | Migration Guidance / Codemod |
|---|---|---|---|
| BC-01 | v1.5.0 | Method `Client.Execute()` renamed to `Client.Do()` | Rename call sites; signature identical |
| BC-02 | v2.0.0 | Context parameter required as first argument | Pass `ctx context.Context` through callers |
| BC-03 | v2.0.0 | Dropped support for legacy TLS 1.0/1.1 | Verify upstream endpoints support TLS 1.2+ |

---

## 3. 本地代码影响面 (Codebase Call Sites & Impact Surface)
*(Every item MUST carry an exact `file:line` pointer verified against current workspace)*

| Call Site (`file:line`) | Symbol / API Used | Severity | Remediation Strategy |
|---|---|---|---|
| `internal/client/http.go:45` | `Client.Execute(req)` | HIGH | Change to `Client.Do(ctx, req)` |
| `pkg/auth/middleware.go:88` | `LegacyConfigOptions` | MED | Migrate to `NewConfigOptions` struct |

---

## 4. 梯级跳跃路径 (Version Hop Migration Ladder)
*(Do NOT skip major architectural hops if deprecations must be cleaned up first)*

1. **Hop 1: `v1.2.0` ➔ `v1.5.0`**
   - Clean up deprecated APIs while running existing test suite.
   - Verify zero deprecation warnings.
2. **Hop 2: `v1.5.0` ➔ `v2.0.0`**
   - Apply breaking signature updates and dependency lockfile bump.
   - Run full regression suite.

---

## 5. 验证与回归防护 (Test & Verification Gate)
- **Baseline Test Command**: `{baseline_test_cmd}`
- **Targeted Integration Tests**: `{targeted_test_cmd}`
- **Failure Indicators & Rollback Trigger**: [e.g. Any 5xx in smoke tests, memory spike > 20%]

---

## 6. 下游计划交接 (Relay to /dfs-plan)
- Plan Target: `docs/plans/YYYY-MM-DD-upgrade-{package}.md`
- Next Step: `Draft implementation plan via /dfs-plan`
```
