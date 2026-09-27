# Release Checklist & Pre-Flight Gate (`templates/release-checklist.md`)

Use this checklist prior to tagging or publishing any production release.

## Pre-Flight Gate Checklist

- [ ] **1. Clean Working Tree**: `git status --porcelain` is empty (no uncommitted or untracked files).
- [ ] **2. Test Suite Green**: Full test suite passes without skipped tests or warnings (`go test ./...`, `pytest`, `ctest`).
- [ ] **3. Security & Dependency Audit**: Run vulnerability scanners (`govulncheck ./...`, `pip-audit`, `cargo audit`).
- [ ] **4. Backward Compatibility Check**: Public API signatures and serialized data structures remain backward-compatible (or major bump scheduled).
- [ ] **5. SemVer Bump Determinism**:
  - `PATCH`: Backward-compatible bug fixes.
  - `MINOR`: Backward-compatible new features.
  - `MAJOR`: Breaking changes or dropped support.
- [ ] **6. Changelog Generated**: `CHANGELOG.md` updated from Conventional Commits.
- [ ] **7. Rollback Plan Ready**: Verified rollback commands and database restore steps documented in release brief.
- [ ] **8. Tag Signature**: Annotated git tag created (`git tag -a vX.Y.Z -m "release: vX.Y.Z"`).
