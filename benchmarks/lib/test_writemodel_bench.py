"""
Unit tests for the write-model benchmark's timing capture (T-137).

Model-free: `ollama_chat` and `run_tests` are stubbed, so these run in the
suite rather than on the GPU.

WHY. A benchmark cell's `ms` field is wall clock for generate + apply + run
tests, so it is not a generation-rate denominator — s137 could only report
"at least 5.1 tok/s" for exactly this reason. `eval_duration_ms` now comes
from Ollama itself. The invariant worth protecting is not that the happy path
carries the keys, but that the ERROR path does too: `summarize` sums
`r["eval_count"]` across every row, so a failed cell missing the key would
turn one model timeout into a KeyError that aborts the whole report.
"""
import pytest

import writemodel_bench as wb
from writemodel_corpus import Task


NS_PER_MS = 1_000_000
STAT_KEYS = ("eval_count", "eval_duration_ms", "prompt_eval_duration_ms", "load_duration_ms")


@pytest.fixture
def task():
    return Task(
        name="t", bucket="small", target_fn="scale", target_test="test_scale",
        behavior="double the input",
        source="def scale(x):\n    return x * 3\n",
        tests="from mod import scale\n\ndef test_scale():\n    assert scale(2) == 4\n",
    )


def _stub_chat(**overrides):
    resp = {
        "content": "def scale(x):\n    return x * 2\n",
        "eval_count": 600,
        "eval_duration_ms": 40_000,
        "prompt_eval_duration_ms": 2_000,
        "load_duration_ms": 15_000,
    }
    resp.update(overrides)
    return lambda *a, **kw: resp


class TestCallModel:
    def test_returns_every_stat_key_from_the_response(self, monkeypatch):
        monkeypatch.setattr(wb, "ollama_chat", _stub_chat())
        _, stats = wb.call_model("p", "m", 10)
        assert stats == {
            "eval_count": 600,
            "eval_duration_ms": 40_000,
            "prompt_eval_duration_ms": 2_000,
            "load_duration_ms": 15_000,
        }

    def test_absent_timings_become_zero_not_none(self, monkeypatch):
        # An older Ollama, or a warm model omitting load_duration, must not put
        # None into a field that downstream arithmetic divides by.
        monkeypatch.setattr(wb, "ollama_chat", lambda *a, **kw: {"content": "x"})
        _, stats = wb.call_model("p", "m", 10)
        assert set(stats) == set(STAT_KEYS)
        assert all(v == 0 for v in stats.values())

    def test_cold_start_is_retried_exactly_once_then_propagates(self, monkeypatch):
        # NOT a test of call_model's trailing `return "", {...}`: that line is
        # unreachable, since the loop always returns inside the try or re-raises
        # on attempt 2. An earlier draft asserted only `pytest.raises` and so
        # passed with and against the fix — the retry COUNT is what discriminates.
        calls = []

        def always_timeout(*a, **kw):
            calls.append(1)
            raise TimeoutError("cold start")

        monkeypatch.setattr(wb, "ollama_chat", always_timeout)
        monkeypatch.setattr(wb.time, "sleep", lambda _s: None)
        with pytest.raises(TimeoutError):
            wb.call_model("p", "m", 10)
        assert len(calls) == 2, "one retry on cold start, then give up (T-131: 2N)"

    def test_a_non_timeout_error_is_not_retried(self, monkeypatch):
        # Only a cold start earns the second attempt; retrying a real fault
        # doubles the cost of every failure for nothing.
        calls = []

        def boom(*a, **kw):
            calls.append(1)
            raise RuntimeError("bad request")

        monkeypatch.setattr(wb, "ollama_chat", boom)
        with pytest.raises(RuntimeError):
            wb.call_model("p", "m", 10)
        assert len(calls) == 1


class TestRunCellRecord:
    @pytest.fixture(autouse=True)
    def _no_subprocess(self, monkeypatch):
        monkeypatch.setattr(wb, "run_tests", lambda src, t: (True, True))

    def test_happy_path_record_carries_every_stat_key(self, monkeypatch, task):
        monkeypatch.setattr(wb, "ollama_chat", _stub_chat())
        rec = wb.run_cell(task, "whole_file", "m", 0, 10)
        for key in STAT_KEYS:
            assert key in rec, f"{key} missing from a successful cell"
        assert rec["eval_duration_ms"] == 40_000

    def test_failed_cell_still_carries_every_stat_key(self, monkeypatch, task):
        # summarize() does sum(r["eval_count"] for r in rows) over ALL rows.
        def boom(*a, **kw):
            raise RuntimeError("model exploded")

        monkeypatch.setattr(wb, "ollama_chat", boom)
        rec = wb.run_cell(task, "whole_file", "m", 0, 10)
        assert rec["error"] is not None, "this case exists to exercise the error path"
        for key in STAT_KEYS:
            assert key in rec, f"{key} missing from a FAILED cell — summarize would KeyError"
            assert rec[key] == 0

    def test_wall_clock_is_not_the_generation_time(self, monkeypatch, task):
        # The distinction the whole task exists for. If these were ever the same
        # field, the rate computed from it would silently include apply + tests.
        monkeypatch.setattr(wb, "ollama_chat", _stub_chat())
        rec = wb.run_cell(task, "whole_file", "m", 0, 10)
        assert rec["ms"] != rec["eval_duration_ms"]
        assert rec["ms"] < 1_000, "stubbed cell should be fast; ms is real wall clock"


# --- criterion 5a outcome classification (s139) -------------------------------
#
# `body_has_import` (s137) detects the PREDICTED tell. It cannot distinguish the other ways
# an attempt can respond to needing an unaddressable statement, and the plan pre-registers
# those as separate outcomes. Two metrics make the three cases derivable from one record:
#
#   has_import=True                           -> emitted a function-local import (predicted)
#   references=True, has_import=False         -> USED the module and never imported it; the
#                                                model did not register that it needed a
#                                                top-level statement at all. NameError at run
#                                                time, so it is caught -- but by the tests,
#                                                not by any criterion, which is why it needs
#                                                its own signal.
#   references=False                          -> avoided the module (hand-rolled). Legitimate
#                                                Python and it may even pass, so nothing else
#                                                would flag it.

import json

from writemodel_corpus import generate_import_task


def _unit(body: str, path=("gcd_ratio",), kind="Function") -> str:
    return json.dumps({"op": "replace_unit", "path": list(path), "kind": kind, "body": body})


@pytest.fixture
def import_task():
    return generate_import_task("small", 0)   # gcd_ratio / math


class TestCriterion5aOutcomes:
    def test_records_the_required_module_on_the_record(self, import_task):
        """The record must be self-describing: reading a results file months later, 'was this
        even an import task?' cannot depend on re-deriving it from the task name."""
        m = wb._symbol_metrics(import_task, _unit("def gcd_ratio(a, b):\n    return (a, b)\n"))
        assert m["required_module"] == "math"

    def test_required_module_is_none_for_an_ordinary_task(self, task):
        m = wb._symbol_metrics(task, _unit("def scale(x, factor):\n    return x\n", ("scale",)))
        assert m["required_module"] is None

    def test_function_local_import_is_flagged(self, import_task):
        """The predicted behaviour."""
        body = "def gcd_ratio(a, b):\n    import math\n    g = math.gcd(a, b)\n    return (a // g, b // g)\n"
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_has_import"] is True
        assert m["body_references_module"] is True

    def test_module_used_without_any_import_is_distinguishable(self, import_task):
        """The case body_has_import alone cannot see: it reached for math and never imported
        it anywhere. Distinct from hand-rolling, and distinct from the prediction."""
        body = "def gcd_ratio(a, b):\n    g = math.gcd(a, b)\n    return (a // g, b // g)\n"
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_has_import"] is False
        assert m["body_references_module"] is True

    def test_hand_rolled_fix_is_distinguishable(self, import_task):
        """Avoided the unaddressable statement entirely. A counted outcome, not a failure."""
        body = (
            "def gcd_ratio(a, b):\n"
            "    x, y = a, b\n"
            "    while y:\n"
            "        x, y = y, x % y\n"
            "    return (a // x, b // x)\n"
        )
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_has_import"] is False
        assert m["body_references_module"] is False

    def test_module_reference_is_not_matched_inside_a_longer_name(self, import_task):
        """`aftermath_of(x)` is not a use of `math`. Substring matching here would silently
        inflate the most interesting outcome."""
        body = "def gcd_ratio(a, b):\n    return aftermath_of(a), mathematics(b)\n"
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_references_module"] is False

    def test_from_import_form_counts_as_referencing_the_module(self, import_task):
        """FOUND IN THE FIRST LIVE RECORDS, not by reasoning. `from itertools import accumulate`
        names the module ONLY in the import statement -- the call site is a bare `accumulate`
        with no module name on it -- so an ast.Name scan reports "did not reference itertools"
        about a body that plainly uses it. Left uncorrected, the hand-rolled outcome absorbs
        every from-import and the most interesting count is quietly wrong."""
        body = ("def running_total(xs):\n"
                "    from itertools import accumulate\n"
                "    return list(accumulate(xs))\n")
        t = generate_import_task("small", 1)   # running_total / itertools
        m = wb._symbol_metrics(t, _unit(body, ("running_total",)))
        assert m["body_has_import"] is True
        assert m["body_references_module"] is True

    def test_plain_import_form_counts_as_referencing_the_module(self, import_task):
        body = "def gcd_ratio(a, b):\n    import math\n    return (a, b)\n"
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_references_module"] is True

    def test_importing_an_unrelated_module_is_not_a_reference(self, import_task):
        """The negative control for the two above: an import of something else must not count,
        or every function-local import of any kind would read as using the required module."""
        body = "def gcd_ratio(a, b):\n    import os\n    return (a, b)\n"
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_has_import"] is True
        assert m["body_references_module"] is False


# --- warm-up before the sweep (s139) ------------------------------------------
#
# Cells now record load_duration_ms, so a cold load is visible rather than silently averaged
# into a rate. A warm-up makes the FIRST cell comparable to the rest instead of being the one
# that pays the model load -- without it, cell 1 of every sweep is a different measurement
# regime from cells 2..N and nothing in the output says so.
#
# Recording is kept as well as warming: a model evicted mid-sweep (12GB card, other work) will
# reload, and that must stay visible. Warming is not a substitute for measuring.


class TestWarmup:
    def test_warmup_call_precedes_the_first_cell(self, monkeypatch, task, tmp_path):
        seen = []

        def record(*a, **kw):
            seen.append(kw.get("model"))
            return {"content": "x", "eval_count": 1, "eval_duration_ms": 1,
                    "prompt_eval_duration_ms": 1, "load_duration_ms": 0}

        monkeypatch.setattr(wb, "ollama_chat", record)
        monkeypatch.setattr(wb, "run_tests", lambda src, t: (True, True))
        wb.run_all([task], ["whole_file"], "my-model", 1, 10, str(tmp_path / "o.jsonl"))
        assert len(seen) >= 2, "expected a warm-up call before the sweep's own call"
        assert seen[0] == "my-model", "warm-up must load the model the sweep will use"

    def test_a_failing_warmup_does_not_abort_the_sweep(self, monkeypatch, task, tmp_path):
        """The warm-up is an optimisation, not a precondition. If Ollama is briefly unhappy the
        run should still produce data -- and the cold load will show up in load_duration_ms,
        which is the whole reason that field is recorded rather than assumed away."""
        calls = []

        def flaky(*a, **kw):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("warm-up failed")
            return {"content": "x", "eval_count": 1, "eval_duration_ms": 1,
                    "prompt_eval_duration_ms": 1, "load_duration_ms": 999}

        monkeypatch.setattr(wb, "ollama_chat", flaky)
        monkeypatch.setattr(wb, "run_tests", lambda src, t: (True, True))
        out = tmp_path / "o.jsonl"
        recs = wb.run_all([task], ["whole_file"], "my-model", 1, 10, str(out))
        assert len(recs) == 1, "sweep must still run after a failed warm-up"
        assert recs[0]["load_duration_ms"] == 999, "the cold load must remain visible"


# --- 5a outcome classification as a reportable value (s139) --------------------


class TestClassify5a:
    """The report must name all three outcomes. Counting only the predicted tell is how s137's
    0/12 came to read as a pass: an outcome nothing counts is an outcome nobody sees."""

    def test_function_local_import_wins_over_reference(self):
        # Both flags true is the NORMAL shape of the predicted case -- `import math` then
        # `math.gcd`. Precedence has to be pinned or the two overlap silently.
        assert wb._classify_5a({
            "required_module": "math", "body_parses": True,
            "body_has_import": True, "body_references_module": True,
        }) == "function_local_import"

    def test_used_without_importing(self):
        assert wb._classify_5a({
            "required_module": "math", "body_parses": True,
            "body_has_import": False, "body_references_module": True,
        }) == "used_without_importing"

    def test_avoided_the_module(self):
        assert wb._classify_5a({
            "required_module": "math", "body_parses": True,
            "body_has_import": False, "body_references_module": False,
        }) == "avoided_the_module"

    def test_non_import_task_is_not_classified(self):
        """An ordinary task has no required module, so every 5a outcome is meaningless for it.
        Returning a label anyway would put unrelated rows into the denominator."""
        assert wb._classify_5a({
            "required_module": None, "body_parses": True,
            "body_has_import": False, "body_references_module": None,
        }) is None

    def test_unparseable_body_is_not_classified(self):
        """Silence, not a guess: an unparseable body supports no claim about what it needed,
        and folding it into `avoided` would invent the most convenient answer."""
        assert wb._classify_5a({
            "required_module": "math", "body_parses": False,
            "body_has_import": None, "body_references_module": None,
        }) is None


class TestBodyIsActuallyAUnit:
    """FOUND BY REPRODUCING AN ANOMALOUS CELL, not by reading the code.

    Two live cells emitted `from itertools import accumulate` + a bare `return list(...)` --
    the body WITHOUT its `def` line. Spliced in, that puts a `return` at module level, so the
    module raises on import and EVERY filler test dies with it. The run recorded
    `body_parses: True` and `body does not parse 0/12`.

    Both facts are true and neither helps: `ast.parse` builds an AST for a module-level
    `return` quite happily -- the SyntaxError is raised by `compile()`, not by the parser. The
    signal that was actually present is `body_units == 0`: a body declared `kind: Function`
    containing no function at all. It was recorded every time and reported never, because the
    report only ever flagged `> 1` unit ("emitted neighbouring code").
    """

    BODY_WITHOUT_DEF = "from itertools import accumulate\nreturn list(accumulate(xs))"

    def test_ast_parse_alone_does_not_catch_it(self):
        """Pins the reason a second check is needed, so nobody 'simplifies' it back later."""
        import ast
        ast.parse(self.BODY_WITHOUT_DEF)   # must NOT raise — that is the whole problem

    def test_body_without_its_def_is_flagged_as_not_compiling(self, import_task):
        m = wb._symbol_metrics(import_task, _unit(self.BODY_WITHOUT_DEF, ("running_total",)))
        assert m["body_parses"] is True, "unchanged: it does parse"
        assert m["body_compiles"] is False, "but it cannot be imported, which is what matters"

    def test_body_without_its_def_records_zero_units(self, import_task):
        m = wb._symbol_metrics(import_task, _unit(self.BODY_WITHOUT_DEF, ("running_total",)))
        assert m["body_units"] == 0

    def test_a_well_formed_unit_compiles_and_counts_one(self, import_task):
        body = "def gcd_ratio(a, b):\n    import math\n    return (a, b)\n"
        m = wb._symbol_metrics(import_task, _unit(body))
        assert m["body_compiles"] is True
        assert m["body_units"] == 1


class TestPromptKindVocabulary:
    """The prompt tells the model which `kind` strings exist. That vocabulary is OWNED by the
    resolver, and until s140 the prompt restated it as a literal — so when `KINDS` grew
    `Constant`/`ClassConstant`, the resolver could address a module constant and the model had
    no way to NAME one. The capability was unreachable and the arm would have reported a clean
    zero for a case it never offered."""

    def _symbol_prompt(self):
        from writemodel_corpus import generate_class_task
        return wb.build_prompt(generate_class_task("small", 0), "symbol_addressed")

    def test_every_kind_the_resolver_accepts_is_offered_to_the_model(self):
        prompt = self._symbol_prompt()
        for kind in wb.KINDS:
            assert f'"{kind}"' in prompt, f"{kind} is resolvable but never offered"

    def test_the_prompt_offers_no_kind_the_resolver_would_reject(self):
        # The other direction, and the one a "does it contain X" check cannot catch: an offered
        # kind the resolver does not know resolves to `unknown_kind` on every use, so the arm
        # would score zero for following its own instructions.
        import re
        offered = set(re.findall(r'"([A-Z][A-Za-z]*)"', self._symbol_prompt()))
        # Names appearing in the worked path example are not kind offers.
        offered -= {"ClassName"}
        assert offered <= set(wb.KINDS), f"offered but unresolvable: {offered - set(wb.KINDS)}"


class TestBodyUnitsFollowsTheResolver:
    """`body_units` == 0 is the s139 fragment signal (a body emitted without its `def` line).
    Until s140 it counted def/class NODE TYPES, so a `Constant` body -- `NAME = value`, no def,
    no class -- scored zero and 12 of 12 correct answers were reported as fragments. The metric
    must use the resolver's own notion of a unit or it drifts every time the resolver learns
    a new one."""

    def _units(self, body, task):
        return wb._symbol_metrics(task, _unit(body))["body_units"]

    def test_a_constant_body_counts_as_one_unit(self, import_task):
        assert self._units("SCALE_FACTOR = 10\n", import_task) == 1

    def test_a_function_body_still_counts_as_one_unit(self, import_task):
        assert self._units("def f(a):\n    return a\n", import_task) == 1

    def test_a_fragment_still_counts_as_zero(self, import_task):
        # THE s139 DEFECT, which the widening must not trade away: `ast.parse` accepts a
        # module-level `return`, so this "parses" while being unimportable.
        assert self._units("    return list(xs)\n", import_task) == 0

    def test_neighbouring_code_still_counts_as_more_than_one(self, import_task):
        assert self._units("A = 1\nB = 2\n", import_task) == 2

    def test_an_import_is_not_a_unit(self, import_task):
        # It is measured by `body_has_import` instead; counting it here would make a
        # function-local import look like emitted neighbouring code.
        assert self._units("import math\n", import_task) == 0
