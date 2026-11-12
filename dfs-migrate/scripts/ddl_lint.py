#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zero-Downtime Database Migration DDL Linter.

Statically audits SQL files for lock-inducing and backward-incompatible operations.
Usage:
    python ddl_lint.py <path_to_migration.sql> [--dialect <mysql|postgres>]
"""

import argparse
import pathlib
import re
import sys


DANGEROUS_PATTERNS = [
    {
        "pattern": r"(?i)ALTER\s+TABLE\s+\w+\s+ADD\s+(?:COLUMN\s+)?\w+\s+[^,;\n]+NOT\s+NULL(?!\s+DEFAULT)",
        "name": "ADD_COLUMN_NOT_NULL_NO_DEFAULT",
        "severity": "CRITICAL",
        "message": "Adding a NOT NULL column without DEFAULT locks the entire table and breaks legacy writes. Use nullable or provide DEFAULT.",
        "ladder": "Phase 1: Add as nullable -> Phase 2: Backfill -> Phase 3: Add NOT NULL constraint."
    },
    {
        "pattern": r"(?i)ALTER\s+TABLE\s+\w+\s+DROP\s+(?:COLUMN\s+)?\w+",
        "name": "DROP_COLUMN_SYNC",
        "severity": "HIGH",
        "message": "Direct DROP COLUMN immediately breaks currently running application instances reading that column.",
        "ladder": "Phase 4: Stop application writes/reads -> Phase 5: Drop column after verification."
    },
    {
        "pattern": r"(?i)ALTER\s+TABLE\s+\w+\s+(?:RENAME|CHANGE)(?:\s+COLUMN)?\s+\w+\s+(?:TO\s+)?\w+",
        "name": "RENAME_COLUMN_SYNC",
        "severity": "CRITICAL",
        "message": "Direct RENAME COLUMN breaks any running instance querying the old column name.",
        "ladder": "Phase 1: Add new column -> Phase 2: Dual-write -> Phase 3: Switch reads -> Phase 5: Drop old."
    },
    {
        "pattern": r"(?i)CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)\w+\s+ON",
        "name": "SYNC_CREATE_INDEX",
        "severity": "MEDIUM",
        "message": "CREATE INDEX without CONCURRENTLY (PostgreSQL) or ALGORITHM=INPLACE, LOCK=NONE (MySQL) can block write traffic on large tables.",
        "ladder": "Use CREATE INDEX CONCURRENTLY (PG) or append ALGORITHM=INPLACE, LOCK=NONE (MySQL)."
    },
    {
        "pattern": r"(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?\w+",
        "name": "DROP_TABLE_DANGEROUS",
        "severity": "CRITICAL",
        "message": "Direct DROP TABLE is irreversible without PITR recovery and acquires heavy metadata locks.",
        "ladder": "Ensure table is decommissioned, rename to _deprecated_<timestamp>, verify zero queries, then drop."
    }
]


def lint_sql_file(file_path: pathlib.Path, dialect: str) -> list[dict]:
    if not file_path.is_file():
        print(f"❌ File not found: {file_path}")
        return [{"severity": "CRITICAL", "message": f"File not found: {file_path}"}]

    content = file_path.read_text(encoding="utf-8")
    violations = []

    for rule in DANGEROUS_PATTERNS:
        matches = list(re.finditer(rule["pattern"], content))
        for m in matches:
            # calculate line number
            line_no = content[:m.start()].count("\n") + 1
            matched_snippet = m.group(0).strip().replace("\n", " ")
            violations.append({
                "line": line_no,
                "rule": rule["name"],
                "severity": rule["severity"],
                "message": rule["message"],
                "ladder": rule["ladder"],
                "snippet": matched_snippet
            })

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Zero-Downtime DDL Linter")
    parser.add_argument("file", help="Path to SQL file")
    parser.add_argument("--dialect", choices=["mysql", "postgres", "auto"], default="auto")
    args = parser.parse_args()

    sql_file = pathlib.Path(args.file)
    print(f"🔍 Auditing DDL file: {sql_file}")
    print("=" * 60)

    violations = lint_sql_file(sql_file, args.dialect)

    if not violations:
        print("✅ Zero dangerous DDL patterns detected! Safe for zero-downtime execution.")
        return 0

    critical_count = sum(1 for v in violations if v["severity"] == "CRITICAL")
    print(f"🚨 Found {len(violations)} DDL risk violation(s) ({critical_count} CRITICAL):\n")
    for v in violations:
        print(f"  [{v['severity']}] Line {v['line']}: {v['rule']}")
        print(f"    Snippet : {v['snippet']}")
        print(f"    Hazard  : {v['message']}")
        print(f"    Ladder  : {v['ladder']}\n")

    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
