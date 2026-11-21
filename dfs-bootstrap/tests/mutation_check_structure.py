"""Mutation check for the structure gate and overlay mode.

A green suite proves the assertions ran; it does not prove they can fail. Each mutation injects one
defect into a scratch copy and asserts the *named* test goes red. The pristine tree is never written.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent

SUITES = (
    "tests/test_structure_gate.py",
    "tests/test_overlay.py",
    "tests/test_bootstrap_script.py",
    "tests/test_template_quality.py",
    "tests/test_hygiene_gate.py",
    "tests/test_performance.py",
    # blocks added with the 2026-11-17 bootstrap rewrite; they hold behavior no other suite covers
    "tests/test_hook_activation.py",
    "tests/test_repo_root.py",
)

# (rule, target file, old text, new text, test that must fail, suite index)
MUTATIONS = [
    (
        "cycle-detection-off",
        "templates/repo/check_repo_structure.py",
        "            if len(component) > 1:",
        "            if False:",
        "test_two_module_cycle_is_rejected",
        0,
    ),
    (
        "fanout-off",
        "templates/repo/check_repo_structure.py",
        '        if len(targets) > cfg["max_fanout"]:',
        "        if False:",
        "test_hub_module_is_rejected",
        0,
    ),
    (
        "func-len-off",
        "templates/repo/check_repo_structure.py",
        '            if length > cfg["max_function_lines"]:',
        "            if False:",
        "test_long_function_is_rejected",
        0,
    ),
    (
        "nesting-off",
        "templates/repo/check_repo_structure.py",
        '            if depth > cfg["max_nesting"]:',
        "            if False:",
        "test_deep_nesting_is_rejected",
        0,
    ),
    (
        "god-class-off",
        "templates/repo/check_repo_structure.py",
        '            if len(methods) > cfg["max_methods"]:',
        "            if False:",
        "test_class_with_too_many_methods_is_rejected",
        0,
    ),
    (
        "stub-body-off",
        "templates/repo/check_repo_structure.py",
        "            reason = _body_is_stub(node)",
        "            reason = None",
        "test_pass_only_body_is_rejected",
        0,
    ),
    (
        "stub-comment-off",
        "templates/repo/check_repo_structure.py",
        "        if STUB_COMMENT_RE.search(line):",
        "        if False:",
        "test_elision_comment_is_rejected",
        0,
    ),
    (
        "abstract-exemption-removed",
        "templates/repo/check_repo_structure.py",
        "    if _is_abstract_method(func):\n        return None",
        "    if False:\n        return None",
        "test_abstract_method_is_allowed",
        0,
    ),
    (
        "structure-config-silent-fallback",
        "templates/repo/check_repo_structure.py",
        '    try:\n        loaded = json.loads(path.read_text(encoding="utf-8"))\n    except json.JSONDecodeError as exc:',
        '    try:\n        loaded = json.loads(path.read_text(encoding="utf-8"))\n    except ValueError as exc:\n        return cfg\n    except json.JSONDecodeError as exc:',
        "test_malformed_config_exits_two",
        0,
    ),
    (
        "venv-not-skipped",
        "templates/repo/check_repo_structure.py",
        'SKIP_DIRS = frozenset(\n    {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache",\n     "build", "dist", ".tox", ".eggs", "site-packages", ".worktrees"}\n)',
        "SKIP_DIRS = frozenset()",
        "test_venv_and_worktrees_are_ignored",
        0,
    ),
    # --- overlay mode ---
    (
        "overlay-exclude-off",
        "scripts/dfs_bootstrap/repo_config.py",
        "    wanted = [*OVERLAY_PRIVATE_PATHS, *REQUIRED_IGNORES]",
        "    wanted = []",
        "test_status_diff_and_staged_are_all_empty",
        1,
    ),
    (
        "overlay-hook-in-worktree",
        "scripts/dfs_bootstrap/constants.py",
        "OVERLAY_HOOK_DIR = pathlib.Path(\".git\") / \"dfs-hooks\"",
        "OVERLAY_HOOK_DIR = pathlib.Path(\".githooks\")",
        "test_hook_lives_inside_dot_git",
        1,
    ),
    (
        'overlay-local-attributes-off',
        'scripts/dfs_bootstrap/repo_config.py',
        '    return _ensure(target / ".git" / "info" / "attributes", GITATTRIBUTES_LINES, ATTRIBUTES_HEADER,',
        '    return _ensure(target / ".git" / "info" / "attributes", [], ATTRIBUTES_HEADER,',
        'test_local_attributes_pin_lf_without_touching_tracked_file',
        1,
    ),
    (
        'overlay-edits-tracked-gitignore',
        'scripts/dfs_bootstrap/cli.py',
        '        repo_config.ensure_local_exclude(target, args.dry_run)\n        repo_config.ensure_local_attributes(target, args.dry_run)',
        '        repo_config.ensure_gitignore(target, args.dry_run)\n        repo_config.ensure_gitattributes(target, args.dry_run)',
        'test_tracked_ignore_and_attributes_are_byte_identical',
        1,
    ),
    (
        "pin-gate-rejects-local-attributes",
        "templates/repo/check_repo_hygiene.py",
        '    sources = [root / ".gitattributes", root / ".git" / "info" / "attributes"]',
        '    sources = [root / ".gitattributes"]',
        "test_upstream_commit_keeps_overlay_clean",
        1,
    ),
    # --- upstream conflict handling (a fork that already has AGENTS.md / hook) ---
    (
        'overlay-overwrites-tracked-agents',
        'scripts/dfs_bootstrap/anchors.py',
        '    if overlay and gitops.is_tracked(target, RULES_SSOT_FILE):',
        '    if False:',
        'test_agents_md_is_byte_identical_after_bootstrap',
        1,
    ),
    (
        'overlay-overwrites-tracked-claude',
        'scripts/dfs_bootstrap/anchors.py',
        '    if overlay and gitops.is_tracked(target, POINTER_FILE):',
        '    if False:',
        'test_claude_md_is_byte_identical_after_bootstrap',
        1,
    ),
    (
        "no-private-anchor-fallback",
        "scripts/dfs_bootstrap/anchors.py",
        '        _write_private_anchor(target, dry_run)\n        return',
        "        return",
        "test_private_anchor_carries_the_rules_instead",
        1,
    ),
    (
        "private-anchor-not-excluded",
        "scripts/dfs_bootstrap/constants.py",
        '    "AGENTS.dfs.md",\n',
        "",
        "test_private_anchor_is_invisible_to_git",
        1,
    ),
    (
        'hooks-path-blindly-reset',
        'scripts/dfs_bootstrap/hook.py',
        '    if current not in CHAINED_DIRS and not take_hooks_path:',
        '    if False:  # blind reset - planted defect',
        'test_force_hook_without_take_hooks_path_refuses_the_switch',
        6,
    ),
    (
        "emit-ci-omits-ratchet-step",
        "templates/repo/ci-steps-github.yml",
        "        run: python3 scripts/check_repo_structure.py --ratchet-guard",
        "        run: python3 scripts/check_repo_structure.py --all  # guard removed",
        "test_emit_ci_works_without_vault_root_or_existing_target",
        2,
    ),
    (
        "emit-ci-guard-test-loses-assertion",
        "templates/repo/ci-wiring-guard-test.py.txt",
        '        self.assertIn("--ratchet-guard", text, "the ratchet guard must be wired next to the audit")',
        '        pass  # assertion removed',
        "test_emit_ci_works_without_vault_root_or_existing_target",
        2,
    ),
    (
        'doctor-misses-eol-gap',
        'scripts/dfs_bootstrap/doctor.py',
        'LINE:    ("EOL check under .githooks/", ',
        '    ("EOL check under .githooks/", ("密钥",)),  # MUTATED: EOL no longer detected',
        'test_doctor_detects_project_hook_gaps',
        2,
    ),
    (
        "emit-checks-drops-hygiene",
        "templates/githooks-dfs-checks.sh",
        '    dfs_hyg_out="$("$dfs_checks_py" -B "$dfs_checks_root/scripts/check_repo_hygiene.py" --staged 2>&1)"',
        '    dfs_hyg_out=""  # hygiene removed',
        "test_emit_checks_is_read_only_and_sourceable",
        2,
    ),
    (
        "emit-checks-structure-not-opt-in",
        "templates/githooks-dfs-checks.sh",
        'if [ "${DFS_STRUCTURE_LOCAL:-0}" = "1" ] && \\',
        'if true && \\',
        "test_emit_checks_is_read_only_and_sourceable",
        2,
    ),
    (
        "template-import-order-regression",
        "templates/repo/check_repo_structure.py",
        "import sys\nfrom pathlib import Path",
        "from pathlib import Path\nimport sys",
        "test_leading_import_block_is_ruff_i001_clean",
        3,
    ),
    (
        "gate-version-marker-removed",
        "templates/repo/check_repo_hygiene.py",
        "# dfs-bootstrap-gate-version: 4",
        "# (marker stripped)",
        "test_templates_carry_gate_version_marker",
        3,
    ),
    (
        'gate-upgrade-never-happens',
        'scripts/dfs_bootstrap/gates.py',
        '        if key is not None and wanted_key is not None and key == wanted_key:\n            say("OK", f"{rel} already at gate version {GATE_VERSION}")\n            continue',
        '        if key is not None and wanted_key is not None and key == wanted_key:\n            say("OK", f"{rel} already at gate version {GATE_VERSION}")\n            continue\n        if key is not None:\n            continue  # NEVER upgrade - planted defect',
        'test_old_dfs_gate_is_upgraded_with_backup',
        3,
    ),
    (
        'rules-anchor-substring-false-positive',
        'scripts/dfs_bootstrap/anchors.py',
        '    return ANCHOR_HEADER in text and any(token in text for token in ANCHOR_TOOL_TOKENS)',
        '    return "工程规范与避坑检索" in text',
        'test_routing_row_titled_like_anchor_is_not_a_false_positive',
        2,
    ),
    (
        "hook-chain-disabled",
        "templates/githooks-pre-commit.sh",
        'chain_upstream "$@"',
        ": # chain disabled",
        "test_hook_chain_reports_the_upstream_hook",
        1,
    ),
    (
        "hook-chain-failure-swallowed",
        "templates/githooks-pre-commit.sh",
        '            printf \'[CHAIN] upstream hook failed: %s\\n\' "$candidate" >&2\n            exit 1',
        '            printf \'[CHAIN] upstream hook failed: %s\\n\' "$candidate" >&2\n            return 0',
        "test_upstream_hook_failure_blocks_the_commit",
        1,
    ),
    # --- baseline tolerance (ratchet) ---
    (
        "ratchet-off",
        "templates/repo/check_repo_structure.py",
        "        if limit and seen[tag] <= limit:\n            absorbed[tag] = absorbed.get(tag, 0) + 1\n            continue",
        "        if False:\n            absorbed[tag] = absorbed.get(tag, 0) + 1\n            continue",
        "test_existing_count_is_tolerated_and_reported",
        0,
    ),
    (
        "ratchet-swallows-all",
        "templates/repo/check_repo_structure.py",
        "        limit = cfg[RATCHET_KEYS[tag]] if tag in RATCHET_KEYS else 0",
        "        limit = 10**9",
        "test_one_more_than_tolerance_is_rejected",
        0,
    ),
    (
        "ratchet-cross-class-leak",
        "templates/repo/check_repo_structure.py",
        '    "[STUB]": "allowed_stub",',
        '    "[STUB]": "allowed_func_len",',
        "test_tolerance_is_per_class",
        0,
    ),
    (
        "ratchet-suppression-silent",
        "templates/repo/check_repo_structure.py",
        '        tail = f" (baseline tolerated: {detail})"',
        '        tail = ""',
        "test_existing_count_is_tolerated_and_reported",
        0,
    ),
    # -- JSON / explain --
    (
        "json-loses-tolerated-count",
        "templates/repo/check_repo_structure.py",
        '        "findings_tolerated": len(failures) - len(kept),',
        '        "findings_tolerated": 0,',
        "test_json_reports_counts_and_verdict",
        0,
    ),
    (
        "explain-loses-provenance",
        "templates/repo/check_repo_structure.py",
        '                print(f"provenance: measured_at_commit={prov.get(\'measured_at_commit\', \'unknown\')}")',
        '                print("provenance: hidden")',
        "test_explain_shows_source_and_provenance",
        0,
    ),
    # --- baseline automation ---
    (
        "emit-baseline-hardcoded-count",
        "templates/repo/check_repo_structure.py",
        "    counts = {key: 0 for key in RATCHET_KEYS.values()}\n    for msg in failures:",
        "    counts = {key: 0 for key in RATCHET_KEYS.values()}\n    for msg in []:",
        "test_emit_baseline_writes_measured_counts_with_provenance",
        0,
    ),
    (
        "ratchet-guard-ignores-increase",
        "templates/repo/check_repo_structure.py",
        "        if current[key] > int(committed.get(key, 0))",
        "        if False",
        "test_ratchet_guard_fails_when_tolerance_rose",
        0,
    ),
    # --- opt-in checks: [DEAD] / [TEST_GAP] / [DUP] ---
    (
        "dead-check-disabled",
        "templates/repo/check_repo_structure.py",
        '    limit = cfg["max_dead_exports"]\n    if limit < 0:\n        return []',
        '    limit = cfg["max_dead_exports"]\n    if True:\n        return []',
        "test_unreferenced_symbol_is_rejected_when_enabled",
        0,
    ),
    (
        "dead-ignores-references",
        "templates/repo/check_repo_structure.py",
        "            if corpus.count(name) > 1:",
        "            if True:",
        "test_unreferenced_symbol_is_rejected_when_enabled",
        0,
    ),
    (
        "dead-private-names-not-exempt",
        "templates/repo/check_repo_structure.py",
        '            if name.startswith("_") or name in EXEMPT_EXPORT_NAMES:',
        "            if name in EXEMPT_EXPORT_NAMES:",
        "test_private_names_are_exempt",
        0,
    ),
    (
        "test-gap-disabled",
        "templates/repo/check_repo_structure.py",
        '    if cfg["require_test_for_src"] <= 0:\n        return []',
        "    if True:\n        return []",
        "test_src_module_without_test_is_rejected_when_enabled",
        0,
    ),
    (
        "test-gap-ignores-suffix-convention",
        "templates/repo/check_repo_structure.py",
        '        elif stem.endswith("_test"):\n            test_stems.add(stem[: -len("_test")])',
        '        elif False:\n            test_stems.add(stem)',
        "test_suffix_style_test_name_also_counts",
        0,
    ),
    (
        "dup-disabled",
        "templates/repo/check_repo_structure.py",
        '    min_lines = cfg["max_dup_lines"]\n    if min_lines <= 0:\n        return []',
        '    min_lines = cfg["max_dup_lines"]\n    if True:\n        return []',
        "test_identical_function_bodies_are_rejected_when_enabled",
        0,
    ),
    (
        # The function's own name must not reach the key. It is normalised in TWO places (the
        # wrapper's `name="_"` and `Erase.visit_FunctionDef` for nested defs), so a mutation that
        # touches only one is a no-op — both must be removed for the defect to be observable.
        "dup-keeps-function-name-in-key",
        "templates/repo/check_repo_structure.py",
        '        body=[ast.FunctionDef(name="_", args=sig, body=body.body, decorator_list=[],\n'
        '                              returns=None, type_comment=None)],\n'
        '        type_ignores=[],\n'
        '    )\n'
        '    erased = ast.fix_missing_locations(Erase().visit(wrapper))',
        '        body=[ast.FunctionDef(name=node.name, args=sig, body=body.body, decorator_list=[],\n'
        '                              returns=None, type_comment=None)],\n'
        '        type_ignores=[],\n'
        '    )\n'
        '    _wrapper_holder = wrapper\n'
        '    erased = ast.fix_missing_locations(Erase().visit(wrapper))\n'
        '    erased.body[0].name = node.name',
        "test_same_arity_different_name_is_a_duplicate",
        0,
    ),
    (
        "dup-drops-signature",
        "templates/repo/check_repo_structure.py",
        "        body=[ast.FunctionDef(name=\"_\", args=sig, body=body.body, decorator_list=[],",
        "        body=[ast.FunctionDef(name=\"_\", args=ast.arguments(posonlyargs=[], args=[], "
        "vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=body.body, decorator_list=[],",
        "test_same_body_different_arity_is_not_a_duplicate",
        0,
    ),
    (
        "dup-mirror-guard-removed",
        "templates/repo/check_repo_structure.py",
        "            if _is_mirrored_copy(rel, first_rel):\n                continue",
        "            if False:\n                continue",
        "test_mirrored_build_tree_is_not_a_duplicate",
        0,
    ),
    (
        "dup-mirror-guard-too-broad",
        "templates/repo/check_repo_structure.py",
        "    return a[-min(len(a), len(b)):] == b[-min(len(a), len(b)):] and (len(a) != len(b))",
        "    return True",
        "test_genuine_duplicate_in_unrelated_dirs_is_still_caught",
        0,
    ),
    # --- scope-granular hygiene ratchet ---
    (
        "hygiene-unlisted-bucket-not-strict",
        "templates/repo/check_repo_hygiene.py",
        "        if seen[key] <= ratchet.get(key, 0):",
        "        if seen[key] <= ratchet.get(key, ratchet.get('ABS_PATH|docs', 0)):",
        "test_unlisted_production_scope_is_rejected",
        4,
    ),
    (
        "hygiene-ratchet-off",
        "templates/repo/check_repo_hygiene.py",
        "        if seen[key] <= ratchet.get(key, 0):",
        "        if False:",
        "test_existing_debt_bucket_is_absorbed_and_named",
        4,
    ),
    (
        "hygiene-ratchet-swallows-all",
        "templates/repo/check_repo_hygiene.py",
        "        if seen[key] <= ratchet.get(key, 0):",
        "        if seen[key] <= 10**9:",
        "test_one_more_than_bucket_allowance_is_rejected",
        4,
    ),
    (
        "hygiene-correctness-class-ratchetable",
        "templates/repo/check_repo_hygiene.py",
        'RATCHET_CATEGORIES = frozenset({"ABS_PATH", "BLOAT", "LARGE", "BUDGET"})',
        'RATCHET_CATEGORIES = frozenset({"ABS_PATH", "BLOAT", "LARGE", "BUDGET", "CONFLICT"})',
        "test_correctness_class_is_never_ratcheted",
        4,
    ),
    (
        "hygiene-root-scope-collapsed",
        "templates/repo/check_repo_hygiene.py",
        "    scope = path.split(\"/\", 1)[0] if \"/\" in path else ROOT_SCOPE",
        '    scope = "docs"',
        "test_root_scope_is_a_separate_bucket",
        4,
    ),
    (
        "hygiene-emit-baseline-hardcoded",
        "templates/repo/check_repo_hygiene.py",
        "    for msg in findings:\n        key = _bucket_key(msg)\n        if key is not None:\n            counts[key] = counts.get(key, 0) + 1",
        "    for msg in []:\n        key = _bucket_key(msg)\n        if key is not None:\n            counts[key] = counts.get(key, 0) + 1",
        "test_emit_baseline_self_measures_with_provenance",
        4,
    ),
    (
        "hygiene-guard-ignores-increase",
        "templates/repo/check_repo_hygiene.py",
        "        if current[key] > committed.get(key, 0)",
        "        if False",
        "test_guard_fails_when_bucket_rose",
        4,
    ),
    (
        "hygiene-guard-misses-new-bucket",
        "templates/repo/check_repo_hygiene.py",
        "        for key in current\n        if current[key] > committed.get(key, 0)",
        "        for key in committed\n        if current[key] > committed.get(key, 0)",
        "test_guard_catches_newly_added_bucket",
        4,
    ),
    (
        "hygiene-json-loses-bucket",
        "templates/repo/check_repo_hygiene.py",
        '        "by_bucket": dict(sorted(by_bucket.items())),',
        '        "by_bucket": {},',
        "test_json_reports_buckets_and_verdict",
        4,
    ),
    # --- --no-git filesystem mode ---
    (
        "no-git-uses-git-index",
        "templates/repo/check_repo_hygiene.py",
        "    paths = _walk_paths(root) if no_git else _git_paths(root, staged=staged)",
        "    paths = _git_paths(root, staged=staged)",
        "test_plain_directory_audits_without_git",
        4,
    ),
    (
        "no-git-scratch-not-skipped",
        "templates/repo/check_repo_hygiene.py",
        "     \".ruff_cache\", \"build\", \"dist\", \".tox\", \".eggs\", \"site-packages\", \".worktrees\"}",
        "     \"build\", \"dist\", \".tox\", \".eggs\", \"site-packages\", \".worktrees\"}",
        "test_skips_scratch_dirs_like_structure_gate",
        4,
    ),
    (
        "no-git-staged-not-rejected",
        "templates/repo/check_repo_hygiene.py",
        '        ap.error("--staged reads the git index; it cannot be combined with --no-git")',
        "        pass",
        "test_staged_is_rejected_with_no_git",
        4,
    ),
    (
        "no-git-eol-pin-not-skipped",
        "templates/repo/check_repo_hygiene.py",
        "    if not no_git:\n        failures.extend(check_gitattributes_pins(root))",
        "    if True:\n        failures.extend(check_gitattributes_pins(root))",
        "test_eol_pin_is_git_only",
        4,
    ),
    # --- self-audit: the skill's own source must pass its own gates ---
    (
        "self-audit-structure-catches-nesting",
        "scripts/dfs_bootstrap/cli.py",
        "    readonly = _run_readonly_mode(args)\n    if readonly is not None:\n        return readonly",
        "    readonly = _run_readonly_mode(args)\n    if readonly is not None:\n        if True:\n"
        "            if True:\n                if True:\n                    if True:\n                        if True:\n"
        "                            return readonly",
        "test_structure_gate_passes_on_skill_source",
        3,
    ),
    (
        "self-audit-hygiene-catches-host-path",
        "scripts/dfs_bootstrap/constants.py",
        'GATE_VERSION = "4"',
        'GATE_VERSION = "4"\n_INJECTED = "D:/Code/demo/x.py"  # injected for self-audit test',  # git:allow-abs-path
        "test_hygiene_gate_passes_on_skill_source",
        3,
    ),
    # --- migrated from the retired tests/mutation_check.py (bootstrap-script suite, idx 2) ---
    # That script had rotted: 4/16 anchors no longer matched. The 15 that still target live
    # assertions are kept here; migrating them replaced its single-suite runner, so no coverage
    # was lost when the old file was deleted.
    (
        "rules-ssot",
        "scripts/dfs_bootstrap/constants.py",
        'POINTER_BODY = (\n    "@AGENTS.md\\n"',
        'POINTER_BODY = (\n    "## [NOTE] 工程规范与避坑检索\\n"',
        "test_agents_md_carries_rules_and_claude_md_is_only_a_pointer",
        2,
    ),
    # Swapped 2026-11-19. The old entry mutated VAULT_ROOT_TOKEN, which the anchor no longer
    # emits — no assertion could observe it, so it would have gone UNCAUGHT (a silent coverage
    # hole). The graded property is now the one that matters: the anchor must carry a resolvable
    # tool pointer instead of an inert path.
    (
        "anchor-loses-its-tool-pointer",
        "scripts/dfs_bootstrap/anchors.py",
        '        "- 检索避坑规范：调用 `search_vault` MCP\\n"\n'
        '        "- 稳定经验调用 `save_inbox_draft` 沉淀；临时问题、决策和踩坑写入 WORKMEMORY。\\n"',
        '        "- 知识库检索见仓库文档\\n"',
        "test_anchor_names_a_tool_and_carries_no_path",
        2,
    ),
    (
        "no-gitattributes",
        "scripts/dfs_bootstrap/constants.py",
        'GITATTRIBUTES_LINES = [\n    ".githooks/** text eol=lf",\n    "WORKMEMORY/** text eol=lf",\n    "*.sh text eol=lf",\n]',
        "GITATTRIBUTES_LINES = []",
        "test_writes_gitignore_gitattributes_hook_hygiene_and_workmemory",
        2,
    ),
    (
        'hook-not-upgraded',
        'scripts/dfs_bootstrap/hook.py',
        '    wrote = _write_hook(hook, body, dry_run, keep=True)\n    if not dry_run:\n        say("OK", f"upgraded hook v{installed}',
        '    wrote = False  # never upgrade - planted defect\n    if not dry_run:\n        say("OK", f"upgraded hook v{installed}',
        'test_older_dfs_hook_is_upgraded_with_backup',
        2,
    ),
    (
        'repo-root-guard-off',
        'scripts/dfs_bootstrap/cli.py',
        '    if top is None or top == target:\n        return None',
        '    if True:\n        return None  # no repository-root detection - planted defect',
        'test_subdirectory_target_is_refused_and_writes_nothing',
        7,
    ),
    (
        "hygiene-gate-absent-from-hook",
        "templates/githooks-pre-commit.sh",
        '[ -f "scripts/check_repo_hygiene.py" ] && \\',
        "false && \\",
        "test_hook_invokes_the_hygiene_gate",
        2,
    ),
    (
        "abs-path-rule-disabled",
        "templates/repo/check_repo_hygiene.py",
        'if "git:allow-abs-path" not in line and HOST_PATH_RE.search(line):',
        "if False and HOST_PATH_RE.search(line):",
        "test_rejects_host_absolute_path",
        2,
    ),
    (
        "conflict-rule-disabled",
        "templates/repo/check_repo_hygiene.py",
        'if "git:allow-conflict-marker" not in line and CONFLICT_RE.match(line):',
        "if False and CONFLICT_RE.match(line):",
        "test_rejects_conflict_marker",
        2,
    ),
    (
        "budget-rule-disabled",
        "templates/repo/check_repo_hygiene.py",
        "        if nlines > max_lines or len(data) > max_ctx_bytes:",
        "        if False:",
        "test_rejects_bloated_agents_md",
        2,
    ),
    (
        "bloat-rule-disabled",
        "templates/repo/check_repo_hygiene.py",
        'if suffix in SOURCE_SUFFIXES and nlines > max_source_lines and "git:allow-bloat" not in text:',
        "if False:",
        "test_rejects_oversized_module",
        2,
    ),
    (
        "pin-gate-disabled",
        "templates/repo/check_repo_hygiene.py",
        "        failures.extend(check_gitattributes_pins(root))",
        "        pass  # pin check disabled",
        "test_missing_pin_is_reported",
        2,
    ),
    (
        "config-error-collapsed",
        "templates/repo/check_repo_hygiene.py",
        "    try:\n        loaded = json.loads(path.read_text(encoding=\"utf-8\"))\n    except json.JSONDecodeError as exc:",
        "    try:\n        loaded = json.loads(path.read_text(encoding=\"utf-8\"))\n    except ValueError as exc:\n        return cfg\n    except json.JSONDecodeError as exc:",
        "test_malformed_config_exits_two_not_one",
        2,
    ),
    (
        "hook-crlf-gate-disabled",
        "templates/githooks-pre-commit.sh",
        "            if [ -f \"$path\" ] && [ \"$(tr -cd '\\r' < \"$path\" | wc -c)\" -gt 0 ]; then",
        "            if false; then",
        "test_hook_rejects_crlf_in_the_hook_directory",
        2,
    ),
    (
        "secret-scan-disabled",
        "templates/githooks-pre-commit.sh",
        '    CONTENT_HITS="$(git grep --cached -nIE "${GREP_ARGS[@]}" 2>/dev/null | grep -vF -- "$PRAGMA" || true)"',
        '    CONTENT_HITS=""',
        "test_hook_still_blocks_a_synthetic_secret",
        2,
    ),
    (
        'workmemory-rescaffolded',
        'scripts/dfs_bootstrap/workmemory.py',
        '    absent = [name for name in WORKMEMORY_FILES if not (dest / name).exists()]',
        '    absent = list(WORKMEMORY_FILES)  # rescaffold over history - planted defect',
        'test_workmemory_history_is_never_rescaffolded',
        2,
    ),
    (
        "worktrees-not-ignored",
        "scripts/dfs_bootstrap/constants.py",
        '    ".worktrees/",\n    ".vault-exec-ledger.json",',
        "",
        "test_writes_gitignore_gitattributes_hook_hygiene_and_workmemory",
        2,
    ),
    (
        "version-constant-drifts-from-marker",
        "scripts/dfs_bootstrap/constants.py",
        'GATE_VERSION = "4"',
        'GATE_VERSION = "99"',
        "test_version_markers_match_bootstrap_constants",
        3,
    ),
    # --- hook scheduling, proven by observed lifetimes (not wall-clock ceilings) ---
    (
        "hook-gates-serialized",
        "templates/githooks-pre-commit.sh",
        '    "$@" > "$LOG_DIR/$label.log" 2>&1 &\n    PIDS+=($!)\n',
        '    "$@" > "$LOG_DIR/$label.log" 2>&1 &\n    PIDS+=($!)\n    wait "$!"\n',
        "test_two_gates_run_concurrently",
        5,
    ),
    (
        "structure-gate-never-skipped",
        "templates/githooks-pre-commit.sh",
        "[ -n \"$(git diff --cached --name-only --diff-filter=ACMR -- '*.py')\" ]; then",
        "true ]; then",
        "test_structure_gate_skipped_when_no_python_is_staged",
        5,
    ),
    (
        "gate-template-exceeds-line-budget",
        "templates/repo/check_repo_hygiene.py",
        "ROOT = Path(__file__).resolve().parent.parent",
        "ROOT = Path(__file__).resolve().parent.parent\n" + "# padding\n" * 400,
        "test_gate_templates_fit_their_own_bloat_budget",
        3,
    ),
]


def build_test_map(root: pathlib.Path, index: int) -> dict[str, str]:
    """Map bare test method names to 'Class.method' once per suite (stdlib ast, no imports).

    Mutation checking only needs to know that ONE named test went red. Running the entire suite for
    every mutation is O(mutations x tests) — on this repo that was ~22s per bootstrap mutation.
    """
    import ast
    source = (root / SUITES[index]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    mapping: dict[str, str] = {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        for fn in (n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            if fn.name.startswith("test_"):
                mapping.setdefault(fn.name, f"{cls.name}.{fn.name}")
    return mapping


def run_suite(root: pathlib.Path, index: int, only: str | None = None) -> tuple[int, str]:
    cmd = [sys.executable, "-B", SUITES[index]]
    if only:
        cmd.append(only)
    proc = subprocess.run(
        cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def failing(output: str) -> set[str]:
    names = set(re.findall(r"^(?:FAIL|ERROR): (\S+)", output, re.MULTILINE))
    return {n.split("(")[0] for n in names}


def _mutate(original: str, old: str, new: str) -> tuple[str | None, str | None]:
    """Apply one mutation anchor; return (mutated_text, error) — error is None on success.

    ``LINE:`` anchors replace a whole line by unique prefix, avoiding backslash escaping.
    """
    if old.startswith("LINE:"):
        needle = old[5:]
        lines = original.splitlines(keepends=True)
        hits = [i for i, line in enumerate(lines) if line.startswith(needle)]
        if len(hits) != 1:
            return None, f"line-prefix occurs {len(hits)}x (must be 1)"
        lines[hits[0]] = new + "\n"
        return "".join(lines), None
    if original.count(old) != 1:
        return None, f"anchor occurs {original.count(old)}x (must be 1)"
    return original.replace(old, new, 1), None


def _check_baselines(work: pathlib.Path) -> list[str]:
    """Every suite must be green before mutations; a red baseline makes results meaningless."""
    problems: list[str] = []
    for i, suite in enumerate(SUITES):
        code, out = run_suite(work, i)
        print(f"baseline {suite}: exit={code} failing={sorted(failing(out)) or 'none'}")
        if code != 0:
            print("BASELINE IS RED — mutations cannot be judged against a red baseline")
            print(out[-2000:])
            problems.append(f"baseline {suite} is red")
    return problems


def _run_mutations(
    work: pathlib.Path, test_maps: list[dict[str, str]], pristine: dict[str, str]
) -> list[str]:
    """Run each mutation against ONLY its target test; record MISS/WRONG/NOOP as problems."""
    problems: list[str] = []
    for rule, rel, old, new, expected, idx in MUTATIONS:
        target = work / rel
        original = pristine.setdefault(rel, target.read_text(encoding="utf-8"))
        mutated, error = _mutate(original, old, new)
        if error is not None:
            problems.append(f"{rule}: {error} in {rel}")
            print(f"NOOP  {rule}: {error}")
            continue
        target.write_text(mutated, encoding="utf-8", newline="\n")
        code, out = run_suite(work, idx, test_maps[idx][expected])
        target.write_text(original, encoding="utf-8", newline="\n")

        failed = {name.split(".")[-1] for name in failing(out)}
        if code == 0:
            problems.append(f"{rule}: suite stayed GREEN")
            print(f"MISS  {rule}: suite still green")
        elif expected not in failed:
            problems.append(f"{rule}: expected {expected}, actually {sorted(failed)}")
            print(f"WRONG {rule}: expected {expected}, got {sorted(failed)}")
        else:
            print(f"CAUGHT {rule} -> {expected}")
    return problems


def main() -> int:
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp) / "skill"
        shutil.copytree(SRC, work, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        test_maps = [build_test_map(work, i) for i in range(len(SUITES))]
        unmatched = {rule for rule, _, _, _, expected, idx in MUTATIONS
                     if expected not in test_maps[idx]}
        if unmatched:
            print(f"TEST MAP INCOMPLETE — no Class.method for: {sorted(unmatched)}")
            return 1

        baseline_problems = _check_baselines(work)
        if baseline_problems:
            return 1

        pristine: dict[str, str] = {}
        problems.extend(_run_mutations(work, test_maps, pristine))

        # Restore check: verify bytes, not another 66s of full-suite runs. Every mutation restores
        # its own file immediately; a byte comparison is strictly stronger than re-running tests
        # for detecting a leaked mutation, and the final targeted runs already proved behavior.
        for rel, original in pristine.items():
            if (work / rel).read_text(encoding="utf-8") != original:
                problems.append(f"restore failed: mutation text leaked into {rel}")

    print()
    if problems:
        print(f"MUTATION CHECK FAILED ({len(problems)} problem(s)):")
        for p in problems:
            print("  -", p)
        return 1
    print(f"MUTATION CHECK PASSED: {len(MUTATIONS)} mutation(s) all CAUGHT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
