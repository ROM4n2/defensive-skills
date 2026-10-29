---
name: dfs-release
description: Draft semantic releases, changelogs, rollback plans, and verify published releases. Use when the user asks to cut a release, tag a version, write a changelog, or check whether a release actually shipped.
license: MIT
metadata:
  version: 0.4.0
  platforms: linux, macos, windows
  hermes:
    tags:
    - release
    - semver
    - changelog
    - rollback
    - deployment
    - git-tag
    - release-notes
    related_skills:
    - dfs-pipeline
    - dfs-review
    - dfs-handoff
---


# DFS-RELEASE: Semantic Versioning, Changelog, Rollback & Post-Release Gate

Standardize the production release lifecycle: pre-flight verification -> version bump -> changelog + rollback plan -> tagging -> **post-release verification**.

## The Pre-Flight Gate Invariant (RFC 2119 MUST)
> Verify on the exact commit you tag: `git status --porcelain` is empty AND all project gates are green. A green gate certifies ONLY what it executes (e.g. smoke != test suite). Any commit after audit re-opens audit.

---

## The 5-Stage Release Lifecycle

`Stage 1: Pre-Flight Audit` -> `Stage 2: Version Bump` -> `Stage 3: Notes & Rollback` -> `Stage 4: Tag & Push` -> `Stage 5: Post-Release Verification`

---

## Stage 1: Pre-Flight Conformance Audit
1. Load `templates/release-checklist.md` Section A via `read_file(path='templates/release-checklist.md')`.
2. **Exact CI Command & Target-Set Parity (MUST)**: Copy exact test/linter invocations and directories from `.github/workflows/*.yml`. Verify clean git state, test gates, and security audit.
3. **Enumerate version surfaces**: Confirm all surfaces derive from a single source of truth pinned by tests.
4. **Baseline skip comparison**: Record `N passed / M skipped` with skip reasons; record full execution summaries.

## Stage 2: Version Bump & Changelog Draft
1. Inspect commits since last tag. Use `scripts/changelog_gen.py --version X.Y.Z` as an aid, but curate CHANGELOG by hand.
2. Bump version in single source of truth and all surfaces. Breaking changes strictly mandate MAJOR.

## Stage 3: Release Notes & Rollback Brief
1. Load `templates/changelog-template.md` via `read_file(path='templates/changelog-template.md')`.
2. Must document **Known Limitations** (what is not fixed) and **Rollback Brief** across four independent axes: artifact downgrade, data location/format, schema migrations, and config/channel state.

## Stage 4: Atomic Tagging & Push
1. Commit bump (`chore(release): vX.Y.Z`). Annotated tag (`git tag -a`) MUST sit on the bump commit.
2. Push branch and tag; capture pipeline run ID.

## Stage 5: Post-Release Verification & Notes — do NOT stop at the tag
1. **Report without blocking the session.** Make a **single** status check and report: run id, per-job conclusions, expected duration, and what happens next. Then hand control back — **never** burn the turn in a 20–40 minute `sleep` poll loop. The user will ask for the result when they want it.
2. **If any producer job went red, the publish job is usually skipped ⇒ no Release exists while the tag does.** Go to *Post-Tag Failure Recovery*.
3. **Verify the published assets**: count, names, sizes, and any signature/content gate (mobile signing, "the archive contains X"). Three assets out of four is a **silent** failure.
4. **Release notes**: the pipeline's release body is usually **static boilerplate** (it cannot read your CHANGELOG) ⇒ append the version-specific sections yourself:
   `gh release view <tag> --json body` → append 本次重点 (highlights) + known limitations → `gh release edit <tag> --notes-file <f>` → re-read to confirm. Then record this as a standing step **in the repo's own ops doc**, so the next releaser doesn't rediscover it.
5. **Repo Metadata & Declaration-Implementation Reconciliation (MUST)**: Audit README.md and architecture docs against physical codebase reality (recompute LOC, package/module counts, test counts, CLI flags, feature tables); purge declared-but-unbuilt or built-but-undocumented drift before closing release. Check description/homepage/topics via `gh repo view`.
6. **Record + report**: write the release event into the repo's coordination log (WORKMEMORY / CHANGELOG / release ledger) and give the user the final card: version, tag → commit, asset table, what remains open.

## Post-Tag Failure Recovery
If a pipeline job fails after tagging, do NOT re-run blindly to "get green" and do NOT re-cut without mathematical flake/deterministic proof and explicit user approval. Follow the operational runbook in [templates/release-checklist.md](templates/release-checklist.md) Section C.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"Tests failed on a flaky integration test, but core unit tests passed so I can release."* | **Production Regression Escape**: Releasing on broken pipelines leaks real defects disguised as flakes. | All pre-flight tests MUST pass with exit code 0 before tagging. No exceptions. |
| *"There are uncommitted local edits, but they don't affect this version release."* | **Tainted Release Artifacts**: Tags point to commits that don't match the built binaries or author state. | `git status --porcelain` MUST be completely empty before tagging. |
| *"The change feels minor, so I will bump PATCH even though an API parameter was removed."* | **Downstream Consumer Breakage**: Violating SemVer semantics breaks client builds unexpectedly. | Any backward-incompatible API change strictly mandates a MAJOR bump. |
| *"Rollback is obvious (just revert git commit), so I won't write rollback steps in changelog."* | **Prolonged Outage Recovery**: During an active incident, operators need exact binary downgrade commands without guessing. | Every release section MUST document explicit artifact / data / schema rollback steps (Stage 3.3). |
| *"Three platforms are green, ship it."* | **Per-platform blind spot**: the fourth platform's tests never ran. | Know each job's coverage (Gate coverage rule); a red platform means fix, not skip. |
| *"The pipeline's release body is fine."* | **Misleading release notes**: users read them as the contract, and a missing asset goes unnoticed. | Stage 5.3/5.4: verify assets and append the version-specific sections. |
| *"Tagged it — the pipeline will handle the rest."* | **Tag ≠ Release**: a red producer job skips the publish job, leaving an orphan tag. | Stage 5.2 + Post-Tag Failure Recovery. |
| *"I'll poll until the build finishes so I can report the final result."* | **Session hostage**: 20–40 min of the user's turn consumed by waiting. | Single status check + report + hand back; the user asks for the final table. |

---

## Checkable Completion Criterion
- Tagged commit verified on exact HEAD with `git status --porcelain` empty and pre-flight gates exit 0.
- Release notes published with highlights, known limitations, and 4-axis rollback brief.
- Published release assets verified (count, names, sizes non-zero) and CI pipeline green.
