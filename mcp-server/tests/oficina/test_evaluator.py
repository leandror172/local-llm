"""Tests for oficina.evaluator — evaluation + delta-scoped attribution (T5, P2-D8/D12/D13).

The pure `attributable_failures` tests (the P2-D12 masking-hole guard, acceptance criterion 3 both
directions) have model-generated bodies. The anti-cheat (git diff) and `evaluate` (real
validator/pytest subprocess) tests are hand-written — subprocess/git is not delegated.

Not converted to the executable-spec DSL (`ref:test-executable-spec`): mixed file — the pure
`attributable_failures()` family is convertible, but the `evaluate`/anti-cheat half asserts on real
subprocess/git outcomes (a distinct assertion kind, rule 3), so a partial conversion would split
the file for little gain. Revisit if the `attributable_failures()` family grows.
"""

import subprocess
import sys

import pytest

from ollama_mcp.oficina.evaluator import (
    EvaluationError,
    attributable_failures,
    diff_touches_test_files,
    evaluate,
)
from ollama_mcp.oficina.parser import STAGE_COMPILE, STAGE_TEST, ParsedFailure

TARGET_FILES = ["area.py"]
TEST_FILES = ["test_area.py"]


def _pf(file, key, stage=STAGE_TEST):
    """A ParsedFailure whose error_key is (key, 'd'), attributed to `file`."""
    return ParsedFailure(stage, file, (key, "d"), f"raw:{key}")


# --- attributable_failures: delta-scoping (P2-D12) — model-generated bodies -------------


def test_out_of_scope_wart_in_baseline_is_subtracted():
    """A current failure in an out-of-scope file (not target, not test) that also appears in
    the baseline is a pre-existing wart — it is NOT attributable to this iteration."""
    baseline = [_pf("other.py", "w")]
    current = [_pf("other.py", "w")]
    assert attributable_failures(current, baseline, TARGET_FILES, TEST_FILES) == []


def test_new_out_of_scope_failure_not_in_baseline_stays():
    """An out-of-scope failure that is NOT in the baseline is new signal — it stays attributable."""
    baseline = []
    current = [_pf("other.py", "w")]
    result = attributable_failures(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == current


def test_target_file_failure_never_subtracted():
    """A failure in the TARGET file is never subtracted even if an identical error_key is in
    the baseline — this is the masking-hole guard: a misnamed/absent target must stay live."""
    baseline = [_pf("area.py", "undef")]
    current = [_pf("area.py", "undef")]
    result = attributable_failures(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == current


def test_test_file_failure_never_subtracted():
    """A failure attributed to a TEST file (e.g. the import ERROR a missing target causes) is
    never subtracted even if its key is in the baseline — the masking inverse (criterion 3b)."""
    baseline = [_pf("test_area.py", "importerror")]
    current = [_pf("test_area.py", "importerror")]
    result = attributable_failures(current, baseline, TARGET_FILES, TEST_FILES)
    assert result == current


def test_mixed_keeps_in_scope_drops_out_of_scope_wart():
    """Given both an out-of-scope wart (in baseline) and a target failure, attributable_failures keeps only
    the target failure."""
    wart = _pf("other.py", "w")
    tgt = _pf("area.py", "u")
    baseline = [wart, tgt]
    current = [wart, tgt]
    result = attributable_failures(current, baseline, TARGET_FILES, TEST_FILES)
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


def test_diff_basename_collision_is_not_flagged(tmp_path):
    """T-98 regression: a changed file sharing a declared test file's basename
    (src/test_area.py vs declared test_area.py) is NOT a cheat — basename matching
    fired anti-cheat on the target's own writes, so evaluation never ran."""
    repo = _repo_with_commit(tmp_path)
    c0 = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    (repo / "src").mkdir()
    (repo / "src" / "test_area.py").write_text("x = 1\n")
    c1 = _commit_all(repo, "target shares the declared test file's basename")
    assert diff_touches_test_files(repo, c0, c1, TEST_FILES) == []


def test_scope_collision_wart_is_subtracted_not_attributed():
    """T-98 regression (review scenario): a pre-existing wart in lib/util.py with target
    src/util.py is out-of-scope and baseline-subtracted — the loop can still pass."""
    wart = _pf("lib/util.py", "wart-key", stage=STAGE_COMPILE)
    assert attributable_failures([wart], [wart], ["src/util.py"], TEST_FILES) == []


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


def test_evaluate_raises_when_test_command_cannot_run(tmp_path):
    """A test_cmd that exits non-zero with no parseable summary (here: a missing binary) RAISES
    rather than returning [] — otherwise 'tests never ran' would read as 'passed' (false Delivered)."""
    (tmp_path / "area.py").write_text("def area(w, h):\n    return w * h\n")
    spec = {
        "deliverable": {"kind": "function", "target": str(tmp_path / "area.py")},
        "acceptance": {"test_cmd": "this-binary-does-not-exist-xyz", "test_files": []},
    }
    with pytest.raises(EvaluationError):
        evaluate(tmp_path, tmp_path, spec)


def test_evaluate_times_out_a_hanging_test_command(tmp_path):
    """A hanging test_cmd is bounded by budgets.wall_clock_s and raises rather than blocking the
    worker forever (the infinite-loop-in-generated-code hazard)."""
    (tmp_path / "area.py").write_text("def area(w, h):\n    return w * h\n")
    spec = {
        "deliverable": {"kind": "function", "target": str(tmp_path / "area.py")},
        "acceptance": {"test_cmd": "sleep 30", "test_files": []},
        "budgets": {"wall_clock_s": 1},
    }
    with pytest.raises(EvaluationError):
        evaluate(tmp_path, tmp_path, spec)


# --- edit mode (T-110, E-D2/E-D7): compile runs iff the target is present at C0 ----


def test_evaluate_skips_compile_when_target_absent_at_c0(tmp_path):
    """The evaluator skips the compile stage when the target file is absent at C0 (greenfield).

    Edit-mode C0 differs: the committed target is present, so compile runs on its current content
    (covered by the broken-target/clean-target tests). Here the target is absent, so evaluation
    goes straight to the test stage — which surfaces the import failure of the not-yet-written
    module. Every failure is test-stage, proving compile ran only because a target was present."""
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
    failures = evaluate(tmp_path, tmp_path, spec)
    assert failures
    assert all(failure.stage == STAGE_TEST for failure in failures)


def test_omitted_sibling_function_is_attributable(tmp_path):
    """T6 omission simulation (acceptance criterion 6): an edit iteration that rewrites the
    target but DROPS a sibling function produces that sibling's failure as an ATTRIBUTABLE
    regression — test outcomes are always in scope for delta-scoping, so the loop can never
    deliver an omission whose victim is covered by the declared tests (E-D6's behavioral net)."""
    (tmp_path / "geometry.py").write_text(
        "def area(w, h):\n    return w + h\n\n\ndef perimeter(w, h):\n    return 2 * (w + h)\n"
    )
    (tmp_path / "test_geometry.py").write_text(
        "from geometry import area, perimeter\n\n\n"
        "def test_area():\n    assert area(2, 3) == 6\n\n\n"
        "def test_perimeter():\n    assert perimeter(2, 3) == 10\n"
    )
    spec = {
        "deliverable": {"kind": "function", "target": str(tmp_path / "geometry.py")},
        "acceptance": {
            "test_cmd": f"{sys.executable} -m pytest -q",
            "test_files": ["test_geometry.py"],
        },
    }
    baseline = evaluate(tmp_path, tmp_path, spec)  # edit-mode C0: area fails, perimeter passes
    (tmp_path / "geometry.py").write_text("def area(w, h):\n    return w * h\n")  # fix + omission
    current = evaluate(tmp_path, tmp_path, spec)
    attributable = attributable_failures(
        current, baseline, ["geometry.py"], ["test_geometry.py"]
    )
    assert attributable, "the dropped sibling's failure must stay live"
    # The pytest -q short summary for a collection error is just "ERROR <file>" (the ImportError
    # naming the dropped symbol prints ABOVE the summary block) — so the pin is on scope+class,
    # not on the sibling's name. Product note: omission-by-import-breakage yields thin repair
    # feedback; recorded in the T-110 plan notes.
    failure = attributable[0]
    assert failure.file == "test_geometry.py"
    assert failure.error_key[0].startswith("pytest-error")


# --- Go twins (T-92 Phase 3): evaluate() dispatches by the resolved language --
# Real `go build` / `go test -json` subprocesses, mirroring the Python
# integration tests above. Fixture programs local-model-generated
# (call 8b750b184149); tests hand-written per this file's convention.

GO_MOD = "module example.com/probe\n\ngo 1.23\n"
GO_AREA_BROKEN = "package probe\n\nfunc Area(w, h int) int {\n\treturn mathutil.Volume(w, h)\n}\n"
GO_AREA = "package probe\n\nfunc Area(w, h int) int {\n\treturn w * h\n}\n"
GO_TEST_PASSING = (
    "package probe\n\nimport (\n\t\"testing\"\n)\n\n"
    "func TestArea(t *testing.T) {\n\tif got := Area(2, 3); got != 6 {\n"
    "\t\tt.Errorf(\"Area(2,3) = %d, want 6\", got)\n\t}\n}\n"
)
GO_TEST_FAILING = (
    "package probe\n\nimport (\n\t\"testing\"\n)\n\n"
    "func TestArea(t *testing.T) {\n\tif got := Area(2, 3); got != 7 {\n"
    "\t\tt.Errorf(\"Area(2,3) = %d, want 7\", got)\n\t}\n}\n"
)


def _go_project(tmp_path, area_src, test_src):
    (tmp_path / "go.mod").write_text(GO_MOD)
    (tmp_path / "area.go").write_text(area_src)
    (tmp_path / "area_test.go").write_text(test_src)


def _go_spec(tmp_path, test_cmd="go test -json ./..."):
    return {
        "deliverable": {"kind": "function", "target": str(tmp_path / "area.go")},
        "acceptance": {"test_cmd": test_cmd, "test_files": ["area_test.go"]},
    }


def test_evaluate_go_reports_compile_failure_on_broken_target(tmp_path):
    """A Go target with an undefined reference fails the COMPILE stage — run as
    `go build ./...` in the worktree (R3), keyed `go-…` — and the test stage is
    not reached (P2-D8 first-failing-stage)."""
    _go_project(tmp_path, GO_AREA_BROKEN, GO_TEST_PASSING)
    failures = evaluate(tmp_path, tmp_path, _go_spec(tmp_path))
    assert failures and failures[0].stage == STAGE_COMPILE
    assert failures[0].error_key[0].startswith("go-")


def test_evaluate_go_clean_project_yields_no_failures(tmp_path):
    """A compiling Go target whose test passes evaluates to zero failures."""
    _go_project(tmp_path, GO_AREA, GO_TEST_PASSING)
    assert evaluate(tmp_path, tmp_path, _go_spec(tmp_path)) == []


def test_evaluate_go_test_failure_attributes_worktree_relative_file(tmp_path):
    """A failing Go test yields a test-stage failure whose .file resolves
    worktree-relative through the -json Package field (R4): 'area_test.go' at
    the module root, keyed go-test-failed:…"""
    _go_project(tmp_path, GO_AREA, GO_TEST_FAILING)
    failures = evaluate(tmp_path, tmp_path, _go_spec(tmp_path))
    assert failures and failures[0].stage == STAGE_TEST
    assert failures[0].file == "area_test.go"
    assert failures[0].error_key[0].startswith("go-test-failed:")


def test_evaluate_go_imposes_json_on_plain_test_cmd(tmp_path):
    """A2: the Go test stage OWNS the command. A caller test_cmd WITHOUT -json still
    yields structurally attributed failures — the stage imposes `go test -json ./...`,
    because honoring a plain `go test` would silently lose Package-field attribution
    (the P2-D12 masking hole reintroduced as a caller default)."""
    _go_project(tmp_path, GO_AREA, GO_TEST_FAILING)
    failures = evaluate(tmp_path, tmp_path, _go_spec(tmp_path, test_cmd="go test ./..."))
    assert failures and failures[0].file == "area_test.go"
