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

import subprocess

from ollama_mcp.oficina.ledger import Ledger, fold_state
from ollama_mcp.oficina.loop import EvaluatedLoop
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
    return {
        "deliverable": {"kind": "function", "target": str(repo / "area.py")},
        "objective": "implement area(w, h) returning w*h",
        "acceptance": {"test_cmd": "true", "test_files": ["test_area.py"]},
        "budgets": {"iterations": iterations, "fresh_starts": fresh_starts},
        "workspace": "worktree",
    }


class FakeCoder:
    """Records each prompt; returns the next canned content."""

    def __init__(self, contents):
        self.contents = list(contents)
        self.prompts = []

    def __call__(self, prompt, model, run_id):
        self.prompts.append(prompt)
        content = self.contents.pop(0) if self.contents else "def area(w, h):\n    return w * h\n"
        return GenerationResult(content=content, model=model, eval_count=10, duration_ms=1.0)


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


def given_a_function_run(tmp_path):
    """A normal function run: target is area.py (absent at C0), one committed test file."""
    return _Run(tmp_path)


def given_a_function_run_whose_target_is_a_test_file(tmp_path):
    """A run rigged so any coder write lands ON a declared test_file — every generation
    necessarily tampers with the acceptance criteria (the cheat we mean to catch)."""
    run = _Run(tmp_path)
    run.target = run.repo / "test_area.py"
    return run


def when_the_coder_iterates(*, on, writing, and_evaluation_yields, with_baseline=CLEAN, injecting=""):
    """Drive the loop over `on`: `writing` is the coder's per-iteration output, and
    `and_evaluation_yields` the per-iteration evaluations. The C0 baseline (`with_baseline`,
    CLEAN by default) is prepended automatically; `injecting` is a pre-resolved <refs> block."""
    spec = _spec(on.repo, iterations=len(writing) or 1)
    spec["deliverable"]["target"] = str(on.target)
    evaluate = FakeEvaluate([with_baseline, *and_evaluation_yields])
    workspace = Workspace(spec, "rid1", on.tmp_path / "run", evaluate)
    on.ledger = Ledger(on.tmp_path / "events.jsonl")
    on.coder = FakeCoder(writing)
    on.result = EvaluatedLoop(
        spec, "rid1", workspace, evaluate, on.coder, on.ledger, refs_block=injecting
    ).run()


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
