"""Tests for verify_overlay() — T-58.

Run from overlays/:
    python3 -m pytest test_verify.py -q
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure overlays/ is on path so `from lib.actions import ...` resolves.
sys.path.insert(0, str(Path(__file__).parent))

from lib.actions import verify_overlay
from lib import report


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_report():
    """Clear accumulated report actions before and after each test."""
    report._actions.clear()
    yield
    report._actions.clear()


@pytest.fixture()
def home_isolation(monkeypatch, tmp_path):
    """Monkeypatch $HOME → tmp dir so always_user_files never touch real ~/.claude."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


# ── overlay / target factory ──────────────────────────────────────────────────


def _make_overlay(tmp_path, *, name="ov", version=1):
    """Create a minimal overlay directory tree.

    Returns (overlay_dir, files_dir, tmpl_dir, base_manifest).
    """
    overlay_dir = tmp_path / "overlays" / name
    files_dir = overlay_dir / "files"
    tmpl_dir = overlay_dir / "templates"
    files_dir.mkdir(parents=True)
    tmpl_dir.mkdir()
    manifest = {"name": name, "version": version}
    return overlay_dir, files_dir, tmpl_dir, manifest


def _make_target(tmp_path, sub="target"):
    t = tmp_path / sub
    t.mkdir()
    return t


# ── case 1: all-same → tally (0, 0, 0) ──────────────────────────────────────


def test_all_same(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    src_file = files_dir / "tool.sh"
    src_file.write_bytes(b"#!/bin/sh\necho hello\n")
    dest_file = target / "tool.sh"
    dest_file.write_bytes(src_file.read_bytes())  # byte-identical copy
    m["files"] = {"tool.sh": "tool.sh"}

    tally = verify_overlay(m, ov_dir, target, "project")
    assert tally == (0, 0, 0), f"expected (0,0,0) got {tally}"
    statuses = [a["action"] for a in report._actions]
    assert all(s == "SAME" for s in statuses), f"non-SAME actions: {statuses}"


# ── case 2: diff → DIFF, n_diff==1 ───────────────────────────────────────────


def test_diff(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    (files_dir / "tool.sh").write_bytes(b"#!/bin/sh\necho NEW\n")
    (target / "tool.sh").write_bytes(b"#!/bin/sh\necho OLD\n")
    m["files"] = {"tool.sh": "tool.sh"}

    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert n_diff == 1
    assert n_missing == 0
    assert n_src == 0
    assert any(a["action"] == "DIFF" for a in report._actions)


# ── case 3: missing dest → MISSING, n_missing==1 ─────────────────────────────


def test_missing_dest(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    (files_dir / "tool.sh").write_bytes(b"#!/bin/sh\necho hello\n")
    m["files"] = {"tool.sh": "tool.sh"}
    # dest does NOT exist

    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert n_missing == 1
    assert n_diff == 0
    assert n_src == 0
    assert any(a["action"] == "MISSING" for a in report._actions)


# ── case 4: always_user_file checked at isolated $HOME → DIFF ────────────────
# Guards the motivating bug: stale verifier.py at ~/.claude/tools/handoff/


def test_always_user_file_diff(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    # Source file (newer)
    (files_dir / "handoff").mkdir()
    (files_dir / "handoff" / "engine.py").write_bytes(b"# NEW engine\n")

    # Installed file under fake home (stale)
    dest_dir = home_isolation / ".claude" / "tools" / "handoff"
    dest_dir.mkdir(parents=True)
    (dest_dir / "engine.py").write_bytes(b"# OLD engine\n")

    m["always_user_files"] = {"handoff/engine.py": "tools/handoff/engine.py"}

    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert n_diff >= 1, f"expected n_diff>=1 but got ({n_diff},{n_missing},{n_src})"
    assert any(a["action"] == "DIFF" for a in report._actions)


# ── case 5a: templates DIFF is EXPECTED, not a gate (T-82 reverses decision (a)) ──


def test_template_diff_does_not_gate_exit(tmp_path, home_isolation):
    """T-82 reverses T-58's "Decision (a)".

    The old contract — "DIFF and MISSING both gate exit, same as overlay-owned;
    USER-MANAGED label kept in report for readability only" — made --verify exit 1 on
    every repo that had ever held a session, because session-log.md diverges from its
    starter template immediately. A gate that always trips is a gate nobody reads, which
    is how latent-topic-graph's unresolvable `tasks-append` role survived every run.
    """
    ov_dir, _, tmpl_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    (tmpl_dir / "session-log.md.tmpl").write_bytes(b"# NEW template content\n")
    dest = target / ".claude" / "session-log.md"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"# OLD user-modified content\n")
    m["templates"] = {"session-log.md.tmpl": ".claude/session-log.md"}

    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert (n_diff, n_missing, n_src) == (0, 0, 0)
    assert any(a["action"] == "EXPECTED" for a in report._actions)
    assert not any(a["action"] == "DIFF" for a in report._actions)


# ── case 5b: manual_if_exists MISSING gates exit (decision (a)) ──────────────


def test_manual_if_exists_missing_gates_exit(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    (files_dir / "registry.yaml").write_bytes(b"# registry\n")
    m["manual_if_exists"] = [".claude/handoff/registry.yaml"]
    # dest does NOT exist

    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert n_missing >= 1, f"manual_if_exists MISSING should gate exit: ({n_diff},{n_missing},{n_src})"
    assert any(a["action"] == "MISSING" for a in report._actions)


# ── case 6: merge_section marker logic (SAME / DIFF / MISSING) ───────────────


def _section_overlay(tmp_path):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path, name="myov", version=3)
    target = _make_target(tmp_path)
    sections_dir = ov_dir / "sections"
    sections_dir.mkdir()
    (sections_dir / "rules.md").write_bytes(b"## Rules\nDo things.\n")
    m["merge_sections"] = {
        "CLAUDE.md": {"file": "sections/rules.md", "merge_hint": "top"}
    }
    return ov_dir, m, target


def test_merge_section_same(tmp_path, home_isolation):
    ov_dir, m, target = _section_overlay(tmp_path)
    (target / "CLAUDE.md").write_bytes(
        b"# CLAUDE\n<!-- overlay:myov v3 -->\n## Rules\nDo things.\n<!-- /overlay:myov -->\n"
    )
    tally = verify_overlay(m, ov_dir, target, "project")
    assert tally == (0, 0, 0), f"matching version → SAME, got {tally}"
    assert any(a["action"] == "SAME" for a in report._actions)


def test_merge_section_diff_version(tmp_path, home_isolation):
    ov_dir, m, target = _section_overlay(tmp_path)
    (target / "CLAUDE.md").write_bytes(
        b"# CLAUDE\n<!-- overlay:myov v1 -->\n## Old Rules\n<!-- /overlay:myov -->\n"
    )
    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert n_diff >= 1, f"version mismatch → DIFF: ({n_diff},{n_missing},{n_src})"
    assert any(a["action"] == "DIFF" for a in report._actions)


def test_merge_section_missing_marker(tmp_path, home_isolation):
    ov_dir, m, target = _section_overlay(tmp_path)
    (target / "CLAUDE.md").write_bytes(b"# CLAUDE\nNo overlay section here.\n")
    n_diff, n_missing, n_src = verify_overlay(m, ov_dir, target, "project")
    assert n_missing >= 1, f"no marker → MISSING: ({n_diff},{n_missing},{n_src})"
    assert any(a["action"] == "MISSING" for a in report._actions)


# ── case 7: source file missing → SRC-MISSING, no exception ──────────────────


def test_src_missing_no_exception(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    # Manifest points to a non-existent file in overlay/files/
    m["files"] = {"nonexistent.sh": "tool.sh"}

    tally = verify_overlay(m, ov_dir, target, "project")
    n_diff, n_missing, n_src = tally
    assert n_src >= 1, f"src-missing should count: {tally}"
    assert any(a["action"] == "SRC-MISSING" for a in report._actions)


# ── case 8: read-only invariant ───────────────────────────────────────────────


def _snapshot_tree(root: Path) -> dict:
    """Snapshot all files under root as {rel_path: sha256_hex}."""
    import hashlib
    snap = {}
    if not root.exists():
        return snap
    for p in sorted(root.rglob("*")):
        if p.is_file():
            snap[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snap


def test_read_only_invariant(tmp_path, home_isolation):
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    # DIFF scenario: dest differs from source
    (files_dir / "tool.sh").write_bytes(b"#!/bin/sh\necho NEW\n")
    (target / "tool.sh").write_bytes(b"#!/bin/sh\necho OLD\n")
    m["files"] = {"tool.sh": "tool.sh"}

    target_before = _snapshot_tree(target)
    home_before = _snapshot_tree(home_isolation)

    verify_overlay(m, ov_dir, target, "project")

    target_after = _snapshot_tree(target)
    home_after = _snapshot_tree(home_isolation)

    assert target_before == target_after, "verify_overlay must NOT modify target tree"
    assert home_before == home_after, "verify_overlay must NOT modify home tree"


# ── case 9: keystone — fresh install → --verify exits 0 ─────────────────────
# Subprocess install ensures all categories are placed, then --verify confirms.


OVERLAYS_DIR = Path(__file__).parent  # overlays/


def test_keystone_install_then_verify(tmp_path, monkeypatch):
    """Fresh install of session-tracking (project level) → --verify exits 0."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    target = tmp_path / "target"
    target.mkdir()

    # Pre-seed CLAUDE.md with the v7 overlay marker so merge_sections → SAME
    # (manual mode prints TODO and doesn't insert the marker, so we must seed it)
    (target / "CLAUDE.md").write_bytes(
        b"# CLAUDE\n"
        b"<!-- overlay:session-tracking v7 -->\n"
        b"Placeholder session-tracking section.\n"
        b"<!-- /overlay:session-tracking -->\n"
    )

    installer = OVERLAYS_DIR / "install-overlay.py"
    env = dict(os.environ, HOME=str(fake_home))

    # Step 1: install
    r1 = subprocess.run(
        [sys.executable, str(installer), "session-tracking",
         "--target", str(target),
         "--install-level", "project",
         "--mode", "manual"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(OVERLAYS_DIR),
    )
    assert r1.returncode == 0, (
        f"Install subprocess failed:\nSTDOUT:\n{r1.stdout}\nSTDERR:\n{r1.stderr}"
    )

    # Step 2: verify → must exit 0 with no DIFF or MISSING
    r2 = subprocess.run(
        [sys.executable, str(installer), "session-tracking",
         "--target", str(target),
         "--install-level", "project",
         "--verify"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(OVERLAYS_DIR),
    )
    out2 = r2.stdout
    assert "[DIFF]" not in out2, (
        f"Unexpected DIFF after fresh install:\n{out2}"
    )
    assert "[MISSING]" not in out2, (
        f"Unexpected MISSING after fresh install:\n{out2}"
    )
    assert r2.returncode == 0, (
        f"--verify should exit 0 after fresh install:\nSTDOUT:\n{out2}\nSTDERR:\n{r2.stderr}"
    )


# ── case 10: EOL normalize — CRLF dest vs LF src → SAME ─────────────────────


def test_eol_normalize_crlf_is_same(tmp_path, home_isolation):
    """A dest file with CRLF line endings vs LF source must be reported SAME."""
    ov_dir, files_dir, _, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)

    # Source uses LF only
    (files_dir / "tool.sh").write_bytes(b"#!/bin/sh\necho hello\n")
    # Dest has the same content but with CRLF line endings
    (target / "tool.sh").write_bytes(b"#!/bin/sh\r\necho hello\r\n")
    m["files"] = {"tool.sh": "tool.sh"}

    tally = verify_overlay(m, ov_dir, target, "project")
    assert tally == (0, 0, 0), f"CRLF↔LF should be SAME (EOL-normalized), got {tally}"
    assert all(a["action"] == "SAME" for a in report._actions)


# ══════════════════════════════════════════════════════════════════════════════
# T-82 + locator contract: --verify must ask the right question per ownership
#
# Byte-equality is the wrong question for a file the repo OWNS. session-log.md
# diverges from its starter template after one session; a per-repo register
# diverges by design. Gating on those made --verify permanently red, so nobody
# read it — which is how a `tasks-append` role pointing at a ref block that never
# existed survived in latent-topic-graph through every verify run.
#
# Three questions, one per kind of ownership:
#   overlay-owned files  -> are the bytes what we shipped?      (drift, gates)
#   merge sections       -> is the version marker current?      (behind, gates)
#   user-managed files   -> do the register's locators resolve? (contract)
# ══════════════════════════════════════════════════════════════════════════════

# The locator contract check imports the register primitive from the overlay's own
# package. Make it importable for the test process.
sys.path.insert(0, str(Path(__file__).parent / "session-tracking" / "src"))


def _statuses():
    return [a["action"] for a in report._actions]


def _reason_for(action):
    return " ".join(a["reason"] for a in report._actions if a["action"] == action)


def _ov(tmp_path):
    ov = tmp_path / "ov"
    (ov / "files").mkdir(parents=True)
    (ov / "templates").mkdir(parents=True)
    return ov


def _tgt(tmp_path):
    t = tmp_path / "target"
    t.mkdir()
    return t


# ── gating semantics (T-82) ──────────────────────────────────────────────────


def test_template_divergence_is_expected_and_does_not_gate(tmp_path, home_isolation):
    """session-log.md differs from its starter template after one session. Always."""
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    (ov / "templates" / "session-log.md.tmpl").write_text("# Log\n")
    (tgt / "session-log.md").write_text("# Log\n\n## 2026-07-09 - Session 1\n")
    m = {"name": "ov", "version": 1, "templates": {"session-log.md.tmpl": "session-log.md"}}

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert "EXPECTED" in _statuses()
    assert "DIFF" not in _statuses()
    assert (n_diff, n_missing, n_src) == (0, 0, 0)


def test_template_absent_still_gates(tmp_path, home_isolation):
    """Not installed is actionable; diverged is not."""
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    (ov / "templates" / "session-log.md.tmpl").write_text("# Log\n")
    m = {"name": "ov", "version": 1, "templates": {"session-log.md.tmpl": "session-log.md"}}

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert "MISSING" in _statuses()
    assert n_missing == 1


def test_manual_if_exists_divergence_is_expected_and_does_not_gate(tmp_path, home_isolation):
    """A per-repo register has per-repo locators. Differing IS the design."""
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    (ov / "files" / "registry.yaml").write_text("version: 1\nroles: {}\n")
    (tgt / "registry.yaml").write_text("version: 1\nroles: {a: {}}\n")
    m = {"name": "ov", "version": 1, "manual_if_exists": ["registry.yaml"]}

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert "EXPECTED" in _statuses()
    assert (n_diff, n_missing, n_src) == (0, 0, 0)


def test_overlay_owned_file_divergence_still_gates(tmp_path, home_isolation):
    """Regression: real drift in an overlay-owned file is what --verify is FOR."""
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    (ov / "files" / "tool.sh").write_text("v2\n")
    (tgt / "tool.sh").write_text("v1\n")
    m = {"name": "ov", "version": 1, "files": {"tool.sh": "tool.sh"}}

    n_diff, _, _ = verify_overlay(m, ov, tgt, "project")

    assert "DIFF" in _statuses()
    assert n_diff == 1


# ── locator contract ─────────────────────────────────────────────────────────


REGISTER = """version: 1
roles:
  tasks-append:
    file: tasks.md
    locator: {type: ref_block, key: deferred-infra}
    write_mode: append
    used_by: [write]
  quick-pointers:
    file: context.md
    locator: {type: ref_block, key: quick-pointers}
    write_mode: nomodel
    used_by: [read]
"""


def _with_register(tmp_path, register=REGISTER):
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    (tgt / "registry.yaml").write_text(register)
    m = {"name": "ov", "version": 1, "verify_locators": {"register": "registry.yaml"}}
    return ov, tgt, m


def test_write_role_with_absent_block_is_broken_and_gates(tmp_path, home_isolation):
    """latent-topic-graph's live bug: tasks-append pointed at ref:deferred-infra,
    which never existed. Any handoff task append would fail to locate its region.
    Byte-comparison cannot see this."""
    ov, tgt, m = _with_register(tmp_path)
    (tgt / "tasks.md").write_text("# Tasks\nno block here\n")
    (tgt / "context.md").write_text("<!-- ref:quick-pointers -->\nx\n<!-- /ref:quick-pointers -->\n")

    n_diff, _, _ = verify_overlay(m, ov, tgt, "project")

    assert "BROKEN" in _statuses()
    assert "tasks-append" in _reason_for("BROKEN")
    assert n_diff == 1


def test_read_only_role_with_absent_block_is_absent_and_does_not_gate(tmp_path, home_isolation):
    """expenses/web-research: no ref:quick-pointers block. resume prints its
    fallback — advisory, not broken."""
    ov, tgt, m = _with_register(tmp_path)
    (tgt / "tasks.md").write_text("<!-- ref:deferred-infra -->\nx\n<!-- /ref:deferred-infra -->\n")
    (tgt / "context.md").write_text("nothing here\n")

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert "ABSENT" in _statuses()
    assert "quick-pointers" in _reason_for("ABSENT")
    assert (n_diff, n_missing, n_src) == (0, 0, 0)


def test_role_pointing_at_a_missing_file_is_broken(tmp_path, home_isolation):
    ov, tgt, m = _with_register(tmp_path)
    (tgt / "context.md").write_text("x\n")

    n_diff, _, _ = verify_overlay(m, ov, tgt, "project")

    assert "BROKEN" in _statuses()
    assert n_diff == 1


def test_all_locators_resolving_reports_same_and_does_not_gate(tmp_path, home_isolation):
    ov, tgt, m = _with_register(tmp_path)
    (tgt / "tasks.md").write_text("<!-- ref:deferred-infra -->\nx\n<!-- /ref:deferred-infra -->\n")
    (tgt / "context.md").write_text("<!-- ref:quick-pointers -->\ny\n<!-- /ref:quick-pointers -->\n")

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert (n_diff, n_missing, n_src) == (0, 0, 0)
    assert "2/2" in _reason_for("SAME")


def test_checklist_role_is_skipped_not_crashed(tmp_path, home_isolation):
    """_locate_checklist raises without a task_id — there is no payload here, so the
    contract check can only assert the file exists."""
    reg = ("version: 1\nroles:\n  tasks-checkoff:\n    file: tasks.md\n"
           "    locator: {type: checklist, scope: file}\n"
           "    write_mode: checkoff\n    used_by: [write]\n")
    ov, tgt, m = _with_register(tmp_path, reg)
    (tgt / "tasks.md").write_text("- [ ] (T-01) thing\n")

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert "BROKEN" not in _statuses()
    assert (n_diff, n_missing, n_src) == (0, 0, 0)


def test_no_verify_locators_key_records_nothing(tmp_path, home_isolation):
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    m = {"name": "ov", "version": 1}

    assert verify_overlay(m, ov, tgt, "project") == (0, 0, 0)
    assert _statuses() == []


def test_missing_register_is_skipped_not_broken(tmp_path, home_isolation):
    """An uninstalled repo has no register. That is manual_if_exists' MISSING to
    report, not the contract check's."""
    ov, tgt = _ov(tmp_path), _tgt(tmp_path)
    m = {"name": "ov", "version": 1, "verify_locators": {"register": "registry.yaml"}}

    n_diff, n_missing, n_src = verify_overlay(m, ov, tgt, "project")

    assert "BROKEN" not in _statuses()
    assert (n_diff, n_missing, n_src) == (0, 0, 0)
