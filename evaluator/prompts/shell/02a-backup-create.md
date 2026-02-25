---
id: sh-02a-backup-create
domain: shell
difficulty: easy
timeout: 120
description: Atomic backup creation with mktemp, trap, and size output
decomposed_from: sh-02-backup-rotation
---

Write `backup-create.sh`: `./backup-create.sh <source-dir> <backup-dir>`

Creates `backup_YYYY-MM-DD_HH-MM-SS.tar.gz` in backup-dir.

Output:
```
[INFO] Creating backup of /path/to/source...
[INFO] Backup created: /path/to/backup_2024-02-10_14-32-01.tar.gz (45 MB)
```

Requirements:
- `set -euo pipefail`
- `mktemp` for atomic creation: write to temp file in backup-dir, then `mv` to final name
- `trap` to clean up the temp file on exit (including errors)
- Exit 1 if source dir is missing or backup dir cannot be created
- Works on GNU/Linux and macOS (BSD tar)
