"""Contract for `oficina/judge.py` — the Phase-2 rubric judge at packaging (P4-T5).

The judge CLASSIFIES scope; `drift.py` already measured magnitude. It is handed those numbers
rather than asked to derive them, because this tier reads numbers far more reliably than it
computes them — and the mechanical layer produced them for free.

A judge outcome never blocks delivery: S17 gates DPO *chosen labels*, not `Delivered`, and H1
is Claude-gated by design. So every failure mode here degrades to a report, never to a dead run.

Injected-seam SUT: `chat` is a fake, so nothing in these tests touches a GPU or a network.
"""

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
SOME_DRIFT = {"hunks": [[1, 2]], "lines_added": 2, "lines_removed": 0, "max_verbatim_run_vs_tests": 0}

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

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert len(chat.calls) == 2  # the two phase-2 criteria, not the phase-1 one
    assert [c["name"] for c in result["criteria"]] == ["correctness", "scope"]


def test_the_judge_is_handed_the_drift_numbers():
    """Measured for free by the mechanical layer; recomputing them here would spend the
    judge's context on arithmetic it is worse at than the deterministic pass."""
    chat = _FakeChat(_scored(5), _scored(5))

    judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert "lines_added" in chat.calls[0]["prompt"]
    assert "max_verbatim_run_vs_tests" in chat.calls[0]["prompt"]


def test_a_low_score_fails_the_gate():
    """`passed` is the S17 signal. Any criterion below 3 withholds it."""
    chat = _FakeChat(_scored(5), _scored(2))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert result["passed"] is False


def test_all_criteria_at_or_above_the_cut_pass_the_gate():
    """The negative control for the one above — the gate must be able to say yes."""
    chat = _FakeChat(_scored(3), _scored(5))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert result["passed"] is True
    assert result["judge_verdict"] == 3  # the worst criterion, not their average (P4-D8)


def test_a_broken_judge_call_degrades_to_a_report():
    """A judge failure must never take a run down — it is a report, and the run is already
    delivered by the time it speaks."""
    chat = _FakeChat(RuntimeError("model exploded"), _scored(5))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert result["criteria"][0]["score"] is None
    assert "model exploded" in result["criteria"][0]["reasoning"]


def test_unparseable_output_scores_none_rather_than_guessing():
    """Structured output is reliable, not guaranteed. When identity of the score is unknown,
    say so — the T-105 rule that mislabeled beats missing only in the wrong direction."""
    chat = _FakeChat("not json at all", _scored(5))

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

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

    result = judge_deliverable(A_RUBRIC, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert result["passed"] is False
    assert result["judge_verdict"] == 2


def test_a_criterion_below_its_declared_cut_fails_the_gate():
    """P4-D9. The same score is a pass or a fail depending on the rubric: 3 clears the default
    of 3 and misses a declared 4. Without this the new field would be the second per-criterion
    number in that YAML that nothing reads (see `weight`, deleted in P4-D10)."""
    chat = _FakeChat(_scored(3), _scored(5))

    result = judge_deliverable(A_RUBRIC_DECLARING_ITS_CUTS, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert result["passed"] is False
    assert result["criteria"][0]["passing_score"] == 4  # the report explains its own verdict


def test_a_criterion_at_its_declared_cut_passes_the_gate():
    """The negative control — a declared cut must be able to say yes, or it is not a cut."""
    chat = _FakeChat(_scored(4), _scored(4))

    result = judge_deliverable(A_RUBRIC_DECLARING_ITS_CUTS, AN_OBJECTIVE, A_CHANGE_DIFF, SOME_DRIFT, chat)

    assert result["passed"] is True
    assert result["judge_verdict"] == 4
