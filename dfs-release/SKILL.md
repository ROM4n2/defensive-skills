---
name: dfs-release
description: Draft semantic releases, changelogs, rollback plans, and verify published releases. Use when the user asks to cut a release, tag a version, write a changelog, or check whether a release actually shipped.
license: MIT
metadata:
  version: 0.3.0
  platforms: linux, macos, windows
  hermes:
    tags: [release, semver, changelog, rollback, deployment, git-tag, release-notes]
    related_skills: [dfs-pipeline, dfs-review, dfs-handoff]
---
# DFS-RELEASE: Semantic Versioning, Changelog, Rollback & Post-Release Gate

Standardize the production release lifecycle: pre-flight verification → version bump → changelog + rollback plan → tagging → **post-release verification**.

## [MUST] The Pre-Flight Gate Invariant (RFC 2119 MUST)
> **Verify, on the exact commit you are about to tag: `git status --porcelain` empty AND the project's own gates green (test suite + the artifact/packaging smoke gate, if the repo has one).**
> "Green on my machine last night" is not evidence; "green on **that commit**" is. Any commit that lands after the audit re-opens the audit.

### Gate coverage — know what each gate actually runs
A green gate certifies **only what it executes**. Before tagging, list the gates that will run on the tagged commit and mark which surface each one covers.

- An artifact-smoke job that builds + launches the binary but **does not run the test suite** certifies nothing about tests.
- N platform jobs each run their own platform's tests ⇒ a macOS-only test defect can hide behind three green platforms.
- ⇒ If the release pipeline is the **first** place a surface gets tested, you are using production as the test rig.

## The 5-Stage Release Lifecycle

```
  [Stage 1: Pre-Flight Conformance Audit & Workspace Hygiene]
                                │
                                ▼
  [Stage 2: Version Bump & Changelog Draft]
                                │
                                ▼
  [Stage 3: Release Notes & Rollback Brief]
                                │
                                ▼
  [Stage 4: Atomic Tagging & Push]
                                │
                                ▼
  [Stage 5: Post-Release Verification & Notes]   ← a pushed tag is not a release
```

---

## Stage 1: Pre-Flight Conformance Audit
1. Load `templates/release-checklist.md` via `read_file(path='templates/release-checklist.md')`.
2. Verify:
   - Clean git state: `git diff --stat` / `git status --porcelain` empty.
   - Project gates green **on this commit**: `go test -race ./...` / `pytest -q` / `cargo test`, plus the packaging/artifact smoke gate if the repo has one.
   - Security audit **if the ecosystem has a scanner** (`govulncheck` / `pip-audit` / `cargo audit`): record tool + version. A missing scanner is a **recorded gap**, not a pass.
3. **Enumerate the version surfaces.** Find *every* place the version lives (package manifest, mobile `versionCode`, cache-buster / `CACHE_NAME`, a UI "current version" label, shields/badges, docs). Confirm the repo has a **single source of truth** and a test pinning the copies to it. A missed surface is a *silent* failure class: the artifact ships claiming version A while the app reports B, and nothing turns red.
4. **Skips must be explained and baseline-compared** (report `N passed / M skipped`, and why each group skips). A blanket "0 skipped" rule gets ignored or lied about; an *unexplained increase* in skips is the real signal.
5. **Checkable Completion Criterion**: `git status --porcelain` empty; test + smoke commands exit 0 **and their summaries are recorded in full** (never `| head` / `| tail` the pass/fail summary — truncation hides failures and a pipe eats the upstream exit code); the version-surface list and skip counts are written down.

## Stage 2: Version Bump & Changelog Draft
1. Decide the bump from the commits since the last tag. `scripts/changelog_gen.py --version X.Y.Z` (dry-run by default) is a **drafting aid**, or read the log yourself.
2. **The generator is mechanical — hand-curated changelogs win.** If the repo's `CHANGELOG.md` has narrative entries, a "latest version" header line, or a README that keeps only the last N release summaries, treat the generated text as **input** and edit by hand. Never let the tool rewrite that file: it will clobber the header and the ordering convention. (`--write` is opt-in; `--version` is mandatory — a silent default writes garbage version headers.)
3. Bump the version in the single source of truth **and in every surface** from Stage 1.3.
4. **Checkable Completion Criterion**: all surfaces agree with the source of truth (ideally the repo's own test proves it); the new CHANGELOG entry is non-empty; the bump level matches the commit content — **any backward-incompatible change mandates MAJOR, no exceptions**.

## Stage 3: Release Notes & Rollback Brief
1. Load `templates/changelog-template.md` via `read_file(path='templates/changelog-template.md')`.
2. The new entry MUST carry **[MUST] Known Limitations** — what this release does *not* fix, especially anything a user could mistake for a defect or a speed-up. An undeclared known limitation becomes a support ticket or a false promise.
3. The **[MUST] Rollback** subsection MUST separate the independent axes — "revert the commit" is not a rollback plan:
   - **Code / artifact**: previous version's package, and whether users *can* downgrade (a mobile `versionCode` is one-way ⇒ uninstall/reinstall — say so).
   - **Data**: does this release *move* data (new directory / host / format)? Then the old version may not find it — document the manual step and the backup left behind.
   - **Schema**: additive (new column/index — old code still reads it) vs destructive (needs a down-migration **and** a restore path).
   - **Config / secrets / channel state** (registry tags, distribution channels).
4. **Checkable Completion Criterion**: the entry has non-empty Known-Limitations and Rollback subsections; every axis has a command or an explicit "N/A because …".

## Stage 4: Atomic Tagging & Push
1. Commit the release (`chore(release): vX.Y.Z` or the repo's convention).
2. **The tag MUST sit on the commit that carries the bump**, and MUST satisfy the repo's own tag↔version guard if it has one (e.g. a build-time assertion that `tag == "v" + APP_VERSION`). Use an annotated tag (`git tag -a`).
3. Push the branch and the tag, letting the tag trigger the release pipeline.
4. **Checkable Completion Criterion**: `git tag -l vX.Y.Z` shows the annotated tag; the tag commit is the bump commit; the tag-triggered pipeline run exists (**record its run id** — you will need it in Stage 5).

## Stage 5: Post-Release Verification & Notes — do NOT stop at the tag
1. **Report without blocking the session.** Make a **single** status check and report: run id, per-job conclusions, expected duration, and what happens next. Then hand control back — **never** burn the turn in a 20–40 minute `sleep` poll loop. The user will ask for the result when they want it.
2. **If any producer job went red, the publish job is usually skipped ⇒ no Release exists while the tag does.** Go to *Post-Tag Failure Recovery*.
3. **Verify the published assets**: count, names, sizes, and any signature/content gate (mobile signing, "the archive contains X"). Three assets out of four is a **silent** failure.
4. **Release notes**: the pipeline's release body is usually **static boilerplate** (it cannot read your CHANGELOG) ⇒ append the version-specific sections yourself:
   `gh release view <tag> --json body` → append 本次重点 (highlights) + known limitations → `gh release edit <tag> --notes-file <f>` → re-read to confirm. Then record this as a standing step **in the repo's own ops doc**, so the next releaser doesn't rediscover it.
5. **Repo metadata drifts too**: description / homepage / topics (tags) accumulate staleness for years — check them at release time (`gh repo view`).
6. **Record + report**: write the release event into the repo's coordination log (WORKMEMORY / CHANGELOG / release ledger) and give the user the final card: version, tag → commit, asset table, what remains open.

## Post-Tag Failure Recovery (tag exists, pipeline red)
1. **Do not re-run the red job to "get green", and do not re-tag blindly.** First classify: *flake* or *deterministic*? **Show the arithmetic.** (Example: a printed `1.1e+04` vs a measured `10658.46` is a 3.2% gap against a 3% tolerance — deterministic on that runner, so a retry is a coin flip **that also leaves the defect in the released commit**.)
2. Fix the root cause on a **new commit** — gate/test defects included: they are release blockers, not nuisances.
3. **Re-cutting a tag is destructive ⇒ explicit user approval.** It is safe only when all three hold, and you MUST state them out loud: ① no Release was published; ② nobody downloaded/installed that version; ③ no one-way counter (mobile `versionCode`) was distributed.
4. Re-cut: `git push origin :refs/tags/vX.Y.Z` → `git tag -d vX.Y.Z` → re-tag the fix commit → push the tag, then run Stage 5 again on the new run.
5. If the tag **was** consumed, do not re-cut — ship the fix as the next patch version.

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
