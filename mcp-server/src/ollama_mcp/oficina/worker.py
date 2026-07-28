"""oficina worker — main loop: pop → intake → generate → package → events (T6).

Lazy daemon (P1-D9): the worker's FIRST act is to claim the pidfile; if it loses
the double-spawn race it exits immediately. It runs a retention sweep, then drains
the FIFO one run at a time, emitting run events to each run's ledger and
WorkerStarted/WorkerStopped to the worker ledger, and exits when the queue empties.

Generation is an INJECTABLE seam (mirrors T5's start_time_reader): the default
builds its own OllamaClient and runs today's generate_code/ask_ollama semantics per
the deliverable profile (P1-D3), tagging every call in calls.jsonl with run_id
(acceptance #6). Tests inject a fake generate — no GPU, no async, fully sync.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ollama_mcp.client import OllamaTimeoutError

from .config import default_root, load_retention_config
from .fifo import Fifo
from .intake import LOOP_KINDS, check_intake
from .ledger import Ledger
from .retention import sweep
from .store import Store
from .workerproc import WorkerProc


@dataclass
class GenerationResult:
    """Outcome of one generation stage."""

    content: str
    model: str
    eval_count: int
    duration_ms: float
    # The identity of the underlying chat call, echoed from ChatResponse (P4-T3).
    # This is what makes the ledger↔calls.jsonl join identity-based: without it the
    # only shared key is run_id, which is per-RUN, so matching an iteration to the call
    # that produced it would be ORDER-based — the positional fallback T-105 banned
    # (and anti-cheat iterations record a verdict without an evaluation, so the
    # positions do not even line up). Defaulted so injected fakes stay valid.
    call_id: str = ""


GenerateFn = Callable[[Dict[str, Any], str], GenerationResult]


def worker_argv() -> list[str]:
    """The argv that spawns a detached worker process (used by submit + acceptance)."""
    return [sys.executable, "-m", "ollama_mcp.oficina.worker"]


def _failure_triad(stage: str, exc: Exception) -> Dict[str, Any]:
    """Build a where/whose/what triad for a Failed event."""
    model_faults = (OllamaTimeoutError,)
    whose = "model" if isinstance(exc, model_faults) else "system"
    return {"where": stage, "whose": whose, "what": f"{type(exc).__name__}: {exc}"}


def _resolve_model(spec: Dict[str, Any], kind: str, srv) -> str:
    """Pick the model: explicit spec.model, else a per-profile default."""
    model = spec.get("model", "auto")
    if model and model != "auto":
        return model
    return srv._DEFAULT_CODEGEN_MODEL if kind == "file" else srv.DEFAULT_MODEL


def _build_prompt(spec: Dict[str, Any], srv) -> str:
    """Objective, optionally prefixed with a server-side context-files block."""
    prompt = spec["objective"]
    files = (spec.get("context") or {}).get("files") or []
    if files:
        block = srv._build_context_block([srv.ContextFile(path=f) for f in files])
        prompt = f"{block}\n\n{prompt}"
    return prompt


def _cold_start_grace(call: Callable[[], GenerationResult]) -> GenerationResult:
    """Run ``call``, retrying ONCE on a cold-start timeout (conventions doc).

    A first-call timeout is usually the model loading into VRAM — the retry hits a warm
    model. The single shared spelling of the grace convention (T-95): the worker's
    ``GenerateFn`` seam and every loop iteration's coder call both route through it.
    """
    try:
        return call()
    except OllamaTimeoutError:
        return call()


def _chat_generation(
    prompt: str,
    model: str,
    run_id: str,
    *,
    timeout: int,
    num_predict: Optional[int] = None,
    strip_fences: bool = True,
    # P4-T5: the judge is the third caller of this one transport (T-95 — per-call transport
    # is ONE spelling). It is the only one that needs a system prompt and a response schema,
    # so both are opt-in seams rather than a second transport that would miss calls.jsonl.
    system: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> GenerationResult:
    """One Ollama chat call → ``GenerationResult`` — the shared generation transport (T-95).

    Owns the call convention for BOTH the single-shot default and the loop's per-iteration
    coder: client lifecycle, ``think=False``, ``run_id`` tagging (calls.jsonl), bounded
    ``num_predict`` (T-91), fence stripping. Deliberately emits NO events — the single-shot
    path narrates via GenerationStarted/Finished, the loop via IterationStarted/Evaluated,
    and per-call telemetry lives in calls.jsonl joined on run_id (T-99 decision (b)).
    """
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
                system=system,
                format=schema,
                # T-105: oficina does NOT route through the generate_code MCP tool —
                # this seam goes straight to the client, so it must self-attribute.
                # Verdicts for these are per-RUN (via run_result), not per-call.
                tool="oficina",
            )
        finally:
            await client.close()

    resp = asyncio.run(_call())
    content = srv._strip_code_fences(resp.content) if strip_fences else resp.content
    return GenerationResult(
        content=content, model=resp.model,
        eval_count=resp.eval_count, duration_ms=resp.total_duration_ms,
        call_id=resp.call_id,
    )


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


def model_context_limit(model: str) -> Optional[int]:
    """The model's effective context window in tokens, or None when undeterminable.

    The window is the ``num_ctx`` PARAMETER Ollama reports for the model. Absence is
    NOT "the architectural maximum" — the model would then run at Ollama's own unstated
    default — so an absent or unreadable value yields None rather than a guess: guessing
    high silently disables the caller's fit check, guessing low aborts valid work. Every
    failure (transport, status, shape, parse) lands on the same None channel; the ceiling
    is a value-or-absence, never a sentinel in the value channel (T-112).
    """
    descriptor = _fetch_model_descriptor(model)
    if not descriptor:
        return None
    return _num_ctx_from_parameters(descriptor.get("parameters", ""))


def _fetch_model_descriptor(model: str) -> Optional[Dict[str, Any]]:
    """The model's /api/show descriptor, or None if it cannot be retrieved."""
    import asyncio

    from ollama_mcp.client import OllamaClient

    async def _call() -> Any:
        client = OllamaClient()
        try:
            return await client.fetch_model_descriptor(model)
        finally:
            await client.close()

    try:
        return asyncio.run(_call())
    except Exception:  # noqa: BLE001 — an undeterminable ceiling is None, never a raise
        return None


def _num_ctx_from_parameters(parameters: str) -> Optional[int]:
    """Read ``num_ctx`` out of Ollama's ``name<whitespace>value`` parameter blob.

    The trailing space in the prefix match keeps a longer parameter that merely
    starts with the same letters from being mistaken for it.
    """
    for line in parameters.splitlines():
        if line.startswith("num_ctx "):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def _default_generate(spec: Dict[str, Any], run_id: str) -> GenerationResult:
    """Run one generation via the shared transport (imports server lazily)."""
    from ollama_mcp import server as srv

    kind = spec["deliverable"]["kind"]
    return _chat_generation(
        _build_prompt(spec, srv),
        _resolve_model(spec, kind, srv),
        run_id,
        timeout=spec.get("timeout_s", 1800),
        strip_fences=(kind == "file"),
    )


class Worker:
    """The detached run worker, rooted at ``root``."""

    def __init__(
        self,
        root: str | os.PathLike,
        generate: Optional[GenerateFn] = None,
        proc: Optional[WorkerProc] = None,
        loop_coder=None,
        loop_evaluate=None,
        loop_judge=None,
    ) -> None:
        self.root = Path(root)
        self.store = Store(root)
        self.fifo = Fifo(root)
        self.proc = proc or WorkerProc(root)
        self.worker_ledger = Ledger(self.root / "worker-events.jsonl")
        self._generate = generate or _default_generate
        # P2 loop seams (injected for tests); resolved to the real ones lazily in _run_loop.
        self._loop_coder = loop_coder
        self._loop_evaluate = loop_evaluate
        self._loop_judge = loop_judge

    def _run_ledger(self, run_id: str) -> Ledger:
        """The ledger for one run (the worker owns it post-queue-pop, P1-D6)."""
        return Ledger(self.store.events_path(run_id))

    def _is_cancelled(self, run_id: str) -> bool:
        """True if the cooperative cancel flag file has been written (P1-D6)."""
        return (self.store.run_dir(run_id) / "cancel").exists()

    def _generate_with_cold_start_grace(self, spec: Dict[str, Any], run_id: str) -> GenerationResult:
        """Run the GenerateFn seam through the shared cold-start grace (one retry)."""
        return _cold_start_grace(lambda: self._generate(spec, run_id))

    def _run_generation(self, ledger: Ledger, run_id: str, spec: Dict[str, Any]) -> Optional[GenerationResult]:
        """Emit GenerationStarted, run the seam, emit Finished; Failed on error."""
        ledger.generation_started({"model": spec.get("model", "auto")})
        try:
            gen = self._generate_with_cold_start_grace(spec, run_id)
        except Exception as exc:  # noqa: BLE001 — any stage error becomes a Failed event
            ledger.failed(_failure_triad("generation", exc))
            return None
        ledger.generation_finished(
            {"model": gen.model, "eval_count": gen.eval_count, "duration_ms": gen.duration_ms}
        )
        return gen

    def _package(self, ledger: Ledger, run_id: str, spec: Dict[str, Any], gen: GenerationResult) -> None:
        """Write the deliverable and emit Delivered (report lives in the payload)."""
        kind = spec["deliverable"]["kind"]
        if kind == "file":
            target = spec["deliverable"]["target"]
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_text(gen.content, encoding="utf-8")
            deliverable = {"kind": "file", "target": target}
        else:
            deliverable = {"kind": "answer", "answer": gen.content}
        report = {"model": gen.model, "eval_count": gen.eval_count, "chars": len(gen.content)}
        ledger.delivered({"report": report, "deliverable": deliverable})

    def _resolve_refs_block(self, spec: Dict[str, Any], run_id: str) -> str:
        """Resolve context.refs into a <refs> block (P2 carried-from-P1). Best-effort, fail-loud.

        This is the seam a run spec uses to inject docs — including a mermaid diagram anchor
        (T-93) — into the loop's stable prompt prefix at zero token cost. A failed resolution
        never fails the run, but is recorded as RefsDropped in the worker ledger (T-96) —
        the run must not silently lose the docs it asked for.
        """
        refs = (spec.get("context") or {}).get("refs") or []
        if not refs:
            return ""
        import asyncio

        from ollama_mcp.server import _build_refs_block

        try:
            block = asyncio.run(_build_refs_block(refs, None))
        except Exception as exc:  # noqa: BLE001 — refs are best-effort context, never fatal
            self._note_refs_dropped(run_id, refs, f"{type(exc).__name__}: {exc}")
            return ""
        if block.startswith("Error:"):
            self._note_refs_dropped(run_id, refs, block)
            return ""
        return block

    def _note_refs_dropped(self, run_id: str, refs: list, reason: str) -> None:
        """Record a requested-but-unresolved refs block in the worker ledger (T-96)."""
        self.worker_ledger.refs_dropped({"run_id": run_id, "refs": refs, "reason": reason})

    def _judge_delivered(
        self, ledger: Ledger, spec: Dict[str, Any], result: Any, run_id: str
    ) -> Dict[str, Any]:
        """Judge the packaged deliverable once (P4-D1), emit `Judged`, return the verdict.

        Opt-in: a spec without `acceptance.rubric` is delivered exactly as it was before P4.
        A failing verdict does NOT block `Delivered` — S17 gates DPO chosen labels, not
        delivery — and a judge that cannot run at all is reported, never raised, because by
        this point the deliverable already exists.
        """
        from .judge import judge_deliverable, load_rubric

        rubric_id = (spec.get("acceptance") or {}).get("rubric")
        if not rubric_id:
            return {}
        judge = self._loop_judge or default_judge(run_id)
        try:
            verdict = judge_deliverable(
                load_rubric(rubric_id), spec.get("objective", ""),
                result.change, result.drift, judge,
            )
        except Exception as exc:  # noqa: BLE001 — the gate reports, it does not fail the run
            verdict = {"rubric": rubric_id, "passed": False,
                       "judge_verdict": 0, "criteria": [],
                       "error": f"judge unavailable: {exc}"}
        ledger.judged(verdict)
        return verdict

    def _run_loop(self, ledger: Ledger, run_id: str, spec: Dict[str, Any]) -> None:
        """Run the evaluated loop (P2) for a code kind; emit terminal Delivered on success.

        The loop itself emits AssemblyDone / iteration events / Exhausted / Cancelled; the
        worker owns only the terminal Delivered (packaging) — the deliverable is the run branch,
        so packaging references it rather than writing the target. The workspace is always torn
        down (remove worktree + prune), keeping the branch.
        """
        from .errors import TriadError
        from .evaluator import evaluate as default_evaluate
        from .loop import EvaluatedLoop, default_coder
        from .workspace import Workspace

        num_predict = (spec.get("budgets") or {}).get("num_predict")
        coder = self._loop_coder or default_coder(
            num_predict=num_predict, timeout=spec.get("timeout_s", 1800)
        )
        evaluate = self._loop_evaluate or default_evaluate
        run_dir = self.store.run_dir(run_id) / "workspace"
        workspace = Workspace(spec, run_id, run_dir, evaluate)
        loop = EvaluatedLoop(
            spec, run_id, workspace, evaluate, coder, ledger,
            is_cancelled=lambda: self._is_cancelled(run_id),
            refs_block=self._resolve_refs_block(spec, run_id),
        )
        try:
            result = loop.run()
        except Exception as exc:  # noqa: BLE001 — any stage error becomes a Failed event
            # A TriadError (assembly OR evaluation) carries its own precise attribution.
            triad = exc.triad if isinstance(exc, TriadError) else _failure_triad("loop", exc)
            ledger.failed(triad)
            return
        finally:
            workspace.teardown()

        if result.outcome == "delivered":
            report = {
                "model": result.model,
                "iterations": result.iterations_used,
                "branch": result.branch,
                "commit": result.best_snapshot,
                # P4-D3: magnitude, measured for free. Numbers and ranges only — this payload
                # is paid for in Claude's context on every run_result (P4-D6), so the hunk list
                # is bounded; the loop's own `drift` keeps every range.
                "drift": _compact_drift(result.drift),
                # P4-T6: how the deliverable was reached, not just that it was.
                "iterations_trail": _iterations_trail(ledger),
            }
            judged = self._judge_delivered(ledger, spec, result, run_id)
            if judged:
                # The `Judged` event already holds the full verdict; the report gets the clipped
                # copy. Criteria entries are shortened, never dropped — they carry the cuts.
                report["judge"] = _compact_judge(judged)
            ledger.delivered(
                {
                    "report": report,
                    "deliverable": {
                        "kind": spec["deliverable"]["kind"],
                        "target": spec["deliverable"]["target"],
                        "branch": result.branch,
                        "commit": result.best_snapshot,
                    },
                }
            )
        # exhausted → Exhausted already emitted (folds to failed); cancelled → Cancelled emitted.

    def process_run(self, run_id: str) -> None:
        """Drive one run through intake → generate/loop → package, honoring cancel."""
        ledger = self._run_ledger(run_id)
        spec = self.store.load_spec(run_id)
        if self._is_cancelled(run_id):
            ledger.cancelled({"stage": "intake"})
            return
        result = check_intake(spec)
        if not result.accepted:
            ledger.intake_rejected(result.rejection.payload)
            return
        if self._is_cancelled(run_id):
            ledger.cancelled({"stage": "pre_generation"})
            return
        if spec["deliverable"]["kind"] in LOOP_KINDS:
            self._run_loop(ledger, run_id, spec)
            return
        gen = self._run_generation(ledger, run_id, spec)
        if gen is None:
            return
        if self._is_cancelled(run_id):
            ledger.cancelled({"stage": "pre_packaging"})
            return
        self._package(ledger, run_id, spec, gen)

    def run_once(self) -> Optional[str]:
        """Pop and process one run; return its id, or None if the queue is empty."""
        run_id = self.fifo.pop()
        if run_id is None:
            return None
        self.process_run(run_id)
        return run_id

    def run(self) -> None:
        """Claim the pidfile (FIRST act), sweep retention, drain the queue, exit."""
        if not self.proc.claim_pidfile():
            return  # lost the double-spawn race — a live worker already owns the store
        self.worker_ledger.worker_started({"pid": os.getpid()})
        try:
            sweep(self.store, self.worker_ledger, load_retention_config())
            while self.run_once() is not None:
                pass
        finally:
            self.worker_ledger.worker_stopped({"pid": os.getpid()})
            self.proc.pidfile.unlink(missing_ok=True)


def main() -> None:
    """Entry point for ``python -m ollama_mcp.oficina.worker``."""
    Worker(default_root()).run()


if __name__ == "__main__":
    main()
