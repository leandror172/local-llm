"""T-96 — refs resolution fallback + fail-loud drop (worker + server script location).

Structural/wiring tests (they vary the environment `given`, not an input sequence)
— imperative style per the executable-spec taxonomy, like test_worker.py.

Contracts under test (to be implemented):

1. ``server._ref_lookup_script() -> str`` resolves the ref-lookup script path:
   - ``OFICINA_REF_LOOKUP`` env var (direct script path) wins outright;
   - else ``LLM_REPO_ROOT`` env var (read at CALL time, not import time)
     -> ``<root>/.claude/tools/ref-lookup.sh``;
   - else package-relative fallback: the mcp-server checkout lives inside the llm
     repo, so ``Path(server.__file__).resolve().parents[3]`` is the repo root
     -> ``<repo>/.claude/tools/ref-lookup.sh`` (this file EXISTS in this checkout).

2. ``Worker._resolve_refs_block(spec, run_id) -> str`` (signature gains run_id):
   - spec without ``context.refs`` -> returns ``""``, emits NOTHING;
   - resolution succeeds -> returns the block, emits NOTHING;
   - resolution fails (``_build_refs_block`` returns an ``Error:`` string OR
     raises) -> returns ``""`` AND emits a ``RefsDropped`` event to the WORKER
     ledger (``worker-events.jsonl``) with payload ``{run_id, refs, reason}``.
     Never raises: refs stay best-effort context — but never a SILENT drop.

3. ``Ledger.refs_dropped(payload)`` named emitter exists; ``"RefsDropped"`` is in
   ``ledger.WORKER_EVENTS`` (worker observability channel — NOT a run event; the
   frozen run-event registry ``_STATE_BY_EVENT`` is untouched).
"""

from __future__ import annotations

import json
from pathlib import Path

import ollama_mcp.server as server
from ollama_mcp.oficina.ledger import WORKER_EVENTS
from ollama_mcp.oficina.worker import Worker


A_REFS_SPEC = {
    "deliverable": {"kind": "answer", "target": "out.md"},
    "context": {"refs": ["delegate-p2-loop-diagram"]},
    "prompt": "irrelevant",
}

A_SPEC_WITHOUT_REFS = {
    "deliverable": {"kind": "answer", "target": "out.md"},
    "prompt": "irrelevant",
}


def _worker_events(root: Path) -> list[dict]:
    """All events currently in the worker ledger at ``root`` (empty if absent)."""
    path = root / "worker-events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- 1. script resolution (server-side, mirrors evaluator._validate_code_script) ---


def test_ref_lookup_script_env_override_wins(monkeypatch):
    """OFICINA_REF_LOOKUP set -> returned verbatim, even with LLM_REPO_ROOT also set."""
    monkeypatch.setenv("OFICINA_REF_LOOKUP", "/custom/path/ref-lookup.sh")
    monkeypatch.setenv("LLM_REPO_ROOT", "/some/other/root")
    assert server._ref_lookup_script() == "/custom/path/ref-lookup.sh"


def test_ref_lookup_script_uses_llm_repo_root(monkeypatch):
    """No override, LLM_REPO_ROOT set -> <root>/.claude/tools/ref-lookup.sh."""
    monkeypatch.delenv("OFICINA_REF_LOOKUP", raising=False)
    repo_root = Path("/llm-repo-root")
    monkeypatch.setenv("LLM_REPO_ROOT", str(repo_root))
    expected_path = repo_root / ".claude" / "tools" / "ref-lookup.sh"
    assert server._ref_lookup_script() == str(expected_path)


def test_ref_lookup_script_reads_env_at_call_time(monkeypatch):
    """LLM_REPO_ROOT set AFTER import still wins over the package-relative fallback
    (the helper must not cache config.REPO_ROOT's import-time snapshot)."""
    monkeypatch.delenv("OFICINA_REF_LOOKUP", raising=False)
    monkeypatch.setenv("LLM_REPO_ROOT", "/first-root")
    first = server._ref_lookup_script()
    monkeypatch.setenv("LLM_REPO_ROOT", "/second-root")
    second = server._ref_lookup_script()
    assert first != second
    assert second == str(Path("/second-root") / ".claude" / "tools" / "ref-lookup.sh")


def test_ref_lookup_script_falls_back_package_relative(monkeypatch):
    """Neither env var set -> the checkout's own .claude/tools/ref-lookup.sh,
    and that path exists on disk in this repo."""
    monkeypatch.delenv("OFICINA_REF_LOOKUP", raising=False)
    monkeypatch.delenv("LLM_REPO_ROOT", raising=False)
    expected_path = Path(server.__file__).resolve().parents[3] / ".claude" / "tools" / "ref-lookup.sh"
    assert server._ref_lookup_script() == str(expected_path)
    assert expected_path.exists()


# --- 2. worker fail-loud (RefsDropped to the worker ledger, never silent) ----------


def test_no_refs_requested_returns_empty_and_emits_nothing(tmp_path):
    """A spec without context.refs -> "" and an empty worker ledger."""
    worker = Worker(tmp_path)
    result = worker._resolve_refs_block(A_SPEC_WITHOUT_REFS, "rid-96")
    assert result == ""
    events = _worker_events(tmp_path)
    assert not events


def test_successful_resolution_returns_block_and_emits_nothing(tmp_path, monkeypatch):
    """_build_refs_block returns a real block -> block returned unchanged, no event.
    (monkeypatch server._build_refs_block to an async fake returning '<refs>ok</refs>')"""
    async def _fake_build_refs_block(refs, root):
        return "<refs>ok</refs>"
    monkeypatch.setattr(server, "_build_refs_block", _fake_build_refs_block)
    worker = Worker(tmp_path)
    result = worker._resolve_refs_block(A_REFS_SPEC, "rid-96")
    assert result == "<refs>ok</refs>"
    events = _worker_events(tmp_path)
    assert not events


def test_error_string_resolution_emits_refs_dropped(tmp_path, monkeypatch):
    """_build_refs_block returns 'Error: ...' -> "" returned, and the worker ledger
    holds one RefsDropped whose payload carries run_id, the requested refs list,
    and the Error string as reason."""
    async def _fake_build_refs_block(refs, root):
        return "Error: failed to resolve refs"
    monkeypatch.setattr(server, "_build_refs_block", _fake_build_refs_block)
    worker = Worker(tmp_path)
    result = worker._resolve_refs_block(A_REFS_SPEC, "rid-96")
    assert result == ""
    events = _worker_events(tmp_path)
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "RefsDropped"
    payload = event["payload"]
    assert payload["run_id"] == "rid-96"
    assert payload["refs"] == ["delegate-p2-loop-diagram"]
    assert "failed to resolve refs" in payload["reason"]


def test_raising_resolution_emits_refs_dropped(tmp_path, monkeypatch):
    """_build_refs_block raises -> "" returned (never propagates), RefsDropped
    emitted with the exception text as reason."""
    async def _fake_build_refs_block(refs, root):
        raise RuntimeError("boom")
    monkeypatch.setattr(server, "_build_refs_block", _fake_build_refs_block)
    worker = Worker(tmp_path)
    result = worker._resolve_refs_block(A_REFS_SPEC, "rid-96")
    assert result == ""
    events = _worker_events(tmp_path)
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "RefsDropped"
    payload = event["payload"]
    assert payload["run_id"] == "rid-96"
    assert payload["refs"] == ["delegate-p2-loop-diagram"]
    assert "boom" in payload["reason"]


# --- 3. ledger registry ------------------------------------------------------------


def test_refs_dropped_is_a_worker_event_not_a_run_event():
    """RefsDropped is in WORKER_EVENTS and NOT in the frozen run-event registry."""
    import ollama_mcp.oficina.ledger as ledger
    assert "RefsDropped" in WORKER_EVENTS
    assert "RefsDropped" not in ledger.RUN_EVENTS


def test_every_repo_relative_asset_honours_llm_repo_root(monkeypatch, tmp_path):
    """Three resolvers had grown their own copy of "env override, else repo-relative", with
    `parents[N]` depths that differed by module and only ONE — ref-lookup — honouring
    LLM_REPO_ROOT. A detached worker started with the variable set but the package relocated
    therefore resolved refs while failing to resolve rubrics and the validator, for no stated
    reason. They now share `config.repo_root()`."""
    from ollama_mcp.oficina.evaluator import _validate_code_script
    from ollama_mcp.oficina.judge import _rubrics_dir
    from ollama_mcp.server import _ref_lookup_script

    monkeypatch.setenv("LLM_REPO_ROOT", str(tmp_path))
    for var in ("OFICINA_REF_LOOKUP", "OFICINA_VALIDATE_CODE", "OFICINA_RUBRICS"):
        monkeypatch.delenv(var, raising=False)

    assert str(tmp_path) in _ref_lookup_script()
    assert str(tmp_path) in _validate_code_script()
    assert str(tmp_path) in str(_rubrics_dir())


def test_each_asset_keeps_its_own_override(monkeypatch, tmp_path):
    """The shared root is the only thing shared: each asset's own env override still wins, and
    still points somewhere entirely different from the others (the seam, per
    ref:patterns-code-extract-keep-divergence — the root is the mechanism, the overrides are
    the divergence)."""
    from ollama_mcp.oficina.judge import _rubrics_dir

    monkeypatch.setenv("LLM_REPO_ROOT", str(tmp_path / "root"))
    monkeypatch.setenv("OFICINA_RUBRICS", str(tmp_path / "elsewhere"))

    assert str(_rubrics_dir()) == str(tmp_path / "elsewhere")
