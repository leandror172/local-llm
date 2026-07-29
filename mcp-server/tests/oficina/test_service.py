"""Tests for oficina.service — submit handoff, status fold, result discrimination, cancel.

Synchronous tests (plain ``def``), not async.

Not converted to the executable-spec DSL (`ref:test-executable-spec`): mixed verb surface
(submit / status / result / cancel), not one homogeneous behavioral family — no single
given/when/then shape fits. Revisit only if a homogeneous sub-family emerges.
"""

import os

import pytest

from ollama_mcp.oficina import service
from ollama_mcp.oficina.fifo import Fifo
from ollama_mcp.oficina.ledger import Ledger
from ollama_mcp.oficina.store import Store, UnknownRunError


def _spy_ensure():
    """An ensure_worker spy recording the roots it was asked to ensure."""
    calls = []
    def _fn(root):
        calls.append(root)
    return _fn, calls


def _valid_spec():
    return {"deliverable": {"kind": "answer"}, "objective": "q"}


def test_submit_returns_run_id_watchcmd_position(tmp_path):
    """submit returns run_id, a watch_cmd naming the run, and a queue_position."""
    fn, calls = _spy_ensure()
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    assert isinstance(res["run_id"], str) and res["run_id"]
    assert res["run_id"] in res["watch_cmd"]
    assert res["queue_position"] == 1


def test_submit_creates_dir_spec_and_runsubmitted_before_queue(tmp_path):
    """submit persists spec.json and appends RunSubmitted, then pushes the marker."""
    fn, calls = _spy_ensure()
    store = Store(tmp_path)
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    run_id = res["run_id"]
    assert store.run_dir(run_id).exists()
    assert (store.run_dir(run_id) / "spec.json").exists()
    events = Ledger(store.events_path(run_id)).read()
    assert events[0]["event"] == "RunSubmitted"


def test_submit_records_origin_cwd_in_runsubmitted_payload(tmp_path):
    """RunSubmitted carries submitted_from = the submitter's cwd (T-89 D2: annotate, never filter)."""
    fn, calls = _spy_ensure()
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    events = Ledger(Store(tmp_path).events_path(res["run_id"])).read()
    payload = events[0]["payload"]
    assert payload["submitted_from"] == os.getcwd()
    assert payload["queue_position"] == 1


def test_submit_pushes_queue_marker(tmp_path):
    """After submit the run's marker is poppable from the FIFO."""
    fn, calls = _spy_ensure()
    fifo = Fifo(tmp_path)
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    assert fifo.pop() == res["run_id"]


def test_submit_ensures_worker(tmp_path):
    """submit invokes the injected ensure_worker exactly once with the root."""
    fn, calls = _spy_ensure()
    service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    assert len(calls) == 1


def test_submit_rejects_non_mapping_spec(tmp_path):
    """A spec that isn't a mapping raises SpecShapeError (not even a run)."""
    fn, calls = _spy_ensure()
    with pytest.raises(service.SpecShapeError):
        service.submit(tmp_path, ["not", "a", "dict"], ensure_worker=fn)


def test_submit_rejects_spec_without_deliverable(tmp_path):
    """A spec missing a deliverable mapping raises SpecShapeError."""
    fn, calls = _spy_ensure()
    with pytest.raises(service.SpecShapeError):
        service.submit(tmp_path, {"objective": "q"}, ensure_worker=fn)


def test_status_unknown_run_raises(tmp_path):
    """status on an unknown run_id raises UnknownRunError."""
    with pytest.raises(UnknownRunError):
        service.status(tmp_path, "nope")


def test_status_folds_state_and_slices_events(tmp_path):
    """status returns folded state and events sliced by since_offset with next_offset."""
    fn, calls = _spy_ensure()
    store = Store(tmp_path)
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    run_id = res["run_id"]
    led = Ledger(store.events_path(run_id))
    led.generation_started({})
    led.delivered({"report": {}, "deliverable": {"kind": "answer", "answer": "x"}})
    st = service.status(tmp_path, run_id)
    assert st["state"] == "completed"
    assert st["next_offset"] == 3
    st2 = service.status(tmp_path, run_id, since_offset=2)
    assert all(e["offset"] >= 2 for e in st2["events"])
    assert len(st2["events"]) == 1


def test_result_unknown_run_raises(tmp_path):
    """result on an unknown run_id raises UnknownRunError."""
    with pytest.raises(UnknownRunError):
        service.result(tmp_path, "nope")


def test_result_not_terminal_raises(tmp_path):
    """result on a still-working run raises RunNotTerminalError."""
    fn, calls = _spy_ensure()
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    with pytest.raises(service.RunNotTerminalError):
        service.result(tmp_path, res["run_id"])  # only RunSubmitted so state is queued


def test_result_completed_returns_report_and_deliverable(tmp_path):
    """result on a Delivered run returns its report + deliverable, artifacts_pruned False."""
    fn, calls = _spy_ensure()
    store = Store(tmp_path)
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    run_id = res["run_id"]
    Ledger(store.events_path(run_id)).delivered({"report": {"summary": "done"}, "deliverable": {"kind": "answer", "answer": "42"}})
    out = service.result(tmp_path, run_id)
    assert out["state"] == "completed"
    assert out["report"] == {"summary": "done"}
    assert out["deliverable"]["answer"] == "42"
    assert out["artifacts_pruned"] is False


def test_result_pruned_still_returns_report(tmp_path):
    """result on a completed run whose artifacts were pruned still returns the report."""
    import shutil
    fn, calls = _spy_ensure()
    store = Store(tmp_path)
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    run_id = res["run_id"]
    Ledger(store.events_path(run_id)).delivered({"report": {"summary": "done"}, "deliverable": {"kind": "answer", "answer": "42"}})
    shutil.rmtree(store.artifacts_dir(run_id))
    out = service.result(tmp_path, run_id)
    assert out["report"] == {"summary": "done"}
    assert out["artifacts_pruned"] is True


def test_cancel_writes_flag_and_returns_state(tmp_path):
    """cancel writes the cancel flag file and returns the current state."""
    fn, calls = _spy_ensure()
    store = Store(tmp_path)
    res = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)
    run_id = res["run_id"]
    out = service.cancel(tmp_path, run_id)
    assert (store.run_dir(run_id) / "cancel").exists()
    assert "state" in out


def test_cancel_unknown_run_raises(tmp_path):
    """cancel on an unknown run_id raises UnknownRunError."""
    with pytest.raises(UnknownRunError):
        service.cancel(tmp_path, "nope")


# --- P2 loop terminal/phase surfacing ---------------------------------------


def test_result_exhausted_run_surfaces_best_attempt(tmp_path):
    """An exhausted loop run is terminal 'failed' whose result carries the Exhausted payload AND
    a deliverable pointing at the best-attempt branch/commit (S11: never a silent empty result)."""
    fn, _ = _spy_ensure()
    store = Store(tmp_path)
    run_id = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)["run_id"]
    Ledger(store.events_path(run_id)).exhausted(
        {
            "spent": {"iterations": 3, "fresh_starts": 1},
            "limit_hit": "exhausted",
            "best_attempt_ref": "abc123",
            "branch": "oficina-run-x",
        }
    )
    out = service.result(tmp_path, run_id)
    assert out["state"] == "failed"
    assert out["report"]["limit_hit"] == "exhausted"
    assert out["deliverable"]["branch"] == "oficina-run-x"
    assert out["deliverable"]["commit"] == "abc123"


def test_status_phase_reflects_loop_events(tmp_path):
    """A run that is assembling/iterating reports a loop phase, not the stale 'queued' — the
    phase map must know the P2 events or a working loop run looks like it was never picked up."""
    fn, _ = _spy_ensure()
    store = Store(tmp_path)
    run_id = service.submit(tmp_path, _valid_spec(), ensure_worker=fn)["run_id"]
    led = Ledger(store.events_path(run_id))
    led.assembly_done(
        {"worktree_path": "w", "base_commit": "c", "test_files_materialized": [], "baseline_failure_count": 1}
    )
    led.iteration_started(
        {"iteration": 1, "tier": 1, "budget_remaining": {"iterations": 2, "fresh_starts": 1}}
    )
    out = service.status(tmp_path, run_id)
    assert out["state"] == "working"
    assert out["phase"] == "looping"


def test_the_phase_map_covers_every_run_event():
    """Event registration has three registries across two modules — `_STATE_BY_EVENT` and
    `_NON_FOLDING_RUN_EVENTS` in `ledger.py`, `_PHASE_BY_EVENT` here — and nothing checked that a
    new event reached all of them. `fold_phase` tolerates unknown names SILENTLY, so a miss can
    only be noticed by someone wondering why a phase looks stale: `Judged` was omitted, and a run
    reported `looping` through its whole judging window.

    This pins the registries against each other. An event that genuinely should not move the
    phase goes in `_PHASE_NEUTRAL_EVENTS` — declared, so "neutral" and "forgotten" stop looking
    identical."""
    from ollama_mcp.oficina.ledger import RUN_EVENTS
    from ollama_mcp.oficina.service import _PHASE_BY_EVENT, _PHASE_NEUTRAL_EVENTS

    declared = set(_PHASE_BY_EVENT) | set(_PHASE_NEUTRAL_EVENTS)
    assert declared == set(RUN_EVENTS), (
        f"undeclared: {set(RUN_EVENTS) - declared}; "
        f"not a run event: {declared - set(RUN_EVENTS)}"
    )
