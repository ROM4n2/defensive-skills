---
name: dfs-perf
description: Profile multi-language benchmarks, races, and query plans. Use when the user reports slowness, a performance regression, or asks for a benchmark.
license: MIT
metadata:
  version: 0.2.0
  platforms: linux, macos, windows
  hermes:
    tags: [performance, profiling, benchmarks, race-detection, pprof, query-plan]
    related_skills: [dfs-refactor, dfs-review]
---
# DFS-PERF: Multi-Language Performance & Benchmark Profiling

Execute high-rigor performance profiling, memory allocation auditing, data race detection, and database query plan optimization across Go, Python, C++, and SQL.

## [MUST] The Physical Measurement Invariant (RFC 2119 MUST)
> **Never claim a performance improvement without physical before-and-after benchmark numbers from identical test environments.**
> Speculative optimizations without profiling receipts are strictly prohibited. Zero data races (`-race`) permitted.

---

## [NOTE] Automated Benchmark CLI
Use the bundled profiling runner for automated detection and execution:
```bash
python scripts/benchmark_runner.py --dir . --lang auto --race
```
Take the protocol below that the `--lang auto` verdict selects, and touch only that one.

---

## The Multi-Language Profiling Matrix

### 1. Go Profiling Protocol (MUST)
- **Automated Runner**: `python scripts/benchmark_runner.py --lang go --race --bench .`
- **Benchmark Baseline**: `go test -bench=. -benchmem -count=5 ./...`
- **Race Condition Detection**: `go test -race ./...` (Zero data races permitted)
- **Heap Escape Analysis**: `go build -gcflags="-m -m" ./... 2>&1 | grep "escapes to heap"`
- **CPU & Memory Profiles**:
  ```bash
  go test -bench=BenchmarkTarget -cpuprofile=cpu.pprof -memprofile=mem.pprof
  go tool pprof -top cpu.pprof
  ```
- **Checkable Completion Criterion**:
  - `go test -race` returns exit code 0; `benchstat` or before/after ns/op delta recorded.

### 2. Python Profiling Protocol
- **Micro-Benchmark**: `pytest --benchmark-only --benchmark-autosave`
- **Function Line Profiler**: `python -m cProfile -s cumtime script.py | head -n 25`
- **Memory Leak Detection**: `tracemalloc` top-10 allocation snapshot.
- **Checkable Completion Criterion**:
  - Profiling profile captured; hot-spot functions identified with CPU/cumulative time receipts.

### 3. C++ Profiling Protocol
- **Google Benchmark**: `cmake --build build --target run_benchmarks && ./build/benchmarks`
- **Valgrind / AddressSanitizer**: `g++ -fsanitize=address,undefined -g ...`
- **Zero Memory Leaks**: Verify Valgrind output reports `0 errors from 0 contexts`.
- **Checkable Completion Criterion**:
  - ASan/Valgrind run completes with 0 errors; benchmark throughput numbers recorded.

### 4. SQL Database Query Plan Protocol (MySQL / PostgreSQL)
- **Explain Analyze**: `EXPLAIN ANALYZE SELECT ...`
- **Tree Format**: `EXPLAIN FORMAT=TREE SELECT ...`
- **Index Optimization Rules**:
  - Verify `type` is `ref`, `eq_ref`, or `range` (Zero `ALL` full-table scans on tables > 10k rows);
  - Verify `Extra` contains `Using index` (Covering index).
- **Checkable Completion Criterion**:
  - Query plan tree captured; verified zero full table scans (`ALL`) on tables > 10k rows.

---

## [ANTI] Common Rationalizations & Anti-Patterns

| Agent Rationalization (Anti-Pattern) | Real Hazard | Defensive Guard (MUST) |
|---|---|---|
| *"This refactor looks faster, so I won't run before/after benchmarks."* | **Performance Regressions**: Intuitive 'optimizations' often defeat compiler branch predictors or cache lines. | Mandatory Measurement: Must present concrete `ns/op` or latency numbers before and after. |
| *"The data race is just a benign read counter, so it is safe to ignore."* | **Silent Memory Corruption**: Under Go/C++ memory models, unsynchronized reads produce undefined behavior. | Zero Race Invariant: `go test -race` or ThreadSanitizer MUST pass with 0 warnings. |
| *"I'll optimize this helper function that takes 0.1% of runtime."* | **Premature Optimization (Amdahl's Law Trap)**: Wasting complexity on cold paths yields zero system speedup. | Profile First: Use CPU/pprof traces to identify genuine hot paths before touching code. |
| *"I ran the benchmark once and latency dropped by 20%."* | **Noisy Neighbor & Warmup Bias**: Single-run benchmarks reflect OS jitter and CPU scaling artifacts. | Run benchmarks with multiple iterations (`-count=5`) and analyze with statistical tools like `benchstat`. |

---

## Report Schema Archival
Load `templates/perf-report-schema.md` via `read_file(path='templates/perf-report-schema.md')` to format the final Before vs After speedup evaluation card. The card is done when it carries two numbers measured from the same command — before and after. A speedup claim backed by one run is not a result.
- **Checkable Completion Criterion**:
  - Performance evaluation card rendered with measured before-and-after metrics from identical commands.
