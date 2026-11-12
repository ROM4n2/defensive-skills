#!/usr/bin/env python3
"""DFS 2.0 Mechanical Quality Gate.

Exit codes (RFC 2119 strict):
  0: All checks passed cleanly.
  1: Defect class detected (emits file:line to stderr).
  2: Environment error or invalid arguments (unusable execution context).
"""
import sys
import os
import ast
import re
import argparse
from pathlib import Path

# Generic pattern matching machine-specific personal home and drive paths
# Does NOT hardcode any specific author/user name
DEFAULT_BANNED_PATH_RE = re.compile(
    r'(?:[A-Za-z]:/(?:Users|Obsidian|home|Code|Documents)/[A-Za-z0-9_.-]+|/(?:home|Users)/[A-Za-z0-9_.-]+)',
    re.IGNORECASE
)

def check_python_file(fp: Path, content: str, banned_re, check_defects: bool = True, fail_fast: bool = False) -> list[str]:
    """Inspect Python AST for defects and hardcoded path string constants."""
    violations = []
    try:
        tree = ast.parse(content, filename=str(fp))
    except SyntaxError:
        return [f"{fp}:1: [SYNTAX_ERROR] failed to parse python AST"]

    # 1. Check vacuous tests via AST
    if check_defects:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                body = [
                    s for s in node.body
                    if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))
                ]
                if len(body) == 0 or (len(body) == 1 and (
                    isinstance(body[0], ast.Pass) or
                    (isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and body[0].value.value is Ellipsis)
                )):
                    violations.append(f"{fp}:{node.lineno}: [VACUOUS_TEST] empty test body in '{node.name}'")
                    if fail_fast:
                        return violations

    # 2. Check hardcoded path string constants in AST (ignores code comments)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            norm_val = node.value.replace('\\', '/')
            if banned_re.search(norm_val):
                violations.append(f"{fp}:{node.lineno}: [HARDCODED_PATH] found absolute path literal '{node.value}'")
                if fail_fast:
                    return violations

    return violations

def check_markdown_file(fp: Path, content: str, banned_re, fail_fast: bool = False) -> list[str]:
    """Inspect Markdown text line by line for hardcoded path literals."""
    violations = []
    for idx, line in enumerate(content.splitlines(), 1):
        norm_line = line.replace('\\', '/')
        m = banned_re.search(norm_line)
        if m:
            violations.append(f"{fp}:{idx}: [HARDCODED_PATH] found absolute path literal '{m.group(0)}'")
            if fail_fast:
                return violations
    return violations

def main():
    parser = argparse.ArgumentParser(description="DFS 2.0 Mechanical Gate Runner")
    parser.add_argument("--scan-dir", required=True, help="Directory to scan")
    parser.add_argument(
        "--check-defects",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Toggle defect class scanning (default: enabled)"
    )
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first violation")
    parser.add_argument("--banned-pattern", default=None, help="Custom regex pattern for forbidden path detection")
    args = parser.parse_args()

    target_dir = Path(args.scan_dir)
    if not target_dir.exists() or not target_dir.is_dir():
        sys.stderr.write(f"ENVIRONMENT_ERROR: scan directory does not exist or is not a directory: {target_dir}\n")
        return 2

    if args.banned_pattern:
        try:
            banned_re = re.compile(args.banned_pattern, re.IGNORECASE)
        except re.error as e:
            sys.stderr.write(f"ENVIRONMENT_ERROR: invalid regex pattern: {e}\n")
            return 2
    else:
        banned_re = DEFAULT_BANNED_PATH_RE

    scanned_targets = 0
    violations = []
    traversal_error = False

    def on_walk_error(err):
        nonlocal traversal_error
        traversal_error = True
        sys.stderr.write(f"ENVIRONMENT_ERROR: traversal failed: {err}\n")

    current_script_path = Path(__file__).resolve()

    for root, _, files in os.walk(target_dir, onerror=on_walk_error):
        if traversal_error:
            return 2
        for f in files:
            if f.endswith(('.md', '.py')):
                fp = (Path(root) / f).resolve()
                if fp == current_script_path:
                    continue
                scanned_targets += 1
                try:
                    content = fp.read_text(encoding='utf-8', errors='replace')
                except Exception as e:
                    sys.stderr.write(f"ENVIRONMENT_ERROR: failed to read {fp}: {e}\n")
                    return 2

                if f.endswith('.py'):
                    file_violations = check_python_file(
                        fp, content, banned_re, check_defects=args.check_defects, fail_fast=args.fail_fast
                    )
                else:
                    file_violations = check_markdown_file(
                        fp, content, banned_re, fail_fast=args.fail_fast
                    )

                violations.extend(file_violations)

                if args.fail_fast and violations:
                    violations = violations[:1]
                    break
        if args.fail_fast and violations:
            break

    # Proof 1: scanned_targets must be non-zero
    if scanned_targets == 0:
        sys.stderr.write("ENVIRONMENT_ERROR: zero targets scanned, empty target set\n")
        return 2

    if violations:
        for v in violations:
            sys.stderr.write(f"{v}\n")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
