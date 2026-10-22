#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-Language Automated Benchmark & Race Profiling Runner.

Usage:
    python benchmark_runner.py [--dir <path>] [--lang <go|python|cpp>] [--race] [--bench <pattern>]
"""

import argparse
import os
import pathlib
import subprocess
import sys


def detect_language(root: pathlib.Path) -> str:
    """Detect dominant tech stack from workspace manifest files."""
    if (root / "go.mod").exists():
        return "go"
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists() or (root / "requirements.txt").exists():
        return "python"
    if (root / "CMakeLists.txt").exists() or (root / "Makefile").exists():
        return "cpp"
    return "unknown"


def run_command(cmd: list[str], cwd: pathlib.Path) -> tuple[int, str]:
    """Execute command and stream output with exit code."""
  print(f" Running: {' '.join(cmd)} (cwd: {cwd})")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout
    except FileNotFoundError as e:
        return 127, f"Error: Command not found - {e}"
    except Exception as e:
        return 1, f"Execution failed: {e}"


def run_go_bench(root: pathlib.Path, bench_pattern: str, check_race: bool) -> int:
    print("=" * 60)
  print(" [Go Runtime Benchmark & Race Audit]")
    print("=" * 60)

    if check_race:
    print("\n Checking for data races (-race)...")
        code, out = run_command(["go", "test", "-race", "./..."], root)
        print(out)
        if code != 0:
      print(" Data race detected! Aborting performance profiling.")
            return code
    print(" Data race check PASSED (clean).")

  print(f"\n Running Benchmarks (pattern: {bench_pattern})...")
    bench_cmd = ["go", "test", f"-bench={bench_pattern}", "-benchmem", "-count=5", "./..."]
    code, out = run_command(bench_cmd, root)
    print(out)
    return code


def run_python_bench(root: pathlib.Path, bench_pattern: str) -> int:
    print("=" * 60)
  print(" [Python Benchmark & cProfile Audit]")
    print("=" * 60)
    
    # Check if pytest-benchmark is installed
    check_code, _ = run_command(["pytest", "--version"], root)
    if check_code == 0:
    print(f"\n Running pytest benchmarks (pattern: {bench_pattern})...")
        cmd = ["pytest", "-k", bench_pattern, "--benchmark-only", "-v"]
        code, out = run_command(cmd, root)
        print(out)
        if code == 0:
            return 0
            
  print("\n Running cProfile snapshot...")
    cmd = [sys.executable, "-m", "cProfile", "-s", "cumtime", "-m", "unittest"]
    code, out = run_command(cmd, root)
    lines = out.splitlines()[:35]
    print("\n".join(lines))
    return code


def run_cpp_bench(root: pathlib.Path) -> int:
    print("=" * 60)
  print("️ [C++ Google Benchmark Audit]")
    print("=" * 60)
    build_dir = root / "build"
    if not build_dir.exists():
    print("️ Build directory not found. Please compile with cmake first.")
        return 1
    
    cmd = ["cmake", "--build", str(build_dir), "--target", "run_benchmarks"]
    code, out = run_command(cmd, root)
    print(out)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Language Automated Benchmark Runner")
    parser.add_argument("--dir", default=".", help="Target workspace directory")
    parser.add_argument("--lang", choices=["go", "python", "cpp", "auto"], default="auto", help="Target stack")
    parser.add_argument("--race", action="store_true", help="Enable race detector (Go)")
    parser.add_argument("--bench", default=".", help="Benchmark pattern (regex or keyword)")
    
    args = parser.parse_args()
    root = pathlib.Path(args.dir).resolve()
    
    lang = args.lang
    if lang == "auto":
        lang = detect_language(root)
    print(f" Auto-detected tech stack: {lang.upper()} at {root}")
        
    if lang == "go":
        return run_go_bench(root, args.bench, args.race)
    elif lang == "python":
        return run_python_bench(root, args.bench)
    elif lang == "cpp":
        return run_cpp_bench(root)
    else:
    print(f" Unknown or unsupported language stack at {root}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
