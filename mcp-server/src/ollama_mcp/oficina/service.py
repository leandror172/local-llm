"""Shared implementation layer for the MCP tools (T7) and the CLI (T8).

One set of functions — ``submit`` / ``status`` / ``result`` / ``cancel`` — behind
both surfaces, so verb logic is never duplicated. Functions RAISE typed errors
for the discriminating failure modes; the thin surfaces convert them (the MCP
tools to error strings per the server convention, the CLI to messages + exit
codes).

``submit`` embodies the happens-before handoff (P1-D6): create run dir + spec →
append RunSubmitted → push queue marker → ensure a worker. The worker can only
discover the run through the queue, so it can never append before the surface's
RunSubmitted. ``ensure_worker`` is an injectable seam (tests pass a spy so no real
process spawns).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .fifo import Fifo
from .ledger import Ledger, fold_state
from .store import Store, UnknownRunError
from .workerproc import WorkerProc

_TERMINAL_STATES = {"completed", "failed", "cancelled"}

_PHASE_BY_EVENT = {
    "RunSubmitted": "queued",
    "IntakeRejected": "intake",
    "GenerationStarted": "generating",
    "GenerationFinished": "packaging",
    # P2 loop phases (folded under the public 'working' state) — without these a
    # function run reports phase='queued' for its whole life while it is iterating.
    "AssemblyDone": "assembling",
    "IterationStarted": "looping",
    "IterationEvaluated": "looping",
    "FreshStart": "looping",
    "ModelEscalated": "looping",
    "Exhausted": "failed",
    "Delivered": "delivered",
    "Failed": "failed",
    "Cancelled": "cancelled",
}


class SpecShapeError(Exception):
    """The submitted object is not shaped like a run spec (not even a run)."""


class RunNotTerminalError(Exception):
    """run_result was asked for a run that has not reached a terminal state."""

    def __init__(self, run_id: str, state: str) -> None:
        super().__init__(f"run {run_id} is not terminal yet (state={state})")
        self.run_id = run_id
        self.state = state


def watch_cmd(run_id: str) -> str:
    """The exact shell command that tails a run to terminal (P1-D10)."""
    return f"oficina watch {run_id}"


def fold_phase(events: List[Dict[str, Any]]) -> str:
    """Fold events to a coarse internal phase, tolerating unknown names."""
    phase = "queued"
    for event in events:
        if event["event"] in _PHASE_BY_EVENT:
            phase = _PHASE_BY_EVENT[event["event"]]
    return phase


def _shape_check(spec: Any) -> Optional[str]:
    """Minimal shape validation — deep rules are the worker's IntakeRejected."""
    if not isinstance(spec, dict):
        return "spec must be a mapping"
    if not isinstance(spec.get("deliverable"), dict):
        return "spec.deliverable must be a mapping"
    return None


def _default_ensure_worker(root: Path) -> None:
    """Ensure a live worker owns the store (spawns one detached if none)."""
    from .worker import worker_argv

    WorkerProc(root).ensure_worker(worker_argv())


def _last_event(events: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    """Return the last event with ``name``, or None."""
    for event in reversed(events):
        if event["event"] == name:
            return event
    return None


def submit(
    root: str | Path,
    spec: Dict[str, Any],
    ensure_worker: Optional[Callable[[Path], None]] = None,
    now_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Persist + queue a run, ensure a worker; return {run_id, watch_cmd, queue_position}."""
    root = Path(root)
    shape_error = _shape_check(spec)
    if shape_error:
        raise SpecShapeError(shape_error)
    store, fifo = Store(root), Fifo(root)
    run_id = store.create_run(spec)
    queue_position = len(fifo._markers()) + 1
    # submitted_from: origin annotation (T-89 D2) — display-only, never a filter key.
    Ledger(store.events_path(run_id)).run_submitted(
        {"queue_position": queue_position, "submitted_from": os.getcwd()}
    )
    fifo.push(run_id, now_ms)
    (ensure_worker or _default_ensure_worker)(root)
    return {"run_id": run_id, "watch_cmd": watch_cmd(run_id), "queue_position": queue_position}


def status(root: str | Path, run_id: str, since_offset: int = 0) -> Dict[str, Any]:
    """Fold the ledger into {state, phase, events[since:], next_offset}."""
    store = Store(root)
    if not store.run_dir(run_id).exists():
        raise UnknownRunError(run_id)
    all_events = Ledger(store.events_path(run_id)).read()
    next_offset = all_events[-1]["offset"] + 1 if all_events else 0
    return {
        "state": fold_state(all_events),
        "phase": fold_phase(all_events),
        "events": [e for e in all_events if e["offset"] >= since_offset],
        "next_offset": next_offset,
    }


def result(root: str | Path, run_id: str) -> Dict[str, Any]:
    """Return the terminal result; raise for unknown / not-terminal (pruned is OK)."""
    store = Store(root)
    if not store.run_dir(run_id).exists():
        raise UnknownRunError(run_id)
    events = Ledger(store.events_path(run_id)).read()
    state = fold_state(events)
    if state not in _TERMINAL_STATES:
        raise RunNotTerminalError(run_id, state)
    artifacts_pruned = not store.artifacts_dir(run_id).exists()
    if state == "completed":
        delivered = _last_event(events, "Delivered")["payload"]
        return {
            "state": state,
            "report": delivered.get("report"),
            "deliverable": delivered.get("deliverable"),
            "artifacts_pruned": artifacts_pruned,
        }
    terminal = (
        _last_event(events, "Failed")
        or _last_event(events, "IntakeRejected")
        or _last_event(events, "Cancelled")
        or _last_event(events, "Exhausted")
    )
    report = terminal["payload"] if terminal else {}
    # Exhausted is a terminal 'failed' with a best attempt attached (S11) — surface the
    # branch/commit as the deliverable so `run_result` is not an empty, pointerless failure.
    deliverable = None
    if terminal and terminal["event"] == "Exhausted":
        branch, commit = report.get("branch"), report.get("best_attempt_ref")
        if branch or commit:
            deliverable = {"best_attempt": True, "branch": branch, "commit": commit}
    return {
        "state": state,
        "report": report,
        "deliverable": deliverable,
        "artifacts_pruned": artifacts_pruned,
    }


def list_runs(root: str | Path) -> List[Dict[str, Any]]:
    """Summarize every run: id, folded state, artifacts footprint, prune eligibility."""
    store = Store(root)
    if not store.runs_dir.exists():
        return []
    summaries: List[Dict[str, Any]] = []
    for run_dir in sorted(store.runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        events = Ledger(store.events_path(run_id)).read()
        artifacts_dir = store.artifacts_dir(run_id)
        artifacts_bytes = sum(f.stat().st_size for f in artifacts_dir.rglob("*") if f.is_file()) if artifacts_dir.exists() else 0
        summaries.append(
            {
                "run_id": run_id,
                "state": fold_state(events),
                "artifacts_bytes": artifacts_bytes,
                "prune_eligible": artifacts_bytes > 0 and fold_state(events) in _TERMINAL_STATES,
            }
        )
    return summaries


def cancel(root: str | Path, run_id: str) -> Dict[str, Any]:
    """Write the cooperative cancel flag (P1-D6); return the current {state}."""
    store = Store(root)
    if not store.run_dir(run_id).exists():
        raise UnknownRunError(run_id)
    (store.run_dir(run_id) / "cancel").write_text("1", encoding="utf-8")
    return {"state": fold_state(Ledger(store.events_path(run_id)).read())}
