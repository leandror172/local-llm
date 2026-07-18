"""Characterization tests for the script-backed persona tools (detect/build/create).

These pin the CURRENT subprocess behavior — stripped stdout on success, the exact
``Error: {tool} exited with code N: ...`` string on non-zero exit, and the timeout
message — BEFORE the shared ``_run_script`` helper is extracted. detect_persona,
build_persona, and create_persona shell out and had zero test coverage; without this
net a "behavior-preserving" refactor of their error strings could not be verified
(passing tests that never exercise the code prove nothing about the extraction).

The subprocess boundary (``asyncio.create_subprocess_exec`` / ``asyncio.wait_for``)
is mocked — no real persona scripts run. Async tests, asyncio_mode=auto.
"""

import asyncio

import pytest

from ollama_mcp import server


class _FakeProc:
    """A stand-in for the asyncio subprocess: fixed returncode + captured streams."""

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self.killed = False

    async def communicate(self):
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True


@pytest.fixture
def persona_env(tmp_path, monkeypatch):
    """A valid REPO_ROOT with the three persona scripts present so isfile guards pass.

    REGISTRY_PATH is nulled so create_persona's post-success registry reload is skipped
    (it's orthogonal to the subprocess behavior under characterization).
    """
    personas = tmp_path / "personas"
    personas.mkdir()
    for name in ("run-detect-persona.sh", "run-build-persona.sh", "run-create-persona.sh"):
        (personas / name).write_text("#!/bin/sh\n")
    monkeypatch.setattr(server, "REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(server, "REGISTRY_PATH", None)
    return tmp_path


def _mock_proc(monkeypatch, proc, *, timeout=False):
    """Patch create_subprocess_exec to yield ``proc``; optionally force a wait_for timeout."""
    async def _fake_exec(*args, **kwargs):
        return proc

    monkeypatch.setattr(server.asyncio, "create_subprocess_exec", _fake_exec)

    if timeout:
        async def _fake_wait_for(coro, timeout):
            coro.close()  # never awaited — close to avoid a RuntimeWarning
            raise asyncio.TimeoutError

        monkeypatch.setattr(server.asyncio, "wait_for", _fake_wait_for)


# --- detect_persona (timeout 30s) --------------------------------------------------


async def test_detect_persona_success_returns_stripped_stdout(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(0, stdout=b"  [json output]  \n"))
    assert await server.detect_persona(str(persona_env)) == "[json output]"


async def test_detect_persona_nonzero_exit_returns_error(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(3, stderr=b"boom detail"))
    assert await server.detect_persona(str(persona_env)) == (
        "Error: detect-persona exited with code 3: boom detail"
    )


async def test_detect_persona_nonzero_empty_stderr_says_unknown(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(1, stderr=b""))
    assert await server.detect_persona(str(persona_env)) == (
        "Error: detect-persona exited with code 1: Unknown error"
    )


async def test_detect_persona_timeout_returns_message_and_kills(persona_env, monkeypatch):
    proc = _FakeProc(0)
    _mock_proc(monkeypatch, proc, timeout=True)
    assert await server.detect_persona(str(persona_env)) == (
        "Error: detect-persona timed out after 30 seconds."
    )
    assert proc.killed


# --- build_persona (timeout 120s) --------------------------------------------------


async def test_build_persona_success_returns_stripped_stdout(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(0, stdout=b"  {spec}  "))
    assert await server.build_persona("a rust dev") == "{spec}"


async def test_build_persona_nonzero_exit_returns_error(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(1, stderr=b"nope"))
    assert await server.build_persona("a rust dev") == (
        "Error: build-persona exited with code 1: nope"
    )


async def test_build_persona_timeout_returns_message_and_kills(persona_env, monkeypatch):
    proc = _FakeProc(0)
    _mock_proc(monkeypatch, proc, timeout=True)
    assert await server.build_persona("a rust dev") == (
        "Error: build-persona timed out after 120 seconds."
    )
    assert proc.killed


# --- create_persona (timeout 60s) --------------------------------------------------


async def test_create_persona_success_returns_stripped_stdout(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(0, stdout=b"  Created my-x  "))
    assert await server.create_persona(role="x", base_model="qwen3:8b") == "Created my-x"


async def test_create_persona_nonzero_exit_returns_error(persona_env, monkeypatch):
    _mock_proc(monkeypatch, _FakeProc(2, stderr=b"bad model"))
    assert await server.create_persona(role="x", base_model="qwen3:8b") == (
        "Error: create-persona exited with code 2: bad model"
    )


async def test_create_persona_timeout_returns_message_and_kills(persona_env, monkeypatch):
    proc = _FakeProc(0)
    _mock_proc(monkeypatch, proc, timeout=True)
    assert await server.create_persona(role="x", base_model="qwen3:8b") == (
        "Error: create-persona timed out after 60 seconds."
    )
    assert proc.killed
