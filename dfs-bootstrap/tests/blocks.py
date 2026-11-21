#!/usr/bin/env python3
"""Run one block of the suite instead of all of it.

Every block is a self-contained unittest module; nothing is mocked, so a block costs what it costs.
While iterating on one behavior, run that block. Run `all` (or the mutation harness) before shipping.

    python -B tests/blocks.py --list
    python -B tests/blocks.py doctor
    python -B tests/blocks.py gates -q            # extra args go to unittest
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

BLOCKS: dict[str, tuple[str, ...]] = {
    # one behavior per block — pick by what you changed
    "root": ("test_repo_root.py",),
    "hook": ("test_hook_activation.py",),
    "doctor": ("test_doctor_modes.py",),
    "report": ("test_report_honesty.py",),
    "repair": ("test_repair_paths.py",),
    "bootstrap": ("test_bootstrap_script.py",),
    "overlay": ("test_overlay.py",),
    "gates": ("test_hygiene_gate.py", "test_structure_gate.py"),
    "template": ("test_template_quality.py",),
    "perf": ("test_performance.py",),
}

BLOCKS["all"] = tuple(sorted({name for files in BLOCKS.values() for name in files}))


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "--list"):
        print("blocks:")
        for name in sorted(name for name in BLOCKS if name != "all"):
            print(f"  {name:<10} {', '.join(BLOCKS[name])}")
        print("  all        every module above")
        return 0
    name, extra = argv[0], list(argv[1:])
    if name not in BLOCKS:
        print(f"[ERR] unknown block {name!r}; try --list", file=sys.stderr)
        return 2
    code = 0
    for module in BLOCKS[name]:
        print(f"===== {name}: {module} =====")
        proc = subprocess.run([sys.executable, "-B", str(HERE / module), *extra], cwd=str(HERE))
        code = code or proc.returncode
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
