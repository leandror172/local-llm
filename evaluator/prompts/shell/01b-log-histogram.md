---
id: sh-01b-log-histogram
domain: shell
difficulty: easy
timeout: 120
description: Requests-per-hour histogram from access log
decomposed_from: sh-01-log-analyzer
---

Write a Bash script `log-histogram.sh` that reads an Apache/Nginx access log file and prints a requests-per-hour histogram.

The script takes a log file path as `$1` and prints one line per hour:
```
14:00  342 ████████████████████████████████
15:00   87 ████████
```

Format: `HH:00  count bar` where the bar scales so the busiest hour fills `tput cols` (default 80) minus the label width.

Sample log format (Combined Log Format):
```
192.168.1.1 - - [10/Feb/2024:14:32:01 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "curl/7.68"
```

Requirements:
- Exit 1 with clear error if no file given or file missing
- `awk` to extract the hour field from the timestamp
- `tput cols` for terminal width (default 80 if unavailable)
- `printf` for aligned output
- Works on GNU and BSD
