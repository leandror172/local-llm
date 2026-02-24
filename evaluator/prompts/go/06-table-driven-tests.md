---
id: go-06-table-driven-tests
domain: go
difficulty: medium
timeout: 600
description: Table-driven test suite for a string parser
---

Write a string parser and its complete table-driven test suite in Go.

The parser to implement:

```go
// ParseDuration parses a human-readable duration string into seconds.
// Supports: "30s", "5m", "2h", "1d", "1h30m", "2d12h" (combinations allowed).
// Returns an error for empty strings, unknown units, or invalid numbers.
func ParseDuration(s string) (int64, error)
```

Examples:
- `"30s"` → `30`
- `"5m"` → `300`
- `"2h"` → `7200`
- `"1d"` → `86400`
- `"1h30m"` → `5400`
- `"2d12h"` → `216000`
- `""` → error
- `"5x"` → error
- `"abc"` → error

Requirements for the test file:
1. Use `testing.T` with table-driven tests (`[]struct{ name, input string; want int64; wantErr bool }`)
2. At least 15 test cases covering: simple units, combinations, edge cases (zero values, large numbers), error cases
3. Use `t.Run(tc.name, ...)` for subtests
4. Use `t.Parallel()` at both the top level and each subtest
5. A separate `TestParseDuration_EmptyInput` function demonstrating named error inspection
