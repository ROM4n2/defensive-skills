# dfs-bootstrap — extended playbook (tier 3)

Loaded on demand by `dfs-bootstrap/SKILL.md`. These sections were moved here verbatim to keep the skill body inside the progressive-disclosure budget; the skill keeps the constraints and completion criteria, this file keeps the long-form detail.

---

### Phase 1: Security Git Hooks & .gitignore Protection (MUST)
1. Verify `.gitignore` contains all sensitive patterns (list MUST stay in sync with `REQUIRED_IGNORES` in `scripts/bootstrap.py` — it is the single source of truth):
   ```gitignore
   # Secrets & Local Configs
   config.yaml
   config.yml
   config.local.yaml
   .env
   .env.*
   *.env
   *.secret
   *.pem
   *.key
   *.local.json
   credentials.json
   ```
2. Install `.githooks/pre-commit` from `templates/githooks-pre-commit.sh` with **Unix (LF) line
   endings and no UTF-8 BOM** — a CRLF or BOM shebang stops git from spawning the hook
   (`cannot spawn .githooks/pre-commit`). Normalize the copied file to LF/no-BOM before committing:
   ```bash
   mkdir -p .githooks
   cp templates/githooks-pre-commit.sh .githooks/pre-commit   # first line MUST be exactly: #!/usr/bin/env bash
   chmod +x .githooks/pre-commit
   git config core.hooksPath .githooks
   # Note: For project-specific quality gates or recurring defect checks beyond base security, author them using /dfs-gate.
   ```
3. **Pin LF in `.gitattributes` — otherwise the hook re-breaks on fresh checkout.** On Windows
   `core.autocrlf=true` silently rewrites `pre-commit` to CRLF when git materializes it, undoing the
   normalization above. The repo must pin the endings, not just write LF once:
   ```gitattributes
   .githooks/** text eol=lf
   WORKMEMORY/** text eol=lf   # append-only UTF-8 log; keeps git diffs sane
   *.sh text eol=lf
   ```
   After adding `.gitattributes`, run `git add --renormalize .` so the stored blobs are LF.
4. The secret-scan regex set (OpenAI/AWS/GitHub/Google/Slack keys, JWT, PEM private-key blocks,
   keystore magic bytes) lives inside `templates/githooks-pre-commit.sh`; keep the installed hook and
   the template in sync.

---
