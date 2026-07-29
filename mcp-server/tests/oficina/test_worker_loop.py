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
from ollama_mcp.oficina.report import (
    _MAX_REASONING_CHARS,
    _MAX_REPORTED_HUNKS,
    _compact_drift,
    _compact_judge,
)
from ollama_mcp.oficina.transport import GenerationResult
from ollama_mcp.oficina.worker import Worker


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


A_RUBRIC_YAML = "id: tiny\ncriteria:\n  - name: scope\n    phase: 2\n    description: only what was asked\n    scoring:\n      5: yes\n      1: no\n"


def when_the_worker_runs_the_loop(
    on, *, evaluation_yields, coder_writes=GOOD_AREA,
    judging_with=None, judge_says=None, monkeypatch=None,
):
    """Submit a function run and let the worker route it through the loop. `evaluation_yields`
    are the per-iteration evaluations (the C0 baseline, CLEAN, is prepended automatically).
    `judging_with` names a rubric written into a temp rubrics dir — omitted means no judge,
    which is how every pre-P4 run behaves."""
    spec = _function_spec(on.repo)
    if judging_with:
        rubrics = on.tmp_path / "rubrics"
        rubrics.mkdir(exist_ok=True)
        (rubrics / f"{judging_with}.yaml").write_text(A_RUBRIC_YAML, encoding="utf-8")
        monkeypatch.setenv("OFICINA_RUBRICS", str(rubrics))
        spec["acceptance"]["rubric"] = judging_with
    worker = Worker(
        on.tmp_path / "store",
        loop_coder=_coder(coder_writes),
        loop_evaluate=_Evaluate([CLEAN, *evaluation_yields]),
        loop_judge=(lambda **kw: judge_says) if judge_says else None,
    )
    on.run_id = _submit(on.store, worker, spec)
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


A_PASSING_VERDICT = '{"score": 5, "reasoning": "only the requested change"}'
A_FAILING_VERDICT = '{"score": 1, "reasoning": "unrequested content added"}'


def then_the_delivered_deliverable_names_the_run_branch(on):
    delivered = next(e for e in _events(on) if e["event"] == "Delivered")
    assert delivered["payload"]["deliverable"]["branch"] == f"oficina-run-{on.run_id}"


def then_it_judged_the_deliverable_without_blocking_delivery(on, *, passed):
    """P4-T5: Judged is emitted at packaging and Delivered still happens — S17 gates DPO
    chosen labels, not delivery."""
    names = _event_names(on)
    assert "Judged" in names and "Delivered" in names
    judged = next(e for e in _events(on) if e["event"] == "Judged")
    assert judged["payload"]["passed"] is passed
    assert fold_state(_events(on)) == "completed"  # Judged does not fold


def then_the_delivered_report_carries_drift_and_the_judge(on):
    """The report is Delivered-payload-resident (P4-D6), so both ride there or nowhere."""
    report = next(e for e in _events(on) if e["event"] == "Delivered")["payload"]["report"]
    assert set(report["drift"]) == {
        "hunks", "lines_added", "lines_removed", "max_verbatim_run_vs_tests"
    }
    assert report["judge"]["rubric"] == "tiny"


def then_the_report_narrates_every_iteration(on, *, verdicts):
    """P4-T6: the auto-verdict trail. `auto_verdict` is tests-green and binary — it cannot
    express 1 (improved) — so the report must never present it as a quality judgment."""
    trail = next(e for e in _events(on) if e["event"] == "Delivered")["payload"]["report"]["iterations_trail"]
    assert [step["tests_passed"] for step in trail] == verdicts
    assert [step["iteration"] for step in trail] == list(range(1, len(verdicts) + 1))
    assert all("error_keys" not in step for step in trail)  # compact by construction (P4-D6)


def then_no_judgement_was_recorded(on):
    """A run without a rubric is delivered exactly as it was before P4."""
    assert "Judged" not in _event_names(on)
    assert "judge" not in next(
        e for e in _events(on) if e["event"] == "Delivered"
    )["payload"]["report"]


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


def test_a_rubric_bearing_run_is_judged_at_packaging(tmp_path, monkeypatch):
    """The judge runs once at packaging and its verdict rides the Delivered report."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(
        run, evaluation_yields=[CLEAN], judging_with="tiny",
        judge_says=A_PASSING_VERDICT, monkeypatch=monkeypatch,
    )
    then_it_judged_the_deliverable_without_blocking_delivery(run, passed=True)
    then_the_delivered_report_carries_drift_and_the_judge(run)


def test_a_failing_judge_still_delivers(tmp_path, monkeypatch):
    """S17 gates DPO chosen labels, not delivery — H1 is Claude-gated, so a low score is
    information, not a veto."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(
        run, evaluation_yields=[CLEAN], judging_with="tiny",
        judge_says=A_FAILING_VERDICT, monkeypatch=monkeypatch,
    )
    then_it_judged_the_deliverable_without_blocking_delivery(run, passed=False)


def test_the_report_narrates_a_multi_iteration_run(tmp_path):
    """A run that failed once then passed leaves a two-step trail — the narrative a reviewer
    needs to see how the deliverable was reached, not just that it was."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(run, evaluation_yields=[FAILS("a"), CLEAN])
    then_the_report_narrates_every_iteration(run, verdicts=[False, True])


def test_a_run_without_a_rubric_is_not_judged(tmp_path):
    """The gate is opt-in: P4 must not silently start judging every existing spec."""
    run = given_a_git_repo(tmp_path)
    when_the_worker_runs_the_loop(run, evaluation_yields=[CLEAN])
    then_no_judgement_was_recorded(run)


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


# --- report compaction ------------------------------------------------------
# Pure functions (payload in → trimmed payload out), so these stay imperative rather than
# borrowing the DSL above: no sequence to narrate (`ref:test-executable-spec` rules 5 and 6).


def test_a_rambling_judge_reasoning_is_clipped_in_the_report():
    """The report rides in the Delivered payload and is paid for in the caller's context on
    EVERY `run_result` (P4-D6), so compactness is a constraint rather than a preference. The
    system prompt asks the judge for one concise sentence — but nothing makes a model obey a
    prompt, so the bound is enforced here instead of hoped for. The FULL text still survives in
    the `Judged` event, which nobody pays for unless they go looking."""
    verdict = {"passed": True, "criteria": [
        {"name": "scope_adherence", "score": 5, "passing_score": 4, "reasoning": "x" * 400},
    ]}

    compact = _compact_judge(verdict)

    assert len(compact["criteria"][0]["reasoning"]) <= _MAX_REASONING_CHARS
    assert verdict["criteria"][0]["reasoning"] == "x" * 400  # the original is left alone


def test_compaction_keeps_the_cut_that_explains_the_verdict():
    """`criteria[]` is not free-form report prose: each entry carries the `passing_score` its
    score was judged against (P4-D9). Entries may be SHORTENED, never dropped or reshaped — a
    report that loses them states a verdict it cannot explain."""
    verdict = {"passed": False, "criteria": [
        {"name": "scope_adherence", "score": 2, "passing_score": 4, "reasoning": "short"},
        {"name": "objective_met", "score": 5, "passing_score": 4, "reasoning": "short"},
    ]}

    compact = _compact_judge(verdict)

    assert [c["name"] for c in compact["criteria"]] == ["scope_adherence", "objective_met"]
    assert compact["criteria"][0]["passing_score"] == 4
    assert compact["criteria"][0]["score"] == 2


def test_a_scattered_diff_reports_bounded_hunks_and_says_how_many_there_were():
    """A plausible scattered rename on the 580-line loop.py measures ~60 ranges, and a
    2000-line target scales linearly. Truncating silently would read as "that was all of
    them", so the total rides along."""
    drift = {"hunks": [[i, i] for i in range(1, 61)], "lines_added": 60, "lines_removed": 60}

    compact = _compact_drift(drift)

    assert len(compact["hunks"]) == _MAX_REPORTED_HUNKS
    assert compact["hunks_total"] == 60


def test_an_untruncated_hunk_list_carries_no_total():
    """The negative control, and the reason `hunks_total` is conditional: present means "there
    were more", absent means "this is all of them". Emitted unconditionally it would carry no
    bits — first principle 6, the rule that dropped `files_touched` at build time."""
    drift = {"hunks": [[1, 2], [9, 9]], "lines_added": 3, "lines_removed": 1}

    assert _compact_drift(drift) == drift
