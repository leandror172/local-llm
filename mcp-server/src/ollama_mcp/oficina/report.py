"""What the delivery report contains, and how large it is allowed to get.

The report rides in the `Delivered` event payload (P4-D6) and is paid for in the caller's
context on EVERY `run_result`, with no pointer indirection to hide behind — so compactness is a
contract, not a preference, and the bounds belong beside the thing they bound.

They did not, and it showed: `_compact_drift` was applied where the worker assembles the
delivered report while `Exhausted` and `Cancelled` passed drift raw, even though those payloads
ARE the report on their paths. A bound that holds only where someone remembered to call it is a
bound with no owner. Both the worker and the loop now call in here.

Full fidelity is never lost — it stays in the events these projections read from (`Judged`, and
the loop's own `LoopResult.drift`), which nobody pays for unless they go looking.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .ledger import Ledger


def _iterations_trail(ledger: Ledger) -> List[Dict[str, Any]]:
    """The delivery report's iteration narrative, folded from the run's own ledger (P4-T6).

    Carries only what a reviewer acts on. This report lives inside the `Delivered` event
    payload (P4-D6) and is paid for in the caller's context on every `run_result`, with no
    pointer indirection to hide behind — so `error_keys` (unbounded) and `auto_verdict` are
    deliberately omitted. `auto_verdict` is a binary restatement of `passed` on a 0/1/2 scale
    that structurally cannot express "improved", which is exactly why presenting it as a
    verdict misleads; the field is surfaced here as `tests_passed` instead, naming what it
    actually knows.
    """
    return [
        {
            "iteration": payload.get("iteration"),
            "tests_passed": payload.get("passed"),
            "failure_class": payload.get("failure_class"),
            # The model editing its own acceptance criteria is the strongest single thing a
            # reader acts on, and `failure_class: structural` alone leaves it indistinguishable
            # from a compile error — so the anti-cheat rejection is named, not implied.
            "cheated": payload.get("stage_failed") == "anti_cheat",
            # T-3: names the exact calls.jsonl record that produced this iteration.
            "call_id": payload.get("call_id"),
        }
        for payload in _iteration_payloads(ledger)
    ]


def _iteration_payloads(ledger: Ledger) -> List[Dict[str, Any]]:
    """Each IterationEvaluated payload, in order."""
    return [
        event.get("payload") or {}
        for event in ledger.read()
        if event.get("event") == "IterationEvaluated"
    ]


# The report is `Delivered`-payload-resident and is paid for in the caller's context on EVERY
# `run_result`, with no pointer indirection to hide behind (P4-D6). So its variable-length parts
# are BOUNDED here rather than trusted to stay small. Full fidelity survives in the events they
# were taken from (`Judged`; the loop's own drift), which nobody pays for unless they go looking.
_MAX_REASONING_CHARS = 200
_MAX_REPORTED_HUNKS = 10


def _compact_judge(verdict: Dict[str, Any]) -> Dict[str, Any]:
    """The judge verdict as the REPORT carries it — a trimmed copy; the original is untouched.

    Only the prose is clipped. `criteria[]` entries are never dropped or reshaped: each carries
    the `passing_score` its score was judged against (P4-D9), and a report without them states a
    verdict it cannot explain. The system prompt asks for one concise sentence — but a prompt is
    a request, not a bound, and this payload cannot afford to find that out in production.
    """
    return {
        **verdict,
        "criteria": [
            {**c, "reasoning": _clipped(str(c.get("reasoning", "")), _MAX_REASONING_CHARS)}
            for c in verdict.get("criteria", [])
        ],
    }


def _compact_drift(drift: Dict[str, Any]) -> Dict[str, Any]:
    """Drift as the REPORT carries it: at most `_MAX_REPORTED_HUNKS` ranges.

    `hunks_total` appears ONLY when ranges were dropped, so its presence means "there were more"
    and its absence means "this is all of them". Emitted unconditionally it would carry no bits —
    first principle 6, the rule that dropped `files_touched` at build time.
    """
    hunks = drift.get("hunks") or []
    if len(hunks) <= _MAX_REPORTED_HUNKS:
        return drift
    return {**drift, "hunks": hunks[:_MAX_REPORTED_HUNKS], "hunks_total": len(hunks)}


def _clipped(text: str, limit: int) -> str:
    """`text` bounded to `limit` characters, ellipsised when it had to give."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
