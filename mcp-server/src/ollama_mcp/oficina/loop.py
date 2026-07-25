"""The evaluated coder⇄evaluator loop (P2-T6; P2-D1/D2/D4/D7/D10).

This is the value inflection of oficina: instead of P1's single shot, generate → evaluate
cheaply every iteration → classify the failure (rule-based, no model call — P2-D4) → repair
or fresh-start → budget out. The `function` kind is whole-file-against-pre-authored-tests,
Python, 3 iterations, one persona, no escalation ladder — **greenfield or edit** by whether the
target is committed at HEAD (E-D2, detected in ``workspace.assemble``); the loop consumes the
resulting ``Assembly.mode`` and treats both uniformly through the same whole-file write.

Collaborators are INJECTED (coder, evaluate, workspace, ledger) so the loop is unit-testable
with fakes — no GPU, no git required in the pure path. The worker (T7) wires the real ones.

Prompt layout obeys P2-D2 via ``build_prompt``: the stable parts (system/constraints/context/
current_file/tests/objective) are byte-identical every iteration; only ``repair_feedback``/
``previous_attempt`` vary, so the KV prefix is reused. Two parts are **mode-selected but still
run-constant**: the constraints variant (E-D4 — greenfield from-scratch vs edit preserve-the-rest)
and, in edit mode, ``current_file`` (the target's C0 content, E-D3). Fresh-start (P2-D7) drops the
variable tail but keeps the stable prefix.

Generation is bounded by ``num_predict`` (T-91): the sync path used to inherit the model default
and truncate functions mid-body. Greenfield floors/caps at ``NUM_PREDICT``; edit mode sizes the
budget to the current file (E-D9) so a whole-file rewrite of a large module is never truncated —
an explicit ``budgets.num_predict`` always wins. Resolved post-assembly, when the file size is known.

The input-fit guard (T-112) refuses a generation that cannot fit: Ollama's window holds the prompt
AND the generated tokens, and an overrun is NOT rejected — generation proceeds while the oldest
tokens are evicted, so the model silently loses the head of its own instructions.
"""

from __future__ import annotations

import difflib
import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .evaluator import LANGUAGES, attributable_failures, diff_touches_test_files
from .errors import ContextBudgetError
from .intake import Budgets, resolve_language
from .parser import ParsedFailure, category_for
from .prompt import build_prompt
from .workspace import Workspace, target_relpath
from .worker import GenerationResult, _chat_generation, _cold_start_grace, model_context_limit

# (prompt, model, run_id, *, num_predict) -> GenerationResult. The coder writes nothing; the
# loop places output. num_predict is passed per call (E-D9) because the edit-mode floor is only
# known post-assembly (file size); it is optional so trivial fakes may ignore it.
CoderFn = Callable[..., GenerationResult]

# First slice defaults (P2-D1): single Python persona, bounded generation (T-91 / P2-D10).
# Coder model + system line live in the per-language pack (T-92 Phase 4, in
# .evaluator — incl. the measured 16K-variant rationale). These aliases keep the
# established import surface (tests, non-loop fallbacks).
DEFAULT_CODER_MODEL = LANGUAGES["python"].coder_model
NUM_PREDICT = 2048  # floored so a function is never truncated; capped to bound runaway
EDIT_NUM_PREDICT_CAP = 8192  # E-D9 ceiling for the file-size-derived edit-mode floor
GREENFIELD_ITERATIONS = 3  # the P2 default iteration budget
EDIT_ITERATIONS = 1  # T-114: s127 (5/5) — iteration 1 lands ~90-95% and retries never saw their own residual; a reviewed edit run gets one shot

_SYSTEM = LANGUAGES["python"].system_prompt
# No leading "CONSTRAINTS:" label in either variant — prompt.SEGMENTS already prepends that header
# for the 'constraints' segment; embedding it again doubled the header in every prompt.
# Greenfield (E-D4): generate the file from scratch. Kept BYTE-IDENTICAL (pinned in a test).
_CONSTRAINTS = (
    "- Implement ONLY the objective; do not modify the tests.\n"
    "- One responsibility per function; name functions after what they return or do.\n"
    "- Return the complete file content, no markdown fences."
)
# Edit (E-D4): the CURRENT FILE segment carries the file being modified; preserve the rest.
_EDIT_CONSTRAINTS = (
    "- Modify the current file to meet the objective; do not modify the tests.\n"
    "- Preserve all code the objective does not require changing.\n"
    "- Return the complete updated file content, no markdown fences."
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


def _attempt_as_diff(baseline: str, attempt: str) -> str:
    """The coder's last attempt as a unified diff against the committed file (T-120).

    An edit-run prompt already carries the committed file as ``current_file``, so replaying the
    whole modified file would pay for that file twice in one prompt — and the whole-file write
    pays for it a third time on the way out."""
    return "".join(
        difflib.unified_diff(
            baseline.splitlines(keepends=True),
            attempt.splitlines(keepends=True),
            fromfile="the committed file",
            tofile="your last attempt",
            n=3,
        )
    )


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
        context_limit_for: Callable[[str], Optional[int]] = model_context_limit,
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
        # T-114: an explicit budgets.iterations ALWAYS wins; otherwise the effective max is
        # resolved post-assembly by mode (edit lands in 1, greenfield keeps 3), mirroring
        # _num_predict (E-D9). Provisional until run() knows the mode.
        self._explicit_iterations = budgets.iterations
        self.max_iterations = self._explicit_iterations or GREENFIELD_ITERATIONS
        self.max_fresh_starts = budgets.fresh_starts
        self.max_wall_clock_s = budgets.wall_clock_s
        # E-D9: an explicit budget ALWAYS wins; otherwise the effective num_predict is resolved
        # post-assembly (edit mode sizes to the current file). Set to the floor until run() knows.
        self._explicit_num_predict = budgets.num_predict
        self._num_predict = NUM_PREDICT
        # R1: language is resolved once (declared wins, else target extension);
        # None (no loop-language contract) falls back to the Python pack. The pack
        # supplies the language axis (coder model + system line, A1/Phase 4);
        # it composes with the mode axis (_CONSTRAINTS / _EDIT_CONSTRAINTS) —
        # both selections are run-constant, so the P2-D2 cache contract holds.
        self.language = resolve_language(spec.get("deliverable") or {}) or "python"
        self._pack = LANGUAGES.get(self.language, LANGUAGES["python"])
        self.model = spec.get("model") or "auto"
        if self.model == "auto":
            self.model = self._pack.coder_model
        # Loop-carried run state (one EvaluatedLoop instance == one run; set up by run()).
        self._branch = ""
        self._fresh_used = 0
        self._signatures_seen: set = set()
        self._best: Optional[GenerationResult] = None
        self._best_failures: Optional[int] = None
        self._best_snapshot: Optional[str] = None
        # T-112: the input-fit guard (context window).
        self.context_limit_for = context_limit_for
        self._context_limit = None
        # T-120: the committed target content on an edit run, None on greenfield. Set once at
        # assembly; the previous attempt is shown as a diff against it rather than in full.
        self._edit_baseline: Optional[str] = None

    def _stable_prompt_parts(self, assembly) -> Dict[str, str]:
        """The run-constant prompt parts (P2-D2): system + constraints + the assembled parts, with
        any pre-resolved refs block prepended to the context (docs/diagrams before file context).

        The constraints variant is selected by ``assembly.mode`` (E-D4): edit mode states the
        preservation contract, greenfield keeps today's from-scratch constraints. The system
        line is selected by ``self.language`` (A1) — both selections are run-constant, and the
        ordering is shared, so the cache holds.
        """
        constraints = _EDIT_CONSTRAINTS if assembly.mode == "edit" else _CONSTRAINTS
        parts = {
            "system": self._pack.system_prompt,
            "constraints": constraints,
            **assembly.stable_parts,
        }
        if self.refs_block:
            parts["context"] = "\n\n".join(
                p for p in (self.refs_block, parts.get("context", "")) if p
            )
        return parts

    def _resolve_num_predict(self, assembly) -> int:
        """The effective per-call generation budget (E-D9). An explicit ``budgets.num_predict``
        always wins. Otherwise greenfield keeps the NUM_PREDICT floor/cap; edit mode sizes to the
        current file — ``max(NUM_PREDICT, ceil(chars/4) * 2)`` capped at ``EDIT_NUM_PREDICT_CAP`` —
        so a whole-file rewrite is never truncated mid-file (the T-91 class one level up)."""
        if self._explicit_num_predict is not None:
            return self._explicit_num_predict
        if assembly.mode == "edit":
            current_file = assembly.stable_parts.get("current_file", "")
            derived = math.ceil(len(current_file) / 4) * 2
            return min(EDIT_NUM_PREDICT_CAP, max(NUM_PREDICT, derived))
        return NUM_PREDICT

    def _resolve_max_iterations(self, assembly) -> int:
        """The effective per-run iteration budget (T-114). An explicit ``budgets.iterations``
        always wins. Otherwise the mode decides: an ``edit`` run gets EDIT_ITERATIONS (s127:
        iteration 1 lands the fix and retries never saw their own residual); greenfield keeps
        GREENFIELD_ITERATIONS."""
        if self._explicit_iterations is not None:
            return self._explicit_iterations
        if assembly.mode == "edit":
            return EDIT_ITERATIONS
        return GREENFIELD_ITERATIONS

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
            "previous_attempt": self._previous_attempt_view(gen.content),
        }

    def _previous_attempt_view(self, content: str) -> str:
        """What the model is shown of its own last attempt (T-120).

        Greenfield replays the content, exactly as it always has. An edit run shows a diff
        against the committed file instead — the same information at a fraction of the tokens.
        An attempt identical to the baseline diffs to nothing, and an empty segment is dropped
        from the prompt entirely, so that signal is stated rather than allowed to vanish."""
        if self._edit_baseline is None:
            return content
        if content == self._edit_baseline:
            return "You returned the committed file unchanged — nothing was modified."
        return _attempt_as_diff(self._edit_baseline, content)

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
            "previous_attempt": self._previous_attempt_view(gen.content),
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

    def _generate_with_snapshot(self, k, prev_sha, prompt, target_rel, test_files, worktree) -> Any:
        # The prompt is built by the caller (T-112): the input-fit guard has to weigh the real
        # prompt before generating, and building it twice would be two sites to keep in sync.
        from ollama_mcp import server as srv  # lazy — compose the server's fence stripper (E-D5)

        self._emit_iteration_started(k)
        gen = self.coder(prompt, self.model, self.run_id, num_predict=self._num_predict)
        # The loop owns its write invariant (E-D5): strip fences here so a fenced response never
        # lands on disk to mislead the compile stage — regardless of what the injected coder returns.
        content = srv._strip_code_fences(gen.content)
        target_path = worktree / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        snapshot = self.workspace.snapshot(f"oficina iteration {k} ({self.run_id})")

        cheated = diff_touches_test_files(worktree, prev_sha, snapshot, test_files)
        return cheated, gen, snapshot

    def _context_overflow(self, prompt: str) -> Optional[str]:
        """Why this generation cannot fit the model's window, or None when it can (T-112).

        The window holds the prompt AND the generated tokens, so the resolved per-call budget
        is counted beside the prompt estimate. An unresolvable ceiling disables the guard —
        the caller was already told once, at resolve time."""
        if self._context_limit is None:
            return None
        estimated = math.ceil(len(prompt) / 4)
        if estimated + self._num_predict <= self._context_limit:
            return None
        return (
            f"prompt ~{estimated} tokens + generation budget {self._num_predict} "
            f"exceeds the model's {self._context_limit}-token context window"
        )

    def run(self) -> LoopResult:
        """Assemble, then iterate generate→evaluate→classify→repair/fresh-start until terminal."""
        assembly = self.workspace.assemble(emit=self.ledger.assembly_done)
        # E-D9: now that the mode and current-file size are known, fix the per-call generation budget.
        self._num_predict = self._resolve_num_predict(assembly)
        # T-114: with the mode known, fix the iteration budget (edit -> 1, greenfield -> 3).
        self.max_iterations = self._resolve_max_iterations(assembly)
        # T-120: remember the committed content (edit runs only) for the previous-attempt diff.
        self._edit_baseline = assembly.stable_parts.get("current_file") or None
        worktree = assembly.worktree_path
        base_repo = assembly.base_repo
        target_rel = target_relpath(self.spec["deliverable"]["target"], base_repo)
        target_files = [target_rel]
        test_files = (self.spec.get("acceptance") or {}).get("test_files") or []
        baseline = assembly.baseline_failures

        stable = self._stable_prompt_parts(assembly)
        variable: Dict[str, str] = {}
        self._branch = assembly.branch
        prev_sha = assembly.c0_sha
        self._best_snapshot = prev_sha
        started_at = time.monotonic()

        # T-112: resolve the window ONCE per run. An unresolvable ceiling is announced once,
        # here — not per iteration — so the guard's absence is on the record exactly one time.
        self._context_limit = self.context_limit_for(self.model)
        if self._context_limit is None:
            self.ledger.context_limit_unknown({"model": self.model})

        for k in range(1, self.max_iterations + 1):
            if self._time_limit_reached(started_at):
                return self._exhausted(iterations_used=k - 1, limit_hit="timeout")
            if self.is_cancelled():
                self.ledger.cancelled({"stage": "looping", "iteration": k})
                return self._result_from(
                    "cancelled", self._best, iterations_used=k - 1, snapshot=self._best_snapshot
                )

            # T-112: refuse before generating. Iteration 1 has nothing to salvage, so it is a
            # fail-loud triad; later iterations already hold a best attempt, so they exhaust.
            prompt = build_prompt({**stable, **variable})
            overflow = self._context_overflow(prompt)
            if overflow:
                if k == 1:
                    raise ContextBudgetError(overflow)
                return self._exhausted(iterations_used=k - 1, limit_hit="context_budget")

            cheated, gen, snapshot = self._generate_with_snapshot(k, prev_sha, prompt, target_rel, test_files, worktree)
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

    The construction-time ``num_predict`` is a FALLBACK (NUM_PREDICT floor/cap when None):
    the loop now owns per-call resolution (E-D9) and passes an effective value on every call,
    which wins — so the worker's construction-time ``num_predict=budgets.num_predict`` is inert
    on the loop path (an explicit budget wins inside ``_resolve_num_predict`` instead); only a
    direct 3-arg call (tests/legacy) sees the baked value. ``timeout`` comes from
    ``spec.timeout_s`` (wired by the worker, T-95).
    Built as a factory so the loop stays free of async/GPU concerns and tests inject a fake.
    Transport + cold-start grace are the worker's shared per-call helpers (T-95 decision (b)) —
    the loop emits NO Generation events; per-call telemetry lives in calls.jsonl, run_id-tagged.
    """
    baked = num_predict or NUM_PREDICT

    def _coder(prompt: str, model: str, run_id: str, num_predict: Optional[int] = None) -> GenerationResult:
        effective = num_predict if num_predict is not None else baked
        return _cold_start_grace(
            lambda: _chat_generation(
                prompt, model, run_id, timeout=timeout, num_predict=effective
            )
        )

    return _coder
