"""Tests for oficina.workerproc — pidfile exclusivity, PID-reuse guard, detach.

Synchronous tests (plain ``def``), not async. Integration tests spawn real
detached processes and clean them up.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import ollama_mcp
from ollama_mcp.oficina.workerproc import WorkerProc, _proc_start_time

# A start-time reader that always reports the same token — lets the pidfile
# tests control the "recorded vs live" start-time comparison deterministically.
_FIXED_START = "START-TOKEN"


def _fixed_reader(_pid):
    return _FIXED_START


def _kill_quietly(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


@pytest.fixture
def dead_pid():
    """A PID guaranteed dead: spawn a trivial process and reap it."""
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


@pytest.fixture
def spawned():
    """Collect spawned pids and kill them at teardown."""
    pids = []
    yield pids
    for pid in pids:
        _kill_quietly(pid)


# --- Real start-time reader (locks the reuse-guard mechanism) ---------------


def test_proc_start_time_is_stable_nonempty_string_for_live_pid():
    """The real /proc reader returns a stable, non-empty token for a live pid."""
    first = _proc_start_time(os.getpid())
    second = _proc_start_time(os.getpid())
    assert isinstance(first, str) and first != ""
    assert first == second


def test_proc_start_time_none_for_dead_pid(dead_pid):
    """The real /proc reader returns None for a pid that no longer exists."""
    assert _proc_start_time(dead_pid) is None


# --- Pidfile mechanics (delegated bodies) -----------------------------------


def test_claim_pidfile_writes_pid_and_start(tmp_path):
    """A successful claim records this process's pid and start-time."""
    wp = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    assert wp.claim_pidfile() is True
    data = wp.read_pidfile()
    assert data["pid"] == os.getpid()
    assert data["start"] == _FIXED_START


def test_second_live_claim_fails(tmp_path):
    """Once a live owner holds the pidfile, a second claim is refused (exclusivity)."""
    wp = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    assert wp.claim_pidfile() is True  # First claim succeeds
    wp2 = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    assert wp2.claim_pidfile() is False  # Second claim fails


def test_owner_is_live_false_when_no_pidfile(tmp_path):
    """With no pidfile there is no owner."""
    wp = WorkerProc(tmp_path)
    assert wp.owner_is_live() is False


def test_owner_is_live_true_when_pid_alive_and_start_matches(tmp_path):
    """A pidfile for a live pid with a matching start-time is a live owner."""
    wp = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    wp.pidfile.write_text(
        json.dumps({"pid": os.getpid(), "start": _FIXED_START}), encoding="utf-8"
    )
    assert wp.owner_is_live() is True


def test_stale_dead_pid_is_recovered(tmp_path, dead_pid):
    """A pidfile naming a dead pid is stale; claim recovers ownership."""
    wp = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    wp.pidfile.write_text(
        json.dumps({"pid": dead_pid, "start": "whatever"}), encoding="utf-8"
    )
    assert wp.owner_is_live() is False  # Dead PID
    assert wp.claim_pidfile() is True  # Recovers ownership
    assert wp.read_pidfile()["pid"] == os.getpid()


def test_pid_reuse_detected_via_start_mismatch(tmp_path):
    """A live pid whose recorded start-time differs is treated as stale (PID reuse)."""
    wp = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    wp.pidfile.write_text(
        json.dumps({"pid": os.getpid(), "start": "STALE-DIFFERENT"}), encoding="utf-8"
    )
    assert wp.owner_is_live() is False  # PID alive but start mismatch => reused/stale
    assert wp.claim_pidfile() is True  # Recovers ownership
    assert wp.read_pidfile()["start"] == _FIXED_START


# --- Detached spawn (integration) -------------------------------------------


def test_spawn_detached_returns_alive_pid(tmp_path, spawned):
    """spawn_detached launches a real process whose pid is alive."""
    wp = WorkerProc(tmp_path)
    pid = wp.spawn_detached(["sleep", "30"])
    spawned.append(pid)
    assert wp.is_alive(pid)


def test_spawn_detached_redirects_stdio_to_worker_log(tmp_path, spawned):
    """The detached process's stdout lands in worker.log."""
    wp = WorkerProc(tmp_path)
    pid = wp.spawn_detached(["sh", "-c", "echo hello_oficina"])
    spawned.append(pid)
    deadline = time.time() + 5
    while time.time() < deadline and not wp.log_path.exists():
        time.sleep(0.05)
    time.sleep(0.2)
    assert wp.log_path.exists()
    assert "hello_oficina" in wp.log_path.read_text(encoding="utf-8")


def test_detached_child_survives_parent_exit(tmp_path, spawned):
    """A child spawned detached outlives the parent that spawned it."""
    src_root = str(Path(ollama_mcp.__file__).resolve().parent.parent)
    code = (
        "from ollama_mcp.oficina.workerproc import WorkerProc;"
        f"wp = WorkerProc({str(tmp_path)!r});"
        "print(wp.spawn_detached(['sleep', '30']))"
    )
    env = {**os.environ, "PYTHONPATH": src_root}
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, env=env, timeout=20,
    )
    assert out.returncode == 0, out.stderr
    grandchild = int(out.stdout.strip())
    spawned.append(grandchild)
    # The parent (-c process) has exited; the grandchild must still be alive.
    time.sleep(0.5)
    assert WorkerProc(tmp_path).is_alive(grandchild)


# --- ensure_worker decision (P1-D9) -----------------------------------------


def test_ensure_worker_spawns_when_no_live_owner(tmp_path, spawned):
    """With no live owner, ensure_worker spawns a detached worker and returns its pid."""
    wp = WorkerProc(tmp_path)
    pid = wp.ensure_worker(["sleep", "30"])
    spawned.append(pid)
    assert wp.is_alive(pid)
    assert pid != os.getpid()


def test_ensure_worker_skips_spawn_when_owner_live(tmp_path):
    """When a live owner already holds the pidfile, ensure_worker does not spawn."""
    wp = WorkerProc(tmp_path, start_time_reader=_fixed_reader)
    wp.pidfile.write_text(
        json.dumps({"pid": os.getpid(), "start": _FIXED_START}), encoding="utf-8"
    )
    returned = wp.ensure_worker(["sleep", "30"])
    assert returned == os.getpid()
