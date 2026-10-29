# dfs-upgrade — extended playbook (tier 3)

Loaded on demand by `dfs-upgrade/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

## [NOTE] Worked Example — Upgrading a Client Library

Input: *"We need to upgrade github.com/alice/httpclient from v1.3.0 to v2.1.0."*

1. **Discovery**: Current `v1.3.0`, target `v2.1.0`. Intermediate span: `[v1.4.0, v2.0.0, v2.1.0]`.
2. **Changelog Delta**:
   - `BC-01` (`v1.4.0`): Added `httpclient.DoWithContext(ctx, req)` and deprecated `httpclient.Do(req)`.
   - `BC-02` (`v2.0.0`): Removed `httpclient.Do(req)`. `Client` struct constructor requires options builder.
3. **Impact Surface**:
   - `internal/gateway/fetcher.go:34`: Uses deprecated `Do(req)` (HIGH).
   - `pkg/auth/client.go:82`: Uses raw `Client{}` literal instead of options builder (HIGH).
   - Zero-hit receipt: `rg 'LegacyTransport'` returned exit 1 (not used).
4. **Hop Strategy**:
   - Hop 1: Bump to `v1.4.0`, switch all call sites to `DoWithContext`, verify tests pass.
   - Hop 2: Bump to `v2.1.0`, adopt options builder, verify all tests pass.
5. **Output**: Record findings in `templates/impact-report-template.md` and hand over to `/dfs-plan`.
