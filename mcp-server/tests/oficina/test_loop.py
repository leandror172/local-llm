"""Tests for oficina.loop — the evaluated coder⇄evaluator loop (T6, P2-D1/D2/D4/D7/D10).

Real Workspace + Ledger against a temp git repo; the coder and evaluate are fakes (no GPU).
The fake evaluate's FIRST result is consumed by assemble() as the C0 baseline; the rest are
per-iteration. Bodies are hand-written — this is stateful orchestration with event assertions.
"""

import subprocess

from ollama_mcp.oficina.ledger import Ledger, fold_state
from ollama_mcp.oficina.loop import EvaluatedLoop
from ollama_mcp.oficina.parser import STAGE_TEST, ParsedFailure
from ollama_mcp.oficina.workspace import Workspace
from ollama_mcp.oficina.worker import GenerationResult


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


def _fail(key, file="test_area.py"):
    # Realistic test-stage key (pytest-failed: prefix) so category_for can classify it.
    return ParsedFailure(STAGE_TEST, file, (f"pytest-failed:{key}", "d"), f"boom:{key}")


def _events(ledger, name):
    return [e for e in ledger.read() if e["event"] == name]


def _loop(tmp_path, repo, evaluate, coder, iterations=3, fresh_starts=1):
    spec = _spec(repo, iterations, fresh_starts)
    workspace = Workspace(spec, "rid1", tmp_path / "run", evaluate)
    ledger = Ledger(tmp_path / "events.jsonl")
    return EvaluatedLoop(spec, "rid1", workspace, evaluate, coder, ledger), ledger


# --- convergence ------------------------------------------------------------


def test_converges_on_iteration1_when_first_eval_passes(tmp_path):
    """Baseline then an empty iteration-1 evaluation -> delivered on iteration 1."""
    repo = _repo(tmp_path)
    ev = FakeEvaluate([[], []])  # C0 baseline, then iter1 clean
    coder = FakeCoder(["def area(w, h):\n    return w * h\n"])
    loop, ledger = _loop(tmp_path, repo, ev, coder)
    result = loop.run()
    assert result.outcome == "delivered" and result.iterations_used == 1
    assert _events(ledger, "Exhausted") == []


def test_iteration_evaluated_carries_auto_verdict_2_on_pass(tmp_path):
    """A passing iteration records auto_verdict 2 on IterationEvaluated."""
    repo = _repo(tmp_path)
    loop, ledger = _loop(tmp_path, repo, FakeEvaluate([[], []]), FakeCoder(["ok"]))
    loop.run()
    evaluated = _events(ledger, "IterationEvaluated")
    assert evaluated[-1]["payload"]["auto_verdict"] == 2
    assert evaluated[-1]["payload"]["passed"] is True


# --- exhaustion -------------------------------------------------------------


def test_exhausts_with_distinct_failures_and_attaches_best(tmp_path):
    """Three distinct in-scope failures -> exhausted, Exhausted event, best content attached."""
    repo = _repo(tmp_path)
    ev = FakeEvaluate([[], [_fail("a")], [_fail("b")], [_fail("c")]])
    coder = FakeCoder(["try1", "try2", "try3"])
    loop, ledger = _loop(tmp_path, repo, ev, coder)
    result = loop.run()
    assert result.outcome == "exhausted" and result.limit_hit == "exhausted"
    assert result.content  # best attempt attached (non-empty), never a silent empty (S11)
    assert len(_events(ledger, "Exhausted")) == 1
    assert fold_state(ledger.read()) == "failed"


def test_exhausted_iteration_evaluated_records_verdict_0(tmp_path):
    """A failing iteration records auto_verdict 0."""
    repo = _repo(tmp_path)
    ev = FakeEvaluate([[], [_fail("a")], [_fail("b")], [_fail("c")]])
    loop, ledger = _loop(tmp_path, repo, ev, FakeCoder(["1", "2", "3"]))
    loop.run()
    assert _events(ledger, "IterationEvaluated")[0]["payload"]["auto_verdict"] == 0


# --- cache contract (P2-D2) at the loop level -------------------------------


def test_stable_prefix_is_reused_across_iterations(tmp_path):
    """Iteration 2's prompt begins with iteration 1's whole prompt — the stable prefix is
    byte-identical and only the variable repair tail is appended (P2-D2)."""
    repo = _repo(tmp_path)
    ev = FakeEvaluate([[], [_fail("a")], [_fail("b")], [_fail("c")]])
    coder = FakeCoder(["try1", "try2", "try3"])
    loop, _ = _loop(tmp_path, repo, ev, coder)
    loop.run()
    assert coder.prompts[1].startswith(coder.prompts[0])


def test_repair_feedback_reaches_next_prompt(tmp_path):
    """After a failure, the next prompt carries the repair feedback and previous attempt."""
    repo = _repo(tmp_path)
    ev = FakeEvaluate([[], [_fail("a")], [_fail("b")], [_fail("c")]])
    coder = FakeCoder(["try1", "try2", "try3"])
    loop, _ = _loop(tmp_path, repo, ev, coder)
    loop.run()
    assert "did not pass" in coder.prompts[1]
    assert "try1" in coder.prompts[1]


# --- fresh-start on repetition (P2-D7) --------------------------------------


def test_repeated_signature_triggers_fresh_start(tmp_path):
    """The same failure signature on two iterations fires exactly one FreshStart, and the
    fresh-start prompt drops the variable tail (back to the stable prefix)."""
    repo = _repo(tmp_path)
    ev = FakeEvaluate([[], [_fail("a")], [_fail("a")], [_fail("b")]])
    coder = FakeCoder(["try1", "try2", "try3"])
    loop, ledger = _loop(tmp_path, repo, ev, coder)
    loop.run()
    fresh = _events(ledger, "FreshStart")
    assert len(fresh) == 1
    # iteration-3 prompt (post fresh-start) has no repair tail -> equals the stable-only prompt.
    assert coder.prompts[2] == coder.prompts[0]


# --- anti-cheat (P2-D13) ----------------------------------------------------


def test_iteration_editing_tests_is_rejected(tmp_path):
    """If an iteration's write lands on a test_file, the iteration is rejected as a cheat
    (stage_failed=anti_cheat) rather than accepted."""
    repo = _repo(tmp_path)
    spec = _spec(repo, iterations=1)
    # Point the target AT the test file so the coder's write tampers with the acceptance criteria.
    spec["deliverable"]["target"] = str(repo / "test_area.py")
    ev = FakeEvaluate([[]])  # only the C0 baseline is consumed; the cheat short-circuits eval
    coder = FakeCoder(["def test_area():\n    assert True  # tampered\n"])
    workspace = Workspace(spec, "rid1", tmp_path / "run", ev)
    ledger = Ledger(tmp_path / "events.jsonl")
    loop = EvaluatedLoop(spec, "rid1", workspace, ev, coder, ledger)
    loop.run()
    evaluated = _events(ledger, "IterationEvaluated")
    assert evaluated[0]["payload"]["stage_failed"] == "anti_cheat"
