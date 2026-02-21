---
id: sh-03-health-check
domain: shell
difficulty: medium
timeout: 300
description: Service health check with retry and alerting
---

Write `health-check.sh` that monitors services from an INI-style config file.

Config format:
```
[http]
url=https://api.example.com/health
timeout=5
expected_status=200

[tcp]
host=db.internal
port=5432
timeout=3

[process]
name=nginx
```

Checks: HTTP (curl), TCP (`nc -z`), process (`pgrep`)
Each check retries 3× with 2s delay before failing.

Output:
```
[2024-02-10 14:32:01] ✓ http:api.example.com - OK (123ms)
[2024-02-10 14:32:02] ✗ tcp:db.internal:5432 - FAILED (connection refused)
```

Requirements: parse INI with bash built-ins only, `set -euo pipefail`, concurrent checks with `&` + `wait`, optional `--log FILE` and `--notify-email ADDRESS`
