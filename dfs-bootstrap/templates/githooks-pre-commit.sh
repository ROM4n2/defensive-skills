#!/usr/bin/env bash
# Git Pre-commit: secret scan + repository gates, run in parallel.
# dfs-bootstrap-hook-version: 5
#
# The version marker is load-bearing: `bootstrap.py` upgrades a hook carrying an older marker and
# preserves (never overwrites) a project-owned hook carrying none. Bump it on every behaviour change.
#
# CHAINING (MUST): this hook delegates to the upstream hook when one exists, and its failure aborts
# the commit. Without this, installing our hook silently disables every check the repository already
# had (`make test`, lint, license headers) — a gate that turns off other gates is worse than no gate.
#
# PARALLELISM (MUST): the repository gates below are independent and run concurrently. Sequentially a
# 490-module repo spends ~8.4 s in the structure gate alone, and a pre-commit that slow gets bypassed
# with `--no-verify`.
set -u

# --- upstream chain ---------------------------------------------------------
# `core.hooksPath` points at this directory, so the upstream hook's original location is discovered
# from the two conventional places. DFS_UPSTREAM_HOOKS overrides for unusual layouts.
chain_upstream() {
    local self candidate
    self="$(basename "$0")"
    local candidates=()
    [ -n "${DFS_UPSTREAM_HOOKS:-}" ] && candidates+=("$DFS_UPSTREAM_HOOKS/$self")
    candidates+=(".githooks/$self" ".git/hooks/$self")
    for candidate in "${candidates[@]}"; do
        [ -f "$candidate" ] && [ -x "$candidate" ] || continue
        # Never recurse into ourselves.
        if [ "$(cd "$(dirname "$candidate")" 2>/dev/null && pwd -P)/$(basename "$candidate")" = \
             "$(cd "$(dirname "$0")" 2>/dev/null && pwd -P)/$self" ]; then
            continue
        fi
        if ! "$candidate" "$@"; then
            printf '[CHAIN] upstream hook failed: %s\n' "$candidate" >&2
            exit 1
        fi
        printf '[CHAIN] upstream hook passed: %s\n' "$candidate" >&2
        return 0
    done
    return 0
}

chain_upstream "$@"
# --- end upstream chain -----------------------------------------------------

PRAGMA='git:allow-secret'

# One `git grep --cached` over the whole index replaces one `git show` per staged file. Measured on a
# 1004-file repo: 3.6 s for the whole index versus 8.8 s for 300 files with the per-file form, because
# the per-file form is O(N) process spawns.
PATTERNS='OpenAI/Anthropic key|sk-[A-Za-z0-9]{20,}
AWS Access Key ID|AKIA[A-Z0-9]{16}
GitHub PAT (classic)|ghp_[A-Za-z0-9]{36}
GitHub PAT (fine-grained)|github_pat_[A-Za-z0-9_]{20,}
Google API Key|AIza[A-Za-z0-9_-]{30,}
Slack token|xox[baprs]-[A-Za-z0-9-]{10,}
JWT|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}
PEM private key|-----BEGIN [A-Z ]*PRIVATE KEY-----
Java keystore base64 (JKS)|/u3\+7Q
Java keystore base64 (JCEKS)|zs7[O]z'

GREP_ARGS=()
while IFS='|' read -r label regex; do
    [ -n "${regex:-}" ] || continue
    GREP_ARGS+=(-e "$regex")
done <<< "$PATTERNS"

STAGED="$(git diff --cached --name-only --diff-filter=ACMR)"

# --- check 1: sensitive filenames -------------------------------------------
NAME_HITS=""
while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
        *.example|*.sample|*.template) continue ;;
    esac
    case "$path" in
        .env|*/.env|*.secret|*credentials*|*.pem|*.key|*id_rsa*|*id_ed25519*|\
        *.jks|*.jks.b64|*.keystore|*.p12|*.pfx|*signing.properties|*keystore.properties)
            NAME_HITS="${NAME_HITS}${path}"$'\n'
            ;;
    esac
done <<< "$STAGED"

# --- check 2: secret content, one pass over the index ------------------------
CONTENT_HITS=""
if [ "${#GREP_ARGS[@]}" -gt 0 ]; then
    CONTENT_HITS="$(git grep --cached -nIE "${GREP_ARGS[@]}" 2>/dev/null | grep -vF -- "$PRAGMA" || true)"
fi

# --- check 3: CRLF under .githooks/ (the only check needing worktree bytes) --
# `text eol=lf` files are normalised by `git add`, so scanning the index blob for CRLF is dead code.
# A CRLF script under .githooks/ cannot be executed by bash, so that narrow case reads the worktree.
EOL_HITS=""
while IFS= read -r path; do
    case "$path" in
        .githooks/*)
            if [ -f "$path" ] && [ "$(tr -cd '\r' < "$path" | wc -c)" -gt 0 ]; then
                EOL_HITS="${EOL_HITS}${path}"$'\n'
            fi
            ;;
    esac
done <<< "$STAGED"

if [ -n "$NAME_HITS" ] || [ -n "$CONTENT_HITS" ] || [ -n "$EOL_HITS" ]; then
    echo "[SECURITY ALERT] 发现潜在敏感凭据、敏感文件或不可执行钩子，提交已被拦截：" >&2
    if [ -n "$NAME_HITS" ]; then
        while IFS= read -r path; do
            [ -n "$path" ] && printf '   - [NAME] %s (敏感配置文件不应入库)\n' "$path" >&2
        done <<< "$NAME_HITS"
    fi
    if [ -n "$EOL_HITS" ]; then
        while IFS= read -r path; do
            [ -n "$path" ] && printf '   - [EOL] %s (工作区为 CRLF，bash 无法执行；需 LF + 无 BOM)\n' "$path" >&2
        done <<< "$EOL_HITS"
    fi
    if [ -n "$CONTENT_HITS" ]; then
        while IFS= read -r line; do
            [ -n "$line" ] || continue
            loc="${line%%:*}"
            rest="${line#*:}"
            lineno="${rest%%:*}"
            payload="${rest#*:}"
            label="secret"
            while IFS='|' read -r cand_label cand_regex; do
                [ -n "${cand_regex:-}" ] || continue
                if printf '%s' "$payload" | grep -qE -e "$cand_regex" 2>/dev/null; then
                    label="$cand_label"
                    break
                fi
            done <<< "$PATTERNS"
            printf '   - [LINE] %s:%s (%s)\n' "$loc" "$lineno" "$label" >&2
        done <<< "$CONTENT_HITS"
    fi
    echo "" >&2
    echo "请撤出该文件或将密钥迁移至环境变量；若为误报可在行内添加注释: # $PRAGMA" >&2
    exit 1
fi

# --- check 4: repository gates, launched in parallel ------------------------
PY_BIN=""
if [ -x ".venv/Scripts/python.exe" ]; then
    PY_BIN=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
    PY_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
fi
[ -n "$PY_BIN" ] || exit 0

LOG_DIR="$(mktemp -d)"
trap 'rm -rf "$LOG_DIR"' EXIT
PIDS=()
LABELS=()

launch() {
    local label="$1"; shift
    "$@" > "$LOG_DIR/$label.log" 2>&1 &
    PIDS+=($!)
    LABELS+=("$label")
}

# hygiene reads the index and is always cheap (~0.1 s).
[ -f "scripts/check_repo_hygiene.py" ] && \
    launch hygiene "$PY_BIN" -B scripts/check_repo_hygiene.py --staged

# structure must see the whole import graph (a cycle spans unstaged modules), so it runs only when
# the commit touches Python at all.
if [ -f "scripts/check_repo_structure.py" ] && \
   [ -n "$(git diff --cached --name-only --diff-filter=ACMR -- '*.py')" ]; then
    launch structure "$PY_BIN" -B scripts/check_repo_structure.py
fi

FAILED=0
for i in "${!PIDS[@]}"; do
    if ! wait "${PIDS[$i]}"; then
        cat "$LOG_DIR/${LABELS[$i]}.log" >&2
        FAILED=1
    fi
done

exit "$FAILED"
