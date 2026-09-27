# Minimal Reproduction Scaffolds (`repro-scaffold`)

Minimal standalone reproduction templates for isolating bugs prior to modifying any production code.

## 1. Python Minimal Repro Scaffold (`scratch/repro.py`)

```python
#!/usr/bin/env python3
"""Minimal reproduction script for [Bug/Issue Summary].
Expected: [Expected behavior]
Actual: [Observed failure/exception]
"""
import sys

def test_reproduce():
    # 1. Arrange: set up minimal inputs and preconditions
    input_data = ...

    # 2. Act: invoke the buggy function or pathway
    result = ...

    # 3. Assert: confirm expected behavior (fails while bug is present)
    assert result == expected, f"Bug reproduced: got {result!r}"

if __name__ == "__main__":
    test_reproduce()
```

## 2. Go Minimal Repro Scaffold (`scratch/repro_test.go`)

```go
package repro_test

import (
	"testing"
)

func TestBugReproduction(t *testing.T) {
	// 1. Arrange: isolated inputs
	// 2. Act: call target function
	// 3. Assert: verify failure
	t.Fatalf("Bug reproduced: unexpected failure")
}
```

## 3. Node/TypeScript Minimal Repro Scaffold (`scratch/repro.ts`)

```typescript
import assert from "node:assert/strict";

async function reproduce() {
  // 1. Arrange
  // 2. Act
  // 3. Assert
}

reproduce().catch((err) => {
  console.error("Bug reproduced:", err);
  process.exit(1);
});
```

## Invariants
1. **Zero Production Mutation**: Do not touch production code before the repro script fails reliably.
2. **Minimal Dependency**: Keep the reproduction script self-contained with minimal external dependencies.
3. **Regression Promotion**: After fixing the root cause, promote the repro into a permanent test case.
