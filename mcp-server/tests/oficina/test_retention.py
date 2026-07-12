"""Tests for oficina.retention — per-policy firing, payload, dry-run, ledger safety.

Synchronous tests (plain ``def``), not async.
"""

import json
import os

import pytest

from ollama_mcp.oficina.config import RetentionConfig
from ollama_mcp.oficina.ledger import Ledger
from ollama_mcp.oficina.retention import sweep
from ollama_mcp.oficina.store import Store


def _make_run(store, artifact_bytes=b"artifact-data", report="the report"):
    """Create a run with a Delivered event (report) and one artifact file."""
    run_id = store.create_run({"deliverable": {"kind": "answer"}, "objective": "x"})
    Ledger(store.events_path(run_id)).delivered({"report": report})
    artifact = store.artifacts_dir(run_id) / "out.txt"
    artifact.write_bytes(artifact_bytes)
    return run_id


def _set_artifacts_mtime(store, run_id, epoch):
    """Force the artifacts dir mtime to a specific epoch (for TTL tests)."""
    os.utime(store.artifacts_dir(run_id), (epoch, epoch))


@pytest.fixture
def worker_ledger(tmp_path):
    return Ledger(tmp_path / "worker-events.jsonl")


def test_keep_runs_policy_prunes_runs_beyond_limit(tmp_path, worker_ledger):
    """artifacts_keep_runs=1 prunes the older runs' artifacts, keeps the newest."""
    store = Store(tmp_path)
    r1 = _make_run(store)
    os.utime(store.run_dir(r1), (1000, 1000))
    r2 = _make_run(store)
    os.utime(store.run_dir(r2), (2000, 2000))
    r3 = _make_run(store)
    os.utime(store.run_dir(r3), (3000, 3000))

    config = RetentionConfig(workspaces_ttl_days=99999, artifacts_keep_runs=1)
    records = sweep(store, worker_ledger, config)

    assert len(records) == 2
    for record in records:
        assert record.policy == "artifacts_keep_runs"

    assert store.artifacts_dir(r3).exists()
    assert not store.artifacts_dir(r1).exists()
    assert not store.artifacts_dir(r2).exists()


def test_ttl_policy_prunes_old_workspace(tmp_path, worker_ledger):
    """workspaces_ttl_days fires for artifacts older than the TTL."""
    store = Store(tmp_path)
    run_id = _make_run(store)
    _set_artifacts_mtime(store, run_id, 1000)

    config = RetentionConfig(workspaces_ttl_days=7, artifacts_keep_runs=99999)
    records = sweep(store, worker_ledger, config, now=10**9)

    assert len(records) == 1
    assert records[0].policy == "workspaces_ttl_days"
    assert not store.artifacts_dir(run_id).exists()


def test_retention_pruned_payload_carries_what_bytes_policy(tmp_path, worker_ledger):
    """Each RetentionPruned event names what, bytes_freed, and which policy fired."""
    store = Store(tmp_path)
    run_id = _make_run(store)

    config = RetentionConfig(workspaces_ttl_days=99999, artifacts_keep_runs=0)
    records = sweep(store, worker_ledger, config)

    assert len(records) == 1
    record = records[0]
    assert record.what == "artifacts"
    assert record.bytes_freed > 0
    assert record.policy == "artifacts_keep_runs"

    events = worker_ledger.read()
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "RetentionPruned"
    payload = event["payload"]
    assert "what" in payload
    assert "bytes_freed" in payload
    assert "policy" in payload
    assert "run_id" in payload
    assert payload["what"] == "artifacts"
    assert payload["policy"] == "artifacts_keep_runs"


def test_silence_when_nothing_pruned(tmp_path, worker_ledger):
    """With everything within limits, sweep prunes nothing and emits no events."""
    store = Store(tmp_path)
    _make_run(store)

    config = RetentionConfig(workspaces_ttl_days=99999, artifacts_keep_runs=20)
    records = sweep(store, worker_ledger, config)

    assert records == []
    assert worker_ledger.read() == []


def test_dry_run_touches_nothing(tmp_path, worker_ledger):
    """dry_run returns the would-prune records but deletes nothing and emits nothing."""
    store = Store(tmp_path)
    r1 = _make_run(store)
    r2 = _make_run(store)

    config = RetentionConfig(workspaces_ttl_days=99999, artifacts_keep_runs=0)
    records = sweep(store, worker_ledger, config, dry_run=True)

    assert len(records) == 2
    assert store.artifacts_dir(r1).exists()
    assert store.artifacts_dir(r2).exists()
    assert worker_ledger.read() == []


def test_events_jsonl_never_pruned(tmp_path, worker_ledger):
    """Pruning removes artifacts but leaves events.jsonl (the report) intact."""
    store = Store(tmp_path)
    run_id = _make_run(store)
    events_before = store.events_path(run_id).read_text()

    config = RetentionConfig(workspaces_ttl_days=99999, artifacts_keep_runs=0)
    records = sweep(store, worker_ledger, config)

    assert len(records) == 1
    assert not store.artifacts_dir(run_id).exists()
    assert store.events_path(run_id).exists()
    assert store.events_path(run_id).read_text() == events_before


def test_bytes_freed_matches_artifact_size(tmp_path, worker_ledger):
    """bytes_freed in the record equals the pruned artifact's byte size."""
    store = Store(tmp_path)
    run_id = _make_run(store, artifact_bytes=b"x" * 512)

    config = RetentionConfig(workspaces_ttl_days=99999, artifacts_keep_runs=0)
    records = sweep(store, worker_ledger, config)

    assert len(records) == 1
    assert records[0].bytes_freed == 512
