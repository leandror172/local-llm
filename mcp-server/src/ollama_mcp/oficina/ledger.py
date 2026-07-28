"""Event-sourced JSONL ledger for oficina runs (P1-D5, P1-D6).

Each ledger line is one JSON envelope ``{offset, ts, event, payload}`` where
``offset`` is the 0-based line index (NOT a byte offset). State is a fold over
the ``event`` names; unknown event names MUST be tolerated (forward
compatibility for draft-PN events).

Single-writer discipline (P1-D6) is enforced by call topology, not locks: the
MCP surface appends only ``RunSubmitted`` before queueing; the worker appends
everything after. Appends are raw ``O_APPEND`` single-line writes — a crashed
writer leaves a torn last line, which reads tolerate by JSON parse failure on
the last line only. An earlier-line parse failure is real corruption.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Public-state fold mapping (event model § "Public state fold"). Its keys ARE the
# frozen run-event registry (ref:delegate-event-model) — RUN_EVENTS derives from it
# below so the two can never drift.
_STATE_BY_EVENT: dict[str, str] = {
    "RunSubmitted": "queued",
    "IntakeRejected": "failed",
    "GenerationStarted": "working",
    "GenerationFinished": "working",
    "AssemblyDone": "working",  # P2-T4 (P2-D13): worktree + C0 baseline built
    "IterationStarted": "working",  # P2-T6: loop events
    "IterationEvaluated": "working",
    "FreshStart": "working",
    "ModelEscalated": "working",
    "Exhausted": "failed",
    "Delivered": "completed",
    "Failed": "failed",
    "Cancelled": "cancelled",
}

# Run events that carry information without moving the run's public state. Membership of
# the fold map and membership of the run ledger are ORTHOGONAL, and conflating them put a
# run event in the worker registry (see below) — so the two are named separately here.
_NON_FOLDING_RUN_EVENTS: frozenset[str] = frozenset(
    {
        # T-112: the input-fit guard could not resolve the model's context ceiling, so it
        # is not running for this run. The event exists so the guard's ABSENCE is visible
        # to whoever reads the RUN (`run_status`), never inferred — which is why it is a
        # run event despite having been filed under WORKER_EVENTS until session 131. It is
        # emitted on the run ledger (`loop.py`, via `self.ledger`); the old classification
        # was inert only because nothing asserted it.
        "ContextLimitUnknown",
        # P4-T5: the Phase-2 rubric judge's outcome at packaging. Does not fold — the run
        # is `working` before and after, and a failing judge does NOT block `Delivered`
        # (S17 gates DPO chosen labels, not delivery; H1 is Claude-gated by design).
        "Judged",
    }
)

RUN_EVENTS: frozenset[str] = frozenset(_STATE_BY_EVENT) | _NON_FOLDING_RUN_EVENTS
WORKER_EVENTS: frozenset[str] = frozenset(
    {
        "WorkerStarted",
        "WorkerStopped",
        "RetentionPruned",
        "RefsDropped",
    }
)


class LedgerCorruptionError(Exception):
    """Raised when a non-terminal ledger line fails to parse (real corruption)."""


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string (Zulu)."""
    return datetime.now(timezone.utc).isoformat()


def _read_valid_events(path: Path) -> List[Dict[str, Any]]:
    """Read all intact event envelopes from ``path``.

    Tolerates a single torn last line (crashed writer) by dropping it. A parse
    failure on any earlier line is real corruption and raises.
    """
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    # Drop trailing blank lines so a torn line followed only by blanks is still
    # recognized as the (tolerated) last line rather than a mid-file failure.
    while lines and not lines[-1].strip():
        lines.pop()
    events: List[Dict[str, Any]] = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if i == len(lines) - 1:
                break  # tolerate a torn last line (crashed writer)
            raise LedgerCorruptionError(f"Failed to parse line {i}: {exc}")
    return events


def _valid_prefix_bytes(path: Path) -> int:
    """Return the byte length of the leading run of valid, newline-terminated lines.

    Everything after this offset is crashed-writer tail junk (a torn line, a
    non-newline-terminated line, or trailing blanks) and is safe to truncate.
    """
    data = path.read_bytes()
    good_end = 0
    pos = 0
    while pos < len(data):
        newline = data.find(b"\n", pos)
        if newline == -1:
            break  # unterminated final line — torn tail
        line = data[pos:newline]
        if not line.strip():
            break  # blank line — tail junk
        try:
            json.loads(line)
        except json.JSONDecodeError:
            break  # torn/garbage line — stop before it
        good_end = newline + 1  # include the newline
        pos = newline + 1
    return good_end


class Ledger:
    """Append-only event ledger bound to one ``events.jsonl`` file."""

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)

    def _repair_tail(self) -> None:
        """Heal a crashed-writer tail before appending (P1-D6: single writer).

        Truncates any torn/blank tail back to the end of the last valid,
        newline-terminated line, so the append never lands on a torn line
        (which would swallow the new event) nor turns the tear into a permanent
        mid-file corruption. Safe from races: only the sole writer truncates.
        """
        if not self.path.exists():
            return
        good_end = _valid_prefix_bytes(self.path)
        if good_end < self.path.stat().st_size:
            with open(self.path, "r+b") as f:
                f.truncate(good_end)

    def _append(self, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Repair any torn tail, then append one envelope with a disk-derived offset."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._repair_tail()
        envelope = {
            "offset": len(_read_valid_events(self.path)),
            "ts": _now_iso(),
            "event": event,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(envelope) + "\n")
        return envelope

    def read(self, since_offset: int = 0) -> List[Dict[str, Any]]:
        """Return envelopes whose offset is >= ``since_offset``, in order."""
        events = _read_valid_events(self.path)
        return [e for e in events if e["offset"] >= since_offset]

    # --- Named emitters (public API; never call _append at call sites) -------

    def run_submitted(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("RunSubmitted", payload)

    def intake_rejected(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("IntakeRejected", payload)

    def generation_started(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("GenerationStarted", payload)

    def generation_finished(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("GenerationFinished", payload)

    def assembly_done(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("AssemblyDone", payload)

    def iteration_started(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("IterationStarted", payload)

    def iteration_evaluated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("IterationEvaluated", payload)

    def fresh_start(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("FreshStart", payload)

    def model_escalated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("ModelEscalated", payload)

    def exhausted(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("Exhausted", payload)

    def delivered(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("Delivered", payload)

    def failed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("Failed", payload)

    def cancelled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("Cancelled", payload)

    def worker_started(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("WorkerStarted", payload)

    def worker_stopped(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("WorkerStopped", payload)

    def retention_pruned(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("RetentionPruned", payload)

    def refs_dropped(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("RefsDropped", payload)

    def context_limit_unknown(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("ContextLimitUnknown", payload)

    def judged(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._append("Judged", payload)


def fold_state(events: List[Dict[str, Any]]) -> str:
    """Fold an ordered event list into a public state, tolerating unknowns."""
    current = "queued"
    for event in events:
        if event["event"] in _STATE_BY_EVENT:
            current = _STATE_BY_EVENT[event["event"]]
    return current
