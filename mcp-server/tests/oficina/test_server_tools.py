"""Tests for the oficina MCP tools in server.py — wiring + result discrimination.

Async tests (the tools are async). ensure_worker is monkeypatched to a no-op so
no real worker process spawns; OFICINA_ROOT points the store at tmp_path.
"""

import json

import pytest

from ollama_mcp import server
from ollama_mcp.oficina import service
from ollama_mcp.oficina.ledger import Ledger
from ollama_mcp.oficina.store import Store


@pytest.fixture(autouse=True)
def isolated_root(tmp_path, monkeypatch):
    """Point the tools at a temp store and stub out worker spawning."""
    monkeypatch.setenv("OFICINA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "_default_ensure_worker", lambda root: None)
    return tmp_path


async def test_submit_run_returns_run_id(isolated_root):
    out = json.loads(await server.submit_run({"deliverable": {"kind": "answer"}, "objective": "q"}))
    assert out["run_id"]
    assert out["run_id"] in out["watch_cmd"]


async def test_submit_run_bad_spec_returns_error(isolated_root):
    out = await server.submit_run({"objective": "no deliverable"})
    assert out.startswith("Error:")


async def test_run_status_reports_queued(isolated_root):
    submitted = json.loads(await server.submit_run({"deliverable": {"kind": "answer"}, "objective": "q"}))
    status = json.loads(await server.run_status(submitted["run_id"]))
    assert status["state"] == "queued"
    assert status["events"][0]["event"] == "RunSubmitted"


async def test_run_status_unknown_returns_error(isolated_root):
    out = await server.run_status("does-not-exist")
    assert out.startswith("Error: unknown run_id")


async def test_run_result_not_terminal_returns_error(isolated_root):
    submitted = json.loads(await server.submit_run({"deliverable": {"kind": "answer"}, "objective": "q"}))
    out = await server.run_result(submitted["run_id"])
    assert out.startswith("Error: run not terminal yet")


async def test_run_result_unknown_returns_error(isolated_root):
    out = await server.run_result("does-not-exist")
    assert out.startswith("Error: unknown run_id")


async def test_run_result_completed_returns_report(isolated_root):
    submitted = json.loads(await server.submit_run({"deliverable": {"kind": "answer"}, "objective": "q"}))
    run_id = submitted["run_id"]
    store = Store(isolated_root)
    Ledger(store.events_path(run_id)).delivered(
        {"report": {"summary": "ok"}, "deliverable": {"kind": "answer", "answer": "42"}}
    )
    out = json.loads(await server.run_result(run_id))
    assert out["state"] == "completed"
    assert out["report"] == {"summary": "ok"}


async def test_cancel_run_writes_flag_and_returns_state(isolated_root):
    submitted = json.loads(await server.submit_run({"deliverable": {"kind": "answer"}, "objective": "q"}))
    run_id = submitted["run_id"]
    out = json.loads(await server.cancel_run(run_id))
    assert "state" in out
    assert (Store(isolated_root).run_dir(run_id) / "cancel").exists()


async def test_cancel_run_unknown_returns_error(isolated_root):
    out = await server.cancel_run("does-not-exist")
    assert out.startswith("Error: unknown run_id")
