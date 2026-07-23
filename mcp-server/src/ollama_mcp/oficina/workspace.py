"""Per-run git-worktree workspace for the evaluated loop (P2-T4; P2-D5/D13).

One worktree per run, *reused* across iterations (not recreated per iteration): toolchain
incremental caches persist, and delta-scoped evaluation (S16/P2-D12) becomes a cheap git diff
between per-iteration snapshots in the same tree. The deliverable is a branch + diff report.

**Assembling** (P2-D13) is the ordered substep sequence:
``worktree add <base> on a run branch → detect mode → materialize/verify test_files → commit C0
→ evaluate C0 → build the stable prompt prefix → AssemblyDone``. What C0 contains is
**mode-dependent** (E-D2): in a **greenfield** run the target is absent, so C0 excludes the
deliverable and the delta-scope baseline (P2-D12) and anti-cheat (any iteration touching a
test_file, T5) are free; in an **edit** run the target is already committed at HEAD, so it is
present at C0 (its content becomes the ``current_file`` stable part and the compile stage runs on
it at baseline). The mode is the target's presence at HEAD in the checkout — no spec field; a
target on disk but NOT at HEAD is a fail-loud ``AssemblyError`` (E-D2a: the model can't see
uncommitted WIP). The tests are always pinned by C0 regardless of mode.

**Teardown** removes the worktree AND prunes the target's worktree registry — P2-D5's advisor
note: retention's ``rm -rf`` of the workspace dir would otherwise leave a dangling
``.git/worktrees/<id>`` entry in the target repo, accumulating one per run.

Evaluation is an INJECTED seam (``EvaluateFn``, mirroring P1's ``start_time_reader``/``generate``)
so assembling is testable without running real validators/pytest; the worker passes the real
evaluator (T5) in.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .errors import TriadError
from .parser import ParsedFailure

# (worktree_path, base_repo, spec) -> failures observed in the current worktree state.
# base_repo is needed to map the target's repo-relative path into the worktree.
EvaluateFn = Callable[[Path, Path, Dict[str, Any]], List[ParsedFailure]]

# Commit identity for oficina's own snapshots — never depends on the host's git config
# (tests and CI may have none).
_GIT_IDENTITY = ["-c", "user.email=oficina@localhost", "-c", "user.name=oficina"]


class AssemblyError(TriadError):
    """An assembling failure; ``whose`` defaults to the payload (a bad spec, not the system)."""

    def __init__(self, where: str, what: str, whose: str = "payload") -> None:
        super().__init__(where, what, whose)


@dataclass
class Assembly:
    """The result of assembling — everything the loop needs to start iterating."""

    worktree_path: Path
    base_repo: Path
    branch: str
    c0_sha: str
    baseline_failures: List[ParsedFailure]
    stable_parts: Dict[str, str]
    test_files_materialized: List[str] = field(default_factory=list)
    mode: str = "greenfield"  # "edit" when the target is committed at HEAD (E-D2), else greenfield


def target_relpath(target: str, base_repo: "Path | str") -> str:
    """The target's path relative to the repo top-level, canonicalizing BOTH sides.

    base_repo is git's PHYSICAL top-level, so a symlink-spelled target (e.g. ~/workspaces →
    /mnt/i/workspaces on this host) would otherwise relpath to a '../..'-escaping path.
    The loop's write side and the evaluator's compile side both use this ONE mapping so
    they can never disagree about which worktree file is the target.
    """
    return os.path.relpath(os.path.realpath(target), os.path.realpath(str(base_repo)))


def _git(repo: Path, *args: str) -> str:
    """Run ``git -C <repo> <args>`` and return stdout (stripped); raise on nonzero."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssemblyError(
            "assembling",
            f"git {' '.join(args)} failed: {result.stderr.strip()}",
            whose="system",
        )
    return result.stdout.strip()


class Workspace:
    """A run's git worktree — assemble, snapshot each iteration, tear down."""

    def __init__(
        self,
        spec: Dict[str, Any],
        run_id: str,
        run_dir: Path,
        evaluate: EvaluateFn,
    ) -> None:
        self.spec = spec
        self.run_id = run_id
        self.run_dir = Path(run_dir)
        self._evaluate = evaluate
        self.worktree_path = self.run_dir / "worktree"
        self.branch = f"oficina-run-{run_id}"
        self._base_repo: Optional[Path] = None

    # --- lifecycle ----------------------------------------------------------

    def assemble(self, emit: Optional[Callable[[Dict[str, Any]], Any]] = None) -> Assembly:
        """Build the worktree + C0 baseline; optionally emit AssemblyDone via ``emit``."""
        base_repo = self._resolve_base_repo()
        self._add_worktree(base_repo)
        # Fail fast on the uncommitted-target guard (E-D2a) before C0/evaluate do any work.
        mode, current_file = self._detect_mode(base_repo)
        materialized = self._materialize_test_files()
        c0_sha = self._commit(f"oficina C0 baseline ({self.run_id})")
        baseline_failures = self._evaluate(self.worktree_path, base_repo, self.spec)
        stable_parts = self._build_stable_parts(current_file)

        assembly = Assembly(
            worktree_path=self.worktree_path,
            base_repo=base_repo,
            branch=self.branch,
            c0_sha=c0_sha,
            baseline_failures=baseline_failures,
            stable_parts=stable_parts,
            test_files_materialized=materialized,
            mode=mode,
        )
        if emit is not None:
            emit(
                {
                    "worktree_path": str(self.worktree_path),
                    "base_commit": c0_sha,
                    "test_files_materialized": materialized,
                    "baseline_failure_count": len(baseline_failures),
                    "mode": mode,
                }
            )
        return assembly

    def snapshot(self, message: str) -> str:
        """Commit the current worktree state on the run branch; return the commit sha.

        One per iteration — powers the delta-scope diff (T5) and crash forensics.
        """
        return self._commit(message)

    def teardown(self) -> None:
        """Remove the worktree and prune the target's worktree registry (P2-D5).

        Idempotent and best-effort: a missing worktree is not an error. The run branch
        is intentionally LEFT — it is the deliverable (S15).
        """
        base_repo = self._base_repo or self._resolve_base_repo(strict=False)
        if base_repo is None:
            return
        subprocess.run(
            ["git", "-C", str(base_repo), "worktree", "remove", "--force", str(self.worktree_path)],
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(base_repo), "worktree", "prune"],
            capture_output=True,
            text=True,
        )

    # --- internals ----------------------------------------------------------

    def _resolve_base_repo(self, strict: bool = True) -> Optional[Path]:
        """The git top-level containing the deliverable target."""
        if self._base_repo is not None:
            return self._base_repo
        target = (self.spec.get("deliverable") or {}).get("target")
        start = Path(target).parent if target else Path.cwd()
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            if strict:
                raise AssemblyError("assembling", f"target is not inside a git repo: {target!r}")
            return None
        self._base_repo = Path(result.stdout.strip())
        return self._base_repo

    def _add_worktree(self, base_repo: Path) -> None:
        """Create the run worktree on a fresh run branch from HEAD."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        _git(base_repo, "worktree", "add", "-b", self.branch, str(self.worktree_path), "HEAD")

    def _detect_mode(self, base_repo: Path) -> tuple[str, str]:
        """Classify the run as ``edit`` or ``greenfield`` and return ``(mode, current_file)`` (E-D2).

        The discriminator is target presence at HEAD in the freshly-checked-out worktree — no
        spec field. ``current_file`` is the target's RAW committed content (returned verbatim so
        the model sees the file exactly), and is ``""`` for greenfield. Contract:
        - target committed with content  → ``("edit", <raw content>)``;
        - target committed but empty     → greenfield (nothing to preserve, E-D2b);
        - target absent from disk        → greenfield (today's from-scratch generation);
        - target on disk but NOT at HEAD → ``AssemblyError`` (E-D2a): the worktree checks out
          HEAD, so the model cannot see uncommitted WIP; silent greenfield would generate
          against an invisible file and collide with it on delivery.
        """
        target = self.spec.get("deliverable", {}).get("target")
        if not target:
            return ("greenfield", "")
        relpath = target_relpath(target, base_repo)
        worktree_target_path = self.worktree_path / relpath
        if worktree_target_path.exists():
            content = worktree_target_path.read_text(encoding="utf-8")
            return ("edit", content) if content.strip() else ("greenfield", "")
        if (base_repo / target).exists():
            raise AssemblyError(
                "assembling",
                f"target {target!r} exists on disk but is not committed at HEAD — "
                "commit it to edit it, or point at a new path for greenfield",
            )
        return ("greenfield", "")

    def _materialize_test_files(self) -> List[str]:
        """Guarantee every declared test_file exists in the worktree (P2-D13).

        First slice: tests are committed in the target repo, so the worktree checkout
        already carries them — we verify presence. A declared-but-absent test_file is an
        assembling failure (there is no content source to author from in the v1 schema).
        """
        test_files = ((self.spec.get("acceptance") or {}).get("test_files")) or []
        materialized: List[str] = []
        for rel in test_files:
            if not (self.worktree_path / rel).exists():
                raise AssemblyError(
                    "assembling",
                    f"declared test_file not present in worktree: {rel}",
                )
            materialized.append(rel)
        return materialized

    def _commit(self, message: str) -> str:
        """Stage everything in the worktree and commit (allow-empty); return the sha."""
        _git(self.worktree_path, "add", "-A")
        _git(self.worktree_path, *_GIT_IDENTITY, "commit", "--allow-empty", "-m", message)
        return _git(self.worktree_path, "rev-parse", "HEAD")

    def _build_stable_parts(self, current_file: str = "") -> Dict[str, str]:
        """The run-constant prompt parts (P2-D2): objective, tests-as-context, context files.

        System/constraints/refs are layered on in T6; this fills the parts that come from
        the assembled worktree. Tests are read from the worktree (dual role: on disk for
        test_cmd, in the prompt as acceptance context — P2-D13); ``_materialize_test_files``
        has already guaranteed each declared test exists. Context files render through the
        server's ``_build_context_block`` — the same block the single-shot path feeds the
        model, so the two paths cannot drift on context formatting. In edit mode
        ``current_file`` carries the target's committed content (E-D3); it is run-constant
        (the C0 content) and so belongs in the stable prefix — omitted when empty (greenfield).
        """
        parts: Dict[str, str] = {"objective": self.spec.get("objective", "") or ""}
        if current_file:
            parts["current_file"] = current_file

        test_files = ((self.spec.get("acceptance") or {}).get("test_files")) or []
        test_blocks = [
            f"# {rel}\n{(self.worktree_path / rel).read_text(encoding='utf-8')}"
            for rel in test_files
        ]
        if test_blocks:
            parts["tests"] = "\n\n".join(test_blocks)

        context_files = ((self.spec.get("context") or {}).get("files")) or []
        if context_files:
            from ollama_mcp import server as srv  # lazy, mirrors worker._build_prompt

            parts["context"] = srv._build_context_block(
                [srv.ContextFile(path=str(Path(f).resolve())) for f in context_files]
            )

        return parts
