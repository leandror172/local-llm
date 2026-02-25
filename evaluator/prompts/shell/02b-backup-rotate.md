---
id: sh-02b-backup-rotate
domain: shell
difficulty: easy
timeout: 120
description: Backup rotation — keep N newest, delete the rest
decomposed_from: sh-02-backup-rotation
---

Write `backup-rotate.sh`: `./backup-rotate.sh <backup-dir> [--keep N]`

Scans backup-dir for files matching `backup_*.tar.gz`, keeps the N newest by filename sort (filenames are timestamped so lexicographic order = chronological order), and deletes the rest.

Default N is 7 if `--keep` is not provided.

Output:
```
[INFO] Rotation: kept 7, deleted 2 old backups
```

If fewer than N backups exist, print kept count and delete nothing:
```
[INFO] Rotation: kept 3, nothing to delete
```

Requirements:
- `set -euo pipefail`
- Exit 1 if backup-dir does not exist
- Use `ls -1 | sort` (or `printf '%s\n' backup_*.tar.gz | sort`) — do not parse `ls` for metadata
- Works on GNU/Linux and macOS
