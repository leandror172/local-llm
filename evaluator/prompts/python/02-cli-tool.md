---
id: python-02-cli-tool
domain: python
difficulty: easy
timeout: 180
description: Click CLI tool with subcommands and configuration file
---

Write a CLI tool using `click` that manages a local key-value store (JSON file at `~/.mystore.json`).

Commands:
1. `store set <key> <value>` — save key=value
2. `store get <key>` — print value or "Key not found" with exit code 1
3. `store delete <key>` — remove key; error if not found
4. `store list [--json]` — list all keys; with `--json` print full JSON
5. `store clear --confirm` — delete all entries; `--confirm` flag required

Requirements:
- Top-level `@click.group()` named `store`
- `--config PATH` option on the group to override the default file path
- `click.echo` for all output (not `print`)
- Atomic writes: write to temp file then `os.replace`
- Type hints on all functions
