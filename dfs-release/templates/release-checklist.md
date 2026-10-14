# Release Checklist & Gates (`templates/release-checklist.md`)

Two gates, in order: **Pre-Flight** (before the tag) and **Post-Release** (after the pipeline).
A pushed tag is not a release — do not report "released" until the Post-Release gate passes.

## A. Pre-Flight Gate (before tagging)

- [ ] **1. Clean Working Tree**: `git status --porcelain` is empty (no uncommitted or untracked files).
- [ ] **2. Gates Green on THIS Commit**: run the project's test command(s) **and** its packaging/artifact smoke gate, on the exact commit that will be tagged. (Not "green last night"; not "green before the last commit".) Record the output **in full** — never pipe the pass/fail summary through `head`/`tail` (truncation hides failures and the pipe eats the exit code).
- [ ] **3. Gate Coverage Stated**: for the tagged commit, list each gate (local + CI jobs) and the surface it covers. A smoke job that builds/launches but does **not** run the suite covers no tests; N platform jobs each cover only their own platform.
- [ ] **4. Skip Policy**: record `N passed / M skipped` and **why** each group skips (platform-gated, env-gated, optional tool missing). An unexplained *increase* in skips is the signal — not skips per se.
- [ ] **5. Security & Dependency Audit** (if the ecosystem has one): `govulncheck ./...`, `pip-audit`, `cargo audit`. Record tool + version. No scanner available ⇒ write it down as an explicit gap.
- [ ] **6. Version Surfaces Enumerated**: list *every* place the version string appears (manifest, mobile `versionCode`, cache-buster / `CACHE_NAME`, UI version label, badges, docs) and confirm they all derive from **one source of truth** (ideally with a test pinning them to it). A missed surface fails silently.
- [ ] **7. Backward Compatibility Check**: public API signatures and serialized data stay compatible (or a MAJOR bump + migration notes are scheduled).
- [ ] **8. SemVer Bump Determinism**:
  - `PATCH`: backward-compatible bug fixes.
  - `MINOR`: backward-compatible new features.
  - `MAJOR`: breaking changes or dropped support.
- [ ] **9. Changelog Finalized**: the new entry is written (hand-curated where the repo curates it), and older entries/README "latest N" summaries are rotated per repo convention.
- [ ] **10. Known Limitations Written**: what this release does *not* fix — especially anything a user could mistake for a defect or a speed-up.
- [ ] **11. Rollback Plan Ready**, with all four axes separated: **artifact** (and whether users *can* downgrade — mobile `versionCode` is one-way), **data** (a data-location/format move is not undone by a code revert; document the manual step + the backup), **schema** (additive vs destructive down-migration), **config/channel**.
- [ ] **12. Tag Placement**: the tag is annotated (`git tag -a`), sits on the commit that carries the bump, and satisfies the repo's tag↔version guard if one exists.
- [ ] **13. Tag-Triggered Pipeline Started**: record the run id right away — Stage B needs it.

## B. Post-Release Gate (after the pipeline)

- [ ] **14. All Producer Jobs Green**: every platform/artifact job succeeded. Any red job ⇒ the publish step is usually **skipped**: the tag exists but no Release does — go to *Post-Tag Failure Recovery* in `SKILL.md`.
- [ ] **15. Published Assets Verified**: expected count, names, sizes, and signature/content gates (mobile signing, "archive contains X"). Three of four assets is a silent failure.
- [ ] **16. Release Notes Completed**: if the pipeline body is static boilerplate, append the version-specific sections (highlights + known limitations) via `gh release edit <tag> --notes-file <f>`, then re-read the body to confirm the append landed.
- [ ] **17. Repo Metadata Checked**: description / homepage / topics (tags) still describe the current product.
- [ ] **18. Release Recorded**: event written to the repo's coordination log (WORKMEMORY / CHANGELOG / ledger) and the final card reported to the user (version, tag → commit, asset table, open items).
