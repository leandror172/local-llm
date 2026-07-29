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

**The cut lives in the rubric, not here (P4-D9).** A criterion may declare a `passing_score`
beside its own 1-5 scale; `_DEFAULT_PASSING_SCORE` covers those that do not. A cut is a claim
*about* a scale, and keeping the two in different files is exactly how a coherent severity
ladder came to sit one rung above a threshold nobody had re-read against it.
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml

from .transport import _chat_generation

# The judge answers one criterion at a time; this is the shape it must answer in.
VERDICT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "reasoning": {"type": "string"},
    },
    "required": ["score", "reasoning"],
}

# The cut for a criterion that does not declare its own `passing_score` (P4-D9).
_DEFAULT_PASSING_SCORE = 3


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
    from ollama_mcp.config import repo_root  # one owner for "where the repo is"

    return Path(repo_root()) / "evaluator" / "rubrics"


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
        "judge_verdict": _min_score(scored),
        "criteria": scored,
    }


def unavailable_verdict(rubric_id: str, reason: str) -> Dict[str, Any]:
    """The verdict for a judge that could not run at all — the same shape a scored one has.

    Lives here rather than at the call site because this module owns the invariant that
    `judge_verdict` and `passed` agree (P4-D8). A second literal elsewhere is a second place
    that agreement is hand-typed rather than derived, and a second place to forget a new key —
    on the path a report reader most needs to be well-formed.

    `rubric_id` is the caller's requested NAME, not the `id` declared inside the YAML that
    `judge_deliverable` reports: when the load itself failed there is no parsed rubric to read
    an id from. The two coincide whenever a rubric file is named after its own id.
    """
    return {
        "rubric": rubric_id,
        "passed": False,
        "judge_verdict": 0,
        "criteria": [],
        "error": reason,
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
    """One criterion's verdict; an unscoreable criterion reports why instead of raising.

    The verdict carries its own `passing_score`, so the gate and the reader resolve the cut
    from one place, and the report can explain why a 3 failed rather than merely stating it.
    """
    identity = {"name": criterion["name"], "passing_score": _passing_score(criterion)}
    try:
        reply = chat(
            system=_judge_system_prompt(),
            prompt=_judge_user_prompt(objective, change, drift, criterion),
            schema=VERDICT_SCHEMA,
        )
        parsed = _parsed_verdict(reply)
        # The coercions stay INSIDE the try deliberately: a non-integer score degrades to ONE
        # criterion reporting a judge error, whereas hoisting them out would escape to the
        # caller's blanket handler and poison the whole verdict as "judge unavailable".
        return {**identity, "score": int(parsed["score"]),
                "reasoning": str(parsed.get("reasoning", ""))}
    except Exception as exc:  # a judge failure is a report, never a dead run
        return {**identity, "score": None, "reasoning": f"judge error: {exc}"}


def _parsed_verdict(reply: str) -> Dict[str, Any]:
    """The model's reply as a verdict object, or an error if it is not one."""
    parsed = json.loads(reply)
    if not isinstance(parsed, dict) or "score" not in parsed:
        raise ValueError("reply carried no score")
    return parsed


def _judge_system_prompt() -> str:
    """The one-criterion framing, mirroring the evaluator's Phase-2 contract.

    **Criterion-INVARIANT, deliberately (T-129).** Ollama's KV prefix cache reuses a LEADING
    token sequence and the system message heads it, so anything varying in here invalidates the
    prefix for every call after the first. The criterion's name, description and scale used to
    be built in here — the one part that changes per call, sitting in front of the ~1,700
    run-constant tokens behind it, which were therefore re-evaluated cold every time. Measured
    before the move (`prompt_eval_duration_ms`, never `prompt_eval_count` — Ollama reports full
    tokens regardless of reuse, `ref:ollama-kv-prefix-cache`): 1.393 then 1.392 ms per token
    across a run's two calls. The second call cost exactly what the first did, per token.

    The forward reference is what makes this a move rather than a mutilation: a bare relocation
    would leave this message demanding a score for a criterion it never names, and instructions
    that reference something absent are their own failure mode. It names the user message
    explicitly — the criterion is not late in THIS message, it is in the next one.
    """
    return (
        "You are an impartial code evaluation judge. "
        "Score an LLM output on exactly ONE criterion.\n\n"
        "The criterion, its description and its 1-5 scoring scale appear at the END of the "
        "user message, after the material you are judging.\n\n"
        'Respond ONLY with a JSON object: '
        '{"score": <integer 1-5>, "reasoning": "<one concise sentence>"}'
    )


def _scoring_scale(criterion: Dict[str, Any]) -> str:
    """The criterion's rungs, highest first.

    Extracted when T-129 moved the criterion block between messages: the scale had to travel
    with the block, and a scale that silently failed to travel would leave the judge scoring
    1-5 with no statement of what a rung means — the calibration failure P4-D9 was opened to
    fix, arriving by a different route. One owner is one place for that to be true.
    """
    return "\n".join(
        f"  {k}: {v}" for k, v in sorted((criterion.get("scoring") or {}).items(), reverse=True)
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

    **The criterion block is the TAIL (T-129).** Everything above it is identical for every
    criterion of a run, so it is the prefix Ollama's KV cache can hold; the one varying part
    sits behind it where re-evaluation costs only its own tokens. The judge still scores one
    criterion per call — the evaluator's Phase-2 design for reliability at this tier — it just
    reads which one at the end.
    """
    return (
        f"## Objective\n{objective}\n\n"
        f"## What the run actually changed (unified diff)\n{change}\n\n"
        "## Drift already measured (do not recompute)\n"
        f"- hunks: {drift.get('hunks', [])}\n"
        f"- lines_added: {drift.get('lines_added', 0)}\n"
        f"- lines_removed: {drift.get('lines_removed', 0)}\n"
        f"- max_verbatim_run_vs_tests: {drift.get('max_verbatim_run_vs_tests', 0)}\n\n"
        f"## The criterion to score\n"
        f"Criterion: {criterion['name']}\n"
        f"Description: {criterion['description']}\n\n"
        f"Scoring scale (1-5):\n{_scoring_scale(criterion)}\n\n"
        f"Score the output on the criterion: **{criterion['name']}**"
    )


def _passing_score(criterion: Dict[str, Any]) -> int:
    """The cut for one criterion — declared beside the scale it judges, else the default.

    Rubrics that declare none keep `_DEFAULT_PASSING_SCORE`: the other shipped rubrics'
    ladders have not been read, so imposing a raised cut on them would be the same unexamined
    assumption, pointed the other way.
    """
    return criterion.get("passing_score", _DEFAULT_PASSING_SCORE)


def _all_criteria_pass(scored: List[Dict[str, Any]]) -> bool:
    """The S17 signal — withheld unless every criterion was read AND cleared its own cut.

    There are two ways a gate fails to see, and both withhold. An **unscoreable criterion**: a
    gate that cannot see is not a gate that passes. An **empty criterion set**: `all([])` is
    True, so a rubric declaring no phase-2 criteria would otherwise pass having judged nothing
    and called no model — while `_min_score` reports 0 beside it. That is exactly the
    number-vs-boolean disagreement P4-D8 exists to remove, so the emptiness check belongs here
    rather than at the caller.
    """
    return bool(scored) and all(
        c["score"] is not None and c["score"] >= c["passing_score"] for c in scored
    )


def _min_score(scored: List[Dict[str, Any]]) -> int:
    """The worst criterion's score; 0 when any criterion could not be scored.

    Reduced the way `_all_criteria_pass` gates, so the number and the boolean cannot disagree
    (P4-D8). The mean this replaced got both halves wrong. **A conjunction has no average** — a
    clean criterion must never offset a violated one, and a mean let `scope_adherence 2` beside
    `objective_met 5` report 4. And **an unscoreable criterion is not a low score, it is the
    absence of a verdict** — reducing over only the criteria that *did* score reported 5 on a
    run whose gate withheld, which a min over the same filtered subset would have done too.
    """
    if not scored or any(c["score"] is None for c in scored):
        return 0
    return min(c["score"] for c in scored)


JUDGE_MODEL = "my-judge-q25c14-16k"
JUDGE_TIMEOUT_S = 300


def default_judge(run_id: str, model: str = JUDGE_MODEL, timeout: int = JUDGE_TIMEOUT_S):
    """A `chat(system, prompt, schema) -> str` for the judge, on the shared transport.

    The judge persona shares the coder's base (P4-D2), so packaging costs no model swap
    (`ref:delegate-gpu-policy`). Fences are left alone: the reply is schema-constrained JSON,
    not code, and stripping is a codegen concern.

    **`run_id` is required, never defaulted.** The reason this module owns its call rather than
    composing the evaluator's transport is that the record must be *attributable*; it originally
    passed `""`, which is worse than absent because it is a value that looks like one — anything
    grouping `calls.jsonl` by run merged every run's judge calls into one empty-string bucket.
    A default would let that return silently. **Per-criterion `call_id` is deliberately NOT
    recorded (P4-D11):** a run makes one judge call per criterion, and matching ids to criteria
    from an ordered list is the positional fallback T-105 banned. Whoever needs it must thread
    the id back through the `chat` seam, not collect it side-band.
    """

    def _judge_chat(*, system: str, prompt: str, schema: Dict[str, Any]) -> str:
        return _chat_generation(
            prompt, model, run_id, timeout=timeout, strip_fences=False,
            system=system, schema=schema,
        ).content

    return _judge_chat
