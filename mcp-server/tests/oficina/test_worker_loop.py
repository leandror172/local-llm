"""Tests for the worker's P2 loop routing (T7): function→loop, answer→single-shot.

The loop path uses a real git repo + real Workspace/Ledger with injected fake coder/evaluate.
"""

import subprocess

from ollama_mcp.oficina.ledger import Ledger, fold_state
from ollama_mcp.oficina.parser import STAGE_TEST, ParsedFailure
from ollama_mcp.oficina.store import Store
from ollama_mcp.oficina.worker import GenerationResult, Worker


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _repo(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    (repo / "test_area.py").write_text("def test_area():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "seed")
    return repo


def _function_spec(repo):
    return {
        "deliverable": {"kind": "function", "target": str(repo / "area.py")},
        "objective": "implement area",
        "acceptance": {"test_cmd": "true", "test_files": ["test_area.py"]},
        "budgets": {"iterations": 3, "fresh_starts": 1},
        "workspace": "worktree",
    }


def _coder(content="def area(w, h):\n    return w * h\n"):
    def _fn(prompt, model, run_id):
        return GenerationResult(content=content, model="fake", eval_count=5, duration_ms=1.0)
    return _fn


class _Evaluate:
    def __init__(self, results):
        self.results = list(results)

    def __call__(self, worktree, base_repo, spec):
        return self.results.pop(0) if self.results else []


def _fail(key):
    return ParsedFailure(STAGE_TEST, "test_area.py", (f"pytest-failed:{key}", "d"), f"b:{key}")


def _submit(store, worker, spec):
    run_id = store.create_run(spec)
    Ledger(store.events_path(run_id)).run_submitted({"queue_position": 1})
    worker.fifo.push(run_id)
    return run_id


def _events(store, run_id):
    return [e["event"] for e in Ledger(store.events_path(run_id)).read()]


def test_function_kind_routes_to_loop_and_delivers(tmp_path):
    """A function run goes through the loop (AssemblyDone + iteration events) to Delivered,
    NOT the single-shot GenerationStarted path."""
    repo = _repo(tmp_path)
    store = Store(tmp_path / "store")
    worker = Worker(
        tmp_path / "store", loop_coder=_coder(), loop_evaluate=_Evaluate([[], []])
    )
    run_id = _submit(store, worker, _function_spec(repo))
    worker.process_run(run_id)
    names = _events(store, run_id)
    assert "AssemblyDone" in names and "IterationEvaluated" in names
    assert "Delivered" in names and "GenerationStarted" not in names


def test_function_kind_exhaustion_folds_to_failed(tmp_path):
    """A function run that never passes emits Exhausted and folds to failed."""
    repo = _repo(tmp_path)
    store = Store(tmp_path / "store")
    ev = _Evaluate([[], [_fail("a")], [_fail("b")], [_fail("c")]])
    worker = Worker(tmp_path / "store", loop_coder=_coder(), loop_evaluate=ev)
    run_id = _submit(store, worker, _function_spec(repo))
    worker.process_run(run_id)
    assert "Exhausted" in _events(store, run_id)
    assert fold_state(Ledger(store.events_path(run_id)).read()) == "failed"


def test_delivered_payload_references_the_run_branch(tmp_path):
    """The loop's Delivered deliverable names the run branch + commit (the deliverable IS the branch)."""
    repo = _repo(tmp_path)
    store = Store(tmp_path / "store")
    worker = Worker(tmp_path / "store", loop_coder=_coder(), loop_evaluate=_Evaluate([[], []]))
    run_id = _submit(store, worker, _function_spec(repo))
    worker.process_run(run_id)
    delivered = next(
        e for e in Ledger(store.events_path(run_id)).read() if e["event"] == "Delivered"
    )
    assert delivered["payload"]["deliverable"]["branch"] == "oficina-run-" + run_id


def test_loop_tears_down_worktree(tmp_path):
    """After the run the worktree directory is removed (teardown), leaving the branch."""
    repo = _repo(tmp_path)
    store = Store(tmp_path / "store")
    worker = Worker(tmp_path / "store", loop_coder=_coder(), loop_evaluate=_Evaluate([[], []]))
    run_id = _submit(store, worker, _function_spec(repo))
    worker.process_run(run_id)
    assert not (store.run_dir(run_id) / "workspace" / "worktree").exists()
    branches = subprocess.run(
        ["git", "-C", str(repo), "branch", "--list", f"oficina-run-{run_id}"],
        capture_output=True,
        text=True,
    ).stdout
    assert f"oficina-run-{run_id}" in branches


def test_answer_kind_still_uses_single_shot(tmp_path):
    """A non-loop kind (answer) is unaffected: GenerationStarted→Finished→Delivered."""
    store = Store(tmp_path / "store")
    worker = Worker(
        tmp_path / "store",
        generate=lambda spec, run_id: GenerationResult("42", "fake", 3, 1.0),
    )
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.process_run(run_id)
    names = _events(store, run_id)
    assert names == ["RunSubmitted", "GenerationStarted", "GenerationFinished", "Delivered"]
