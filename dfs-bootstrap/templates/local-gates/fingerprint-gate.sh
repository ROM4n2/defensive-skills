#!/usr/bin/env bash
# dfs-bootstrap-local-gate-version: 1
#
# 本机指纹闸（local-only，**不入库**）。dfs-bootstrap 的规范模板。
#
# 为什么不在 `.githooks/`：那里被 git 跟踪，闸门会被推到远端、改变所有克隆的行为，而且它本身
# 就得携带你的用户名/路径——正是它要防的东西。
# 挂载方式：放在 `$GIT_DIR/local-gates/`，在 `core.hooksPath` 指向的目录里放一个 `pre-push`
# 调用它，通过后串原链（说明见 SKILL.md「Local-only gates」）。
#
# 本模板**不含任何本机标识**：模式来自 `$GIT_DIR/local-gates/fingerprints.txt`，每行一个 POSIX
# ERE；空行与 `#` 注释忽略。文件不存在则直接放行并提示（宁可漏挡，也不让没配置的仓库推不动）。
# 占位豁免来自 `fingerprint-allow.txt`（缺省 `<user>|$HOME|$WIKI_PATH`）：已泛化的行不算泄漏。
#
# 指纹判据（2026-11-21 收紧）：fingerprints.txt 只列**含本机身份的绝对路径**（真实用户名目录、
# 个人 vault 盘符路径）。不要列通用工具目录名：它们不含用户身份，且会误伤「ignore 这些目录」的
# 正常注释——那类注释在公开仓是正当内容，拦它等于把「别提交隐私」变成「别解释隐私规则」。
# 真路径已被含身份的项覆盖，去掉裸目录名不会漏挡。具体示例见 SKILL.md（模板自身不带任何标识）。
#
# 搬移豁免（本模板的关键判据）：命中行若在同一提交的父树里已存在同样文本，判为**搬移**放行。
# 起因是 WORKMEMORY 轮转——事件从 work.log 移进 archive/，在 diff 里长得像新增泄漏，而
# PROTOCOL §5.1 又禁止改事件字节 ⇒ 没有这条豁免，人就只能在「违约改历史」和「永不轮转」
# 之间二选一。判据只看「这一行是否已存在于父提交」，所以真正的新增泄漏照样拦。
#
# stdin 协议（git pre-push）：每行 `<local_ref> <local_sha> <remote_ref> <remote_sha>`。
# 扫描范围：本次待推提交的新增行 + 全部提交信息。
# 输出一律 stderr：git 在 Windows 上 spawn 钩子时 stdout 句柄可能不可写。

set -u

say() { printf '%s\n' "$*" >&2; }

ZERO='0000000000000000000000000000000000000000'
GIT_DIR_LOCAL="$(git rev-parse --git-dir)"
PATTERN_FILE="$GIT_DIR_LOCAL/local-gates/fingerprints.txt"
ALLOW_FILE="$GIT_DIR_LOCAL/local-gates/fingerprint-allow.txt"

if [ ! -f "$PATTERN_FILE" ]; then
    say "[fingerprint-gate] 未配置 $PATTERN_FILE ⇒ 放行（写入本机指纹模式后才生效）"
    exit 0
fi

PATTERN="$(grep -vE '^[[:space:]]*(#|$)' "$PATTERN_FILE" | paste -sd'|' -)"
if [ -z "$PATTERN" ]; then
    say '[fingerprint-gate] 指纹模式为空 ⇒ 放行'
    exit 0
fi

if [ -f "$ALLOW_FILE" ]; then
    ALLOW="$(grep -vE '^[[:space:]]*(#|$)' "$ALLOW_FILE" | paste -sd'|' -)"
else
    ALLOW='<user>|\$HOME|\$WIKI_PATH'
fi

TMP_HITS="$(mktemp)"
trap 'rm -f "$TMP_HITS"' EXIT

# 搬移豁免：同一行文本已出现在父提交里 ⇒ 它不是新增泄漏，只是换了文件。
parent_has_line() {
    local sha="$1" content="$2"
    git rev-parse -q --verify "$sha^" >/dev/null 2>&1 || return 1
    git grep -qF -e "$content" "$sha^" >/dev/null 2>&1
}

SHAS=()
while read -r local_ref local_sha remote_ref remote_sha; do
    [ -n "${remote_ref:-}" ] || continue
    if [ "$local_sha" = "$ZERO" ]; then
        say "[fingerprint-gate] 跳过 $remote_ref：删除远端引用"
        continue
    fi
    if [ "$remote_sha" = "$ZERO" ]; then
        say "[fingerprint-gate] 范围：$remote_ref 为首次推送 ⇒ 扫所有不在远端上的提交"
        while IFS= read -r s; do
            [ -n "$s" ] && SHAS+=("$s")
        done < <(git rev-list "$local_sha" --not --remotes)
    else
        say "[fingerprint-gate] 范围：$remote_sha..$local_sha"
        while IFS= read -r s; do
            [ -n "$s" ] && SHAS+=("$s")
        done < <(git rev-list "$remote_sha..$local_sha")
    fi
done

if [ "${#SHAS[@]}" -eq 0 ]; then
    say '[fingerprint-gate] 无待扫提交，放行'
    exit 0
fi

mapfile -t UNIQUE < <(printf '%s\n' "${SHAS[@]}" | sort -u)

for sha in "${UNIQUE[@]}"; do
    while IFS= read -r mline; do
        mline="${mline%$'\r'}"
        if printf '%s' "$mline" | grep -qiE "$PATTERN" && ! printf '%s' "$mline" | grep -qiE "$ALLOW"; then
            printf '提交信息:%s: %s\n' "$sha" "$mline" >> "$TMP_HITS"
        fi
    done < <(git log -1 --format='%B' "$sha")

    file=''
    lineno=0
    while IFS= read -r line; do
        line="${line%$'\r'}"
        case "$line" in
            '+++ /dev/null') file='' ;;
            '+++ b/'*) file="${line#+++ b/}" ;;
            '@@'*)
                hdr="${line#*+}"
                hdr="${hdr%% *}"
                lineno="${hdr%%,*}"
                ;;
            '+'*)
                content="${line#+}"
                if [ -n "$file" ] && printf '%s' "$content" | grep -qiE "$PATTERN" \
                   && ! printf '%s' "$content" | grep -qiE "$ALLOW"; then
                    if parent_has_line "$sha" "$content"; then
                        say "[fingerprint-gate] 豁免 $file:$lineno（父提交已含同一行，属搬移）"
                    else
                        printf '%s:%s: %s\n' "$file" "$lineno" "$content" >> "$TMP_HITS"
                    fi
                fi
                lineno=$((lineno + 1))
                ;;
            '-'*) ;;
        esac
    done < <(git show --no-color --format= --unified=0 --no-renames "$sha")
done

if [ -s "$TMP_HITS" ]; then
    say '[fingerprint-gate] 命中本机路径指纹（已阻断本次推送）：'
    head -n 100 "$TMP_HITS" | sed 's/^/  /' >&2
    total="$(wc -l < "$TMP_HITS" | tr -d ' ')"
    if [ "$total" -gt 100 ]; then
        say "  ...（共 $total 条，只显示前 100 条）"
    fi
    say '[fingerprint-gate] 改法：真实用户名换成 <user>、个人 vault 绝对路径换成 $WIKI_PATH 后重提。'
    exit 1
fi

say "[fingerprint-gate] 通过：${#UNIQUE[@]} 个提交，无本机路径指纹"
exit 0
