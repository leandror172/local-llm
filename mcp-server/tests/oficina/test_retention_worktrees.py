"""T-97 — retention prunes crashed-run worktrees; staleness is run-dir mtime (P2-D5).

Git-integration tests (real ``git`` subprocess against a temp repo) — bodies are
hand-written per the test_workspace.py precedent: subprocess/worktree assertions are
the multi-file-reasoning class the local-model conventions exclude from delegation.
Imperative style (structural tests vary the world, not an input sequence).

Contract under test (retention.py changes):

- The ``workspaces_ttl_days`` policy measures staleness by the RUN DIR mtime (not the
  artifacts dir), and no longer skips runs with empty artifacts — a hard-crashed loop
  run (worktree present, artifacts empty, no teardown) is exactly the state the sweep
  must see.
- For each TTL-stale run the sweep prunes the workspace: resolve the target repo from
  the run's spec.json (``deliverable.target`` -> ``git rev-parse --show-toplevel``),
  ``git worktree remove --force`` + ``git worktree prune`` there, then remove the
  run's ``workspace/`` tree. Decided: if the target repo is gone, the workspace tree
  is STILL removed and the record carries ``git_pruned=False`` (skip recorded, disk
  reclaimed).
- ``PruneRecord`` gains ``git_pruned: bool | None`` (None for artifacts records and
  dry-run workspace records); the RetentionPruned payload for workspace prunes carries
  it. ``artifacts_keep_runs`` never touches workspaces. events.jsonl stays untouchable.
"""

import os
import shutil
import subprocess

import pytest

from ollama_mcp.oficina.config import RetentionConfig
from ollama_mcp.oficina.ledger import Ledger
from ollama_mcp.oficina.retention import sweep
from ollama_mcp.oficina.store import Store

AN_OLD_EPOCH = 1_000_000_000  # 2001 — older than any TTL
TTL = RetentionConfig(workspaces_ttl_days=7, artifacts_keep_runs=100)


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _make_repo(tmp_path):
    """A real git repo with one commit (the worktree base)."""
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    (repo / "seed.py").write_text("x = 1\n")
    _git(repo, "add", "seed.py")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "seed")
    return repo


def _make_crashed_loop_run(store, repo, artifact_bytes=b""):
    """A run whose worktree exists but was never torn down (simulated hard crash)."""
    run_id = store.create_run(
        {"deliverable": {"kind": "function", "target": str(repo / "area.py")}, "objective": "x"}
    )
    if artifact_bytes:
        (store.artifacts_dir(run_id) / "out.txt").write_bytes(artifact_bytes)
    worktree = store.run_dir(run_id) / "workspace" / "worktree"
    worktree.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "-b", f"oficina/{run_id}", str(worktree), "HEAD")
    return run_id


def _age_run(store, run_id):
    os.utime(store.run_dir(run_id), (AN_OLD_EPOCH, AN_OLD_EPOCH))


def _worktree_list(repo):
    out = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("worktree ")]


@pytest.fixture
def worker_ledger(tmp_path):
    return Ledger(tmp_path / "worker-events.jsonl")


def test_stale_crashed_run_workspace_is_pruned_and_unregistered(tmp_path, worker_ledger):
    """TTL-stale crashed run: workspace tree removed, worktree deregistered, git_pruned=True."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo)
    _age_run(store, run_id)

    records = sweep(store, worker_ledger, TTL)

    assert not (store.run_dir(run_id) / "workspace").exists()
    assert _worktree_list(repo) == [str(repo)]
    workspace_records = [r for r in records if r.what == "workspace"]
    assert [(r.run_id, r.policy, r.git_pruned) for r in workspace_records] == [
        (run_id, "workspaces_ttl_days", True)
    ]
    events = worker_ledger.read()
    payloads = [e["payload"] for e in events if e["payload"].get("what") == "workspace"]
    assert payloads and payloads[0]["git_pruned"] is True


def test_target_repo_gone_still_removes_workspace_tree(tmp_path, worker_ledger):
    """Decided rule: repo deleted -> workspace tree still reclaimed, git_pruned=False."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo)
    shutil.rmtree(repo)
    _age_run(store, run_id)

    records = sweep(store, worker_ledger, TTL)

    assert not (store.run_dir(run_id) / "workspace").exists()
    workspace_records = [r for r in records if r.what == "workspace"]
    assert [(r.run_id, r.git_pruned) for r in workspace_records] == [(run_id, False)]


def test_empty_artifacts_crashed_run_is_visible_to_ttl(tmp_path, worker_ledger):
    """The old blind spot: empty artifacts must not hide a stale run from the sweep."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo, artifact_bytes=b"")
    _age_run(store, run_id)

    records = sweep(store, worker_ledger, TTL)

    assert any(r.what == "workspace" and r.run_id == run_id for r in records)


def test_staleness_is_run_dir_not_artifacts(tmp_path, worker_ledger):
    """A FRESH run dir with old artifacts is not TTL-pruned (measure moved off artifacts)."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo, artifact_bytes=b"data")
    os.utime(store.artifacts_dir(run_id), (AN_OLD_EPOCH, AN_OLD_EPOCH))  # run dir stays fresh

    records = sweep(store, worker_ledger, TTL)

    assert records == []
    assert (store.run_dir(run_id) / "workspace").exists()


def test_keep_runs_policy_never_touches_workspaces(tmp_path, worker_ledger):
    """artifacts_keep_runs prunes artifacts only; a fresh run's workspace survives."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo, artifact_bytes=b"data")

    records = sweep(store, worker_ledger, RetentionConfig(artifacts_keep_runs=0))

    assert all(r.what == "artifacts" for r in records)
    assert (store.run_dir(run_id) / "workspace" / "worktree").exists()


def test_dry_run_reports_workspace_but_touches_nothing(tmp_path, worker_ledger):
    """dry_run computes the workspace record (git_pruned=None) without git ops or rmtree."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo)
    _age_run(store, run_id)

    records = sweep(store, worker_ledger, TTL, dry_run=True)

    workspace_records = [r for r in records if r.what == "workspace"]
    assert [(r.run_id, r.git_pruned) for r in workspace_records] == [(run_id, None)]
    assert (store.run_dir(run_id) / "workspace" / "worktree").exists()
    assert len(_worktree_list(repo)) == 2
    assert worker_ledger.read() == []


def test_events_jsonl_survives_workspace_prune(tmp_path, worker_ledger):
    """The hard invariant holds through the new prune class: events.jsonl is untouchable."""
    store = Store(tmp_path / "root")
    repo = _make_repo(tmp_path)
    run_id = _make_crashed_loop_run(store, repo)
    Ledger(store.events_path(run_id)).failed({"where": "loop", "whose": "system", "what": "crash"})
    _age_run(store, run_id)

    sweep(store, worker_ledger, TTL)

    assert store.events_path(run_id).exists()
