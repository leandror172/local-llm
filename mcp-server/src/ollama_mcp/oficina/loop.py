"""The evaluated coder⇄evaluator loop (P2-T6; P2-D1/D2/D4/D7/D10).

This is the value inflection of oficina: instead of P1's single shot, generate → evaluate
cheaply every iteration → classify the failure (rule-based, no model call — P2-D4) → repair
or fresh-start → budget out. The first slice (P2-D1) is `function`-against-pre-authored-tests,
Python, 3 iterations, one persona, no escalation ladder.

Collaborators are INJECTED (coder, evaluate, workspace, ledger) so the loop is unit-testable
with fakes — no GPU, no git required in the pure path. The worker (T7) wires the real ones.

Prompt layout obeys P2-D2 via ``build_prompt``: stable parts (system/constraints/context/tests/
objective) are byte-identical every iteration; only ``repair_feedback``/``previous_attempt`` vary,
so the KV prefix is reused. Fresh-start (P2-D7) drops the variable tail but keeps the stable prefix.

Generation is bounded by ``num_predict`` (T-91): the sync path used to inherit the model default
and truncate functions mid-body; the loop floors it (never truncate a function) and caps it (bound
runaway).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .evaluator import attributable_failures, diff_touches_test_files
from .intake import Budgets
from .parser import ParsedFailure, category_for
from .prompt import build_prompt
from .workspace import Workspace, target_relpath
from .worker import GenerationResult, _chat_generation, _cold_start_grace

# (prompt, model, run_id) -> GenerationResult. The coder writes nothing; the loop places output.
CoderFn = Callable[[str, str, str], GenerationResult]

# First slice defaults (P2-D1): single Python persona, bounded generation (T-91 / P2-D10).
DEFAULT_CODER_MODEL = "my-python-q25c14"
NUM_PREDICT = 2048  # floored so a function is never truncated; capped to bound runaway

_SYSTEM = "You are a precise Python engineer. Implement the objective so every provided test passes."
# No leading "CONSTRAINTS:" label here — prompt.SEGMENTS already prepends that header for the
# 'constraints' segment; embedding it again doubled the header in every prompt.
_CONSTRAINTS = (
    "- Implement ONLY the objective; do not modify the tests.\n"
    "- One responsibility per function; name functions after what they return or do.\n"
    "- Return the complete file content, no markdown fences."
)


@dataclass
class LoopResult:
    """Outcome of the loop — what the worker (T7) turns into Delivered or Exhausted."""

    outcome: str  # "delivered" | "exhausted" | "cancelled"
    content: str
    model: str
    eval_count: int
    duration_ms: float
    iterations_used: int
    branch: str
    best_snapshot: Optional[str]
    limit_hit: Optional[str] = None
    spent: Dict[str, Any] = field(default_factory=dict)


def _signature(failures: List[ParsedFailure]) -> tuple:
    """P2-D7 repetition signature: the sorted set of normalized error_keys."""
    return tuple(sorted({"::".join(f.error_key) for f in failures}))


def _repair_feedback(failures: List[ParsedFailure]) -> str:
    """Behavioral feedback (what failed, not how to fix) for the next iteration."""
    lines = ["The previous attempt did not pass. Observed failures:"]
    for f in failures:
        lines.append(f"- [{f.stage}] {f.raw}")
    lines.append("Make all tests pass. Do NOT edit the tests.")
    return "\n".join(lines)


class EvaluatedLoop:
    """Runs the coder⇄evaluator loop for one run and emits its iteration events."""

    def __init__(
        self,
        spec: Dict[str, Any],
        run_id: str,
        workspace: Workspace,
        evaluate,
        coder: CoderFn,
        ledger,
        is_cancelled: Optional[Callable[[], bool]] = None,
        refs_block: str = "",
    ) -> None:
        self.spec = spec
        self.run_id = run_id
        self.workspace = workspace
        self.evaluate = evaluate
        self.coder = coder
        self.ledger = ledger
        self.is_cancelled = is_cancelled or (lambda: False)
        # Pre-resolved <refs> block (P2 carried-from-P1). Stable → part of the KV prefix.
        # A run spec's context.refs (e.g. a mermaid diagram anchor, T-93) lands here.
        self.refs_block = refs_block
        # Budgets come from the schema of record (intake.Budgets) so defaults live in ONE
        # place; intake has already rejected unknown keys. wall_clock_s is the whole-run
        # safety net (P2-D10), 0/None disables; the per-stage subprocess timeout (evaluator)
        # bounds a single hung run. Checked between iterations.
        budgets = Budgets(**(spec.get("budgets") or {}))
        self.max_iterations = budgets.iterations
        self.max_fresh_starts = budgets.fresh_starts
        self.max_wall_clock_s = budgets.wall_clock_s
        self.model = spec.get("model") or "auto"
        if self.model == "auto":
            self.model = DEFAULT_CODER_MODEL
        # Loop-carried run state (one EvaluatedLoop instance == one run; set up by run()).
        self._branch = ""
        self._fresh_used = 0
        self._signatures_seen: set = set()
        self._best: Optional[GenerationResult] = None
        self._best_failures: Optional[int] = None
        self._best_snapshot: Optional[str] = None

    def _stable_prompt_parts(self, assembly) -> Dict[str, str]:
        """The run-constant prompt parts (P2-D2): system + constraints + the assembled parts, with
        any pre-resolved refs block prepended to the context (docs/diagrams before file context)."""
        parts = {"system": _SYSTEM, "constraints": _CONSTRAINTS, **assembly.stable_parts}
        if self.refs_block:
            parts["context"] = "\n\n".join(
                p for p in (self.refs_block, parts.get("context", "")) if p
            )
        return parts

    def _emit_iteration_started(self, k: int) -> None:
        """Record the iteration and the budget remaining after it (P2-D10)."""
        self.ledger.iteration_started(
            {
                "iteration": k,
                "tier": 1,
                "budget_remaining": {
                    "iterations": self.max_iterations - k,
                    "fresh_starts": self.max_fresh_starts - self._fresh_used,
                },
            }
        )

    def _emit_iteration_evaluated(
        self, k: int, passed: bool, attributable: List[ParsedFailure]
    ) -> None:
        """Record the evaluation verdict; ``auto_verdict`` is the DPO seam (S17)."""
        self.ledger.iteration_evaluated(
            {
                "iteration": k,
                "passed": passed,
                "stage_failed": attributable[0].stage if attributable else None,
                "failure_class": category_for(attributable[0]) if attributable else None,
                "error_keys": [list(f.error_key) for f in attributable],
                "auto_verdict": 2 if passed else 0,
            }
        )

    def _record_cheat_and_feedback(self, k: int, gen: GenerationResult, cheated: List[str]) -> Dict[str, str]:
        """Record the iteration rejected-as-cheat (it edited a test_file, P2-D13) and return the
        repair ``variable`` that steers the next attempt back onto the target only."""
        self.ledger.iteration_evaluated(
            {
                "iteration": k,
                "passed": False,
                "stage_failed": "anti_cheat",
                "failure_class": "structural",
                "error_keys": [],
                "auto_verdict": 0,
                "cheat_touched": cheated,
            }
        )
        return {
            "repair_feedback": f"You edited the tests ({', '.join(cheated)}). Never modify the tests; implement the target only.",
            "previous_attempt": gen.content,
        }

    def _track_best(
        self, gen: GenerationResult, attributable: List[ParsedFailure], snapshot: str
    ) -> None:
        """Keep the attempt with the FEWEST attributable failures — attached on exhaustion (S11)."""
        if self._best_failures is None or len(attributable) < self._best_failures:
            self._best, self._best_failures, self._best_snapshot = gen, len(attributable), snapshot

    def _steer_next_attempt(
        self, k: int, attributable: List[ParsedFailure], gen: GenerationResult
    ) -> Dict[str, str]:
        """Pick the next iteration's variable tail (P2-D7).

        A failure signature already seen this run triggers the (single) fresh start —
        drop the variable tail, keep the stable prefix; otherwise feed back the observed
        failures plus the previous attempt for a repair iteration.
        """
        signature = _signature(attributable)
        if signature in self._signatures_seen and self._fresh_used < self.max_fresh_starts:
            self._fresh_used += 1
            self.ledger.fresh_start(
                {"iteration": k, "signature": list(signature), "reason": "repetition"}
            )
            return {}
        self._signatures_seen.add(signature)
        return {
            "repair_feedback": _repair_feedback(attributable),
            "previous_attempt": gen.content,
        }

    def _result_from(
        self,
        outcome: str,
        attempt: Optional[GenerationResult],
        *,
        iterations_used: int,
        snapshot: Optional[str],
        limit_hit: Optional[str] = None,
        spent: Optional[Dict[str, Any]] = None,
    ) -> LoopResult:
        """Build the terminal LoopResult from ``attempt`` — the delivered generation, or the
        best attempt so far; defaults stand in when no iteration produced one (S11)."""
        return LoopResult(
            outcome=outcome,
            content=attempt.content if attempt else "",
            model=attempt.model if attempt else self.model,
            eval_count=attempt.eval_count if attempt else 0,
            duration_ms=attempt.duration_ms if attempt else 0.0,
            iterations_used=iterations_used,
            branch=self._branch,
            best_snapshot=snapshot,
            limit_hit=limit_hit,
            spent=spent or {},
        )

    def _exhausted(self, *, iterations_used: int, limit_hit: str) -> LoopResult:
        """Emit Exhausted (budget out or wall-clock hit, P2-D10) with the best attempt (S11)."""
        spent = {"iterations": iterations_used, "fresh_starts": self._fresh_used}
        self.ledger.exhausted(
            {
                "spent": spent,
                "limit_hit": limit_hit,
                "best_attempt_ref": self._best_snapshot,
                "branch": self._branch,
            }
        )
        return self._result_from(
            "exhausted",
            self._best,
            iterations_used=iterations_used,
            snapshot=self._best_snapshot,
            limit_hit=limit_hit,
            spent=spent,
        )

    def _time_limit_reached(self, started_at) -> Any:
        return self.max_wall_clock_s and time.monotonic() - started_at > self.max_wall_clock_s

    def _generate_with_snapshot(self, k, prev_sha, stable, target_rel, test_files, variable, worktree) -> Any:
        self._emit_iteration_started(k)
        prompt = build_prompt({**stable, **variable})
        gen = self.coder(prompt, self.model, self.run_id)
        target_path = worktree / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(gen.content, encoding="utf-8")
        snapshot = self.workspace.snapshot(f"oficina iteration {k} ({self.run_id})")

        cheated = diff_touches_test_files(worktree, prev_sha, snapshot, test_files)
        return cheated, gen, snapshot

    def run(self) -> LoopResult:
        """Assemble, then iterate generate→evaluate→classify→repair/fresh-start until terminal."""
        assembly = self.workspace.assemble(emit=self.ledger.assembly_done)
        worktree = assembly.worktree_path
        base_repo = assembly.base_repo
        target_rel = target_relpath(self.spec["deliverable"]["target"], base_repo)
        target_files = [os.path.basename(target_rel)]
        test_files = (self.spec.get("acceptance") or {}).get("test_files") or []
        baseline = assembly.baseline_failures

        stable = self._stable_prompt_parts(assembly)
        variable: Dict[str, str] = {}
        self._branch = assembly.branch
        prev_sha = assembly.c0_sha
        self._best_snapshot = prev_sha
        started_at = time.monotonic()

        for k in range(1, self.max_iterations + 1):
            if self._time_limit_reached(started_at):
                return self._exhausted(iterations_used=k - 1, limit_hit="timeout")
            if self.is_cancelled():
                self.ledger.cancelled({"stage": "looping", "iteration": k})
                return self._result_from(
                    "cancelled", self._best, iterations_used=k - 1, snapshot=self._best_snapshot
                )

            cheated, gen, snapshot = self._generate_with_snapshot(k, prev_sha, stable, target_rel, test_files, variable, worktree)
            prev_sha = snapshot
            if cheated:
                variable = self._record_cheat_and_feedback(k, gen, cheated)
                continue

            current = self.evaluate(worktree, base_repo, self.spec)
            attributable = attributable_failures(current, baseline, target_files, test_files)
            passed = not attributable
            self._emit_iteration_evaluated(k, passed, attributable)
            if passed:
                return self._result_from("delivered", gen, iterations_used=k, snapshot=snapshot)

            self._track_best(gen, attributable, snapshot)
            variable = self._steer_next_attempt(k, attributable, gen)

        return self._exhausted(iterations_used=self.max_iterations, limit_hit="exhausted")


def default_coder(num_predict: Optional[int] = None, timeout: int = 1800) -> CoderFn:
    """The real coder: one bounded `chat` call per iteration (T-91 num_predict).

    ``num_predict=None`` takes the NUM_PREDICT floor/cap default, so callers pass a
    budget value through unconditionally; ``timeout`` comes from ``spec.timeout_s``
    (wired by the worker, T-95). Built as a factory so the loop stays free of async/GPU
    concerns and tests inject a fake. Transport + cold-start grace are the worker's
    shared per-call helpers (T-95 decision (b)) — the loop emits NO Generation events
    by design; per-call telemetry lives in calls.jsonl, run_id-tagged (T-99).
    """
    num_predict = num_predict or NUM_PREDICT

    def _coder(prompt: str, model: str, run_id: str) -> GenerationResult:
        return _cold_start_grace(
            lambda: _chat_generation(
                prompt, model, run_id, timeout=timeout, num_predict=num_predict
            )
        )

    return _coder
