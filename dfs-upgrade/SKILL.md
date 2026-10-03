---
name: dfs-upgrade
description: "Assess breaking changes and upgrade risk for a dependency. Use when upgrading a package version and you need to know what will break and in which files."
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dependencies, upgrade, breaking-changes, impact-analysis]
    related_skills: [dfs-plan, dfs-research, dfs-review]
---

# DFS-UPGRADE: Dependency Upgrade Risk & Impact Assessment

Systematically assess breaking changes, deprecation ladders, and local call-site impacts before modifying manifests, package lockfiles, or production imports.

## 🚨 The Verification-Before-Manifest Invariant (RFC 2119 MUST)
> **NO package manifest (`package.json`, `go.mod`, `Cargo.toml`, `requirements.txt`) or lockfile shall be edited before all intermediate breaking deltas are mapped against physical codebase call sites with binary verification.**
> Jumping major versions without auditing intermediate deprecations violates the Intermediate Hop Ladder.

---

## 🚪 This skill, or `/dfs-research` / `/dfs-plan`?

| | this skill | `/dfs-research` | `/dfs-plan` |
|---|---|---|---|
| The ask | **upgrade impact** — assess what breaks between version A and B | **investigate** — research an unfamiliar topic or library | **plan** — generate bite-sized implementation tasks |
| Output | an **impact report** (`templates/impact-report-template.md`) | a vault knowledge note | an `implementation_plan.md` |
| Feeds | `/dfs-plan` | knowledge vault | `/dfs-exec` |

---

## The 4-Phase Upgrade Protocol

```
  [Phase 1: Manifest & Version Span Discovery]
                      │
                      ▼
  [Phase 2: Upstream Changelog & Delta Catalog]
                      │
                      ▼
  [Phase 3: Codebase Call-Site Impact Mapping (file:line)]
                      │
                      ▼
  [Phase 4: Hop Migration Ladder & Relay to /dfs-plan]
```

### Phase 1: Package & Version Range Discovery
1. **Locate Manifest & Lockfile**:
   - Go: `go.mod` (inspect current version and indirect dependencies via `go list -m all`)
   - Node: `package.json` + `package-lock.json` / `pnpm-lock.yaml`
   - Python: `pyproject.toml` / `requirements.txt` / `poetry.lock`
   - Rust: `Cargo.toml` + `Cargo.lock`
2. **Determine Exact Version Span**:
   - Record installed baseline: `v_old`
   - Record target candidate: `v_new`
   - Enumerate all intermediate minor and major releases: `[v_old, ..., v_new]`
3. **Checkable Completion Criterion**:
   - An explicit tuple `(package, v_old, v_new, intermediate_releases)` is outputted to the user.

---

### Phase 2: Upstream Changelog & Breaking Delta Catalog
Extract all breaking changes across the entire span:
1. **Fetch Upstream Release Notes**:
   - Query repository `CHANGELOG.md`, GitHub Releases, or official migration guides.
   - Inspect release notes for *every* intermediate minor/major release, not just `v_new`.
2. **Catalog Breaking Deltas**:
   - Method/function renames, deletions, or export drops.
   - Signature mutations (added mandatory arguments, return type alterations, context propagation).
   - Configuration schema breaking migrations.
   - Behavioral or concurrency invariant alterations (e.g. sync to async, connection pooling defaults).
3. **Checkable Completion Criterion**:
   - Every identified breaking delta has a unique identifier (`BC-01`, `BC-02`, ...) with source release version citation.

---

### Phase 3: Codebase Impact Surface Mapping
Ground upstream deltas against concrete local workspace files:
1. **Symbol Search & Call-Site Audit**:
   - Execute symbol searches (ripgrep / AST inspection) across the repository.
   - Every detected call site MUST record an exact `file:line` pointer.
2. **Binary Zero-Hit Verification**:
   - If a breaking delta is deemed not used, capture the negative proof: verify that grep for the symbol across the codebase returns exit code 1 (zero hits). Never assume unused without grep evidence.
3. **Severity Classification**:
   - **HIGH**: Direct compilation/runtime breakage; removed API; altered parameter signature.
   - **MED**: Deprecated API functional today but removed in next hop; behavior/config shift.
   - **LOW**: Internal dependency transitive shift; documentation or optional typing adjustment.
4. **Checkable Completion Criterion**:
   - A complete mapping table exists where every entry is either a verified `file:line` pointer or documented zero-hit grep receipt.

---

### Phase 4: Upgrade Hop Strategy & Handover to /dfs-plan
1. **Enforce the Intermediate Hop Ladder**:
   - When jumping major versions, define intermediate hops to clear deprecations while tests remain green.
   - Hop sequence: `v_old ➔ v_intermediate (resolve deprecations) ➔ v_new (apply breaking changes)`.
2. **Generate Structured Impact Report**:
   - Load and follow `templates/impact-report-template.md`.
   - Record baseline test commands, impacted call sites, hop sequence, and regression safeguards.
3. **Relay to Downstream Skills**:
   - Prompt user: `Impact report ready. Proceed with implementation planning via /dfs-plan?`
4. **Checkable Completion Criterion**:
   - The impact report file is written and contains zero unpopulated placeholders.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Risk | Defensive Guard (MUST) |
|---|---|---|
| *"It's only a minor version bump, so I can skip checking changelogs."* | Semantic versioning violations occur frequently in real packages. | Fetch release notes for every version transition regardless of semver tier. |
| *"I'll bump the manifest first and see what compiler errors show up."* | Runtime semantic shifts and silent behavioral bugs produce no compiler errors. | Complete Phase 1-3 call-site analysis before modifying manifests or lockfiles. |
| *"I checked the latest v3.0 release notes, so I'm covered."* | Breaking changes and deprecation notices introduced in v2.x intermediate releases are missed. | Enumerate and inspect all releases across `[v_old, ..., v_new]`. |
| *"We probably don't use this deleted method."* | Guesswork causes production runtime panics. | Every delta must have a physical `file:line` pointer or a zero-hit grep receipt. |

---

## 🧪 Worked Example — Upgrading a Client Library

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
