"""Tests for oficina.cli — verb parity with the service layer, runs/prune/watch.

Synchronous tests (plain ``def``), not async. The CLI shares the service layer,
so these assert the thin verb wiring + output, not re-derived logic.
"""

import json

import pytest

from ollama_mcp.oficina import cli, service
from ollama_mcp.oficina.ledger import Ledger
from ollama_mcp.oficina.store import Store


@pytest.fixture(autouse=True)
def no_spawn(monkeypatch):
    """Stub worker spawning so submit never launches a real process."""
    monkeypatch.setattr(service, "_default_ensure_worker", lambda root: None)


def _write_spec(tmp_path, spec):
    """Write a spec dict to a JSON file and return its path string."""
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return str(path)


def _submit(tmp_path, spec):
    """Run the submit verb and return the parsed result dict."""
    return service.submit(tmp_path, spec, ensure_worker=lambda root: None)


def test_submit_prints_run_id(tmp_path, capsys):
    """cmd_submit prints a JSON handle with a run_id."""
    path = _write_spec(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    code = cli.cmd_submit(tmp_path, path)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["run_id"]


def test_submit_bad_spec_returns_nonzero(tmp_path, capsys):
    """cmd_submit on a shapeless spec returns exit code 1 and prints an error."""
    path = _write_spec(tmp_path, {"objective": "no deliverable"})
    code = cli.cmd_submit(tmp_path, path)
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_status_prints_state(tmp_path, capsys):
    """cmd_status prints the folded state for a known run."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    code = cli.cmd_status(tmp_path, res["run_id"], 0)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] == "queued"


def test_status_unknown_returns_nonzero(tmp_path, capsys):
    """cmd_status on an unknown run returns exit code 1."""
    code = cli.cmd_status(tmp_path, "nope", 0)
    assert code == 1


def test_result_not_terminal_returns_nonzero(tmp_path, capsys):
    """cmd_result on a queued run returns exit code 1."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    code = cli.cmd_result(tmp_path, res["run_id"])
    assert code == 1


def test_result_completed_prints_report(tmp_path, capsys):
    """cmd_result prints the report for a Delivered run."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    run_id = res["run_id"]
    store = Store(tmp_path)
    Ledger(store.events_path(run_id)).delivered({"report": {"summary": "done"}, "deliverable": {"kind": "answer", "answer": "42"}})
    code = cli.cmd_result(tmp_path, run_id)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["report"] == {"summary": "done"}


def test_cancel_prints_state_and_writes_flag(tmp_path, capsys):
    """cmd_cancel prints state and writes the cancel flag."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    run_id = res["run_id"]
    code = cli.cmd_cancel(tmp_path, run_id)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert "state" in out
    assert (Store(tmp_path).run_dir(run_id) / "cancel").exists()


def test_runs_lists_the_run(tmp_path, capsys):
    """cmd_runs lists each run with its state."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    code = cli.cmd_runs(tmp_path)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert any(r["run_id"] == res["run_id"] for r in out)


def test_prune_dry_run_reports_without_deleting(tmp_path, capsys):
    """cmd_prune --dry-run reports would-prune records but deletes nothing."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    run_id = res["run_id"]
    store = Store(tmp_path)
    # give it an artifact so there is something prunable
    (store.artifacts_dir(run_id) / "a.txt").write_text("data")
    code = cli.cmd_prune(tmp_path, dry_run=True)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["dry_run"] is True
    # nothing deleted:
    assert (store.artifacts_dir(run_id) / "a.txt").exists()


def test_watch_returns_when_terminal(tmp_path, capsys):
    """cmd_watch prints events and returns 0 once the run is terminal."""
    res = _submit(tmp_path, {"deliverable": {"kind": "answer"}, "objective": "q"})
    run_id = res["run_id"]
    store = Store(tmp_path)
    Ledger(store.events_path(run_id)).delivered({"report": {}, "deliverable": {"kind": "answer", "answer": "x"}})
    code = cli.cmd_watch(tmp_path, run_id, interval=0.0, _max_iters=1)
    assert code == 0
    out = capsys.readouterr().out
    assert "Delivered" in out
