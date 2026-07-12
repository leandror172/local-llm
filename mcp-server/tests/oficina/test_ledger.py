"""Tests for oficina.ledger — envelope shape, offset slicing, folds, torn lines.

These are synchronous tests (plain ``def``), not async.
"""

import json

import pytest

from ollama_mcp.oficina.ledger import (
    Ledger,
    LedgerCorruptionError,
    fold_state,
)


def _write_lines(path, lines):
    """Write raw text lines (already-serialized) to path, newline-terminated."""
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def test_run_submitted_writes_envelope_shape(tmp_path):
    """A named emitter writes one line whose envelope has offset/ts/event/payload."""
    ledger = Ledger(tmp_path / "events.jsonl")
    result = ledger.run_submitted({"key": "value"})
    assert isinstance(result, dict)
    assert result["offset"] == 0
    assert isinstance(result["ts"], str)
    assert result["event"] == "RunSubmitted"
    assert result["payload"] == {"key": "value"}


def test_first_event_has_offset_zero(tmp_path):
    """The first appended event carries offset 0."""
    ledger = Ledger(tmp_path / "events.jsonl")
    result = ledger.run_submitted({"key": "value"})
    assert result["offset"] == 0


def test_offsets_are_sequential_line_indexes(tmp_path):
    """Each envelope's offset equals its absolute 0-based line index."""
    ledger = Ledger(tmp_path / "events.jsonl")
    first_event = ledger.run_submitted({"key": "value1"})
    second_event = ledger.generation_started({"key": "value2"})
    assert first_event["offset"] == 0
    assert second_event["offset"] == 1


def test_offset_derived_from_disk_across_instances(tmp_path):
    """A fresh Ledger instance resumes offsets from disk, not an in-memory counter."""
    ledger = Ledger(tmp_path / "events.jsonl")
    ledger.run_submitted({"key": "value"})
    del ledger
    new_ledger = Ledger(tmp_path / "events.jsonl")
    result = new_ledger.generation_started({"key": "value2"})
    assert result["offset"] == 1


def test_read_since_offset_slices_by_offset(tmp_path):
    """read(since_offset=k) returns exactly the envelopes with offset >= k."""
    ledger = Ledger(tmp_path / "events.jsonl")
    ledger.run_submitted({"key": "value1"})
    ledger.generation_started({"key": "value2"})
    result = ledger.read(since_offset=1)
    assert len(result) == 1
    assert result[0]["offset"] == 1


def test_read_default_returns_all(tmp_path):
    """read() with no argument returns every event from offset 0."""
    ledger = Ledger(tmp_path / "events.jsonl")
    first_event = ledger.run_submitted({"key": "value1"})
    second_event = ledger.generation_started({"key": "value2"})
    result = ledger.read()
    assert len(result) == 2
    assert result[0] == first_event
    assert result[1] == second_event


def test_named_emitters_carry_correct_event_name(tmp_path):
    """Each named emitter stamps its own frozen event name into the envelope."""
    ledger = Ledger(tmp_path / "events.jsonl")
    assert ledger.run_submitted({"key": "value"})["event"] == "RunSubmitted"
    assert ledger.generation_started({"key": "value"})["event"] == "GenerationStarted"
    assert ledger.delivered({"key": "value"})["event"] == "Delivered"
    assert ledger.cancelled({"key": "value"})["event"] == "Cancelled"
    assert ledger.intake_rejected({"key": "value"})["event"] == "IntakeRejected"


def test_payload_round_trips(tmp_path):
    """The payload dict survives the append/read round-trip unchanged."""
    ledger = Ledger(tmp_path / "events.jsonl")
    original_payload = {"key": "value"}
    written_event = ledger.run_submitted(original_payload)
    read_events = ledger.read()
    assert len(read_events) == 1
    assert read_events[0]["payload"] == original_payload


def test_fold_over_known_events_reaches_terminal_state(tmp_path):
    """fold_state maps a submitted->started->delivered sequence to 'completed'."""
    events = [
        {"event": "RunSubmitted", "payload": {}},
        {"event": "GenerationStarted", "payload": {}},
        {"event": "Delivered", "payload": {}},
    ]
    assert fold_state(events) == "completed"


def test_fold_intake_rejected_is_failed():
    """A lone IntakeRejected folds to 'failed' (terminal rejection)."""
    events = [{"event": "IntakeRejected", "payload": {}}]
    assert fold_state(events) == "failed"


def test_fold_cancelled_is_cancelled():
    """A Cancelled event folds to 'cancelled'."""
    events = [{"event": "Cancelled", "payload": {}}]
    assert fold_state(events) == "cancelled"


def test_fold_tolerates_unknown_event_names():
    """Unknown event names are skipped by the fold, not errors (forward-compat)."""
    events = [
        {"event": "RunSubmitted", "payload": {}},
        {"event": "SomethingFromTheFuture", "payload": {}},
        {"event": "Delivered", "payload": {}},
    ]
    assert fold_state(events) == "completed"


def test_torn_last_line_is_tolerated(tmp_path):
    """A truncated/partial JSON final line (crashed writer) is dropped, not raised."""
    _write_lines(
        tmp_path / "events.jsonl",
        [
            json.dumps({"offset": 0, "ts": "t", "event": "RunSubmitted", "payload": {}}),
            json.dumps({"offset": 1, "ts": "t", "event": "GenerationStarted", "payload": {}}),
            '{"offset": 2, "ts": "x", "eve',
        ],
    )
    ledger = Ledger(tmp_path / "events.jsonl")
    result = ledger.read()
    assert len(result) == 2
    assert result[0]["offset"] == 0
    assert result[1]["offset"] == 1


def test_read_returns_prefix_content_before_torn_line(tmp_path):
    """The prefix events' CONTENT (event names + payloads) survives a torn tail."""
    _write_lines(
        tmp_path / "events.jsonl",
        [
            json.dumps({"offset": 0, "ts": "t", "event": "RunSubmitted", "payload": {"a": 1}}),
            json.dumps({"offset": 1, "ts": "t", "event": "GenerationStarted", "payload": {"b": 2}}),
            '{"offset": 2, "ts": "x", "eve',
        ],
    )
    ledger = Ledger(tmp_path / "events.jsonl")
    result = ledger.read()
    assert [e["event"] for e in result] == ["RunSubmitted", "GenerationStarted"]
    assert [e["payload"] for e in result] == [{"a": 1}, {"b": 2}]


def test_append_after_recomputes_offset_ignoring_torn_line(tmp_path):
    """Offset counting is driven by the same valid-events read as torn detection."""
    _write_lines(
        tmp_path / "events.jsonl",
        [
            json.dumps({"offset": 0, "ts": "t", "event": "RunSubmitted", "payload": {}}),
            json.dumps({"offset": 1, "ts": "t", "event": "GenerationStarted", "payload": {}}),
            '{"offset": 2, "ts": "x", "eve',
        ],
    )
    ledger = Ledger(tmp_path / "events.jsonl")
    result = ledger.delivered({"key": "value"})
    assert result["offset"] == 2
    # Repair-on-append must leave the ledger readable: the torn tail is healed,
    # so read() succeeds and includes the newly appended event (offset 2).
    events = ledger.read()
    assert [e["offset"] for e in events] == [0, 1, 2]
    assert events[2]["event"] == "Delivered"
    assert events[2]["payload"] == {"key": "value"}


def test_append_after_torn_tail_without_newline_swallows_nothing(tmp_path):
    """A torn tail with NO trailing newline is repaired; the new event is not concatenated."""
    # Two valid lines, then a partial JSON fragment with NO trailing newline
    # (the realistic crashed-writer shape).
    (tmp_path / "events.jsonl").write_text(
        json.dumps({"offset": 0, "ts": "t", "event": "RunSubmitted", "payload": {}}) + "\n"
        + json.dumps({"offset": 1, "ts": "t", "event": "GenerationStarted", "payload": {}}) + "\n"
        + '{"offset": 2, "ts": "x", "eve',
        encoding="utf-8",
    )
    ledger = Ledger(tmp_path / "events.jsonl")
    appended = ledger.delivered({"key": "value"})
    assert appended["offset"] == 2
    events = ledger.read()
    assert [e["offset"] for e in events] == [0, 1, 2]
    assert events[2]["event"] == "Delivered"


def test_append_after_torn_tail_with_trailing_blank_line(tmp_path):
    """A torn tail followed by a blank line is repaired; read() succeeds after append."""
    _write_lines(
        tmp_path / "events.jsonl",
        [
            json.dumps({"offset": 0, "ts": "t", "event": "RunSubmitted", "payload": {}}),
            json.dumps({"offset": 1, "ts": "t", "event": "GenerationStarted", "payload": {}}),
            '{"offset": 2, "ts": "x", "eve',
            "",  # trailing blank line after the torn line
        ],
    )
    ledger = Ledger(tmp_path / "events.jsonl")
    appended = ledger.delivered({"key": "value"})
    assert appended["offset"] == 2
    events = ledger.read()
    assert [e["offset"] for e in events] == [0, 1, 2]
    assert events[2]["event"] == "Delivered"


def test_corruption_on_earlier_line_raises(tmp_path):
    """A parse failure on a non-last line is real corruption and raises."""
    _write_lines(
        tmp_path / "events.jsonl",
        [
            '{"offset": 0, "ts": "t", "eve',
            json.dumps({"offset": 1, "ts": "t", "event": "GenerationStarted", "payload": {}}),
        ],
    )
    ledger = Ledger(tmp_path / "events.jsonl")
    with pytest.raises(LedgerCorruptionError):
        ledger.read()
