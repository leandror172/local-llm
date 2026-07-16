"""Tests for oficina.evaluator — evaluation + delta-scoped attribution (T5, P2-D8/D12/D13).

The pure `attribute` tests (the P2-D12 masking-hole guard, acceptance criterion 3 both
directions) have model-generated bodies. The anti-cheat (git diff) and `evaluate` (real
validator/pytest subprocess) tests are hand-written — subprocess/git is not delegated.
"""

import subprocess
import sys

from ollama_mcp.oficina.evaluator import (
    attribute,
    diff_touches_test_files,
    evaluate,
)
from ollama_mcp.oficina.parser import STAGE_COMPILE, STAGE_TEST, ParsedFailure

TARGET_FILES = ["area.py"]
TEST_FILES = ["test_area.py"]


def _pf(file, key, stage=STAGE_TEST):
    """A ParsedFailure whose error_key is (key, 'd'), attributed to `file`."""
    return ParsedFailure(stage, file, (key, "d"), f"raw:{key}")


# --- attribute: delta-scoping (P2-D12) — model-generated bodies -------------


def test_out_of_scope_wart_in_baseline_is_subtracted():
    """A current failure in an out-of-scope file (not target, not test) that also appears in
    the baseline is a pre-existing wart — it is NOT attributable to this iteration."""
    baseline = [_pf("other.py", "w")]
    current = [_pf("other.py", "w")]
    assert attribute(current, baseline, TARGET_FILES, TEST_FILES) == []


def test_new_out_of_scope_failure_not_in_baseline_stays():
    """An out-of-scope failure that is NOT in the baseline is new signal — it stays attributable."""
    baseline = []
    current = [_pf("other.py", "w")]
    result = attribute(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == current


def test_target_file_failure_never_subtracted():
    """A failure in the TARGET file is never subtracted even if an identical error_key is in
    the baseline — this is the masking-hole guard: a misnamed/absent target must stay live."""
    baseline = [_pf("area.py", "undef")]
    current = [_pf("area.py", "undef")]
    result = attribute(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == current


def test_test_file_failure_never_subtracted():
    """A failure attributed to a TEST file (e.g. the import ERROR a missing target causes) is
    never subtracted even if its key is in the baseline — the masking inverse (criterion 3b)."""
    baseline = [_pf("test_area.py", "importerror")]
    current = [_pf("test_area.py", "importerror")]
    result = attribute(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == current


def test_mixed_keeps_in_scope_drops_out_of_scope_wart():
    """Given both an out-of-scope wart (in baseline) and a target failure, attribute keeps only
    the target failure."""
    wart = _pf("other.py", "w")
    tgt = _pf("area.py", "u")
    baseline = [wart, tgt]
    current = [wart, tgt]
    result = attribute(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == [tgt]


# --- anti-cheat: diff must not touch test files (P2-D13) — hand-written ------


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _repo_with_commit(tmp_path):
    repo = tmp_path / "wt"
    repo.mkdir()
    _git(repo, "init")
    (repo / "area.py").write_text("def area(w, h):\n    return 0\n")
    (repo / "test_area.py").write_text("def test_area():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "c0")
    return repo


def _commit_all(repo, msg):
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "--allow-empty", "-m", msg)
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


def test_diff_touching_test_file_is_flagged(tmp_path):
    """Editing a declared test_file between commits is surfaced by diff_touches_test_files."""
    repo = _repo_with_commit(tmp_path)
    c0 = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    (repo / "test_area.py").write_text("def test_area():\n    assert False\n")
    c1 = _commit_all(repo, "tamper with tests")
    touched = diff_touches_test_files(repo, c0, c1, TEST_FILES)
    assert "test_area.py" in touched


def test_diff_touching_only_target_is_clean(tmp_path):
    """Editing only the target file leaves diff_touches_test_files empty."""
    repo = _repo_with_commit(tmp_path)
    c0 = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    (repo / "area.py").write_text("def area(w, h):\n    return w * h\n")
    c1 = _commit_all(repo, "implement area")
    assert diff_touches_test_files(repo, c0, c1, TEST_FILES) == []


# --- evaluate: real stage-ordered evaluation (P2-D8) — hand-written ---------


def test_evaluate_reports_compile_failure_on_broken_target(tmp_path):
    """A syntactically broken target yields a compile-stage failure (test stage not reached)."""
    (tmp_path / "area.py").write_text("def area(w, h)\n    return w * h\n")  # missing colon
    spec = {
        "deliverable": {"kind": "function", "target": str(tmp_path / "area.py")},
        "acceptance": {"test_cmd": "true", "test_files": ["test_area.py"]},
    }
    failures = evaluate(tmp_path, tmp_path, spec)
    assert failures and failures[0].stage == STAGE_COMPILE


def test_evaluate_clean_target_and_passing_test_yields_no_failures(tmp_path):
    """A valid target whose test passes evaluates to zero failures (both stages clean)."""
    (tmp_path / "area.py").write_text("def area(w, h):\n    return w * h\n")
    (tmp_path / "test_area.py").write_text(
        "from area import area\n\n\ndef test_area():\n    assert area(2, 3) == 6\n"
    )
    spec = {
        "deliverable": {"kind": "function", "target": str(tmp_path / "area.py")},
        "acceptance": {
            "test_cmd": f"{sys.executable} -m pytest -q",
            "test_files": ["test_area.py"],
        },
    }
    assert evaluate(tmp_path, tmp_path, spec) == []
