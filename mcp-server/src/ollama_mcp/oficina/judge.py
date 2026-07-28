"""Phase-2 rubric judge, run once at packaging (P4-D1).

**Composes the evaluator's rubrics; owns the model call.** The rubric YAML is the domain
asset — criteria, descriptions, 1-5 scoring scales — and is read as-is, never modified. The
call itself belongs here because oficina has exactly ONE per-call transport spelling (T-95);
routing the judge through `evaluator/lib/evaluate.py`'s own `ollama_chat` would produce a call
absent from `calls.jsonl`, carrying no `run_id` and no `call_id` — the identity P4-T3 threaded
precisely so verdicts can name what they judge. So the prompt strings are re-authored here,
deliberately, and only the strings.

**Nothing here can fail a run.** S17 gates DPO *chosen labels*, not `Delivered`; H1 is
Claude-gated by design (`ref:delegate-non-goals`: not a replacement for Claude's judgment). A
judge that errors, times out, or returns nonsense degrades to a report saying so.
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

# The judge answers one criterion at a time; this is the shape it must answer in.
VERDICT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "reasoning": {"type": "string"},
    },
    "required": ["score", "reasoning"],
}

_PASSING_SCORE = 3


def load_rubric(rubric_id: str) -> Dict[str, Any]:
    """The evaluator rubric named by `rubric_id`, parsed.

    Resolved the way this package already reaches every other evaluator asset: an
    ``OFICINA_RUBRICS`` override first, else repo-relative (mirrors ``_validate_code_script``).
    """
    path = _rubrics_dir() / f"{rubric_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"rubric {rubric_id!r} not found at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _rubrics_dir() -> Path:
    """Where rubrics live — env override, else repo-relative."""
    override = os.environ.get("OFICINA_RUBRICS")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[4] / "evaluator" / "rubrics"


def judge_deliverable(
    rubric: Dict[str, Any],
    objective: str,
    change: str,
    drift: Dict[str, Any],
    chat: Callable[..., str],
) -> Dict[str, Any]:
    """Score every phase-2 criterion of `rubric`, one model call each.

    ``change`` is the run's unified diff, NOT the delivered file — see `_judge_user_prompt`
    for the measurement that decided it.

    One criterion per call is the evaluator's own design for reliability at this tier.
    ``chat`` is injected so the pure path needs no GPU: it is called as
    ``chat(system=..., prompt=..., schema=...)`` and returns the model's raw text.
    """
    scored = [
        _score_criterion(criterion, objective, change, drift, chat)
        for criterion in _phase_2_criteria(rubric)
    ]
    return {
        "rubric": rubric.get("id"),
        "passed": _all_criteria_pass(scored),
        "judge_verdict": _mean_score(scored),
        "criteria": scored,
    }


def _phase_2_criteria(rubric: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The criteria a model judges — phase 1 belongs to the deterministic layer."""
    return [c for c in rubric.get("criteria", []) if c.get("phase") == 2]


def _score_criterion(
    criterion: Dict[str, Any],
    objective: str,
    change: str,
    drift: Dict[str, Any],
    chat: Callable[..., str],
) -> Dict[str, Any]:
    """One criterion's verdict; an unscoreable criterion reports why instead of raising."""
    try:
        reply = chat(
            system=_judge_system_prompt(criterion),
            prompt=_judge_user_prompt(objective, change, drift, criterion),
            schema=VERDICT_SCHEMA,
        )
        parsed = _parsed_verdict(reply)
        return {
            "name": criterion["name"],
            "score": int(parsed["score"]),
            "reasoning": str(parsed.get("reasoning", "")),
        }
    except Exception as exc:  # a judge failure is a report, never a dead run
        return {"name": criterion["name"], "score": None, "reasoning": f"judge error: {exc}"}


def _parsed_verdict(reply: str) -> Dict[str, Any]:
    """The model's reply as a verdict object, or an error if it is not one."""
    parsed = json.loads(reply)
    if not isinstance(parsed, dict) or "score" not in parsed:
        raise ValueError("reply carried no score")
    return parsed


def _judge_system_prompt(criterion: Dict[str, Any]) -> str:
    """The one-criterion framing, mirroring the evaluator's Phase-2 contract."""
    scale = "\n".join(
        f"  {k}: {v}" for k, v in sorted((criterion.get("scoring") or {}).items(), reverse=True)
    )
    return (
        "You are an impartial code evaluation judge. "
        "Score an LLM output on exactly ONE criterion.\n\n"
        f"Criterion: {criterion['name']}\n"
        f"Description: {criterion['description']}\n\n"
        f"Scoring scale (1-5):\n{scale}\n\n"
        'Respond ONLY with a JSON object: '
        '{"score": <integer 1-5>, "reasoning": "<one concise sentence>"}'
    )


def _judge_user_prompt(
    objective: str, change: str, drift: Dict[str, Any], criterion: Dict[str, Any]
) -> str:
    """What the judge reads: the ask, the CHANGE as a unified diff, and the measured drift.

    **The diff, not the delivered file — measured, not assumed (P4-T9).** Replaying the real
    T-119 leak: shown the delivered file plus these same metrics, the judge scored
    `scope_adherence` **5** and wrote "contains only the requested change" about a file with
    114 added lines, 78 of them verbatim from its own tests. Shown the diff instead, the same
    judge, same metrics, same persona scored **2** — "substantial unrequested content added".
    A comparative question is unanswerable from one side of the comparison; the model reasons
    about the file it can see, which looks fine, and treats the numbers as background. The diff
    is also ~33% fewer tokens than the file, so accuracy and cost point the same way (the same
    trade T-120 found for the coder's previous attempt).

    The metrics stay, as NUMBERS rather than something to recompute: the mechanical layer
    produced them for free, and this tier reads a number more reliably than it derives one.
    """
    return (
        f"## Objective\n{objective}\n\n"
        f"## What the run actually changed (unified diff)\n{change}\n\n"
        "## Drift already measured (do not recompute)\n"
        f"- hunks: {drift.get('hunks', [])}\n"
        f"- lines_added: {drift.get('lines_added', 0)}\n"
        f"- lines_removed: {drift.get('lines_removed', 0)}\n"
        f"- max_verbatim_run_vs_tests: {drift.get('max_verbatim_run_vs_tests', 0)}\n\n"
        f"Score the output on the criterion: **{criterion['name']}**"
    )


def _all_criteria_pass(scored: List[Dict[str, Any]]) -> bool:
    """The S17 signal. An unscoreable criterion withholds it — a gate that cannot see is not
    a gate that passes."""
    return all(c["score"] is not None and c["score"] >= _PASSING_SCORE for c in scored)


def _mean_score(scored: List[Dict[str, Any]]) -> int:
    """The rounded mean of the criteria that actually scored; 0 when none did."""
    scores: List[int] = [c["score"] for c in scored if c["score"] is not None]
    return round(sum(scores) / len(scores)) if scores else 0
