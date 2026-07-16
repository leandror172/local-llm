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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .evaluator import attribute, diff_touches_test_files
from .parser import ParsedFailure, category_for
from .prompt import build_prompt
from .workspace import Workspace
from .worker import GenerationResult

# (prompt, model, run_id) -> GenerationResult. The coder writes nothing; the loop places output.
CoderFn = Callable[[str, str, str], GenerationResult]

# First slice defaults (P2-D1): single Python persona, bounded generation (T-91 / P2-D10).
DEFAULT_CODER_MODEL = "my-python-q25c14"
NUM_PREDICT = 2048  # floored so a function is never truncated; capped to bound runaway

_SYSTEM = "You are a precise Python engineer. Implement the objective so every provided test passes."
_CONSTRAINTS = (
    "CONSTRAINTS:\n"
    "- Implement ONLY the objective; do not modify the tests.\n"
    "- One responsibility per function; name functions after what they return or do.\n"
    "- Return the complete file content, no markdown fences."
)


@dataclass
class LoopResult:
    """Outcome of the loop — what the worker (T7) turns into Delivered or Exhausted."""

    outcome: str  # "delivered" | "exhausted"
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
        budgets = spec.get("budgets") or {}
        self.max_iterations = budgets.get("iterations", 3)
        self.max_fresh_starts = budgets.get("fresh_starts", 1)
        self.model = spec.get("model") or "auto"
        if self.model == "auto":
            self.model = DEFAULT_CODER_MODEL

    def run(self) -> LoopResult:
        """Assemble, then iterate generate→evaluate→classify→repair/fresh-start until terminal."""
        assembly = self.workspace.assemble(emit=self.ledger.assembly_done)
        worktree = assembly.worktree_path
        base_repo = assembly.base_repo
        target = self.spec["deliverable"]["target"]
        target_rel = os.path.relpath(target, base_repo)
        target_files = [os.path.basename(target_rel)]
        test_files = (self.spec.get("acceptance") or {}).get("test_files") or []
        baseline = assembly.baseline_failures

        stable = {"system": _SYSTEM, "constraints": _CONSTRAINTS, **assembly.stable_parts}
        if self.refs_block:
            # refs are context: prepend them so docs/diagrams come before file context (P2-D2).
            stable["context"] = "\n\n".join(
                p for p in (self.refs_block, stable.get("context", "")) if p
            )
        variable: Dict[str, str] = {}
        signatures_seen: set = set()
        fresh_used = 0
        prev_sha = assembly.c0_sha
        best: Optional[GenerationResult] = None
        best_failures = None
        best_snapshot = prev_sha

        for k in range(1, self.max_iterations + 1):
            if self.is_cancelled():
                self.ledger.cancelled({"stage": "looping", "iteration": k})
                return LoopResult(
                    outcome="cancelled",
                    content=best.content if best else "",
                    model=best.model if best else self.model,
                    eval_count=best.eval_count if best else 0,
                    duration_ms=best.duration_ms if best else 0.0,
                    iterations_used=k - 1,
                    branch=assembly.branch,
                    best_snapshot=best_snapshot,
                )

            self.ledger.iteration_started(
                {
                    "iteration": k,
                    "tier": 1,
                    "budget_remaining": {
                        "iterations": self.max_iterations - k,
                        "fresh_starts": self.max_fresh_starts - fresh_used,
                    },
                }
            )

            prompt = build_prompt({**stable, **variable})
            gen = self.coder(prompt, self.model, self.run_id)
            target_path = worktree / target_rel
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(gen.content, encoding="utf-8")
            snapshot = self.workspace.snapshot(f"oficina iteration {k} ({self.run_id})")

            cheated = diff_touches_test_files(worktree, prev_sha, snapshot, test_files)
            prev_sha = snapshot
            if cheated:
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
                variable = {
                    "repair_feedback": f"You edited the tests ({', '.join(cheated)}). Never modify the tests; implement the target only.",
                    "previous_attempt": gen.content,
                }
                continue

            current = self.evaluate(worktree, base_repo, self.spec)
            attributable = attribute(current, baseline, target_files, test_files)
            passed = not attributable

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

            if passed:
                return LoopResult(
                    outcome="delivered",
                    content=gen.content,
                    model=gen.model,
                    eval_count=gen.eval_count,
                    duration_ms=gen.duration_ms,
                    iterations_used=k,
                    branch=assembly.branch,
                    best_snapshot=snapshot,
                )

            if best_failures is None or len(attributable) < best_failures:
                best, best_failures, best_snapshot = gen, len(attributable), snapshot

            signature = _signature(attributable)
            if signature in signatures_seen and fresh_used < self.max_fresh_starts:
                fresh_used += 1
                self.ledger.fresh_start(
                    {"iteration": k, "signature": list(signature), "reason": "repetition"}
                )
                variable = {}  # drop the tail; keep the stable prefix (P2-D7)
                continue

            signatures_seen.add(signature)
            variable = {
                "repair_feedback": _repair_feedback(attributable),
                "previous_attempt": gen.content,
            }

        spent = {"iterations": self.max_iterations, "fresh_starts": fresh_used}
        self.ledger.exhausted(
            {"spent": spent, "limit_hit": "exhausted", "best_attempt_ref": best_snapshot}
        )
        return LoopResult(
            outcome="exhausted",
            content=best.content if best else "",
            model=best.model if best else self.model,
            eval_count=best.eval_count if best else 0,
            duration_ms=best.duration_ms if best else 0.0,
            iterations_used=self.max_iterations,
            branch=assembly.branch,
            best_snapshot=best_snapshot,
            limit_hit="exhausted",
            spent=spent,
        )


def default_coder(num_predict: int = NUM_PREDICT, timeout: int = 1800) -> CoderFn:
    """The real coder: one bounded `chat` call per iteration (T-91 num_predict).

    Built as a factory so the loop stays free of async/GPU concerns and tests inject a fake.
    """

    def _coder(prompt: str, model: str, run_id: str) -> GenerationResult:
        import asyncio

        from ollama_mcp import server as srv
        from ollama_mcp.client import OllamaClient

        async def _call() -> Any:
            client = OllamaClient()
            try:
                return await client.chat(
                    prompt=prompt,
                    model=model,
                    think=False,
                    timeout=timeout,
                    run_id=run_id,
                    num_predict=num_predict,
                )
            finally:
                await client.close()

        resp = asyncio.run(_call())
        content = srv._strip_code_fences(resp.content)
        return GenerationResult(
            content=content,
            model=resp.model,
            eval_count=resp.eval_count,
            duration_ms=resp.total_duration_ms,
        )

    return _coder
