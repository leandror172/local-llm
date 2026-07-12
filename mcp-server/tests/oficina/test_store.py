"""Tests for oficina.ids + oficina.store — id minting, run-dir layout, spec round-trip.

Synchronous tests (plain ``def``), not async.
"""

import json

import pytest

from ollama_mcp.oficina import ids
from ollama_mcp.oficina.store import Store, UnknownRunError


def test_mint_run_id_returns_nonempty_string():
    """A minted id is a non-empty string."""
    run_id = ids.mint_run_id()
    assert isinstance(run_id, str)
    assert len(run_id) > 0


def test_mint_run_id_is_unique():
    """Two mints in a row differ (unguessable, not sequential)."""
    first_id = ids.mint_run_id()
    second_id = ids.mint_run_id()
    assert first_id != second_id


def test_create_run_returns_run_id(tmp_path):
    """create_run returns the run_id it minted."""
    store = Store(root=tmp_path)
    spec = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id = store.create_run(spec=spec)
    assert isinstance(run_id, str)
    assert len(run_id) > 0


def test_create_run_builds_layout(tmp_path):
    """create_run creates runs/<id>/ with spec.json, empty events.jsonl, artifacts/."""
    store = Store(root=tmp_path)
    spec = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id = store.create_run(spec=spec)

    run_dir = store.run_dir(run_id)
    assert run_dir.is_dir()

    spec_path = run_dir / "spec.json"
    assert spec_path.exists()
    assert spec_path.is_file()

    events_path = store.events_path(run_id)
    assert events_path.exists()
    assert events_path.is_file()

    artifacts_dir = store.artifacts_dir(run_id)
    assert artifacts_dir.is_dir()


def test_create_run_events_file_is_empty(tmp_path):
    """The freshly created events.jsonl exists and is empty (first append = offset 0)."""
    store = Store(root=tmp_path)
    spec = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id = store.create_run(spec=spec)

    events_path = store.events_path(run_id)
    assert events_path.read_text() == ""


def test_spec_round_trips(tmp_path):
    """A spec persisted by create_run loads back identical via load_spec."""
    store = Store(root=tmp_path)
    spec = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id = store.create_run(spec=spec)

    loaded_spec = store.load_spec(run_id=run_id)
    assert loaded_spec == spec


def test_two_runs_get_distinct_dirs(tmp_path):
    """Two create_run calls produce two different run directories."""
    store = Store(root=tmp_path)
    spec1 = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id1 = store.create_run(spec=spec1)

    spec2 = {"deliverable": {"kind": "summary"}, "objective": "summarize"}
    run_id2 = store.create_run(spec=spec2)

    assert run_id1 != run_id2
    assert store.run_dir(run_id1) != store.run_dir(run_id2)


def test_load_spec_unknown_id_raises(tmp_path):
    """load_spec on an id that was never created raises UnknownRunError."""
    store = Store(root=tmp_path)
    with pytest.raises(UnknownRunError):
        store.load_spec(run_id="nonexistent-id")


def test_artifacts_dir_path_under_run_dir(tmp_path):
    """artifacts_dir(run_id) is nested inside run_dir(run_id)."""
    store = Store(root=tmp_path)
    spec = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id = store.create_run(spec=spec)

    artifacts_dir = store.artifacts_dir(run_id)
    assert store.run_dir(run_id) in artifacts_dir.parents


def test_events_path_under_run_dir(tmp_path):
    """events_path(run_id) is the events.jsonl inside the run dir."""
    store = Store(root=tmp_path)
    spec = {"deliverable": {"kind": "answer"}, "objective": "do the thing"}
    run_id = store.create_run(spec=spec)

    events_path = store.events_path(run_id)
    assert events_path.name == "events.jsonl"
    assert events_path.parent == store.run_dir(run_id)
