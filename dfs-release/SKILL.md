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

## 🚨 The Pre-Flight Gate Invariant (HARD GATE)
> Always verify that `git status --porcelain` is empty and test suites pass 100% green before cutting a release tag or push.
> Ensure the Pre-Flight Gate checklist is fully satisfied prior to publishing.

---

## The 4-Stage Release Procedure

### Stage 1: Pre-Flight Conformance Audit
1. Load `templates/release-checklist.md` via `read_file(path='templates/release-checklist.md')`.
2. Verify:
   - Clean git state: `git diff --stat` and `git status --porcelain` return empty.
   - All tests green: `go test -race ./...` / `pytest -q` / `cargo test`.
   - Security audit: `govulncheck ./...` / `pip-audit` / `cargo audit`.

### Stage 2: Automated Changelog Generation & SemVer Bump
Execute the deterministic changelog runner:
```bash
python scripts/changelog_gen.py --version X.Y.Z
```
Or inspect output in dry-run mode: `python scripts/changelog_gen.py --dry-run`.
The tool parses Conventional Commits since the last tag and suggests the appropriate SemVer bump (MAJOR, MINOR, or PATCH).

### Stage 3: Rollback Brief & Changelog Finalization
1. Load `templates/changelog-template.md` via `read_file(path='templates/changelog-template.md')`.
2. Ensure the generated section in `CHANGELOG.md` explicitly documents the **Rollback Procedure** (binary downgrade, rollback git commit, and migration down-steps).

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
