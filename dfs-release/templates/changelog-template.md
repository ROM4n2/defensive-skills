# Changelog Template (`templates/changelog-template.md`)

Standard Markdown template for version release notes generated from Conventional Commits.

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
- **{component}**: {detailed description of breaking change and upgrade path}

### 🔄 Rollback Procedure
1. Revert deployment image/binary: `{rollback_command}`
2. Git rollback target: `git checkout v{previous_version}`
3. Database migration rollback: `{migration_down_command}` (if applicable)
```
