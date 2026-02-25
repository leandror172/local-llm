---
id: sh-05-deploy-script
domain: shell
difficulty: hard
timeout: 420
description: Zero-downtime deployment script with rollback
---

Write `deploy.sh` for blue-green deployment with symlink swap.

Directory structure:
```
/opt/myapp/
├── releases/20240210-143200/  ← old
├── releases/20240210-160000/  ← new
├── current -> releases/...    ← symlink
└── shared/{.env,uploads/}
```

Usage: `./deploy.sh <artifact-url> [--env production|staging] [--keep N]`

Steps (each printed with timestamp):
1. Download artifact (tar.gz) to temp dir
2. Create release dir with timestamp, extract artifact
3. Symlink `shared/.env` and `shared/uploads/` into release
4. Run `./release/bin/migrate` if exists
5. Verify: `curl -sf http://localhost:8080/health` (30s timeout)
6. Atomic symlink swap: `ln -sfn new /opt/myapp/current`
7. Reload: `systemctl reload myapp`
8. Keep last N (default 5), delete older

Rollback: auto on failure + `./deploy.sh --rollback`
Locking: lock file to prevent concurrent runs
`--dry-run` mode

Requirements: `set -euo pipefail`, `trap` for cleanup/rollback, log to file AND stdout
