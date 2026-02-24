---
id: go-08-slog-handler
domain: go
difficulty: hard
timeout: 600
description: Custom slog.Handler implementation with filtering and formatting
---

Implement a custom `slog.Handler` in Go that writes structured log lines to an `io.Writer`.

Requirements:

1. `FilterHandler` struct that implements `slog.Handler` and wraps another handler
   - Constructor: `NewFilterHandler(inner slog.Handler, minLevel slog.Level) *FilterHandler`
   - Only passes records at or above `minLevel` to the inner handler
   - All four interface methods: `Enabled`, `Handle`, `WithAttrs`, `WithGroup`

2. `TextColorHandler` struct that implements `slog.Handler` and writes colored text
   - Constructor: `NewTextColorHandler(w io.Writer, opts *slog.HandlerOptions) *TextColorHandler`
   - Format: `[LEVEL] time=HH:MM:SS msg="..." key=value key=value`
   - Color codes (ANSI): DEBUG=cyan, INFO=green, WARN=yellow, ERROR=red
   - `WithAttrs` should prepend attrs to all subsequent records
   - `WithGroup` should prefix all attr keys with the group name

3. A `NewLogger(w io.Writer, level slog.Level) *slog.Logger` convenience constructor that:
   - Wraps `TextColorHandler` with `FilterHandler`
   - Returns a ready-to-use `*slog.Logger`

Requirements:
- Full implementation of all `slog.Handler` interface methods
- `WithAttrs` and `WithGroup` must return a new handler (immutable style)
- Include a `main()` that demonstrates all log levels and grouped attributes
