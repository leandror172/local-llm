"""Tests for the T-81 AI-merge stage → apply split.

Contract under test (re-derived, not trusted from green): a merge plan's line
numbers are valid ONLY against the exact pre-image they were computed from, so a
staged handle carries `target_pre_sha256` and `apply_staged_plan` MUST abort
(record STALE, write nothing) unless sha256(current target) == that hash.

Hermetic: the backend is the mock seam (`FakeBackend`), every fixture builds its
own tmp target + tmp plan dir, nothing reads the real repo. Plain sync pytest —
NO asyncio. Run from overlays/:  python3 -m pytest test_merge_stage_apply.py -q
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lib import report
from lib.actions import handle_merge_sections, _read_text_eol
from lib.backends import SchemaMode
from lib.planner import (
    apply_staged_plan,
    stage_all_sections,
    stage_merge,
)

OPEN = "<!-- overlay:session-tracking v11 -->"
CLOSE = "<!-- /overlay:session-tracking -->"
SECTION = "## Overlay Section\nbody line one\nbody line two"


# ── fixtures / seams ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_report():
    report._actions.clear()
    yield
    report._actions.clear()


class FakeBackend:
    """Mock backend seam. `.call` returns a canned plan JSON (or None / non-JSON)
    and increments a counter so tests can assert whether the model was invoked."""

    def __init__(self, plan_json, backend_id="fake-local",
                 schema_mode=SchemaMode.FORMAT_PARAM):
        self._plan_json = plan_json
        self.id = backend_id
        self.schema_mode = schema_mode
        self.call_count = 0
        self.last_prompt = None

    def is_available(self):
        return True

    def call(self, prompt, fmt=None, model_override=None, debug=False):
        self.call_count += 1
        self.last_prompt = prompt
        return self._plan_json


def _plan_json(insert_after_line, delete_ranges=None, reasoning="test"):
    return json.dumps({
        "insert_after_line": insert_after_line,
        "delete_ranges": delete_ranges or [],
        "reasoning": reasoning,
    })


def _write_prompts(tmp_path):
    pd = tmp_path / "prompts"
    pd.mkdir()
    (pd / "merge-plan.txt").write_text(
        "EXISTING:\n<<EXISTING_CONTENT>>\nSECTION:\n<<SECTION_CONTENT>>\nHINT:<<MERGE_HINT>>\n"
    )
    (pd / "merge-plan-schema.json").write_text(json.dumps({"type": "object"}))
    return pd


def _make_target(tmp_path, content, name="CLAUDE.md"):
    dest = tmp_path / "repo" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    return dest


def _plan_path(tmp_path):
    return tmp_path / "plans" / "handle.json"


def _stage(tmp_path, target_content, plan_json, *, merge_hint="place it"):
    """Stage a single target via stage_merge; return (dest, backend, handle_path)."""
    dest = _make_target(tmp_path, target_content)
    prompts = _write_prompts(tmp_path)
    backend = FakeBackend(plan_json)
    existing, _ = _read_text_eol(dest)
    handle = stage_merge(dest, existing, SECTION, OPEN, CLOSE, merge_hint,
                         "auto", None, [backend], prompts, _plan_path(tmp_path), False)
    return dest, backend, handle


def _actions_with(action):
    return [a for a in report._actions if a["action"] == action]


# ── stage ─────────────────────────────────────────────────────────────────────


def test_stage_calls_backend(tmp_path):
    """--stage invokes the backend (defect-(a) fix): call counter >= 1."""
    _, backend, handle = _stage(tmp_path, "line1\nline2\nline3\n", _plan_json(3))
    assert backend.call_count >= 1
    assert handle is not None and handle.exists()


def test_dry_run_does_not_call_backend(tmp_path):
    """--dry-run purity (D1): backend untouched, no handle, only a 'would AI-merge
    … run --stage' record."""
    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "files").mkdir(parents=True)
    section_file = overlay_dir / "files" / "section.md"
    section_file.write_text(SECTION)
    target_root = tmp_path / "repo"
    target_root.mkdir()
    (target_root / "CLAUDE.md").write_text("pre-existing\ncontent\nhere\n")
    prompts = _write_prompts(tmp_path)
    manifest = {"name": "session-tracking", "version": 11,
                "merge_sections": {"CLAUDE.md": {"file": "files/section.md"}}}
    backend = FakeBackend(_plan_json(2))

    before = (target_root / "CLAUDE.md").read_bytes()
    handle_merge_sections(manifest, overlay_dir, target_root, prompts,
                          "ai", False, "auto", None, [backend], True, True, False)

    assert backend.call_count == 0
    assert (target_root / "CLAUDE.md").read_bytes() == before
    reasons = " ".join(a["reason"] for a in report._actions)
    assert "would AI-merge" in reasons and "--stage" in reasons
    assert not (target_root / ".claude").exists()


def test_stage_writes_handle_without_touching_target(tmp_path):
    """Target bytes unchanged after stage; handle file exists."""
    content = "alpha\nbeta\ngamma\n"
    dest = _make_target(tmp_path, content)
    prompts = _write_prompts(tmp_path)
    backend = FakeBackend(_plan_json(2))
    existing, _ = _read_text_eol(dest)
    before = dest.read_bytes()
    handle = stage_merge(dest, existing, SECTION, OPEN, CLOSE, "hint",
                         "auto", None, [backend], prompts, _plan_path(tmp_path), False)
    assert dest.read_bytes() == before
    assert handle.exists()


def test_stage_handle_records_pre_image_hash(tmp_path):
    """target_pre_sha256 == sha256(original pre-image); schema/markers/section present."""
    content = "one\ntwo\nthree\n"
    dest, _, handle = _stage(tmp_path, content, _plan_json(3))
    data = json.loads(handle.read_text())
    existing, _ = _read_text_eol(dest)
    assert data["target_pre_sha256"] == hashlib.sha256(existing.encode("utf-8")).hexdigest()
    assert data["schema"] == "overlay-merge-plan/v1"
    assert data["open_marker"] == OPEN
    assert data["close_marker"] == CLOSE
    assert data["section_content"] == SECTION


def test_stage_stores_overlay_range_corrected_plan(tmp_path):
    """The STORED plan carries the overlay-range-corrected insert_after_line, so
    apply (which trusts the plan verbatim) matches the diff shown at stage time."""
    # Existing already has an overlay block on lines 2-4; model wrongly picks line 3.
    content = (
        "header\n"
        "<!-- overlay:session-tracking v10 -->\n"
        "old body\n"
        "<!-- /overlay:session-tracking -->\n"
        "footer\n"
    )
    _, _, handle = _stage(tmp_path, content, _plan_json(3))
    data = json.loads(handle.read_text())
    assert data["plan"]["insert_after_line"] == 4  # bumped to the block's close line


def test_stage_prints_unified_diff(tmp_path, capsys):
    """Captured stdout contains diff headers and the inserted section text."""
    _stage(tmp_path, "x1\nx2\nx3\n", _plan_json(3))
    out = capsys.readouterr().out
    assert "--- " in out and "+++ " in out
    assert "Overlay Section" in out


def test_stage_degrades_to_todo_on_bad_json(tmp_path):
    """Non-JSON model output → TODO recorded, no handle written, target untouched."""
    dest = _make_target(tmp_path, "p\nq\nr\n")
    prompts = _write_prompts(tmp_path)
    backend = FakeBackend("this is not json at all")
    existing, _ = _read_text_eol(dest)
    before = dest.read_bytes()
    pf = _plan_path(tmp_path)
    handle = stage_merge(dest, existing, SECTION, OPEN, CLOSE, "hint",
                         "auto", None, [backend], prompts, pf, False)
    assert handle is None
    assert not pf.exists()
    assert dest.read_bytes() == before
    assert _actions_with("TODO")


# ── apply ─────────────────────────────────────────────────────────────────────


def test_apply_writes_merged_and_backs_up(tmp_path):
    """After apply the target carries markers+section; .bak exists when do_backup."""
    dest, _, handle = _stage(tmp_path, "a\nb\nc\n", _plan_json(3))
    apply_staged_plan(handle, do_backup=True)
    text = dest.read_text()
    assert OPEN in text and CLOSE in text and "Overlay Section" in text
    assert dest.with_suffix(dest.suffix + ".bak").exists()
    assert _actions_with("APPLY")


def test_apply_aborts_when_target_changed_since_stage(tmp_path):
    """THE INVARIANT: mutate the target between stage and apply → apply records
    STALE, writes nothing, no .bak."""
    dest, _, handle = _stage(tmp_path, "a\nb\nc\n", _plan_json(3))
    mutated = "a\nb\nc\nMUTATED EXTRA LINE\n"
    dest.write_text(mutated)
    apply_staged_plan(handle, do_backup=True)
    assert dest.read_text() == mutated  # untouched by apply
    assert not dest.with_suffix(dest.suffix + ".bak").exists()
    assert _actions_with("STALE")
    assert not _actions_with("APPLY")


def test_apply_errors_on_missing_or_wrong_schema_handle(tmp_path):
    """Missing file / wrong schema → clear ERROR, no write."""
    missing = tmp_path / "nope.json"
    apply_staged_plan(missing, do_backup=True)
    assert _actions_with("ERROR")

    report._actions.clear()
    dest = _make_target(tmp_path, "a\nb\n")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": "wrong/v9", "dest": str(dest),
                               "dest_rel": "CLAUDE.md"}))
    before = dest.read_bytes()
    apply_staged_plan(bad, do_backup=True)
    assert _actions_with("ERROR")
    assert dest.read_bytes() == before


def test_apply_result_equals_stage_time_merge(tmp_path):
    """Independent-path check: expected merged computed as a hard-coded literal
    (delete BEFORE the insert point), NOT by re-calling apply_plan."""
    existing = "A\nB\nC\nD\nE\nF\n"
    plan = _plan_json(5, delete_ranges=[{"start": 3, "end": 4, "reason": "supersede"}])
    dest = _make_target(tmp_path, existing)
    prompts = _write_prompts(tmp_path)
    backend = FakeBackend(plan)
    existing_norm, _ = _read_text_eol(dest)
    handle = stage_merge(dest, existing_norm, "SEC", OPEN, CLOSE, "hint",
                         "auto", None, [backend], prompts, _plan_path(tmp_path), False)
    apply_staged_plan(handle, do_backup=False)
    expected = f"A\nB\nE\n{OPEN}\nSEC\n{CLOSE}\nF\n"
    assert dest.read_text() == expected


def test_stage_then_apply_end_to_end(tmp_path):
    """Full round-trip via stage_all_sections on a target whose plan deletes an
    old superseded block, then apply."""
    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "files").mkdir(parents=True)
    (overlay_dir / "files" / "section.md").write_text(SECTION)
    target_root = tmp_path / "repo"
    target_root.mkdir()
    dest = target_root / "CLAUDE.md"
    dest.write_text("intro\nOLD STALE SECTION\nmore\ntail\n")
    prompts = _write_prompts(tmp_path)
    manifest = {"name": "session-tracking", "version": 11,
                "merge_sections": {"CLAUDE.md": {"file": "files/section.md"}}}
    backend = FakeBackend(_plan_json(
        4, delete_ranges=[{"start": 2, "end": 2, "reason": "old section"}]))

    stage_all_sections(manifest, overlay_dir, target_root, prompts,
                       "auto", None, [backend], None, False)
    handle = target_root / ".claude/local/overlay-merge-plans" / "session-tracking__CLAUDE.md.json"
    assert handle.exists()
    assert dest.read_text() == "intro\nOLD STALE SECTION\nmore\ntail\n"  # untouched

    apply_staged_plan(handle, do_backup=True)
    text = dest.read_text()
    assert OPEN in text and CLOSE in text and "Overlay Section" in text
    assert "OLD STALE SECTION" not in text


def test_apply_preserves_crlf(tmp_path):
    """CRLF target stays CRLF after apply (guards the _read/_write_text_eol reuse)."""
    dest = tmp_path / "repo" / "CLAUDE.md"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"a\r\nb\r\nc\r\n")
    prompts = _write_prompts(tmp_path)
    backend = FakeBackend(_plan_json(3))
    existing, crlf = _read_text_eol(dest)
    assert crlf
    handle = stage_merge(dest, existing, SECTION, OPEN, CLOSE, "hint",
                         "auto", None, [backend], prompts, _plan_path(tmp_path), False)
    apply_staged_plan(handle, do_backup=False)
    raw = dest.read_bytes()
    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")  # no lone LF remains
