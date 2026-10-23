# Dead-Test Prevention, Bidirectional Format Contracts & Quantity Boundaries (`references/dead-test-and-quantity-guards.md`)

Load this reference during TDD Step 1 (authoring tests) and Code Review to prevent tautological tests, silent parser drift, and quantity-dimension bugs.

---

## 1. The Four Dead-Test Defenses (MUST)

1. **Static Assertion Occurrence & Anchor Precheck**:
   - When writing a static source guard (grep/AST/slice check), never slice with a bare substring (`indexOf("def foo")` or `[^{]*{`) that can match a module header comment or stop early at a destructured parameter `{ a, b }`.
   - Anchor slices with a leading newline (`\ndef foo`) and parameter-list-aware boundaries, and assert the target pattern occurs the expected number of times before asserting its contents.
2. **Probe the Real Source (No Re-Implemented Logic in Tests)**:
   - Dynamic tests MUST import and execute the real production function/module. Copying a regex, SQL query, or formula into the test file and testing the copy proves nothing about production code.
3. **Fixture Coherence (Ban Constant-False / Vacuous Fixtures)**:
   - A test loop `for item in items: assert check(item)` over an empty list `items = []` passes vacuously. Every collection-iterating test MUST assert `len(items) > 0` before the loop.
4. **Fixture Shape Fidelity**:
   - Mock/fixture payloads MUST match the exact nesting, types, and edge-case nulls of the real upstream API/DB response (verified against a captured sample), never an idealized hand-typed stub.

---

## 2. Bidirectional Format-Contract Verification (Producer + Consumer) (MUST)

Whenever code writes a structured artifact (Markdown table, JSONL log, config, frontmatter) that another script or parser reads back:
1. **Producer Self-Check**: The writer test MUST parse its own generated output using the real reader/parser (round-trip assertion), never just `assert "key" in output_str`.
2. **Consumer Real-Corpus Check**: The reader/parser test MUST include at least one sample containing real-world formatting hazards (escaped pipes `\|`, trailing whitespace, CRLF line endings, multi-block YAML).

---

## 3. Quantity Semantics & Bounded Domain Extremes (MUST)

The same float can represent three incompatible dimensions: **ratio** (`1.27` = 1.27x the baseline), **share** (`0.0..1.0` proportion of a whole), or **percent** (`0.0..100.0%`). Passing a `ratio` into a consumer expecting a `share` (e.g. a CSS progress bar `width: (1 - ratio) * 100%`) renders `width: -26.8%` or `126.8%` whenever `ratio > 1.0`.

1. **Name the Dimension in Types & Identifiers**: Never pass raw numbers across layers under ambiguous names like `val` or `rate`; name the dimension explicitly (`ratio_to_share(ratio)` vs `share_to_percent(share)`).
2. **Explicit Conversion & Clamping at Bounded Sinks**: Any value feeding a bounded domain (`0..100%` width, `0..1` opacity, angle, bucket index) MUST go through a named conversion function at the boundary and assert the result lies within `[min, max]`.
3. **Mandatory Dual-Extreme Test Fixtures (`> 1` and `< 1`)**: Seed data where `ratio ≈ 0.95..1.0` masks dimension bugs completely. Tests for any ratio/share/percentage calculation MUST include fixtures on **both sides of 1.0** (e.g. `1.27` and `0.45`) plus boundary zeros.
