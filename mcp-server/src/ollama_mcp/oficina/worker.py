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
from .intake import check_intake
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


def _default_generate(spec: Dict[str, Any], run_id: str) -> GenerationResult:
    """Run one generation via the real OllamaClient (imports server lazily)."""
    import asyncio

    from ollama_mcp import server as srv
    from ollama_mcp.client import OllamaClient
    from ollama_mcp.config import DEFAULT_MODEL  # noqa: F401 (kept for parity)

    kind = spec["deliverable"]["kind"]
    prompt = _build_prompt(spec, srv)
    model = _resolve_model(spec, kind, srv)

    async def _call() -> Any:
        client = OllamaClient()
        try:
            return await client.chat(
                prompt=prompt, model=model, think=False,
                timeout=spec.get("timeout_s", 1800), run_id=run_id,
            )
        finally:
            await client.close()

    resp = asyncio.run(_call())
    content = srv._strip_code_fences(resp.content) if kind == "file" else resp.content
    return GenerationResult(
        content=content, model=resp.model,
        eval_count=resp.eval_count, duration_ms=resp.total_duration_ms,
    )


class Worker:
    """The detached run worker, rooted at ``root``."""

    def __init__(
        self,
        root: str | os.PathLike,
        generate: Optional[GenerateFn] = None,
        proc: Optional[WorkerProc] = None,
    ) -> None:
        self.root = Path(root)
        self.store = Store(root)
        self.fifo = Fifo(root)
        self.proc = proc or WorkerProc(root)
        self.worker_ledger = Ledger(self.root / "worker-events.jsonl")
        self._generate = generate or _default_generate

    def _run_ledger(self, run_id: str) -> Ledger:
        """The ledger for one run (the worker owns it post-queue-pop, P1-D6)."""
        return Ledger(self.store.events_path(run_id))

    def _is_cancelled(self, run_id: str) -> bool:
        """True if the cooperative cancel flag file has been written (P1-D6)."""
        return (self.store.run_dir(run_id) / "cancel").exists()

    def _generate_with_cold_start_grace(self, spec: Dict[str, Any], run_id: str) -> GenerationResult:
        """Generate, retrying ONCE on a cold-start timeout (conventions doc)."""
        try:
            return self._generate(spec, run_id)
        except OllamaTimeoutError:
            return self._generate(spec, run_id)

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

    def process_run(self, run_id: str) -> None:
        """Drive one run through intake → generate → package, honoring cancel."""
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
