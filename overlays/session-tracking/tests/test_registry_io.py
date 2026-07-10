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

from sessiontracking.register.registry_io import load_register, RegistryError


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

# The real register is overlay CONFIG, not package code: it ships via the
# installer's manual_if_exists, so it lives in the overlay's files/ dir.
REAL_REGISTRY = Path(__file__).resolve().parents[1] / "files" / "registry.yaml"


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


# ── schema validation (R-D9: the package must refuse an unreadable register) ──


def test_absent_version_is_treated_as_schema_1(tmp_path):
    """Absence cannot prove incompatibility — schema 1 is the only one that ever
    existed, so an unversioned register loads."""
    p = _write(tmp_path, "roles:\n  a:\n    file: x.md\n")
    assert load_register(p) == {"a": {"file": "x.md"}}


def test_supported_version_loads(tmp_path):
    p = _write(tmp_path, "version: 1\nroles:\n  a:\n    file: x.md\n")
    assert load_register(p) == {"a": {"file": "x.md"}}


def test_unsupported_version_is_refused(tmp_path):
    """A present-but-unrecognised version is a hard stop: the repo's config and the
    installed package disagree, and guessing is how config drift becomes data loss."""
    p = _write(tmp_path, "version: 99\nroles:\n  a:\n    file: x.md\n")
    with pytest.raises(RegistryError) as exc:
        load_register(p)
    assert "99" in str(exc.value)
    assert "package" in str(exc.value).lower()


def test_schema_is_checked_before_roles_structure(tmp_path):
    """A future schema may not even have a `roles:` key — report the version
    mismatch, not a confusing structural error."""
    p = _write(tmp_path, "version: 99\nsomething_else: {}\n")
    with pytest.raises(RegistryError) as exc:
        load_register(p)
    assert "99" in str(exc.value)


def test_real_registry_declares_a_supported_schema():
    load_register(REAL_REGISTRY)  # must not raise
