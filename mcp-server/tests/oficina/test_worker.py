"""Tests for oficina.worker — pop→generate→deliver, Failed triad, cancel, cold-start.

Synchronous tests (plain ``def``), not async. Generation is injected (no GPU).
"""

import os

import pytest

from ollama_mcp.client import OllamaTimeoutError
from ollama_mcp.oficina.ledger import Ledger, fold_state
from ollama_mcp.oficina.store import Store
from ollama_mcp.oficina.worker import GenerationResult, Worker
from ollama_mcp.oficina.workerproc import WorkerProc


def _gen_ok(content="def f():\n    return 1\n"):
    """A generate seam that returns a fixed GenerationResult."""
    def _fn(spec, run_id):
        return GenerationResult(content=content, model="fake-model", eval_count=7, duration_ms=12.5)
    return _fn


def _submit(store, fifo_or_worker, spec):
    """Create a run dir + spec and push its marker onto the queue."""
    run_id = store.create_run(spec)
    Ledger(store.events_path(run_id)).run_submitted({"queue_position": 1})
    fifo_or_worker.fifo.push(run_id)
    return run_id


def _events(store, run_id):
    return [e["event"] for e in Ledger(store.events_path(run_id)).read()]


def test_happy_path_answer_pop_generate_deliver(tmp_path):
    """A kind:answer run runs GenerationStarted→Finished→Delivered with the answer."""
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok("42 is the answer"))
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.process_run(run_id)
    names = _events(store, run_id)
    assert names == ["RunSubmitted", "GenerationStarted", "GenerationFinished", "Delivered"]
    events = Ledger(store.events_path(run_id)).read()
    delivered_event = next(e for e in events if e["event"] == "Delivered")
    assert delivered_event["payload"]["deliverable"]["answer"] == "42 is the answer"


def test_happy_path_file_writes_target(tmp_path):
    """A kind:file run writes the generated content to deliverable.target."""
    target = tmp_path / "out.py"
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok("def f():\n    return 1\n"))
    run_id = _submit(store, worker, {"deliverable": {"kind": "file", "target": str(target)}, "objective": "write f"})
    worker.process_run(run_id)
    assert target.read_text() == "def f():\n    return 1\n"
    assert "Delivered" in _events(store, run_id)


def test_delivered_state_is_completed(tmp_path):
    """After a happy run, the ledger folds to 'completed'."""
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok("42 is the answer"))
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.process_run(run_id)
    state = fold_state(Ledger(store.events_path(run_id)).read())
    assert state == "completed"


def test_stage_error_emits_failed_with_triad(tmp_path):
    """A generation exception yields a Failed event carrying where/whose/what."""
    def _boom(spec, run_id):
        raise ValueError("boom")
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_boom)
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.process_run(run_id)
    events = Ledger(store.events_path(run_id)).read()
    failed = [e for e in events if e["event"] == "Failed"]
    assert len(failed) == 1
    payload = failed[0]["payload"]
    assert "where" in payload and "whose" in payload and "what" in payload
    assert "boom" in payload["what"]
    assert "Delivered" not in _events(store, run_id)


def test_cancel_flag_honored_before_generation(tmp_path):
    """A cancel flag set before processing yields Cancelled and no generation."""
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok())
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    (store.run_dir(run_id) / "cancel").write_text("1")
    worker.process_run(run_id)
    names = _events(store, run_id)
    assert "Cancelled" in names
    assert "GenerationStarted" not in names
    assert "Delivered" not in names


def test_cold_start_grace_retries_once(tmp_path):
    """A first-call OllamaTimeoutError is retried once, ending in Delivered."""
    calls = []
    def _flaky(spec, run_id):
        calls.append(1)
        if len(calls) == 1:
            raise OllamaTimeoutError("cold start")
        return GenerationResult(content="ok", model="m", eval_count=1, duration_ms=1.0)
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_flaky)
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.process_run(run_id)
    assert len(calls) == 2
    assert "Delivered" in _events(store, run_id)
    assert "Failed" not in _events(store, run_id)


def test_intake_rejection_emits_event_no_generation(tmp_path):
    """A spec that fails intake yields IntakeRejected and never starts generation."""
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok())
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}})  # NO objective -> intake rejects
    worker.process_run(run_id)
    names = _events(store, run_id)
    assert "IntakeRejected" in names
    assert "GenerationStarted" not in names


def test_worker_claims_pidfile_first_and_exits_if_lost(tmp_path):
    """If a live owner holds the pidfile, run() exits without draining the queue."""
    wp = WorkerProc(tmp_path)
    assert wp.claim_pidfile() is True  # this process now "owns" it, and is alive with a matching start-time
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok())
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.run()
    assert "Delivered" not in _events(store, run_id)
    assert worker.worker_ledger.read() == []  # no WorkerStarted emitted
    assert worker.fifo.pop() == run_id  # queue still holds the run


def test_run_emits_worker_started_and_stopped(tmp_path):
    """run() brackets its work with WorkerStarted/WorkerStopped on the worker ledger."""
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok())  # EMPTY queue
    worker.run()
    names = [e["event"] for e in worker.worker_ledger.read()]
    assert names[0] == "WorkerStarted"
    assert names[-1] == "WorkerStopped"


def test_run_drains_queue_then_exits(tmp_path):
    """run() processes every queued run and returns when the queue empties."""
    store = Store(tmp_path)
    worker = Worker(tmp_path, generate=_gen_ok())
    r1 = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "a"})
    r2 = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "b"})
    worker.run()
    assert "Delivered" in _events(store, r1) and "Delivered" in _events(store, r2)
    assert worker.fifo.pop() is None  # queue drained
