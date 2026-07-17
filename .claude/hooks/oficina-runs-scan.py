#!/usr/bin/env python3
"""SessionStart hook to surface newly-finished oficina runs.

Wired as a SessionStart hook to scan the oficina run store and surface
runs that have completed (Delivered), failed (Failed), or were cancelled
(Cancelled) since last surfaced. Each surfaced run gets a marker file so
it's not resurfaced in subsequent scans.

Fail open: on any error, print nothing and exit 0 — a hook must never break
session startup.
"""
import json
import os
import sys
from pathlib import Path

def _get_store_root() -> Path:
    """Get the oficina store root from env var or default path."""
    store_root = os.environ.get("OFICINA_ROOT")
    if not store_root:
        store_root = Path.home() / ".local/share/oficina"
    return Path(store_root)

def _run_dirs(store_root: Path) -> list[Path]:
    """Return sorted list of run directories under the store root."""
    runs_dir = store_root / "runs"
    if not runs_dir.exists():
        return []
    return sorted(runs_dir.iterdir())

def _read_valid_events(events_path: Path) -> list[dict]:
    """Read events.jsonl file, skipping any line that fails to parse."""
    valid_events = []
    try:
        with open(events_path, "r") as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                try:
                    event = json.loads(stripped_line)
                    valid_events.append(event)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass  # Fail open — ignore any read errors
    return valid_events

def _fold_terminal_state(events: list[dict]) -> tuple[str, str | None]:
    """Determine the run's state and detail from its last valid event."""
    if not events:
        return "not terminal", None
    
    last_event = events[-1]
    event_type = last_event.get("event")
    
    if event_type == "Delivered":
        payload = last_event.get("payload", {})
        deliverable = payload.get("deliverable", {})
        kind = deliverable.get("kind")

        if kind == "function":
            branch = deliverable.get("branch", "unknown")
            detail = f"branch: {branch} — oficina result <run_id>"
        elif kind == "file":
            detail = f"file: {deliverable.get('target', 'unknown')}"
        else:
            detail = "answer ready — oficina result <run_id>"
        return "completed", detail

    elif event_type in ("Failed", "IntakeRejected"):
        payload = last_event.get("payload", {})
        what = payload.get("what")
        return "failed", what or "see oficina result <run_id>"

    elif event_type == "Exhausted":
        # A loop run that never converged: terminal 'failed' with a best attempt on a branch.
        payload = last_event.get("payload", {})
        limit_hit = payload.get("limit_hit", "exhausted")
        return "failed", f"loop {limit_hit} — best attempt on {payload.get('branch', 'the run branch')} — oficina result <run_id>"

    elif event_type == "Cancelled":
        return "cancelled", None

    return "not terminal", None

def _extract_origin(events: list[dict]) -> str:
    """Extract the submitted_from value from the first RunSubmitted event."""
    for event in events:
        if event.get("event") == "RunSubmitted":
            payload = event.get("payload", {})
            return payload.get("submitted_from", "unknown")
    return "unknown"

def _format_run_line(run_id: str, state: str, origin: str, detail: str | None) -> str:
    """Format a run line for output."""
    if state == "cancelled":
        return f"oficina run {run_id} cancelled — submitted from {origin}"
    if state in ("completed", "failed"):
        detail = (detail or "").replace("<run_id>", run_id)
        return f"oficina run {run_id} {state} — submitted from {origin} — {detail}"
    return ""

def _surface_run(run_dir: Path) -> tuple[bool, str, str, str, str | None]:
    """Surface a run if it's terminal and has no surfaced marker."""
    surfaced_marker = run_dir / "surfaced"
    if surfaced_marker.exists():
        return False, "", "", "", None
    
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        return False, "", "", "", None
    
    events = _read_valid_events(events_path)
    state, detail = _fold_terminal_state(events)
    
    if state == "not terminal":
        return False, "", "", "", None
    
    origin = _extract_origin(events)
    line = _format_run_line(run_dir.name, state, origin, detail)
    
    if line:
        surfaced_marker.write_text("1")
        return True, state, origin, line, detail
    return False, "", "", "", None

def main() -> int:
    """Main entry point for the hook script."""
    try:
        store_root = _get_store_root()
        
        run_dirs = _run_dirs(store_root)
        surfaced_runs = []
        
        for run_dir in run_dirs:
            surfaced, state, origin, line, detail = _surface_run(run_dir)
            if surfaced:
                surfaced_runs.append((line, detail))
        
        if not surfaced_runs:
            return 0
        
        # Print header first
        print("oficina: runs finished since last surfaced —")
        
        for line, _ in surfaced_runs:
            print(line)
        
        return 0
    except Exception:
        return 0  # Fail open — a hook must never break session startup

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # Fail open — a hook must never break session startup
