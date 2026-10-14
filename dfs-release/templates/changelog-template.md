# Changelog Template (`templates/changelog-template.md`)

Standard Markdown shape for a release entry. **Adapt to the repo's convention** — if the repo
curates its changelog by hand (narrative entries, a "latest version" header, a README that keeps
only the last N summaries), treat the generator's output as *input* and edit by hand.

```markdown
## [v{version}] - {YYYY-MM-DD}

### 🚀 Features & Enhancements
- **{scope}**: {feat commit description} ([{commit_hash}]({commit_url}))

### 🐛 Bug Fixes & Hotfixes
- **{scope}**: {fix commit description} ([{commit_hash}]({commit_url}))

### ⚡ Performance & Refactoring
- **{scope}**: {perf/refactor description} ([{commit_hash}]({commit_url}))

### 🛡️ Security & Vulnerability Fixes
- **{scope}**: {security fix description} ([{commit_hash}]({commit_url}))

### ⚠️ Breaking Changes
- **{component}**: {breaking change + upgrade path, or "无" if none}

### ⚠️ Known Limitations
- {what this release does NOT fix} — especially anything a user could mistake for a defect or a
  speed-up. {If a metric moved for a non-obvious reason, say what it means (and what it does NOT
  mean) — otherwise the number gets quoted back as a promise.}

### 🔄 Rollback Procedure
Separate the axes — a single "revert the commit" is not a rollback plan:

1. **Artifact / code**: replace with `{previous_version}` package; note whether users *can*
   downgrade (mobile `versionCode` is one-way ⇒ uninstall/reinstall, and state the data loss).
2. **Data**: does this release move data (new directory / host / format)? `{manual step}`
   (+ the backup left behind at `{path}`); the old version may not find the new location.
3. **Schema**: additive (new column/index — old code still reads) vs destructive:
   `{migration_down_command}` + the restore path.
4. **Config / channel**: `{registry tag / distribution channel / secret rotation step}` (or N/A).
```

## Notes

- Every axis either has a command or an explicit "N/A because …" — an empty axis is a gap.
- Keep the entry's numbers **measured**, not inherited from a previous release (statistics go
  stale the moment the pipeline advances).
- Long prose belongs in the repo's own changelog; this template is the minimum shape that makes a
  release auditable after the fact.
