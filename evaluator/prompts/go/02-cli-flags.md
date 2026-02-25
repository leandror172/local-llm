---
id: go-02-cli-flags
domain: go
difficulty: easy
timeout: 600
description: CLI tool with flag parsing and subcommands
---

Write a CLI tool in Go (standard library only, no Cobra) that:

1. Has two subcommands: `add` and `list`
2. The `add` subcommand takes a `--name` string flag and a `--value` integer flag, and prints `Added: name=<name> value=<value>`
3. The `list` subcommand takes a `--json` boolean flag; if set, prints a hardcoded list of 3 items as JSON; otherwise prints them one per line
4. Prints a usage message if called with no subcommand or an unknown subcommand

Requirements:
- Use `flag.NewFlagSet` for subcommand parsing
- `os.Args[1]` selects the subcommand
- Handle missing required flags with a clear error message
- Include `main()` with proper exit codes (0 = success, 1 = error)
