"""Contract for `oficina/judge.py` — the Phase-2 rubric judge at packaging (P4-T5).

The judge CLASSIFIES scope; `drift.py` already measured magnitude. It is handed those numbers
rather than asked to derive them, because this tier reads numbers far more reliably than it
computes them — and the mechanical layer produced them for free.

A judge outcome never blocks delivery: S17 gates DPO *chosen labels*, not `Delivered`, and H1
is Claude-gated by design. So every failure mode here degrades to a report, never to a dead run.

Injected-seam SUT: `chat` is a fake, so nothing in these tests touches a GPU or a network.
"""

import os

import pytest

from ollama_mcp.oficina.judge import judge_deliverable, load_rubric

A_RUBRIC = {
    "id": "code-python",
    "criteria": [
        {"name": "syntax_valid", "phase": 1, "description": "parses", "scoring": {5: "clean"}},
        {"name": "correctness", "phase": 2, "description": "solves it", "scoring": {5: "yes", 1: "no"}},
        {"name": "scope", "phase": 2, "description": "only what was asked", "scoring": {5: "yes", 1: "no"}},
    ],
}

AN_OBJECTIVE = "Add a double() helper. Change nothing else."
A_CHANGE_DIFF = "--- committed\n+++ delivered\n@@ -1,0 +1,2 @@\n+def double(x):\n+    return x * 2\n"
A_DELIVERED_FILE = "def double(x):\n    return x * 2\n"
SOME_DRIFT = {"hunks": [[1, 2]], "lines_added": 2, "lines_removed": 0, "max_verbatim_run_vs_tests": 0}

# The run mode, detected at assembly (E-D2). Named rather than inlined because the two values
# select different QUESTIONS, not merely different strings — see the T-130 block below.
AN_EDIT_RUN = "edit"
A_GREENFIELD_RUN = "greenfield"

# P4-D9: the cut lives beside the scale it judges. `A_RUBRIC` above declares none, so it
# exercises the default; this one exercises a rubric that raises its own bar.
A_RUBRIC_DECLARING_ITS_CUTS = {
    "id": "oficina-edit",
    "criteria": [
        {"name": "scope_adherence", "phase": 2, "description": "only what was asked",
         "passing_score": 4, "scoring": {5: "yes", 1: "no"}},
        {"name": "objective_met", "phase": 2, "description": "does the job",
         "passing_score": 4, "scoring": {5: "yes", 1: "no"}},
    ],
}


class _FakeChat:
    """Returns canned replies in order and records what it was asked."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, *, system, prompt, schema):
        self.calls.append({"system": system, "prompt": prompt, "schema": schema})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def _scored(score):
    return '{"score": %d, "reasoning": "because"}' % score


def test_a_rubric_loads_by_id_from_the_override_directory(tmp_path, monkeypatch):
    """Rubrics resolve like every other evaluator asset oficina reaches for: an env override
    first, repo-relative otherwise."""
    (tmp_path / "tiny.yaml").write_text("id: tiny\ncriteria: []\n", encoding="utf-8")
    monkeypatch.setenv("OFICINA_RUBRICS", str(tmp_path))

    assert load_rubric("tiny")["id"] == "tiny"


def test_a_missing_rubric_names_what_it_looked_for(tmp_path, monkeypatch):
    """The remedy is the caller's, so the error has to say which id and which path failed."""
    monkeypatch.setenv("OFICINA_RUBRICS", str(tmp_path))

    with pytest.raises(Exception) as excinfo:
        load_rubric("absent")

    assert "absent" in str(excinfo.value)


def test_every_phase_2_criterion_gets_its_own_call():
    """One criterion per call is the evaluator's design for reliability at this tier — and
    phase-1 criteria are the deterministic layer's job, never the judge's."""
    chat = _FakeChat(_scored(5), _scored(4))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert len(chat.calls) == 2  # the two phase-2 criteria, not the phase-1 one
    assert [c["name"] for c in result["criteria"]] == ["correctness", "scope"]


def test_the_judge_is_handed_the_drift_numbers():
    """Measured for free by the mechanical layer; recomputing them here would spend the
    judge's context on arithmetic it is worse at than the deterministic pass."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert "lines_added" in chat.calls[0]["prompt"]
    assert "max_verbatim_run_vs_tests" in chat.calls[0]["prompt"]


def test_a_low_score_fails_the_gate():
    """`passed` is the S17 signal. Any criterion below 3 withholds it."""
    chat = _FakeChat(_scored(5), _scored(2))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert result["passed"] is False


def test_all_criteria_at_or_above_the_cut_pass_the_gate():
    """The negative control for the one above — the gate must be able to say yes."""
    chat = _FakeChat(_scored(3), _scored(5))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert result["passed"] is True
    assert result["judge_verdict"] == 3  # the worst criterion, not their average (P4-D8)


def test_a_broken_judge_call_degrades_to_a_report():
    """A judge failure must never take a run down — it is a report, and the run is already
    delivered by the time it speaks."""
    chat = _FakeChat(RuntimeError("model exploded"), _scored(5))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert result["criteria"][0]["score"] is None
    assert "model exploded" in result["criteria"][0]["reasoning"]


def test_unparseable_output_scores_none_rather_than_guessing():
    """Structured output is reliable, not guaranteed. When identity of the score is unknown,
    say so — the T-105 rule that mislabeled beats missing only in the wrong direction."""
    chat = _FakeChat("not json at all", _scored(5))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert result["criteria"][0]["score"] is None
    # P4-D8: a partial reading is not a verdict of the deliverable. Reducing over only the
    # criteria that DID score is how the old mean reported 5 on a run whose gate withheld —
    # and a min over the same filtered subset would have reported 5 too.
    assert result["judge_verdict"] == 0
    assert result["passed"] is False


def test_the_verdict_is_the_worst_criterion_not_their_average():
    """P4-D8. `passed` is a conjunction, so the number shipped beside it must reduce the same
    way or the report carries two answers. This is the T-119 shape: a violated scope criterion
    next to a clean one averages to 4 — above any cut the rubric could set — while the gate
    itself correctly withholds."""
    chat = _FakeChat(_scored(5), _scored(2))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert result["passed"] is False
    assert result["judge_verdict"] == 2


def test_a_criterion_below_its_declared_cut_fails_the_gate():
    """P4-D9. The same score is a pass or a fail depending on the rubric: 3 clears the default
    of 3 and misses a declared 4. Without this the new field would be the second per-criterion
    number in that YAML that nothing reads (see `weight`, deleted in P4-D10)."""
    chat = _FakeChat(_scored(3), _scored(5))

    result = judge_deliverable(
        A_RUBRIC_DECLARING_ITS_CUTS, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN
    )

    assert result["passed"] is False
    assert result["criteria"][0]["passing_score"] == 4  # the report explains its own verdict


def test_a_rubric_with_nothing_to_judge_does_not_pass():
    """The other half of P4-D8's "the number and the boolean cannot disagree".

    `all([])` is True, so a rubric declaring no phase-2 criteria would report a pass having
    judged nothing and made zero model calls — while `judge_verdict` correctly says 0. A gate
    that never ran is not a gate that passed. Latent today (every shipped rubric has phase-2
    criteria) but `acceptance.rubric` accepts any string and `OFICINA_RUBRICS` points anywhere.
    """
    chat = _FakeChat()
    nothing_to_judge = {
        "id": "phase1only",
        "criteria": [{"name": "syntax_valid", "phase": 1, "description": "parses"}],
    }

    result = judge_deliverable(
        nothing_to_judge, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN
    )

    assert result["passed"] is False
    assert result["judge_verdict"] == 0
    assert chat.calls == []  # it did not merely fail the gate, it never asked anything


def test_a_criterion_at_its_declared_cut_passes_the_gate():
    """The negative control — a declared cut must be able to say yes, or it is not a cut."""
    chat = _FakeChat(_scored(4), _scored(4))

    result = judge_deliverable(
        A_RUBRIC_DECLARING_ITS_CUTS, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN
    )

    assert result["passed"] is True
    assert result["judge_verdict"] == 4


# --- T-129: the run-constant material must be a reusable cache prefix ---------------------
#
# Ollama's prefix cache reuses a leading token sequence. These tests pin the SHAPE that makes
# reuse possible; they cannot observe the cache itself, which is why `make accept-p4` remains
# the gate (a fake `chat` never reaches a model, so it can prove structure and nothing else).


def test_the_system_prompt_is_identical_for_every_criterion():
    """T-129. The system message heads the token sequence, so anything varying inside it
    invalidates the prefix for every call after the first. The criterion's name, description
    and scale used to live here — the one part that changes per call, in front of the ~1,700
    run-constant tokens behind it, which were therefore re-evaluated cold every time."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert chat.calls[0]["system"] == chat.calls[1]["system"]


def test_the_shared_prefix_carries_the_expensive_run_constant_material():
    """T-129. The prefix is only worth reusing if the costly part is INSIDE it: the objective,
    the diff and the drift numbers are identical across criteria and are what the ~2.4-3.1 s of
    redundant evaluation was spent on. Measured before the change: 1.393 -> 1.392 ms/token
    across A1's two calls — the second cost exactly what the first did, per token."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    shared = os.path.commonprefix([chat.calls[0]["prompt"], chat.calls[1]["prompt"]])
    assert AN_OBJECTIVE in shared
    assert A_CHANGE_DIFF in shared
    assert "max_verbatim_run_vs_tests" in shared


def test_the_criterion_block_is_the_tail_the_calls_diverge_on():
    """T-129. The varying DATA moves behind the shared material rather than being deleted —
    the judge still scores one criterion at a time (the evaluator's Phase-2 design), it just
    reads which one at the end. If any criterion text leaked into the shared prefix the two
    calls would be asking the same question."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    shared = os.path.commonprefix([chat.calls[0]["prompt"], chat.calls[1]["prompt"]])
    assert "correctness" not in shared
    assert "scope" not in shared
    assert chat.calls[0]["prompt"].rstrip().endswith("correctness**")
    assert chat.calls[1]["prompt"].rstrip().endswith("scope**")


def test_the_invariant_framing_says_where_the_criterion_will_be():
    """T-129. A bare move would leave the system prompt instructing the model to score "one
    criterion" with no criterion in sight until much later — instructions referencing something
    absent. The framing forward-references the tail instead, so the contract stays complete at
    every point the model reads it."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert "END" in chat.calls[0]["system"]


def test_the_scale_reaches_the_model_even_though_it_left_the_system_prompt():
    """T-129 regression guard. The scoring scale is the rubric's load-bearing content — P4-D9
    moved the cut INTO it. Moving the block must relocate the scale, never drop it: a judge
    scoring 1-5 without being shown what each rung means is the calibration failure P4-D9 was
    opened to fix, arriving by a different route."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    asked = chat.calls[0]["system"] + chat.calls[0]["prompt"]
    assert "solves it" in asked  # the description
    assert "yes" in asked and "no" in asked  # both rungs of the scale


# --- T-130: a rubric declares which run mode it can answer about ---------------------------
#
# The mode is DETECTED at assembly (E-D2: target presence at HEAD, no spec field), so unlike
# the rubric NAME it cannot be validated at intake. `applies_to` is a PRECONDITION, not a
# filter: with a rubric shipped for each mode, its only job is to turn a silent incoherence
# into a named refusal.

AN_EDIT_ONLY_RUBRIC = {
    "id": "oficina-edit",
    "applies_to": "edit",
    "criteria": [
        {"name": "scope_adherence", "phase": 2, "description": "only what was asked",
         "passing_score": 4, "scoring": {5: "yes", 1: "no"}},
    ],
}


def test_a_rubric_declaring_another_mode_is_refused_rather_than_answered():
    """T-130. Every rung of the edit ladder presupposes a prior state — "byte-for-byte intact",
    "an incidental edit", "a reviewer would ask to remove" — so a greenfield run has no answer
    to give. A judge asked an unanswerable question still returns a number: the same greenfield
    deliverable, same code and same rubric, scored 5 and then 1 an hour apart. Refusing names
    the request defect instead of laundering it into a verdict."""
    chat = _FakeChat()

    result = judge_deliverable(
        AN_EDIT_ONLY_RUBRIC, AN_OBJECTIVE, A_DELIVERED_FILE, SOME_DRIFT, chat, A_GREENFIELD_RUN
    )

    assert result["passed"] is False
    assert result["judge_verdict"] == 0
    assert "greenfield" in result["error"]
    assert chat.calls == []  # refused before spending a model call on it


def test_a_rubric_declaring_the_run_s_own_mode_is_judged():
    """The negative control — a precondition that never holds is indistinguishable from a
    rubric that cannot judge at all."""
    chat = _FakeChat(_scored(5))

    result = judge_deliverable(
        AN_EDIT_ONLY_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN
    )

    assert result["passed"] is True
    assert len(chat.calls) == 1


def test_a_rubric_declaring_no_mode_judges_any_run():
    """The shipped benchmark rubrics (code-python and its siblings) declare no `applies_to`,
    and they are used by the Layer-4 suite as well as here. An absent precondition must mean
    "no restriction", never "matches nothing" — the latter would silently stop judging every
    run that names one of them."""
    chat = _FakeChat(_scored(5), _scored(5))

    result = judge_deliverable(
        A_RUBRIC, AN_OBJECTIVE, A_DELIVERED_FILE, SOME_DRIFT, chat, A_GREENFIELD_RUN
    )

    assert result["passed"] is True
    assert len(chat.calls) == 2


def test_the_prompt_calls_a_greenfield_artifact_what_it_is():
    """T-130. With no baseline the change IS the delivered file, so the heading that announces
    a unified diff would be describing something the model is not looking at. A judge told it
    is reading a diff, while reading a file, has been handed a contradiction to resolve on its
    own — and P4-T9 already measured that this tier resolves such conflicts by trusting what it
    can see and treating the rest as background."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(
        A_RUBRIC, AN_OBJECTIVE, A_DELIVERED_FILE, SOME_DRIFT, chat, A_GREENFIELD_RUN
    )

    assert "unified diff" not in chat.calls[0]["prompt"]


def test_the_prompt_still_calls_an_edit_artifact_a_unified_diff():
    """Characterization. The edit path is what P4-T9 calibrated and A1/A2 replay; only the
    no-baseline case is new."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat, AN_EDIT_RUN)

    assert "unified diff" in chat.calls[0]["prompt"]
