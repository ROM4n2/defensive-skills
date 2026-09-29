---
name: dfs-perf
description: Profile multi-language benchmarks, races, and query plans. Use when the user reports slowness, a performance regression, or asks for a benchmark.
version: 0.2.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [performance, profiling, benchmarks, race-detection, pprof, query-plan]
    related_skills: [dfs-refactor, dfs-review, dfs-pipeline]
---

# DFS-PERF: Multi-Language Performance & Benchmark Profiling

Execute high-rigor performance profiling, memory allocation auditing, data race detection, and database query plan optimization across Go, Python, C++, and SQL.

## 🛠️ Automated Benchmark CLI
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

### 2. Python Profiling Protocol
- **Micro-Benchmark**: `pytest --benchmark-only --benchmark-autosave`
- **Function Line Profiler**: `python -m cProfile -s cumtime script.py | head -n 25`
- **Memory Leak Detection**: `tracemalloc` top-10 allocation snapshot.

### 3. C++ Profiling Protocol
- **Google Benchmark**: `cmake --build build --target run_benchmarks && ./build/benchmarks`
- **Valgrind / AddressSanitizer**: `g++ -fsanitize=address,undefined -g ...`
- **Zero Memory Leaks**: Verify Valgrind output reports `0 errors from 0 contexts`.

### 4. SQL Database Query Plan Protocol (MySQL / PostgreSQL)
- **Explain Analyze**: `EXPLAIN ANALYZE SELECT ...`
- **Tree Format**: `EXPLAIN FORMAT=TREE SELECT ...`
- **Index Optimization Rules**:
  - Verify `type` is `ref`, `eq_ref`, or `range` (Zero `ALL` full-table scans on tables > 10k rows);
  - Verify `Extra` contains `Using index` (Covering index).

---

## Report Schema Archival
Load `templates/perf-report-schema.md` via `read_file(path='templates/perf-report-schema.md')` to format the final Before vs After speedup evaluation card. The card is done when it carries two numbers measured from the same command — before and after. A speedup claim backed by one run is not a result.
