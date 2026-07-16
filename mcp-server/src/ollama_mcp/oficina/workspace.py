"""Per-run git-worktree workspace for the evaluated loop (P2-T4; P2-D5/D13).

One worktree per run, *reused* across iterations (not recreated per iteration): toolchain
incremental caches persist, and delta-scoped evaluation (S16/P2-D12) becomes a cheap git diff
between per-iteration snapshots in the same tree. The deliverable is a branch + diff report.

**Assembling** (P2-D13) is the ordered substep sequence:
``worktree add <base> on a run branch → materialize/verify test_files → commit C0 (deliverable
ABSENT) → evaluate C0 → build the stable prompt prefix → AssemblyDone``. C0 pins the tests and
excludes the deliverable, which is what makes both the delta-scope baseline (P2-D12) and the
anti-cheat check (any iteration touching a test_file, T5) free.

**Teardown** removes the worktree AND prunes the target's worktree registry — P2-D5's advisor
note: retention's ``rm -rf`` of the workspace dir would otherwise leave a dangling
``.git/worktrees/<id>`` entry in the target repo, accumulating one per run.

Evaluation is an INJECTED seam (``EvaluateFn``, mirroring P1's ``start_time_reader``/``generate``)
so assembling is testable without running real validators/pytest; the worker passes the real
evaluator (T5) in.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .parser import ParsedFailure

# (worktree_path, spec) -> failures observed in the current worktree state.
EvaluateFn = Callable[[Path, Dict[str, Any]], List[ParsedFailure]]

# Commit identity for oficina's own snapshots — never depends on the host's git config
# (tests and CI may have none).
_GIT_IDENTITY = ["-c", "user.email=oficina@localhost", "-c", "user.name=oficina"]


class AssemblyError(Exception):
    """An assembling failure carrying the where/whose/what triad for a Failed event."""

    def __init__(self, where: str, what: str, whose: str = "payload") -> None:
        super().__init__(what)
        self.triad = {"where": where, "whose": whose, "what": what}


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
        materialized = self._materialize_test_files()
        c0_sha = self._commit(f"oficina C0 baseline ({self.run_id})")
        baseline_failures = self._evaluate(self.worktree_path, self.spec)
        stable_parts = self._build_stable_parts()

        assembly = Assembly(
            worktree_path=self.worktree_path,
            base_repo=base_repo,
            branch=self.branch,
            c0_sha=c0_sha,
            baseline_failures=baseline_failures,
            stable_parts=stable_parts,
            test_files_materialized=materialized,
        )
        if emit is not None:
            emit(
                {
                    "worktree_path": str(self.worktree_path),
                    "base_commit": c0_sha,
                    "test_files_materialized": materialized,
                    "baseline_failure_count": len(baseline_failures),
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

    def _build_stable_parts(self) -> Dict[str, str]:
        """The run-constant prompt parts (P2-D2): objective, tests-as-context, context files.

        System/constraints/refs are layered on in T6; this fills the parts that come from
        the assembled worktree. Tests are read from the worktree (dual role: on disk for
        test_cmd, in the prompt as acceptance context — P2-D13).
        """
        parts: Dict[str, str] = {"objective": self.spec.get("objective", "") or ""}

        test_files = ((self.spec.get("acceptance") or {}).get("test_files")) or []
        test_blocks = [
            f"# {rel}\n{(self.worktree_path / rel).read_text(encoding='utf-8')}"
            for rel in test_files
            if (self.worktree_path / rel).exists()
        ]
        if test_blocks:
            parts["tests"] = "\n\n".join(test_blocks)

        context_files = ((self.spec.get("context") or {}).get("files")) or []
        ctx_blocks = [
            f"# {path}\n{Path(path).read_text(encoding='utf-8')}"
            for path in context_files
            if Path(path).exists()
        ]
        if ctx_blocks:
            parts["context"] = "\n\n".join(ctx_blocks)

        return parts
