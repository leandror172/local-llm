"""Render one step of a resume.yaml into output lines.

Every step is (produce raw text) → (present it). `present()` holds all the shared
presentation rules — filters, head, fallback, title suppression, trailing blank — so a
new step kind only has to say how it produces text.

Note the distinction between *empty* and *absent*, which the options encode separately:
a step that yields no lines still prints its title and fallback (it ran, and found
nothing), unless `omit_if_empty` says the whole section should disappear.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List

from sessiontracking.register import locate

from .config import Step


class StepError(Exception):
    """Raised when a step cannot produce its content."""


def present(step: Step, raw: str) -> List[str]:
    """Apply the shared presentation rules to a step's raw text.

    Order: split → drop filtered lines → head → title/fallback → trailing blank.
    Returns [] only when the step is omitted (`omit_if_empty` and nothing to show);
    a trailing blank is never appended to an omitted step.
    """
    # rstrip first: "\n".splitlines() is [""] — one blank line, a NON-empty list — so a
    # whitespace-only producer would defeat omit_if_empty and leave a ghost section.
    # Interior blank lines are preserved; only trailing ones are shed.
    lines = [
        line for line in raw.rstrip("\n").splitlines()
        if not any(re.search(pattern, line) for pattern in step.filters)
    ]
    if step.head is not None:
        lines = lines[: step.head]

    if lines:
        body = lines
        title = [step.title] if step.title else []
    else:
        if step.omit_if_empty:
            return []
        body = [step.fallback] if step.fallback is not None else []
        title = [step.title] if step.title and step.title_on_empty else []

    result = title + body
    if step.trailing_blank:
        result.append("")
    return result


# ── producers: each returns the step's raw text ───────────────────────────────


def _produce_text(step: Step, ctx: "Context") -> str:
    return "\n".join(line.format(date=ctx.date) for line in step.lines)


def _produce_region(step: Step, ctx: "Context") -> str:
    """Resolve a register role (preferred) or a raw ref key.

    A role goes through the SAME `locate()` the handoff writes with, so read and write
    can never disagree about where the region begins.
    """
    if step.role:
        role = ctx.register.get(step.role)
        if role is None:
            raise StepError(
                f"resume step names register role {step.role!r}, which this repo's "
                f"register does not define. Add it to registry.yaml (write_mode: nomodel, "
                f"used_by: [read]) or use `ref_key:` instead."
            )
        target = ctx.repo_root / role["file"]
        if not target.exists():
            raise StepError(f"role {step.role!r} points at missing file: {target}")
        return locate(role, target.read_text()).interior
    return ctx.ref_lookup(step.ref_key)


def _produce_log_next(step: Step, ctx: "Context") -> str:
    """The `### Next` block of the NEWEST session-log entry.

    A fixed kind, not a `run: awk …`, because the overlay owns session-log.md's
    structure and has already changed it once (latest-only + slugged archive).
    """
    role = ctx.register.get(step.role or "log-entry")
    if role is None:
        raise StepError("log_next needs a register role naming the session log file")
    log = ctx.repo_root / role["file"]
    if not log.exists():
        return ""
    return _extract_next_section(log.read_text())


def _extract_next_section(text: str) -> str:
    """The newest entry's heading, then its `### Next` block, up to the next rule.

    The heading is included — it tells you *which* session's Next you are reading.
    Lines between the heading and `### Next` are skipped.
    """
    out: List[str] = []
    found_entry = in_next = False
    for line in text.splitlines():
        if not found_entry:
            if line.startswith("## 20"):
                found_entry = True
                out.append(line)
            continue
        if not in_next:
            if line.startswith("### Next"):
                in_next = True
                out.append(line)
            continue
        if line.startswith("---"):
            break
        out.append(line)
    return "\n".join(out)


def _produce_git_log(step: Step, ctx: "Context") -> str:
    # Plain `git`, deliberately: `rtk git log` silently drops merge commits.
    return ctx.run_shell(f"git -C {ctx.repo_root} log --oneline -{step.count or 5}")


def _produce_git_status(step: Step, ctx: "Context") -> str:
    return ctx.run_shell(f"git -C {ctx.repo_root} status -s")


def _produce_run(step: Step, ctx: "Context") -> str:
    """The escape hatch. Executable config, at Makefile trust level."""
    return ctx.run_shell(step.command)


PRODUCERS: Dict[str, Callable[[Step, "Context"], str]] = {
    "text": _produce_text,
    "region": _produce_region,
    "log_next": _produce_log_next,
    "git_log": _produce_git_log,
    "git_status": _produce_git_status,
    "run": _produce_run,
}


class Context:
    """Everything a producer needs: repo root, the register, the date, a shell."""

    def __init__(self, repo_root: Path, register: Dict[str, Any], date: str):
        self.repo_root = repo_root
        self.register = register
        self.date = date

    def run_shell(self, command: str) -> str:
        proc = subprocess.run(
            command, shell=True, cwd=self.repo_root,
            capture_output=True, text=True,
        )
        return proc.stdout if proc.returncode == 0 else ""

    def ref_lookup(self, key: str) -> str:
        script = self.repo_root / ".claude" / "tools" / "ref-lookup.sh"
        if not script.exists():
            raise StepError(
                f"`ref_key: {key}` needs the ref-indexing overlay's ref-lookup.sh at "
                f"{script}. Prefer `role:` — it resolves through the register."
            )
        return self.run_shell(f"{script} {key}")


def render(step: Step, ctx: Context) -> List[str]:
    """Produce a step's text, then present it."""
    raw = PRODUCERS[step.kind](step, ctx)
    return present(step, raw)
