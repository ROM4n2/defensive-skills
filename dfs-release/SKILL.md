---
name: dfs-release
description: Draft semantic releases, changelogs, and rollback plans. Use when the user asks to cut a release, tag a version, or write a changelog.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [release, semver, changelog, rollback, deployment, git-tag]
    related_skills: [dfs-pipeline, dfs-review, dfs-handoff]
---

# DFS-RELEASE: Semantic Versioning, Changelog & Rollback Gate

Standardize the production software release lifecycle through automated Conventional Commit aggregation, Semantic Versioning (SemVer), pre-flight quality verification, and deterministic rollback plans.

## 🚨 The Pre-Flight Gate Invariant (RFC 2119 MUST)
> **Always verify that `git status --porcelain` is empty and test suites pass 100% green before cutting a release tag or push.**
> Ensure the Pre-Flight Gate checklist is fully satisfied prior to publishing. Cutting releases with uncommitted changes or failing tests is strictly prohibited.

---

## The 4-Stage Release Lifecycle

```
  [Stage 1: Pre-Flight Conformance Audit & Workspace Hygiene]
                                │
                                ▼
  [Stage 2: Conventional Commit Aggregation & SemVer Bump]
                                │
                                ▼
  [Stage 3: Rollback Brief & Changelog Finalization]
                                │
                                ▼
  [Stage 4: Atomic Release Tagging & Verification Receipts]
```

---

## The 4-Stage Release Procedure

### Stage 1: Pre-Flight Conformance Audit
1. Load `templates/release-checklist.md` via `read_file(path='templates/release-checklist.md')`.
2. Verify:
   - Clean git state: `git diff --stat` and `git status --porcelain` return empty.
   - All tests green: `go test -race ./...` / `pytest -q` / `cargo test`.
   - Security audit: `govulncheck ./...` / `pip-audit` / `cargo audit`.
3. **Checkable Completion Criterion**:
   - `git status --porcelain` returns 0 lines; test command exit code 0; security audit exit code 0.

### Stage 2: Automated Changelog Generation & SemVer Bump
1. Execute the deterministic changelog runner:
   ```bash
   python scripts/changelog_gen.py --version X.Y.Z
   ```
   Or inspect output in dry-run mode: `python scripts/changelog_gen.py --dry-run`.
2. The tool parses Conventional Commits since the last tag and suggests the appropriate SemVer bump (MAJOR, MINOR, or PATCH).
3. **Checkable Completion Criterion**:
   - `changelog_gen.py` produces non-empty release notes; SemVer version bump verified against breaking change presence.

### Stage 3: Rollback Brief & Changelog Finalization
1. Load `templates/changelog-template.md` via `read_file(path='templates/changelog-template.md')`.
2. Ensure the generated section in `CHANGELOG.md` explicitly documents the **Rollback Procedure** (binary downgrade, rollback git commit, and migration down-steps).
3. **Checkable Completion Criterion**:
   - `CHANGELOG.md` updated with new version section containing explicit Rollback Procedure subsection.

### Stage 4: Atomic Release Tagging
1. Commit changelog and version files:
   ```bash
   git add CHANGELOG.md
   git commit -m "chore(release): vX.Y.Z"
   ```
2. Tag with annotated message:
   ```bash
   git tag -a vX.Y.Z -m "release: vX.Y.Z"
   ```
3. Output the release summary card to user.
4. **Checkable Completion Criterion**:
   - Annotated git tag exists in `git tag -l vX.Y.Z`; git working tree clean after commit and tag.

---

## 🚫 Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Tests failed on a flaky integration test, but core unit tests passed so I can release."* | **Production Regression Escape**: Releasing on broken pipelines leaks real defects disguised as flakes. | All pre-flight tests MUST pass with exit code 0 before tagging. No exceptions. |
| *"There are uncommitted local edits, but they don't affect this version release."* | **Tainted Release Artifacts**: Tags point to commits that don't match the built binaries or author state. | `git status --porcelain` MUST be completely empty before tagging. |
| *"The change feels minor, so I will bump PATCH even though an API parameter was removed."* | **Downstream Consumer Breakage**: Violating SemVer semantics breaks client builds unexpectedly. | Any backward-incompatible API change strictly mandates a MAJOR bump. |
| *"Rollback is obvious (just revert git commit), so I won't write rollback steps in changelog."* | **Prolonged Outage Recovery**: During an active incident, operators need exact binary downgrade commands without guessing. | Every release section MUST document explicit binary and schema rollback commands. |
