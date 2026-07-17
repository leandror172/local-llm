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
            )
        finally:
            await client.close()

    resp = asyncio.run(_call())
    content = srv._strip_code_fences(resp.content) if strip_fences else resp.content
    return GenerationResult(
        content=content, model=resp.model,
        eval_count=resp.eval_count, duration_ms=resp.total_duration_ms,
    )


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

    def _resolve_refs_block(self, spec: Dict[str, Any]) -> str:
        """Resolve context.refs into a <refs> block (P2 carried-from-P1). Fail-open.

        This is the seam a run spec uses to inject docs — including a mermaid diagram anchor
        (T-93) — into the loop's stable prompt prefix at zero token cost.
        """
        refs = (spec.get("context") or {}).get("refs") or []
        if not refs:
            return ""
        import asyncio

        from ollama_mcp.server import _build_refs_block

        try:
            block = asyncio.run(_build_refs_block(refs, None))
        except Exception:  # noqa: BLE001 — refs are best-effort context, never fatal
            return ""
        return "" if block.startswith("Error:") else block

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
            refs_block=self._resolve_refs_block(spec),
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
            }
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
