# Evaluation Harness Falsification & Audit Verification Pitfalls (`references/verification-pitfalls-and-eval-gates.md`)

Load this reference when verifying counter-intuitive benchmark/evaluation numbers (0% lift, total wipeout, or 100% pass) or checking complex audit claims.

---

## 1. Falsify the Harness Before Judging Capability (The 4-Step Discipline) (MUST)

When an evaluation or benchmark reports a counter-intuitive result (e.g. `0.00` median score on in-corpus questions, 100% `wrong-span`, or an implausibly perfect `1.00`), **do NOT conclude "the feature gives zero lift" and do NOT burn paid API calls re-running**. A 100% wipeout on baseline tasks is strong evidence of a measurement bug:

1. **State the Prior Expectation First**: Write down the minimum pass rate expected on straightforward in-domain tasks if the component works at all. Major conflict with the prior indicts the measurement pipeline first.
2. **Zero-Cost Probes First**: Isolate each hop (`input -> intermediate state -> graded output`) using deterministic, zero-cost probes (direct function calls, SQLite queries, byte-exact hash recomputation in Python) without invoking paid LLM endpoints.
3. **Falsify One Layer at a Time**: Verify and fix in strict order: `Corpus Hygiene -> Observation Channel -> Scoring Metric -> Query Compilation / Model Behavior`. Never stack two fixes in one run ("symptom disappeared" != "measurement is valid").
4. **Explicitly Invalidate Tainted Runs**: In the evaluation report, mark prior runs caused by harness bugs as **INVALIDATED (with root cause)** and designate only the post-fix run as the decision baseline.

---

## 2. The Three RAG / Retrieval Evaluation Gates (MUST)

Before trusting any retrieval or agent evaluation verdict (especially a negative kill-switch criterion), verify all three gates:

1. **Gate 1 — Corpus Hygiene Gate**:
   - Assert the indexed file set matches an explicit extension allowlist (e.g. `.md` only) and excludes hidden directories (`.git/`, `.claude/`, `.trae/`, `.codebuddy/`), evaluation output folders, and the `.db` / `.db-wal` index files themselves (preventing recursive self-indexing bloat and background IDE file edits from mutating the corpus SHA-256 fingerprint into perpetual `ErrCorpusStale`).
   - **Checkable Proof**: Run index build twice back-to-back; the second run MUST report `0 docs / 0 chunks` indexed and an identical corpus fingerprint.
2. **Gate 2 — Observation Channel Gate**:
   - Runtime trace truncation (e.g. `MaxTraceDetail = 512B`) is a valid memory guard in production, but breaks offline evaluation when a single retrieved chunk is `~1.5KB` (truncating JSON on the first hit).
   - **Checkable Proof**: Grade against raw tool outputs captured via an evaluation wrapper/collector, never truncated trace strings. Compare `parsed_hits(full_output)` vs `parsed_hits(trace_detail)` — any difference proves channel truncation.
3. **Gate 3 — Span Coverage Scoring Gate**:
   - Confirm whether returned spans (e.g. `512-rune` fixed chunks) and ground-truth `expect_spans` (short answer paragraphs) share the same granularity. When chunks are wider than answer spans, IoU (`|want ∩ got| / |want ∪ got|`) systematically penalizes valid hits (`~0.09..0.25`); grade with **per-want recall coverage** (`|want ∩ ∪got| / |want|`, capped at `1.0`) instead.

---

## 3. Detailed Audit Claim Verification Pitfalls Catalog

- **Doc comment vs implementation**: Config comments often promise "total budget" while the loop variable resets every iteration. Read the counter's lexical scope.
- **"Same shape" != "same content"**: Equal row counts across two DB snapshots do not prove byte identity; run `cmp` / hash comparison before declaring a copy redundant.
- **Byte caps are not time limits**: Stream size guards bound memory, never wall-clock duration; per-hop timeouts multiplied by retries are worst-case bounds, not a total deadline.
- **Unset config keys masquerading as broken mechanisms**: If auto-gc/TTL did not fire, verify `config --get <key>` is actually set before blaming the eviction code.
- **Hypothetical future I/O vs present in-memory reality**: Refute or downgrade P1 claims ("missing `context.Context` will hang if an I/O impl is added") when all registered implementations are sub-millisecond in-memory operations.
- **Microsecond mutex hold vs macroscopic contention**: Calculate actual hold time (`<1µs` slice copy) and arrival rate before accepting "allocation inside lock" as a P1 bottleneck.
- **Wrong registered remedy for a real defect**: A skim may record "field X is unmasked" when X *is* masked but the endpoint lacks an origin gate. Derive the fix from the code read, and correct the registry entry.
- **Adjudicating a delegate's deviation rationale**: Check a subagent's claim ("version X is broken / flag Y is required") against primary upstream artifacts (release notes, dependency source, actual CLI output), never against the plan's assumption.
- **Comparative mutation proof for weak-test claims**: Prove a test replacement by applying **one mutation** under which the old assertion stays green and the new assertion goes red.
