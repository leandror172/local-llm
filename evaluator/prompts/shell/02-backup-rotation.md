---
id: sh-02-backup-rotation
domain: shell
difficulty: easy
timeout: 180
description: Backup script with rotation and compression
---

Write `backup.sh`: `./backup.sh <source-dir> <backup-dir> [--keep N]`

Creates `backup_YYYY-MM-DD_HH-MM-SS.tar.gz` in backup-dir, then deletes oldest backups keeping only N (default 7).

Output:
```
[INFO] Creating backup of /path/to/source...
[INFO] Backup created: /path/to/backup_2024-02-10_14-32-01.tar.gz (45 MB)
[INFO] Rotation: kept 7, deleted 2 old backups
```

Requirements:
- `set -euo pipefail`
- `mktemp` for atomic creation (write to temp, then `mv`)
- `trap` for cleanup on exit
- Exit 1 if source missing or backup dir creation fails
- Works on GNU/Linux and macOS (BSD tar)
