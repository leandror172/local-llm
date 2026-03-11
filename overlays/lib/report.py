"""Action accumulator and report printer."""

import json
from pathlib import Path

_actions: list[dict] = []


def record(action: str, target: str, reason: str = "", details: str = ""):
    _actions.append({"action": action, "target": target, "reason": reason, "details": details})
    tag = f"[{action}]"
    line = f"  {tag:<12} {target}"
    if reason:
        line += f"  — {reason}"
    print(line)
    if details:
        print(f"               {details}")


def print_report(report_format: str, report_file: str | None):
    counts: dict[str, int] = {}
    for a in _actions:
        counts[a["action"]] = counts.get(a["action"], 0) + 1

    if report_format == "json":
        output = json.dumps(_actions, indent=2)
    else:
        lines = ["", "── Summary " + "─" * 50]
        col_w = max(len(k) for k in counts) if counts else 8
        for action_name, count in sorted(counts.items()):
            lines.append(f"  {action_name:<{col_w + 2}} {count}")
        lines.append("")
        output = "\n".join(lines)

    if report_file:
        Path(report_file).write_text(output)
        print(f"\nReport written to: {report_file}")
    else:
        print(output)
