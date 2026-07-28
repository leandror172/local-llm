"""Tests for oficina.loop — the evaluated coder⇄evaluator loop (T6, P2-D1/D2/D4/D7/D10).

Written in the executable-spec (DSL) style — `docs/patterns/test-authoring-executable-spec.md`
(`ref:test-executable-spec`). Each test body is `given_ … when_ … then_ …`: the scenario and the
expected behavior in English, with named constants/combinators (`CLEAN`, `FAILS(...)`, the content
constants) as the vocabulary. Real Workspace + Ledger against a temp git repo; the coder and
evaluate are fakes (no GPU).

The `when_` verb hides one fixture convention: `FakeEvaluate`'s FIRST result is consumed by
`workspace.assemble()` as the C0 baseline, the rest per-iteration — so `when_` takes only the
per-iteration evaluations and prepends the baseline (overridable via `with_baseline=` for the
delta-scope family). Behavioral tests vary `when_`; the two structural tests (anti-cheat, refs)
keep a bespoke `given_`.
"""

import math
import subprocess

from ollama_mcp.oficina.ledger import Ledger, fold_state
from ollama_mcp.oficina.loop import (
    EDIT_NUM_PREDICT_CAP,
    NUM_PREDICT,
    EvaluatedLoop,
    _CONSTRAINTS,
    _EDIT_CONSTRAINTS,
)
from ollama_mcp.oficina.errors import ContextBudgetError
from ollama_mcp.oficina.parser import STAGE_TEST, ParsedFailure
from ollama_mcp.oficina.workspace import Workspace
from ollama_mcp.oficina.worker import GenerationResult


# --- low-level fakes + git fixture (the machinery the vocabulary sits on) ----


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _repo(tmp_path):
    """A git repo carrying only the committed test file (target absent at C0)."""
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    (repo / "test_area.py").write_text("def test_area():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "seed")
    return repo


def _spec(repo, iterations=3, fresh_starts=1):
    # iterations=None omits the key so the loop resolves the mode default (edit 1, greenfield 3, T-114).
    budgets = {"fresh_starts": fresh_starts}
    if iterations is not None:
        budgets["iterations"] = iterations
    return {
        "deliverable": {"kind": "function", "target": str(repo / "area.py")},
        "objective": "implement area(w, h) returning w*h",
        "acceptance": {"test_cmd": "true", "test_files": ["test_area.py"]},
        "budgets": budgets,
        "workspace": "worktree",
    }


class FakeCoder:
    """Records each prompt and the per-call num_predict; returns the next canned content."""

    def __init__(self, contents):
        self.contents = list(contents)
        self.prompts = []
        self.num_predicts = []
        self.models = []

    def __call__(self, prompt, model, run_id, num_predict=None):
        self.prompts.append(prompt)
        self.num_predicts.append(num_predict)
        self.models.append(model)
        content = self.contents.pop(0) if self.contents else "def area(w, h):\n    return w * h\n"
        # A real chat call mints a fresh call_id per call (P4-T3); the fake mirrors that
        # so a test can tell WHICH call an iteration's ledger event names.
        return GenerationResult(
            content=content, model=model, eval_count=10, duration_ms=1.0,
            call_id=f"call{len(self.prompts)}",
        )


class FakeEvaluate:
    """First call = C0 baseline (from assemble); subsequent = per iteration."""

    def __init__(self, results):
        self.results = list(results)

    def __call__(self, worktree, base_repo, spec):
        return self.results.pop(0) if self.results else []


def _events(ledger, name):
    return [e for e in ledger.read() if e["event"] == name]


def _emitted(ledger, name):
    return any(e["event"] == name for e in ledger.read())


# --- vocabulary: named constants + combinators (the DSL nouns) --------------

GOOD_AREA = "def area(w, h):\n    return w * h\n"
A_TAMPERED_TEST = "def test_area():\n    assert True  # tampered\n"
A_STATE_DIAGRAM = "<refs>\nSTATE DIAGRAM: queued -> working -> completed\n</refs>"

CLEAN: list = []  # an evaluation that found no failures
EVALUATION_NEVER_REACHED: list = []  # per-iteration evals the cheat short-circuits before consuming


# Context windows (T-112). Sized so no test depends on the exact token count of a built
# prompt: the generous window is far above anything these fixtures produce, the tiny one
# is below anything at all, and the middle one sits between a normal prompt and one that
# has swallowed A_HUGE_ATTEMPT as its previous-attempt tail.
A_GENEROUS_WINDOW = 100_000
A_WINDOW_TOO_SMALL_FOR_ANY_PROMPT = 10
A_WINDOW_THAT_FITS_ONLY_THE_FIRST_PROMPT = 5_000
AN_UNDETERMINABLE_WINDOW = None  # /api/show could not tell us — the guard cannot run

A_HUGE_ATTEMPT = "x" * 40_000  # ~10K tokens; fed back as previous_attempt it grows iteration 2


def FAILS(*keys, file="test_area.py"):
    """An evaluation yielding one in-scope test failure per key (realistic pytest-failed key)."""
    return [ParsedFailure(STAGE_TEST, file, (f"pytest-failed:{k}", "d"), f"boom:{k}") for k in keys]


# --- the staged run + given / when / then (the DSL verbs) -------------------


class _Run:
    """A staged function run: where it lives, plus the coder/ledger/result once it has executed."""

    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.repo = _repo(tmp_path)
        self.target = self.repo / "area.py"  # absent at C0 (the normal case)
        self.coder = None
        self.ledger = None
        self.result = None
        self.worktree = None  # the assembled worktree path, set by when_ (for on-disk assertions)
        self.refusal = None  # a ContextBudgetError captured by when_the_coder_is_refused (T-112)


def given_a_function_run(tmp_path):
    """A normal function run: target is area.py (absent at C0), one committed test file."""
    return _Run(tmp_path)


def given_a_function_run_whose_target_is_a_test_file(tmp_path):
    """A run rigged so any coder write lands ON a declared test_file — every generation
    necessarily tampers with the acceptance criteria (the cheat we mean to catch)."""
    run = _Run(tmp_path)
    run.target = run.repo / "test_area.py"
    return run


_ITERATIONS_FROM_WRITING = object()  # sentinel (T-114): derive the iteration budget from len(writing)


def when_the_coder_iterates(
    *, on, writing, and_evaluation_yields, with_baseline=CLEAN, injecting="",
    with_num_predict=None, with_iterations=_ITERATIONS_FROM_WRITING,
    with_context_limit=A_GENEROUS_WINDOW,
):
    """Drive the loop over `on`: `writing` is the coder's per-iteration output, and
    `and_evaluation_yields` the per-iteration evaluations. The C0 baseline (`with_baseline`,
    CLEAN by default) is prepended automatically; `injecting` is a pre-resolved <refs> block;
    `with_num_predict` sets an explicit budgets.num_predict (E-D9 explicit-override case).
    `with_iterations` (T-114): default derives the budget from len(writing); None omits it so
    the loop resolves the mode default (edit 1, greenfield 3); an int sets it explicitly."""
    iterations = (len(writing) or 1) if with_iterations is _ITERATIONS_FROM_WRITING else with_iterations
    spec = _spec(on.repo, iterations=iterations)
    spec["deliverable"]["target"] = str(on.target)
    if with_num_predict is not None:
        spec["budgets"]["num_predict"] = with_num_predict
    evaluate = FakeEvaluate([with_baseline, *and_evaluation_yields])
    workspace = Workspace(spec, "rid1", on.tmp_path / "run", evaluate)
    on.worktree = workspace.worktree_path
    on.ledger = Ledger(on.tmp_path / "events.jsonl")
    on.coder = FakeCoder(writing)
    on.result = EvaluatedLoop(
        spec, "rid1", workspace, evaluate, on.coder, on.ledger, refs_block=injecting,
        context_limit_for=lambda _model: with_context_limit,
    ).run()


def when_the_coder_is_refused(**staging):
    """Drive the loop expecting the input-fit guard (T-112) to refuse it outright.

    Same vocabulary as ``when_the_coder_iterates`` — it delegates — but the refusal lands
    on ``run.refusal`` instead of escaping, so a ``then_`` can read it."""
    try:
        when_the_coder_iterates(**staging)
    except ContextBudgetError as exc:
        staging["on"].refusal = exc


def _iteration_payloads(run):
    return [e["payload"] for e in _events(run.ledger, "IterationEvaluated")]


def then_it_delivered_on_iteration(run, n):
    assert run.result.outcome == "delivered" and run.result.iterations_used == n


def then_it_exhausted_with_the_best_attempt_attached(run):
    assert run.result.outcome == "exhausted" and run.result.limit_hit == "exhausted"
    assert run.result.content  # best attempt attached, never a silent empty result (S11)
    assert _emitted(run.ledger, "Exhausted")
    assert fold_state(run.ledger.read()) == "failed"


def then_it_emitted(run, event, times=None):
    events = _events(run.ledger, event)
    assert len(events) == times if times is not None else bool(events)


def then_the_last_iteration_recorded_a_passing_verdict(run):
    payload = _iteration_payloads(run)[-1]
    assert payload["auto_verdict"] == 2 and payload["passed"] is True


def then_the_first_iteration_recorded_verdict_0(run):
    assert _iteration_payloads(run)[0]["auto_verdict"] == 0


def then_the_exhaustion_says_whose_fault_it_was(run, *, whose):
    """P4-T7: Failed has carried the triad since P2-T3; Exhausted never did, so the terminal a
    reader most needs to attribute was the one that stayed silent about it."""
    payload = [e for e in run.ledger.read() if e["event"] == "Exhausted"][-1]["payload"]
    assert payload["where"] == "loop" and payload["whose"] == whose
    assert "drift" in payload  # the best attempt's drift rides the same report


def then_the_result_reports_the_drift_of_what_was_written(run, lines_added, hunks):
    """P4-D3: the mechanical layer surfaces magnitude on the terminal result, gating nothing."""
    assert run.result.drift["lines_added"] == lines_added
    assert run.result.drift["hunks"] == hunks
    assert run.result.drift["max_verbatim_run_vs_tests"] == 0  # nothing leaked from the tests


def then_each_iteration_names_the_call_that_produced_it(run):
    """The ledger↔calls.jsonl join is by identity, never by position (P4-T3)."""
    named = [p["call_id"] for p in _iteration_payloads(run)]
    assert named == [f"call{i + 1}" for i in range(len(named))]


def then_the_prompt_at_iteration(run, n):
    """Return the prompt the coder saw on iteration `n` (1-based), for the caller to assert on."""
    return run.coder.prompts[n - 1]


def then_iteration_2_prompt_extends_iteration_1(run):
    assert run.coder.prompts[1].startswith(run.coder.prompts[0])


def then_the_post_fresh_start_prompt_dropped_the_repair_tail(run):
    # iteration-3 prompt (after the fresh start) equals iteration 1's stable-only prompt.
    assert run.coder.prompts[2] == run.coder.prompts[0]


def then_the_iteration_was_rejected_as_a_cheat(run):
    evaluated = _events(run.ledger, "IterationEvaluated")
    assert evaluated and evaluated[0]["payload"]["stage_failed"] == "anti_cheat"


def then_it_refused_before_sending_anything_to_the_model(run):
    assert isinstance(run.refusal, ContextBudgetError)
    assert run.coder.prompts == []  # the guard fires before the coder is ever called


def then_the_refusal_blamed_the_payload_at_generation(run):
    triad = run.refusal.triad
    assert triad["where"] == "generation" and triad["whose"] == "payload"
    assert triad["what"]  # a human-readable reason, never blank


def then_it_exhausted_on_the_context_budget(run):
    assert run.result.outcome == "exhausted" and run.result.limit_hit == "context_budget"
    assert run.result.content  # the best attempt is still attached (S11)


# --- convergence ------------------------------------------------------------


def test_converges_on_iteration1_when_first_eval_passes(tmp_path):
    """A clean iteration-1 evaluation delivers on iteration 1, with no Exhausted event."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    then_it_delivered_on_iteration(run, 1)
    then_it_emitted(run, "Exhausted", times=0)


def test_iteration_evaluated_carries_auto_verdict_2_on_pass(tmp_path):
    """A passing iteration records auto_verdict 2 on IterationEvaluated."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    then_the_last_iteration_recorded_a_passing_verdict(run)


def test_the_delivered_result_carries_drift_metrics(tmp_path):
    """A greenfield run wrote a 2-line function, so the whole file is one addition hunk and
    nothing was shared with the acceptance tests — the negative control for A2."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    then_the_result_reports_the_drift_of_what_was_written(run, lines_added=2, hunks=[[1, 2]])


def test_each_iteration_names_its_generating_call(tmp_path):
    """Every IterationEvaluated names the call_id that produced it, so the DPO pass joins
    ledger↔calls.jsonl by identity. Two iterations, so a positional join would still look
    right if the ids were absent — the point is that each verdict names its OWN call."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=["try1", GOOD_AREA], and_evaluation_yields=[FAILS("a"), CLEAN]
    )
    then_each_iteration_names_the_call_that_produced_it(run)


# --- exhaustion -------------------------------------------------------------


def test_exhausts_with_distinct_failures_and_attaches_best(tmp_path):
    """Three distinct in-scope failures -> exhausted, one Exhausted event, best content attached."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=["try1", "try2", "try3"],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
    )
    then_it_exhausted_with_the_best_attempt_attached(run)
    then_it_emitted(run, "Exhausted", times=1)


def test_exhaustion_attributes_the_failure_to_the_model(tmp_path):
    """The coder had its full budget and did not converge — that is the model's, and the
    report has to say so rather than leave a reader to infer it from `limit_hit`."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=["try1", "try2", "try3"],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
    )
    then_the_exhaustion_says_whose_fault_it_was(run, whose="model")


def test_exhausted_iteration_evaluated_records_verdict_0(tmp_path):
    """A failing iteration records auto_verdict 0."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=["1", "2", "3"],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
    )
    then_the_first_iteration_recorded_verdict_0(run)


# --- cache contract (P2-D2) at the loop level -------------------------------


def test_stable_prefix_is_reused_across_iterations(tmp_path):
    """Iteration 2's prompt begins with iteration 1's whole prompt — the stable prefix is
    byte-identical and only the variable repair tail is appended (P2-D2)."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=["try1", "try2", "try3"],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
    )
    then_iteration_2_prompt_extends_iteration_1(run)


def test_repair_feedback_reaches_next_prompt(tmp_path):
    """After a failure, the next prompt carries the repair feedback and previous attempt."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=["try1", "try2", "try3"],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
    )
    prompt = then_the_prompt_at_iteration(run, 2)
    assert "did not pass" in prompt and "try1" in prompt


# --- fresh-start on repetition (P2-D7) --------------------------------------


def test_repeated_signature_triggers_fresh_start(tmp_path):
    """The same failure signature on two iterations fires exactly one FreshStart, and the
    fresh-start prompt drops the variable tail (back to the stable prefix)."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=["try1", "try2", "try3"],
        and_evaluation_yields=[FAILS("a"), FAILS("a"), FAILS("b")],  # a twice -> repetition
    )
    then_it_emitted(run, "FreshStart", times=1)
    then_the_post_fresh_start_prompt_dropped_the_repair_tail(run)


# --- refs injection (carried-from-P1; the T-93 diagram seam) ----------------
# Structural test: varies `given`/wiring (an injected refs block), not the input sequence.


def test_refs_block_is_injected_into_the_stable_prompt(tmp_path):
    """A pre-resolved refs block (e.g. an injected mermaid diagram) appears in the prompt."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN], injecting=A_STATE_DIAGRAM
    )
    assert "STATE DIAGRAM" in then_the_prompt_at_iteration(run, 1)


# --- anti-cheat (P2-D13) ----------------------------------------------------
# Structural test: varies `given` (target IS a test file), so any write is a cheat.


def test_iteration_editing_tests_is_rejected(tmp_path):
    """An iteration whose write lands on a declared test_file is rejected as a cheat (P2-D13),
    not accepted — even if the rigged test would then pass."""
    run = given_a_function_run_whose_target_is_a_test_file(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[A_TAMPERED_TEST], and_evaluation_yields=EVALUATION_NEVER_REACHED
    )
    then_the_iteration_was_rejected_as_a_cheat(run)


# --- edit mode (T-110, E-D2/E-D4/E-D5/E-D9) ---------------------------------
# Edit runs vary the `given` (target committed at HEAD, so assemble picks edit mode) — structural,
# a bespoke `given_`, like anti-cheat and refs. GOOD_AREA (above) is the coder's clean output.

EXISTING_AREA = "def area(w, h):\n    return w + h  # bug: objective wants w * h\n"
FENCED_AREA = "```python\ndef area(w, h):\n    return w * h\n```\n"
# A large committed file: ceil(chars/4)*2 must exceed NUM_PREDICT so the derived floor is visible.
A_BIG_FILE = "# padding line to grow the file\n" * 600 + "def area(w, h):\n    return w + h\n"


def given_an_edit_run(tmp_path, current_content=EXISTING_AREA):
    """A run whose target file (area.py) is already committed at HEAD → edit mode (E-D2)."""
    run = _Run(tmp_path)
    (run.repo / "area.py").write_text(current_content)
    _git(run.repo, "add", "area.py")
    _git(run.repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "seed target")
    return run


A_WRONG_AREA = "def area(w, h):\n    return w - h  # still wrong, and distinctively so\n"


def then_the_repair_prompt_showed_a_diff_not_the_whole_attempt(run, attempt):
    """T-120: the repair tail carries a unified diff against the committed file, and does NOT
    replay `attempt` in full — which would pay for the file a second time in one prompt."""
    prompt = then_the_prompt_at_iteration(run, 2)
    assert "--- the committed file" in prompt and "+++ your last attempt" in prompt
    # .strip() because build_prompt strips every segment — comparing raw bytes would make this
    # negative assertion pass for the wrong reason (a trailing newline it was never going to keep).
    assert attempt.strip() not in prompt


def then_the_repair_prompt_said_nothing_changed(run):
    assert "unchanged" in then_the_prompt_at_iteration(run, 2)


def then_the_target_on_disk_is_unfenced(run):
    """Rule-3 boundary verb (a single filesystem assertion): the on-disk target the compile stage
    reads carries the code with markdown fences stripped (E-D5)."""
    disk = (run.worktree / "area.py").read_text()
    assert "```" not in disk and "def area(w, h):" in disk


def then_the_coder_saw_num_predict(run, expected, *, at=1):
    """The coder's per-call num_predict on iteration `at` (1-based) equals `expected` (E-D9)."""
    assert run.coder.num_predicts[at - 1] == expected


def test_edit_run_shows_the_previous_attempt_as_a_diff(tmp_path):
    """T-120: on an edit run the repair prompt carries a diff against the committed file, not a
    second whole copy of it — the prompt already holds the file as CURRENT FILE."""
    run = given_an_edit_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[A_WRONG_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), CLEAN], with_iterations=2,
    )
    then_the_repair_prompt_showed_a_diff_not_the_whole_attempt(run, A_WRONG_AREA)


def test_greenfield_still_replays_the_whole_previous_attempt(tmp_path):
    """T-120 is edit-mode only: a greenfield run has no committed baseline to diff against, so
    its repair prompt keeps replaying the attempt in full, exactly as before."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[A_WRONG_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), CLEAN], with_iterations=2,
    )
    assert A_WRONG_AREA.strip() in then_the_prompt_at_iteration(run, 2)


def test_an_edit_attempt_identical_to_the_baseline_is_stated_not_silent(tmp_path):
    """T-120: an attempt byte-identical to the committed file diffs to nothing, and an empty
    segment is dropped from the prompt — so 'you changed nothing' is said out loud instead."""
    run = given_an_edit_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[EXISTING_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), CLEAN], with_iterations=2,
    )
    then_the_repair_prompt_said_nothing_changed(run)


def test_edit_run_prompt_carries_current_file_and_edit_constraints(tmp_path):
    """An edit run's prompt shows the CURRENT FILE segment (the committed content) and the edit
    constraints variant (preserve untouched code), not the greenfield from-scratch constraints."""
    run = given_an_edit_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    prompt = then_the_prompt_at_iteration(run, 1)
    assert "CURRENT FILE" in prompt and "return w + h" in prompt
    assert _EDIT_CONSTRAINTS.splitlines()[1] in prompt  # "- Preserve all code ..."


def test_greenfield_run_prompt_has_no_current_file_and_keeps_scratch_constraints(tmp_path):
    """A greenfield run (target absent at C0) renders no CURRENT FILE header and keeps today's
    from-scratch constraints — the compositional half of the byte-identical guarantee."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    prompt = then_the_prompt_at_iteration(run, 1)
    assert "CURRENT FILE" not in prompt
    assert _CONSTRAINTS.splitlines()[0] in prompt  # "- Implement ONLY the objective ..."


def test_greenfield_constraints_are_byte_identical():
    """E-D4 pin: greenfield keeps today's _CONSTRAINTS verbatim (a whole-string constant pin)."""
    assert _CONSTRAINTS == (
        "- Implement ONLY the objective; do not modify the tests.\n"
        "- One responsibility per function; name functions after what they return or do.\n"
        "- Return the complete file content, no markdown fences."
    )


def test_fenced_edit_generation_lands_stripped_on_disk(tmp_path):
    """A fenced coder response in edit mode is stripped before the target write (E-D5)."""
    run = given_an_edit_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[FENCED_AREA], and_evaluation_yields=[CLEAN])
    then_the_target_on_disk_is_unfenced(run)


def test_fenced_greenfield_generation_lands_stripped_on_disk(tmp_path):
    """Fence-strip on the write step applies in BOTH modes — greenfield too (E-D5)."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[FENCED_AREA], and_evaluation_yields=[CLEAN])
    then_the_target_on_disk_is_unfenced(run)


def test_edit_num_predict_floor_derives_from_file_size(tmp_path):
    """E-D9: with no explicit budget, edit mode sizes num_predict to the current file —
    max(NUM_PREDICT, ceil(chars/4)*2) capped at EDIT_NUM_PREDICT_CAP — so a whole-file rewrite
    of a large module is never truncated. A big file raises the floor above the greenfield default."""
    run = given_an_edit_run(tmp_path, current_content=A_BIG_FILE)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    expected = min(EDIT_NUM_PREDICT_CAP, max(NUM_PREDICT, math.ceil(len(A_BIG_FILE) / 4) * 2))
    assert expected > NUM_PREDICT
    then_the_coder_saw_num_predict(run, expected)


def test_explicit_num_predict_budget_overrides_edit_floor(tmp_path):
    """E-D9: an explicit budgets.num_predict ALWAYS wins over the derived edit-mode floor."""
    run = given_an_edit_run(tmp_path, current_content=A_BIG_FILE)
    when_the_coder_iterates(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN], with_num_predict=512
    )
    then_the_coder_saw_num_predict(run, 512)


def test_greenfield_num_predict_is_the_unchanged_default(tmp_path):
    """E-D9: greenfield behavior is unchanged — the coder still sees the NUM_PREDICT floor."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    then_the_coder_saw_num_predict(run, NUM_PREDICT)


# --- iteration budget: mode-resolved default (T-114) ------------------------


def then_it_exhausted_after_iterations(run, n):
    """T-114: the loop ran its budget to exhaustion — exactly `n` iterations, no delivery."""
    assert run.result.outcome == "exhausted" and run.result.iterations_used == n


def test_edit_run_defaults_to_a_single_iteration(tmp_path):
    """T-114: with no explicit budget, an edit run gets ONE iteration — s127 (5/5) showed a
    retry never saw its own residual defect, so a reviewed edit run gets a single shot."""
    run = given_an_edit_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=[GOOD_AREA, GOOD_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
        with_iterations=None,
    )
    then_it_exhausted_after_iterations(run, 1)


def test_greenfield_run_keeps_three_iterations(tmp_path):
    """T-114: greenfield is unchanged — no explicit budget still means three attempts."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=[GOOD_AREA, GOOD_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
        with_iterations=None,
    )
    then_it_exhausted_after_iterations(run, 3)


def test_explicit_iterations_budget_overrides_the_edit_default(tmp_path):
    """T-114: an explicit budgets.iterations ALWAYS wins over the mode default — an edit run
    told to iterate twice does, despite the edit default of one."""
    run = given_an_edit_run(tmp_path)
    when_the_coder_iterates(
        on=run,
        writing=[GOOD_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), FAILS("b")],
        with_iterations=2,
    )
    then_it_exhausted_after_iterations(run, 2)


# --- language axis: persona + system per resolved language (T-92 Phase 3, A1) --
# Structural tests (they vary the GIVEN — the target's extension — per the
# taxonomy), reusing the when_/then_ vocabulary.

A_GO_AREA = "package probe\n\nfunc Area(w, h int) int {\n\treturn w * h\n}\n"


def given_a_go_function_run(tmp_path):
    """A Go-target run: language resolves to 'go' from the .go extension (R1) —
    nothing else about the world changes (evaluation stays injected)."""
    run = _Run(tmp_path)
    run.target = run.repo / "area.go"
    return run


def test_go_run_selects_go_system_and_go_coder_model(tmp_path):
    """A .go target flips BOTH language values: the prompt's system segment names a
    Go engineer, and model "auto" resolves to the Go coder persona. The language
    axis composes with — never replaces — the mode axis (A1)."""
    run = given_a_go_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[A_GO_AREA], and_evaluation_yields=[CLEAN])
    assert "Go engineer" in run.coder.prompts[0]
    assert run.coder.models == ["my-go-q25c14-16k"]


def test_python_run_keeps_python_system_and_coder_model(tmp_path):
    """Characterization: the default (.py target) run still sees the Python system
    line and the Python coder persona — the language axis is purely additive."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN])
    assert "Python engineer" in run.coder.prompts[0]
    assert run.coder.models == ["my-python-q25c14-16k"]


# --- input-fit guard (T-112) ------------------------------------------------


def test_delivers_on_iteration1_when_inside_context_window(tmp_path):
    """A run comfortably inside the window delivers as before, recording no unknown-window note."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN],
        with_context_limit=A_GENEROUS_WINDOW,
    )
    then_it_delivered_on_iteration(run, 1)
    then_it_emitted(run, "ContextLimitUnknown", times=0)


def test_refuses_before_sending_anything_when_first_prompt_cannot_fit(tmp_path):
    """A first prompt that cannot fit the window is refused before the model is called."""
    run = given_a_function_run(tmp_path)
    when_the_coder_is_refused(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN],
        with_context_limit=A_WINDOW_TOO_SMALL_FOR_ANY_PROMPT,
    )
    then_it_refused_before_sending_anything_to_the_model(run)
    then_the_refusal_blamed_the_payload_at_generation(run)


def test_exhausts_on_context_budget_when_the_repair_prompt_outgrows_the_window(tmp_path):
    """An iteration-2 prompt swollen by a huge previous attempt exhausts on the context budget."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[A_HUGE_ATTEMPT, GOOD_AREA], and_evaluation_yields=[FAILS("a")],
        with_context_limit=A_WINDOW_THAT_FITS_ONLY_THE_FIRST_PROMPT,
    )
    then_it_exhausted_on_the_context_budget(run)


def test_delivers_when_the_window_is_undeterminable(tmp_path):
    """An unresolvable window leaves the guard off: the run delivers and says so once."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN],
        with_context_limit=AN_UNDETERMINABLE_WINDOW,
    )
    then_it_delivered_on_iteration(run, 1)
    then_it_emitted(run, "ContextLimitUnknown", times=1)


def test_refuses_when_an_explicit_generation_budget_exceeds_the_window(tmp_path):
    """The RESOLVED budget is counted, not assumed: a prompt that fits is still refused
    when the explicitly requested generation budget will not fit beside it."""
    run = given_a_function_run(tmp_path)
    when_the_coder_is_refused(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN],
        with_context_limit=A_WINDOW_THAT_FITS_ONLY_THE_FIRST_PROMPT,
        with_num_predict=100_000,
    )
    then_it_refused_before_sending_anything_to_the_model(run)
    then_the_refusal_blamed_the_payload_at_generation(run)


# --- terminal reporting: cancellation, no-attempt, the trail ----------------
# Structural: these vary an injected CONTROL SIGNAL or read a ledger projection rather than
# varying an input sequence, so they keep bespoke staging (`ref:test-executable-spec` rule 4).


class _CancelAfter:
    """An `is_cancelled` answering False for the first `n` checks, then True.

    The loop checks once per iteration at the top, so `_CancelAfter(0)` cancels before any work
    happens and `_CancelAfter(1)` cancels after iteration 1 has produced an attempt.
    """

    def __init__(self, n):
        self.n, self.seen = n, 0

    def __call__(self):
        self.seen += 1
        return self.seen > self.n


def when_the_run_is_cancelled(*, on, after, writing, and_evaluation_yields, with_baseline=CLEAN):
    """Drive the loop with cancellation armed — otherwise the same staging as
    `when_the_coder_iterates`, but the cancel seam is the point here, so it is spelled out."""
    spec = _spec(on.repo, iterations=3)
    spec["deliverable"]["target"] = str(on.target)
    evaluate = FakeEvaluate([with_baseline, *and_evaluation_yields])
    workspace = Workspace(spec, "rid1", on.tmp_path / "run", evaluate)
    on.worktree = workspace.worktree_path
    on.ledger = Ledger(on.tmp_path / "events.jsonl")
    on.coder = FakeCoder(writing)
    on.result = EvaluatedLoop(
        spec, "rid1", workspace, evaluate, on.coder, on.ledger,
        context_limit_for=lambda _model: A_GENEROUS_WINDOW,
        is_cancelled=_CancelAfter(after),
    ).run()


def test_a_cancelled_run_reports_its_drift(tmp_path):
    """P4-D3 surfaces drift on every terminal, and `service.result()` returns the `Cancelled`
    payload verbatim as the report — so a terminal omitting it has no drift at all as far as any
    reader is concerned. Two of the three terminals carried it; this is the third."""
    run = given_a_function_run(tmp_path)

    when_the_run_is_cancelled(
        on=run, after=1, writing=[GOOD_AREA], and_evaluation_yields=[FAILS("a")]
    )

    assert run.result.outcome == "cancelled"
    assert _events(run.ledger, "Cancelled")[-1]["payload"]["drift"]["lines_added"] > 0


def test_a_run_with_no_attempt_reports_no_drift_rather_than_a_deletion(tmp_path):
    """With no attempt the delivered content is `""`, so measuring it against an EDIT run's
    committed baseline reports the whole file as removed — telling the reader the run deleted
    their module when it in fact produced nothing at all.

    Not reachable only via cancel: an edit run budgets 1 iteration (T-114), so a single
    anti-cheat rejection also leaves `_best` unset and falls through to `_exhausted`."""
    run = given_an_edit_run(tmp_path)

    when_the_run_is_cancelled(
        on=run, after=0, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN]
    )

    assert run.result.content == ""
    assert run.result.drift == {}  # not lines_removed=<the whole file>
    assert run.result.change == ""


def test_an_exhausted_run_narrates_its_iterations_too(tmp_path):
    """P4-T6 is "the delivery report narrates its iterations", and `_exhausted`'s own docstring
    says its payload IS the report `run_result` returns on that path — but the trail was built
    only on the delivered path. An exhausted run is where the narrative is most useful: its
    reader is the one who has to work out what went wrong."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[GOOD_AREA, GOOD_AREA, GOOD_AREA],
        and_evaluation_yields=[FAILS("a"), FAILS("b"), FAILS("c")],
    )

    trail = _events(run.ledger, "Exhausted")[-1]["payload"]["iterations_trail"]

    assert [step["iteration"] for step in trail] == [1, 2, 3]
    assert all(step["tests_passed"] is False for step in trail)


def test_the_trail_marks_an_iteration_the_anti_cheat_rejected(tmp_path):
    """The model editing its own acceptance criteria is the single strongest thing a reader
    acts on, and the trail rendered it as an ordinary `structural` failure — indistinguishable
    from a compile error. `stage_failed: anti_cheat` was in the ledger the whole time; the
    projection simply dropped it."""
    from ollama_mcp.oficina.worker import _iterations_trail  # the projection under test

    run = given_a_function_run_whose_target_is_a_test_file(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[A_TAMPERED_TEST], and_evaluation_yields=EVALUATION_NEVER_REACHED
    )

    assert [step["cheated"] for step in _iterations_trail(run.ledger)] == [True]


def test_the_drift_comparison_reads_the_tests_assembly_already_read(tmp_path):
    """The declared tests have two consumers — the prompt's tests-as-context block and the drift
    comparison — and one read at assembly is what stops them disagreeing (they had already
    drifted on decoding). The loop takes what assembly read; it does not re-read the files."""
    run = given_a_function_run(tmp_path)
    when_the_coder_iterates(
        on=run, writing=[GOOD_AREA], and_evaluation_yields=[CLEAN]
    )

    assert run.result.drift["max_verbatim_run_vs_tests"] == 0  # computed, not skipped
