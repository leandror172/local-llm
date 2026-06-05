# test_registry_io.py
#
# Contract tests for load_register: parse registry.yaml -> the `roles:` mapping
# that orchestrator.run_handoff consumes. A tiny fixture pins the happy path; a
# smoke test against the REAL registry.yaml guards against drift between the live
# register and the code that reads it.
#
# Flat imports — run from inside the handoff dir.

import textwrap
from pathlib import Path

import pytest

from registry_io import load_register, RegistryError


FIXTURE = textwrap.dedent("""\
    version: 1
    roles:
      log-entry:
        description: New per-session log entry.
        file: .claude/session-log.md
        locator:
          type: structural
          pattern: '^---$'
          occurrence: 1
          position: after
        write_mode: prepend
        used_by: [write]
      current-status:
        description: Current checkpoint.
        file: .claude/session-context.md
        locator:
          type: ref_block
          key: current-status
        write_mode: replace
        used_by: [read, write]
""")

# The real register lives two dirs up from this handoff dir.
REAL_REGISTRY = Path(__file__).resolve().parents[2] / "registry.yaml"


def _write(tmp_path, text):
    p = tmp_path / "registry.yaml"
    p.write_text(text)
    return p


def test_returns_roles_mapping(tmp_path):
    reg = load_register(_write(tmp_path, FIXTURE))
    assert set(reg) == {"log-entry", "current-status"}
    assert reg["log-entry"]["file"] == ".claude/session-log.md"
    assert reg["log-entry"]["write_mode"] == "prepend"
    assert reg["current-status"]["locator"]["type"] == "ref_block"
    assert reg["current-status"]["locator"]["key"] == "current-status"


def test_accepts_str_path(tmp_path):
    reg = load_register(str(_write(tmp_path, FIXTURE)))
    assert "log-entry" in reg


def test_missing_roles_key_raises(tmp_path):
    with pytest.raises(RegistryError):
        load_register(_write(tmp_path, "version: 1\n"))


def test_missing_file_raises(tmp_path):
    with pytest.raises(RegistryError):
        load_register(tmp_path / "does-not-exist.yaml")


def test_real_registry_has_orchestrator_required_roles():
    reg = load_register(REAL_REGISTRY)
    # Roles the orchestrator dereferences by name must exist with the right shape.
    for role in ("header-current-session", "header-current-layer", "tasks-checkoff"):
        assert role in reg
        assert "file" in reg[role] and "write_mode" in reg[role]
    assert reg["header-current-session"]["write_mode"] == "nomodel"
