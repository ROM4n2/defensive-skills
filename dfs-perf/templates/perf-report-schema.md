# Performance Optimization Report Schema (`templates/perf-report-schema.md`)

Use this schema to structure performance benchmarking before vs after reports.

```markdown
# ⚡ Performance Optimization Report: [Component Name]

> **Target Language / Runtime**: [Go 1.24+ / Python 3.11+ / C++20 / MySQL 8.0]
> **Host Environment**: [OS, CPU Model, Core Count, Memory]
> **Baseline Benchmark Hash / Commit**: `[commit_sha]`

---

## 1. 核心指标对比 (Core Metrics Delta)

| Metric | Before Optimization | After Optimization | Delta / Speedup | Verification Status |
|---|---|---|---|---|
| **Latency (p50 / avg)** | 480 ns/op | 62 ns/op | 🚀 **7.74x faster** | Verified |
| **Latency (p99)** | 1,420 ns/op | 185 ns/op | 🚀 **7.67x faster** | Verified |
| **Throughput / QPS** | 24,000 ops/s | 178,000 ops/s | 🚀 **+641%** | Verified |
| **Memory Allocations** | 38 allocs/op (2.4 KB) | 0 allocs/op (0 B) | 🟢 **Zero Alloc (Stack)** | Verified |
| **Data Race Status** | Clean | Clean | ✅ Clean | `-race` Verified |

---

## 2. 瓶颈根因与优化手段 (Bottleneck & Optimization Mechanism)
- **Bottleneck Identified**: [e.g. Unnecessary heap escape due to interface boxing / Lock contention on global mutex]
- **Applied Remediation**: [e.g. Guard clause flattening, sync.Pool reuse, RCU pattern, zero-copy buffer]

---

## 3. 回归防护 (Regression Guard)
- Benchmark test registered at: `tests/bench_component_test.go`
- Target threshold guard: Latency MUST remain < 250 ns/op; Allocations MUST be 0.
```
