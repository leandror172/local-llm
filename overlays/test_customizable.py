"""Tests for the `customizable:` keep-regions installer category (T-61 option b).

Plan: docs/plans/overlay-customizable-regions.md
Run from overlays/:
    python3 -m pytest test_customizable.py -q

API under test (to be implemented in lib/actions.py):
- `_extract_regions(text: str) -> dict[str, str]`
    Scan `overlay-keep:<name>` / `/overlay-keep:<name>` markers (comment-syntax-agnostic:
    match the token anywhere on a line). Return {name: interior} where interior is the
    text strictly BETWEEN the open and close marker lines. Raise ValueError with a clear
    message on an unbalanced (open without close) or duplicate region name.
- `handle_customizable(manifest, overlay_dir, target_root, dry_run, do_backup) -> None`
    Splice per plan: outside regions overlay-owned (new source); inside regions repo-owned
    (preserved; source default = first-install seed). Records via report.record.
    Marker grammar for <name>: [a-z0-9-]+.
- `verify_overlay(...)` extended with a `customizable:` section (per-region SAME / CUSTOMIZED
    (non-gating) / DIFF for outside-region drift (gates) / MISSING / SRC-MISSING).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lib.actions import (  # noqa: E402
    verify_overlay,
    handle_customizable,
    _extract_regions,
)
from lib import report  # noqa: E402


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_report():
    report._actions.clear()
    yield
    report._actions.clear()


@pytest.fixture()
def home_isolation(monkeypatch, tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


# ── overlay / target factory ──────────────────────────────────────────────────


def _make_overlay(tmp_path, *, name="ov", version=1):
    """Minimal overlay tree. Returns (overlay_dir, files_dir, manifest)."""
    overlay_dir = tmp_path / "overlays" / name
    files_dir = overlay_dir / "files"
    files_dir.mkdir(parents=True)
    manifest = {"name": name, "version": version}
    return overlay_dir, files_dir, manifest


def _make_target(tmp_path, sub="target"):
    t = tmp_path / sub
    t.mkdir()
    return t


def _statuses():
    return [a["action"] for a in report._actions]


def _details():
    return " ".join(a.get("reason", "") for a in report._actions)


# ── marker fixtures (aligned with ref:overlay-customizable-acceptance) ─────────

OPEN = "# overlay-keep:reading-guide"
CLOSE = "# /overlay-keep:reading-guide"


def _src_v2():
    """Overlay source AFTER an out-of-region change (SECTION_1_UPDATED)."""
    return (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1_UPDATED\n"
        f"{OPEN}\n"
        "echo DEFAULT_TITLE\n"
        "GUIDE=$(default_filter)\n"
        f"{CLOSE}\n"
        "echo SECTION_5_UNCHANGED\n"
    )


def _installed_customized():
    """Consumer that customized the region but is on OLD out-of-region content."""
    return (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1_OLD\n"
        f"{OPEN}\n"
        "echo CAREER_SEARCH_TITLE\n"
        "GUIDE=$(lighter_filter)\n"
        f"{CLOSE}\n"
        "echo SECTION_5_UNCHANGED\n"
    )


def _setup_customizable(files_dir, target, manifest, *, src, installed,
                        dest_rel="tool.sh", regions=("reading-guide",)):
    """Write a source file + (optional) installed dest + wire the manifest entry."""
    (files_dir / Path(dest_rel).name).write_text(src)
    if installed is not None:
        dest = target / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(installed)
    manifest["customizable"] = {dest_rel: {"keep_regions": list(regions)}}
    return target / dest_rel


# ══════════════════════════════════════════════════════════════════════════════
# Group: marker parse — _extract_regions
# ══════════════════════════════════════════════════════════════════════════════


def test_01_single_region_interior_extracted():
    """One region → {name: interior}; interior is the lines between markers only."""
    regions = _extract_regions(_src_v2())
    assert set(regions) == {"reading-guide"}
    interior = regions["reading-guide"]
    assert "DEFAULT_TITLE" in interior and "default_filter" in interior
    # marker lines themselves are NOT part of the interior
    assert "overlay-keep" not in interior
    # out-of-region content is excluded
    assert "SECTION_1_UPDATED" not in interior


def test_02_multiple_regions_parsed_order_independent():
    """Two regions both parsed regardless of order."""
    text = (
        "# overlay-keep:alpha\n"
        "AAA\n"
        "# /overlay-keep:alpha\n"
        "middle\n"
        "# overlay-keep:beta\n"
        "BBB\n"
        "# /overlay-keep:beta\n"
    )
    regions = _extract_regions(text)
    assert set(regions) == {"alpha", "beta"}
    assert "AAA" in regions["alpha"]
    assert "BBB" in regions["beta"]


def test_03_no_markers_returns_empty():
    """Text with no markers → {}."""
    assert _extract_regions("#!/bin/sh\necho hi\n") == {}


def test_04_unbalanced_open_without_close_raises():
    """Open marker with no matching close → ValueError."""
    text = "# overlay-keep:reading-guide\nSTUFF\n"
    with pytest.raises(ValueError):
        _extract_regions(text)


def test_05_duplicate_region_name_raises():
    """Same region name opened twice → ValueError (ambiguous)."""
    text = (
        "# overlay-keep:dup\nA\n# /overlay-keep:dup\n"
        "# overlay-keep:dup\nB\n# /overlay-keep:dup\n"
    )
    with pytest.raises(ValueError):
        _extract_regions(text)


# ══════════════════════════════════════════════════════════════════════════════
# Group: splice — handle_customizable
# ══════════════════════════════════════════════════════════════════════════════


def test_06_fresh_install_seeds_verbatim(tmp_path, home_isolation):
    """dest missing → dest bytes == source verbatim; mode 0o755; record COPY."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(), installed=None)

    handle_customizable(m, ov_dir, target, False, False)

    assert dest.read_text() == _src_v2()
    assert oct(dest.stat().st_mode & 0o777) == oct(0o755)
    assert "COPY" in _statuses()


def test_07_dest_identical_to_source_skips(tmp_path, home_isolation):
    """dest byte-identical to source → SKIP; dest unchanged."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(), installed=_src_v2())

    handle_customizable(m, ov_dir, target, False, False)

    assert dest.read_text() == _src_v2()
    assert "SKIP" in _statuses()


def test_08_region_customized_rest_identical_preserves(tmp_path, home_isolation):
    """Only the region differs → region interior kept == installed; outside == source."""
    # source with the SAME out-of-region content as installed (only region default differs)
    src = (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1_OLD\n"
        f"{OPEN}\n"
        "echo DEFAULT_TITLE\n"
        "GUIDE=$(default_filter)\n"
        f"{CLOSE}\n"
        "echo SECTION_5_UNCHANGED\n"
    )
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=src, installed=_installed_customized())

    handle_customizable(m, ov_dir, target, False, False)

    merged = dest.read_text()
    assert "CAREER_SEARCH_TITLE" in merged        # repo tweak preserved
    assert "DEFAULT_TITLE" not in merged          # source default not re-applied
    assert "SECTION_1_OLD" in merged and "SECTION_5_UNCHANGED" in merged


def test_09_outside_updated_inside_customized_both_apply(tmp_path, home_isolation):
    """Overlay changed OUTSIDE + repo customized INSIDE → new outside AND kept region."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(),
                               installed=_installed_customized())

    handle_customizable(m, ov_dir, target, False, False)

    merged = dest.read_text()
    assert "SECTION_1_UPDATED" in merged          # overlay out-of-region update applied
    assert "SECTION_1_OLD" not in merged
    assert "CAREER_SEARCH_TITLE" in merged        # region preserved
    assert merged.count(OPEN) == 1 and merged.count(CLOSE) == 1
    assert "UPDATE" in _statuses()


def test_10_overlay_changed_default_repo_untouched_stays_installed(tmp_path, home_isolation):
    """Overlay ships a NEW region default; installed region is repo-owned → stays installed."""
    src = _src_v2().replace("echo DEFAULT_TITLE", "echo NEW_SEED_TITLE")
    installed = _src_v2().replace("echo SECTION_1_UPDATED", "echo SECTION_1_UPDATED")  # same outside
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=src, installed=installed)

    handle_customizable(m, ov_dir, target, False, False)

    merged = dest.read_text()
    assert "DEFAULT_TITLE" in merged              # installed (old seed) region kept
    assert "NEW_SEED_TITLE" not in merged         # overlay's new default NOT pushed in


def test_11_marker_deleted_from_installed_resets_and_warns(tmp_path, home_isolation):
    """Installed file lost the region markers → reset to source default + WARN (decision 3)."""
    installed_no_markers = (
        "#!/usr/bin/env bash\n"
        "echo SECTION_1_UPDATED\n"
        "echo SOMETHING_ELSE\n"
        "echo SECTION_5_UNCHANGED\n"
    )
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(),
                               installed=installed_no_markers)

    handle_customizable(m, ov_dir, target, False, False)

    merged = dest.read_text()
    assert "DEFAULT_TITLE" in merged              # region reset to source default
    assert OPEN in merged and CLOSE in merged     # markers restored from source
    assert "WARN" in _statuses()


def test_12_region_listed_but_missing_in_source_errors(tmp_path, home_isolation):
    """Manifest lists a region whose marker is absent in source → ERROR (decision 2)."""
    src_no_region = "#!/usr/bin/env bash\necho hi\n"
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    _setup_customizable(files_dir, target, m, src=src_no_region, installed=None,
                        regions=("ghost",))

    handle_customizable(m, ov_dir, target, False, False)

    assert "ERROR" in _statuses()
    assert "ghost" in _details()


def test_13_marker_in_source_not_listed_errors(tmp_path, home_isolation):
    """Source has a marker not in keep_regions → ERROR, unsanctioned (source) (decision 1)."""
    src_extra = _src_v2() + "# overlay-keep:rogue\nX\n# /overlay-keep:rogue\n"
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    _setup_customizable(files_dir, target, m, src=src_extra, installed=None)

    handle_customizable(m, ov_dir, target, False, False)

    assert "ERROR" in _statuses()
    assert "rogue" in _details()


def test_14_marker_in_installed_not_listed_errors(tmp_path, home_isolation):
    """Installed file has a marker not in keep_regions → ERROR, unsanctioned (installed) (decision 1)."""
    installed_extra = _installed_customized() + "# overlay-keep:rogue\nX\n# /overlay-keep:rogue\n"
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    _setup_customizable(files_dir, target, m, src=_src_v2(), installed=installed_extra)

    handle_customizable(m, ov_dir, target, False, False)

    assert "ERROR" in _statuses()
    assert "rogue" in _details()


def test_15_idempotent_second_run_stable(tmp_path, home_isolation):
    """Run twice → dest byte-stable; second run records SKIP."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(),
                               installed=_installed_customized())

    handle_customizable(m, ov_dir, target, False, False)
    after_first = dest.read_bytes()
    report._actions.clear()
    handle_customizable(m, ov_dir, target, False, False)

    assert dest.read_bytes() == after_first
    assert "SKIP" in _statuses()


def test_16_crlf_preserved(tmp_path, home_isolation):
    """CRLF installed file, region customized → merged keeps CRLF; tweak preserved."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    installed_crlf = _installed_customized().replace("\n", "\r\n")
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(), installed=installed_crlf)

    handle_customizable(m, ov_dir, target, False, False)

    raw = dest.read_bytes()
    assert b"\r\n" in raw
    assert b"CAREER_SEARCH_TITLE" in raw


def test_17_dry_run_writes_nothing(tmp_path, home_isolation):
    """--dry-run on a customized file → no write; records intended UPDATE."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(),
                               installed=_installed_customized())
    before = dest.read_bytes()

    handle_customizable(m, ov_dir, target, True, False)   # dry_run=True

    assert dest.read_bytes() == before                    # untouched on disk
    assert "UPDATE" in _statuses()


def test_18_backup_created_before_write(tmp_path, home_isolation):
    """Update with do_backup=True → a .bak file created."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    dest = _setup_customizable(files_dir, target, m, src=_src_v2(),
                               installed=_installed_customized())

    handle_customizable(m, ov_dir, target, False, True)   # do_backup=True

    assert any(".bak" in p.name for p in dest.parent.iterdir())


# ══════════════════════════════════════════════════════════════════════════════
# Group: verify_overlay customizable section
# ══════════════════════════════════════════════════════════════════════════════


def test_19_verify_region_default_is_same(tmp_path, home_isolation):
    """Installed == source (region default, outside matches) → SAME, tally (0,0,0)."""
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    _setup_customizable(files_dir, target, m, src=_src_v2(), installed=_src_v2())

    tally = verify_overlay(m, ov_dir, target, "project")

    assert tally == (0, 0, 0)
    assert "SAME" in _statuses()


def test_20_verify_region_customized_is_non_gating(tmp_path, home_isolation):
    """Region customized (marker present, interior differs) → CUSTOMIZED, tally (0,0,0)."""
    # outside matches source; only the region interior differs
    installed = _src_v2().replace("echo DEFAULT_TITLE", "echo CAREER_SEARCH_TITLE")
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    _setup_customizable(files_dir, target, m, src=_src_v2(), installed=installed)

    tally = verify_overlay(m, ov_dir, target, "project")

    assert tally == (0, 0, 0)
    assert "CUSTOMIZED" in _statuses()


def test_21_verify_outside_region_drift_gates(tmp_path, home_isolation):
    """Out-of-region content drifted from source → DIFF, n_diff >= 1."""
    installed = _src_v2().replace("echo SECTION_5_UNCHANGED", "echo SECTION_5_HACKED")
    ov_dir, files_dir, m = _make_overlay(tmp_path)
    target = _make_target(tmp_path)
    _setup_customizable(files_dir, target, m, src=_src_v2(), installed=installed)

    tally = verify_overlay(m, ov_dir, target, "project")

    n_diff, _, _ = tally
    assert n_diff >= 1
    assert "DIFF" in _statuses()
