"""Tests for discriminating installer signals (T-54 + T-80a).

Both bugs are the same defect: an installer signal that fires identically in the
dangerous case and the benign one, therefore carrying zero bits and training the
operator to ignore it.

- T-54  `handle_manual_if_exists` flags [TODO] manual merge on every install, even
        when the installed file is byte-identical to the overlay source.
- T-80a `handle_customizable` warns "reset to overlay default" on every unmarked
        region, even when the reset changes nothing.

Design note (T-80a): decision-3 fires precisely when the installed file has NO
markers, so there is no installed interior to compare against src_regions[name].
The installer cannot locate the region. What it CAN ask is whether the overlay's
default interior is already present verbatim in the installed file:

    present  -> splicing it back is a provable no-op  -> stay silent (INFO)
    absent   -> something else is there and WILL be replaced -> WARN-CLOBBER

Polarity: silence only on proof of safety. Over-warning on ambiguity (a file that
predates the region entirely) is the correct failure direction.

Run from overlays/:
    python3 -m pytest test_signals.py -q
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lib.actions import (  # noqa: E402
    handle_customizable,
    handle_manual_if_exists,
)
from lib import report  # noqa: E402


@pytest.fixture(autouse=True)
def reset_report():
    report._actions.clear()
    yield
    report._actions.clear()


def _statuses():
    return [a["action"] for a in report._actions]


def _reasons():
    return " ".join(a.get("reason", "") for a in report._actions)


def _make_overlay(tmp_path, *, name="ov", version=1):
    overlay_dir = tmp_path / "overlays" / name
    files_dir = overlay_dir / "files"
    files_dir.mkdir(parents=True)
    return overlay_dir, files_dir, {"name": name, "version": version}


def _make_target(tmp_path):
    t = tmp_path / "target"
    t.mkdir()
    return t


# ── T-80a fixtures: the two real repo states from the v10 propagation ─────────

OPEN = "# overlay-keep:reading-guide"
CLOSE = "# /overlay-keep:reading-guide"

DEFAULT_INTERIOR = 'echo "── Pre-session reading guide ──"\nGUIDE=$(default_filter)\n'


def _src_v10():
    """Overlay source: markers wrapped around the default interior."""
    return (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1\n"
        f"{OPEN}\n"
        f"{DEFAULT_INTERIOR}"
        f"{CLOSE}\n"
        "echo SECTION_5\n"
    )


def _installed_expenses():
    """Benign: v9 — no markers, but the region body is the overlay default verbatim.
    v10 only ADDED marker lines around it, so the reset writes back what is there."""
    return (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1\n"
        f"{DEFAULT_INTERIOR}"
        "echo SECTION_5\n"
    )


def _installed_career_search():
    """Destructive: v9 — no markers AND a customized region body. The reset
    silently replaces the repo's variant."""
    return (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1\n"
        'echo "── What to read first ──"\n'
        "GUIDE=$(lighter_filter)\n"
        "echo SECTION_5\n"
    )


def _customizable_manifest(dest_rel="resume.sh"):
    return {
        "name": "ov",
        "version": 10,
        "customizable": {dest_rel: {"keep_regions": ["reading-guide"]}},
    }


def _setup_customizable(tmp_path, installed_text, dest_rel="resume.sh"):
    overlay_dir, files_dir, _ = _make_overlay(tmp_path)
    (files_dir / "resume.sh").write_text(_src_v10())
    target = _make_target(tmp_path)
    (target / dest_rel).write_text(installed_text)
    return overlay_dir, target, _customizable_manifest(dest_rel)


# ── T-80a: the reset warning must discriminate ───────────────────────────────


def test_benign_reset_is_silent(tmp_path):
    """Overlay default already present verbatim -> reset is a provable no-op."""
    overlay_dir, target, manifest = _setup_customizable(tmp_path, _installed_expenses())
    handle_customizable(manifest, overlay_dir, target, dry_run=True, do_backup=False)

    assert "WARN-CLOBBER" not in _statuses()
    assert "INFO" in _statuses()
    assert "no-op" in _reasons()


def test_destructive_reset_warns_loudly(tmp_path):
    """Region body differs from the overlay default -> installing loses it."""
    overlay_dir, target, manifest = _setup_customizable(tmp_path, _installed_career_search())
    handle_customizable(manifest, overlay_dir, target, dry_run=True, do_backup=False)

    assert "WARN-CLOBBER" in _statuses()
    assert "reading-guide" in _reasons()


def test_benign_and_destructive_produce_different_output(tmp_path):
    """The acceptance criterion from T-79: the two real repo states must NOT
    produce byte-identical dry-run output. This is the whole bug."""
    overlay_dir, target, manifest = _setup_customizable(tmp_path, _installed_expenses())
    handle_customizable(manifest, overlay_dir, target, dry_run=True, do_backup=False)
    benign = list(_statuses())

    report._actions.clear()
    overlay_dir, target, manifest = _setup_customizable(
        tmp_path / "second", _installed_career_search()
    )
    handle_customizable(manifest, overlay_dir, target, dry_run=True, do_backup=False)
    destructive = list(_statuses())

    assert benign != destructive


def test_marked_region_is_preserved_without_any_warning(tmp_path):
    """Regression: a repo that correctly wrapped its variant in markers keeps it
    and triggers no reset signal at all."""
    marked = (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1_OLD\n"
        f"{OPEN}\n"
        'echo "── What to read first ──"\n'
        f"{CLOSE}\n"
        "echo SECTION_5\n"
    )
    overlay_dir, target, manifest = _setup_customizable(tmp_path, marked)
    handle_customizable(manifest, overlay_dir, target, dry_run=False, do_backup=False)

    assert "WARN-CLOBBER" not in _statuses()
    assert "INFO" not in _statuses()
    assert 'echo "── What to read first ──"' in (target / "resume.sh").read_text()


def test_file_predating_the_region_warns_rather_than_claiming_clobber(tmp_path):
    """No §2b block at all (latent-topic-graph). We cannot prove the reset is
    safe, so we warn — but the reason must not assert content will be lost."""
    no_section = "#!/usr/bin/env bash\necho SECTION_1\necho SECTION_5\n"
    overlay_dir, target, manifest = _setup_customizable(tmp_path, no_section)
    handle_customizable(manifest, overlay_dir, target, dry_run=True, do_backup=False)

    assert "WARN-CLOBBER" in _statuses()
    assert "not present" in _reasons()


# ── T-54: manual_if_exists must not flag an identical file ───────────────────


def _setup_manual(tmp_path, *, src_text, dest_text=None, dest_rel=".claude/handoff/registry.yaml"):
    overlay_dir, files_dir, _ = _make_overlay(tmp_path)
    (files_dir / Path(dest_rel).name).write_text(src_text)
    target = _make_target(tmp_path)
    if dest_text is not None:
        dest = target / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(dest_text)
    return overlay_dir, target, {"name": "ov", "version": 1, "manual_if_exists": [dest_rel]}


def test_identical_file_is_not_flagged_for_manual_merge(tmp_path):
    """latent-topic-graph's live state: registry.yaml byte-identical to source,
    yet flagged [TODO] on every install."""
    text = "version: 1\nroles: {}\n"
    overlay_dir, target, manifest = _setup_manual(tmp_path, src_text=text, dest_text=text)
    handle_manual_if_exists(manifest, overlay_dir, target, dry_run=True)

    assert "TODO" not in _statuses()
    assert "SAME" in _statuses()


def test_differing_file_is_flagged_for_manual_merge(tmp_path):
    overlay_dir, target, manifest = _setup_manual(
        tmp_path, src_text="version: 2\n", dest_text="version: 1\n"
    )
    handle_manual_if_exists(manifest, overlay_dir, target, dry_run=True)

    assert "TODO" in _statuses()
    assert "SAME" not in _statuses()


def test_eol_difference_alone_does_not_flag(tmp_path):
    """A CRLF working copy of an otherwise identical file must not read as drift —
    the rest of the installer is EOL-normalized (_read_text_eol)."""
    overlay_dir, target, manifest = _setup_manual(
        tmp_path, src_text="version: 1\nroles: {}\n"
    )
    dest = target / ".claude/handoff/registry.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"version: 1\r\nroles: {}\r\n")
    handle_manual_if_exists(manifest, overlay_dir, target, dry_run=True)

    assert "SAME" in _statuses()
    assert "TODO" not in _statuses()


def test_missing_dest_still_copies(tmp_path):
    """Regression: the first-install path is untouched."""
    overlay_dir, target, manifest = _setup_manual(tmp_path, src_text="version: 1\n")
    handle_manual_if_exists(manifest, overlay_dir, target, dry_run=True)

    assert "COPY" in _statuses()


def test_missing_dest_and_missing_source_is_todo(tmp_path):
    overlay_dir, files_dir, _ = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    manifest = {"name": "ov", "version": 1, "manual_if_exists": ["nope.yaml"]}
    handle_manual_if_exists(manifest, overlay_dir, target, dry_run=True)

    assert "TODO" in _statuses()
