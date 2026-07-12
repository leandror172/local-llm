"""Tests for oficina.fifo — marker format, FIFO order, atomicity, pop-on-empty.

Synchronous tests (plain ``def``), not async.
"""

import pytest

from ollama_mcp.oficina.fifo import Fifo


def test_push_creates_marker_in_queue_dir(tmp_path):
    """push writes a marker file into <root>/queue/."""
    fifo = Fifo(tmp_path)
    fifo.push("run1", now_ms=1000)
    assert fifo.queue_dir.is_dir() and len(list(fifo.queue_dir.iterdir())) == 1


def test_marker_name_has_epoch_and_run_id(tmp_path):
    """The marker name is '<epoch-ms>-<run_id>' with the injected timestamp."""
    fifo = Fifo(tmp_path)
    name = fifo.push("run1", now_ms=1000)
    assert name == "1000-run1"


def test_pop_returns_run_id(tmp_path):
    """pop returns the run_id that was pushed."""
    fifo = Fifo(tmp_path)
    fifo.push("run1", now_ms=1000)
    assert fifo.pop() == "run1"


def test_pop_on_empty_returns_none(tmp_path):
    """pop on an empty queue returns None (never raises)."""
    fifo = Fifo(tmp_path)
    assert fifo.pop() is None


def test_fifo_order_by_timestamp(tmp_path):
    """Runs pushed with increasing timestamps pop in ascending (FIFO) order."""
    fifo = Fifo(tmp_path)
    fifo.push("b", now_ms=2000)
    fifo.push("a", now_ms=1000)
    fifo.push("c", now_ms=3000)
    assert fifo.pop() == "a"
    assert fifo.pop() == "b"
    assert fifo.pop() == "c"


def test_pop_removes_marker(tmp_path):
    """After pop the claimed marker no longer exists in the queue dir."""
    fifo = Fifo(tmp_path)
    name = fifo.push("run1", now_ms=1000)
    run_id = fifo.pop()
    assert not (fifo.queue_dir / name).exists() and len(list(fifo.queue_dir.iterdir())) == 0


def test_numeric_prefix_order_not_lexicographic(tmp_path):
    """Ordering is numeric on epoch-ms: 2 pops before 10 (not lexicographic)."""
    fifo = Fifo(tmp_path)
    fifo.push("x", now_ms=2)
    fifo.push("y", now_ms=10)
    assert fifo.pop() == "x"
    assert fifo.pop() == "y"


def test_run_id_with_dash_round_trips(tmp_path):
    """A run_id containing '-' (token_urlsafe) survives push/pop intact."""
    fifo = Fifo(tmp_path)
    run_id = "ab-cd_ef-12"
    fifo.push(run_id, now_ms=1000)
    assert fifo.pop() == run_id


def test_concurrent_pushes_have_distinct_markers(tmp_path):
    """Many pushes at the same timestamp produce distinct marker files."""
    fifo = Fifo(tmp_path)
    names = [fifo.push(f"r{i}", now_ms=1000) for i in range(5)]
    assert len(set(names)) == 5 and len(list(fifo.queue_dir.iterdir())) == 5


def test_push_returns_marker_name(tmp_path):
    """push returns the marker name it created, and that file exists."""
    fifo = Fifo(tmp_path)
    name = fifo.push("run1", now_ms=1000)
    assert isinstance(name, str) and (fifo.queue_dir / name).exists()
