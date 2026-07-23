"""Tests for the worker's P2 loop routing (T7): function→loop, answer→single-shot.

Executable-spec (DSL) style — `docs/patterns/test-authoring-executable-spec.md`
(`ref:test-executable-spec`). The worker's loop path is temporal (it consumes an evaluation
sequence), so the behavioral tests read `given_a_git_repo … when_the_worker_runs_the_loop(
evaluation_yields=[…]) … then_ …`, with `CLEAN`/`FAILS(...)` as the vocabulary. Two tests are
STRUCTURAL and keep bespoke setup per the taxonomy: teardown asserts filesystem state (a distinct
assertion kind — rule 3's boundary), and the answer-kind test varies the `given` (a different kind
+ the single-shot `generate` seam) to prove routing.

The loop path uses a real git repo + real Workspace/Ledger with injected fake coder/evaluate.
"""

import subprocess

from ollama_mcp.oficina.ledger import Ledger, fold_state
from ollama_mcp.oficina.parser import STAGE_TEST, ParsedFailure
from ollama_mcp.oficina.store import Store
from ollama_mcp.oficina.worker import GenerationResult, Worker


# --- low-level machinery ----------------------------------------------------


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


def _coder(content):
    def _fn(prompt, model, run_id, num_predict=None):
        return GenerationResult(content=content, model="fake", eval_count=5, duration_ms=1.0)
    return _fn


class _Evaluate:
    def __init__(self, results):
        self.results = list(results)

    def __call__(self, worktree, base_repo, spec):
        return self.results.pop(0) if self.results else []


def _submit(store, worker, spec):
    run_id = store.create_run(spec)
    Ledger(store.events_path(run_id)).run_submitted({"queue_position": 1})
    worker.fifo.push(run_id)
    return run_id


# --- vocabulary + given / when / then ---------------------------------------

GOOD_AREA = "def area(w, h):\n    return w * h\n"

CLEAN: list = []  # an evaluation that found no failures


def FAILS(*keys, file="test_area.py"):
    """An evaluation yielding one in-scope test failure per key."""
    return [ParsedFailure(STAGE_TEST, file, (f"pytest-failed:{k}", "d"), f"b:{k}") for k in keys]


class _WorkerRun:
    """A git repo + store the worker processes a function run against, plus the run_id after."""

    def __init__(self, tmp_path, repo, store):
        self.tmp_path, self.repo, self.store = tmp_path, repo, store
        self.run_id = None


def given_a_git_repo(tmp_path):
    """A committed git repo (test file present, target absent) + a fresh oficina store."""
    return _WorkerRun(tmp_path, _repo(tmp_path), Store(tmp_path / "store"))


def when_the_worker_runs_the_loop(on, *, evaluation_yields, coder_writes=GOOD_AREA):
    """Submit a function run and let the worker route it through the loop. `evaluation_yields`
    are the per-iteration evaluations (the C0 baseline, CLEAN, is prepended automatically)."""
    worker = Worker(
        on.tmp_path / "store",
        loop_coder=_coder(coder_writes),
        loop_evaluate=_Evaluate([CLEAN, *evaluation_yields]),
    )
    on.run_id = _submit(on.store, worker, _function_spec(on.repo))
    worker.process_run(on.run_id)


def _events(on):
    return Ledger(on.store.events_path(on.run_id)).read()


def _event_names(on):
    return [e["event"] for e in _events(on)]


def then_it_ran_the_loop_to_delivered(on):
    names = _event_names(on)
    assert "AssemblyDone" in names and "IterationEvaluated" in names
    assert "Delivered" in names and "GenerationStarted" not in names  # loop, not single-shot


def then_it_exhausted_and_folded_to_failed(on):
    assert "Exhausted" in _event_names(on)
    assert fold_state(_events(on)) == "failed"


def then_the_delivered_deliverable_names_the_run_branch(on):
    delivered = next(e for e in _events(on) if e["event"] == "Delivered")
    assert delivered["payload"]["deliverable"]["branch"] == f"oficina-run-{on.run_id}"


def then_the_worktree_was_torn_down_leaving_the_branch(on):
    # Structural/filesystem assertion — rule 3's boundary: teardown removes the worktree dir
    # but keeps the run branch (the deliverable).
    assert not (on.store.run_dir(on.run_id) / "workspace" / "worktree").exists()
    branches = subprocess.run(
        ["git", "-C", str(on.repo), "branch", "--list", f"oficina-run-{on.run_id}"],
        capture_output=True,
        text=True,
    ).stdout
    assert f"oficina-run-{on.run_id}" in branches


# --- behavioral family (vary the evaluation sequence) -----------------------


def test_function_kind_routes_to_loop_and_delivers(tmp_path):
    """A function run goes through the loop (AssemblyDone + iteration events) to Delivered,
    NOT the single-shot GenerationStarted path."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(run, evaluation_yields=[CLEAN])
    then_it_ran_the_loop_to_delivered(run)


def test_function_kind_exhaustion_folds_to_failed(tmp_path):
    """A function run that never passes emits Exhausted and folds to failed."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(run, evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")])
    then_it_exhausted_and_folded_to_failed(run)


def test_delivered_payload_references_the_run_branch(tmp_path):
    """The loop's Delivered deliverable names the run branch + commit (the deliverable IS the branch)."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(run, evaluation_yields=[CLEAN])
    then_the_delivered_deliverable_names_the_run_branch(run)


# --- structural tests (keep bespoke setup) ----------------------------------


def test_loop_tears_down_worktree(tmp_path):
    """After the run the worktree directory is removed (teardown), leaving the branch."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(run, evaluation_yields=[CLEAN])
    then_the_worktree_was_torn_down_leaving_the_branch(run)


def test_evaluation_error_attribution_reaches_failed_event(tmp_path):
    """An EvaluationError escaping the loop keeps its own where/whose on the Failed event
    (shared TriadError base) — the worker must not rewrite it to the generic where='loop'."""
    from ollama_mcp.oficina.evaluator import EvaluationError

    store = Store(tmp_path / "store")

    def _raising_evaluate(worktree, base_repo, spec):
        raise EvaluationError("test", "test command produced no parseable result")

    worker = Worker(
        tmp_path / "store",
        loop_coder=_coder(GOOD_AREA),
        loop_evaluate=_raising_evaluate,
    )
    run_id = _submit(store, worker, _function_spec(_repo(tmp_path)))
    worker.process_run(run_id)

    failed = next(e for e in Ledger(store.events_path(run_id)).read() if e["event"] == "Failed")
    assert failed["payload"]["where"] == "test"  # the stage's own attribution, not "loop"
    assert failed["payload"]["whose"] == "system"


def test_answer_kind_still_uses_single_shot(tmp_path):
    """A non-loop kind (answer) is unaffected: it varies the given (answer kind) and the injected
    seam (single-shot generate), and produces GenerationStarted→Finished→Delivered."""
    store = Store(tmp_path / "store")
    worker = Worker(
        tmp_path / "store",
        generate=lambda spec, run_id: GenerationResult("42", "fake", 3, 1.0),
    )
    run_id = _submit(store, worker, {"deliverable": {"kind": "answer"}, "objective": "q"})
    worker.process_run(run_id)
    names = [e["event"] for e in Ledger(store.events_path(run_id)).read()]
    assert names == ["RunSubmitted", "GenerationStarted", "GenerationFinished", "Delivered"]
