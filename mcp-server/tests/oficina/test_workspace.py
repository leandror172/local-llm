"""Tests for oficina.workspace — the per-run git-worktree lifecycle (T4, P2-D5/D13).

These are git-integration tests (real ``git`` subprocess against a temp repo), so the
bodies are hand-written rather than model-generated — subprocess/worktree assertions are
the "multi-file reasoning" class the local-model conventions exclude from delegation.
"""

import subprocess

import pytest

from ollama_mcp.oficina.parser import STAGE_COMPILE, ParsedFailure
from ollama_mcp.oficina.workspace import AssemblyError, Workspace


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _make_repo(tmp_path):
    """A real git repo with one committed test file under tests/."""
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_area.py").write_text(
        "def test_area():\n    from area import area\n    assert area(2, 3) == 6\n"
    )
    _git(repo, "add", "tests/test_area.py")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "seed tests")
    return repo


def _spec(repo):
    return {
        "deliverable": {"kind": "function", "target": str(repo / "area.py")},
        "objective": "implement area(w, h)",
        "acceptance": {"test_cmd": "pytest -q", "test_files": ["tests/test_area.py"]},
        "workspace": "worktree",
    }


def _no_failures(_worktree, _base_repo, _spec):
    return []


def _one_failure(_worktree, _base_repo, _spec):
    return [ParsedFailure(STAGE_COMPILE, "area.py", ("py-x", "y"), "boom")]


def _workspace(tmp_path, repo, evaluate=_no_failures):
    return Workspace(_spec(repo), "rid1", tmp_path / "run", evaluate)


# --- assembling -------------------------------------------------------------


def test_assemble_creates_worktree(tmp_path):
    """After assemble, the worktree path exists and is a git worktree."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    assembly = ws.assemble()
    assert assembly.worktree_path.is_dir()
    listing = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list"], capture_output=True, text=True
    ).stdout
    assert str(assembly.worktree_path) in listing


def test_assemble_commits_c0_baseline(tmp_path):
    """C0 is a real commit on the run branch; the worktree HEAD equals c0_sha."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    assembly = ws.assemble()
    head = subprocess.run(
        ["git", "-C", str(assembly.worktree_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert assembly.c0_sha == head and len(head) == 40


def test_assemble_verifies_declared_test_files(tmp_path):
    """The committed test file is reported as materialized."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    assembly = ws.assemble()
    assert "tests/test_area.py" in assembly.test_files_materialized


def test_assemble_missing_test_file_raises_with_triad(tmp_path):
    """A declared test_file absent from the worktree is an AssemblyError with a triad."""
    repo = _make_repo(tmp_path)
    spec = _spec(repo)
    spec["acceptance"]["test_files"] = ["tests/test_missing.py"]
    ws = Workspace(spec, "rid1", tmp_path / "run", _no_failures)
    with pytest.raises(AssemblyError) as excinfo:
        ws.assemble()
    assert set(excinfo.value.triad) == {"where", "whose", "what"}


def test_assemble_returns_baseline_failures_from_evaluate(tmp_path):
    """The injected evaluate's result becomes the assembly's baseline failures."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo, evaluate=_one_failure)
    assembly = ws.assemble()
    assert len(assembly.baseline_failures) == 1


def test_assemble_emits_assembly_done_with_baseline_count(tmp_path):
    """assemble(emit=...) calls emit once with a payload carrying baseline_failure_count."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo, evaluate=_one_failure)
    captured = []
    ws.assemble(emit=captured.append)
    assert len(captured) == 1
    assert captured[0]["baseline_failure_count"] == 1
    assert "worktree_path" in captured[0] and "base_commit" in captured[0]


def test_stable_parts_include_objective_and_tests(tmp_path):
    """The stable prompt parts carry the objective and the on-disk test content."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    assembly = ws.assemble()
    assert assembly.stable_parts["objective"] == "implement area(w, h)"
    assert "def test_area" in assembly.stable_parts["tests"]


# --- per-iteration snapshot -------------------------------------------------


def test_snapshot_creates_a_new_commit(tmp_path):
    """snapshot commits current state and returns a sha distinct from C0."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    assembly = ws.assemble()
    (assembly.worktree_path / "area.py").write_text("def area(w, h):\n    return w * h\n")
    snap = ws.snapshot("iteration 1")
    assert snap != assembly.c0_sha and len(snap) == 40


# --- teardown ---------------------------------------------------------------


def test_teardown_removes_worktree_without_dangling(tmp_path):
    """After teardown the worktree dir is gone and no entry lingers in the registry."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    assembly = ws.assemble()
    ws.teardown()
    assert not assembly.worktree_path.exists()
    listing = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list"], capture_output=True, text=True
    ).stdout
    assert str(assembly.worktree_path) not in listing


def test_teardown_is_idempotent(tmp_path):
    """Calling teardown twice does not raise."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    ws.assemble()
    ws.teardown()
    ws.teardown()


def test_run_branch_survives_teardown(tmp_path):
    """The run branch is the deliverable — teardown removes the worktree but keeps the branch."""
    repo = _make_repo(tmp_path)
    ws = _workspace(tmp_path, repo)
    ws.assemble()
    ws.teardown()
    branches = subprocess.run(
        ["git", "-C", str(repo), "branch", "--list", "oficina-run-rid1"],
        capture_output=True,
        text=True,
    ).stdout
    assert "oficina-run-rid1" in branches
