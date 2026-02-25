---
id: sh-01a-log-stats
domain: shell
difficulty: easy
timeout: 120
description: Log file statistics — requests, IPs, status codes, URLs (no histogram)
decomposed_from: sh-01-log-analyzer
---

Write a Bash script `log-stats.sh` that analyzes an Apache/Nginx access log file.

The script takes a log file path as `$1` and prints:
1. Total number of requests
2. Number of unique IP addresses
3. Top 10 IPs by request count: `count IP`
4. HTTP status code breakdown: `count status_code`
5. Top 10 requested URLs by count

Sample log format (Combined Log Format):
```
192.168.1.1 - - [10/Feb/2024:14:32:01 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "curl/7.68"
```

Requirements:
- Exit 1 with clear error if no file given or file missing
- `awk` for field extraction, `sort | uniq -c | sort -rn` for counting
- Works on GNU and BSD (avoid GNU-only flags)
