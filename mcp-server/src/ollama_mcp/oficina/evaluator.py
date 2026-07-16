"""Evaluation + delta-scoped attribution for the evaluated loop (P2-T5; P2-D8/D12/D13).

Two responsibilities:

1. **Evaluate** (the real ``EvaluateFn``): run the deliverable through evaluation stages IN
   ORDER (P2-D8) inside the worktree — compile (``validate-code.py``, whose JSON T1 parses)
   then test (``test_cmd``, whose pytest output T1 parses) — and return the failures of the
   first failing stage. First slice: Python only.

2. **Attribute** (delta-scoping, P2-D12 — sharpened post-freeze by the advisor): reduce a
   raw failure set to the failures *this iteration is responsible for*. The rule is NOT blanket
   ``current − baseline``: a current failure is subtracted **only if it is OUT of scope** (in
   neither the target nor a test file) **and** it matches a baseline (C0) failure — i.e. a
   pre-existing environmental wart. **Failures in the target file, and ALL test outcomes, are
   never subtracted.** This is the guard against the masking hole: a misnamed/absent target
   produces an ``undefined foo`` failure that shares C0's baseline key, but it lands in the
   target or a test file (scope target/test), so it stays live and the loop can't declare
   success on broken code.

Anti-cheat (P2-D13): an iteration whose diff touches a declared ``test_file`` is editing the
acceptance criteria — ``diff_touches_test_files`` surfaces it so the loop rejects that iteration.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .parser import (
    SCOPE_OUT,
    STAGE_COMPILE,
    STAGE_TEST,
    ParsedFailure,
    parse_validator_output,
    scope_of,
)


class EvaluationError(Exception):
    """An evaluation failure carrying the where/whose/what triad for a Failed event."""

    def __init__(self, where: str, what: str, whose: str = "system") -> None:
        super().__init__(what)
        self.triad = {"where": where, "whose": whose, "what": what}


# --- delta-scoped attribution (P2-D12) --------------------------------------


def attribute(
    current: List[ParsedFailure],
    baseline: List[ParsedFailure],
    target_files: "list[str] | set[str]",
    test_files: "list[str] | set[str]",
) -> List[ParsedFailure]:
    """Return the failures attributable to this iteration (P2-D12).

    Subtract a current failure ONLY when it is out-of-scope AND its error_key appears in the
    out-of-scope baseline failures. In-scope failures (target file, any test outcome) are
    always live signal.
    """
    baseline_out_keys = {
        failure.error_key
        for failure in baseline
        if scope_of(failure.file, target_files, test_files) == SCOPE_OUT
    }
    return [
        failure
        for failure in current
        if not (
            scope_of(failure.file, target_files, test_files) == SCOPE_OUT
            and failure.error_key in baseline_out_keys
        )
    ]


def diff_touches_test_files(
    worktree: Path,
    from_ref: str,
    to_ref: str,
    test_files: "list[str] | set[str]",
) -> List[str]:
    """The declared test_files whose contents changed between two commits (anti-cheat).

    A non-empty result means the iteration edited the acceptance criteria (P2-D13) — the loop
    must reject that iteration rather than accept a test-run it rigged. Comparison is by
    basename so path spellings agree.
    """
    result = subprocess.run(
        ["git", "-C", str(worktree), "diff", "--name-only", from_ref, to_ref],
        capture_output=True,
        text=True,
    )
    changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    test_basenames = {os.path.basename(t) for t in test_files}
    return [path for path in changed if os.path.basename(path) in test_basenames]


# --- evaluation (the real EvaluateFn) ---------------------------------------


def _validate_code_script() -> str:
    """Resolve the validate-code wrapper: ``OFICINA_VALIDATE_CODE`` env, else repo-relative."""
    override = os.environ.get("OFICINA_VALIDATE_CODE")
    if override:
        return override
    repo_root = Path(__file__).resolve().parents[4]
    return str(repo_root / "benchmarks" / "lib" / "run-validate-code.sh")


# A single evaluation subprocess (compile or one test run) may never outlast this many
# seconds — a generated ``while True`` executed by pytest, or a wedged validator, must not
# hang the worker (and the FIFO behind it) forever. Bounded here, per-invocation; the loop's
# whole-run ``budgets.wall_clock_s`` is the coarser envelope. On expiry the stage raises
# EvaluationError (a system/loop failure, NOT a code defect that flows through delta-scoping).
_STAGE_TIMEOUT_S = 900


def _run_compile_stage(target_in_worktree: Path, timeout_s: int) -> List[ParsedFailure]:
    """Run the compile validator on the target and parse its JSON (T1)."""
    script = _validate_code_script()
    try:
        result = subprocess.run(
            [script, "--quiet", str(target_in_worktree)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise EvaluationError("compile", f"compile validator exceeded {timeout_s}s")
    if result.returncode == 2:
        raise EvaluationError("compile", f"validator tool error: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    return parse_validator_output(STAGE_COMPILE, payload)


def _run_test_stage(worktree: Path, test_cmd: str, timeout_s: int) -> List[ParsedFailure]:
    """Run test_cmd in the worktree and parse the pytest short summary (T1).

    Distinguishes "tests ran and some failed" from "the test command could not run":
    a non-zero exit with NO parseable short-summary failures (pytest missing → rc 127,
    a usage/collection error printed as ``ERROR: ...`` outside the summary block, a crash)
    is a tooling failure and raises EvaluationError. Without this, an un-parseable failure
    reads as zero failures → the loop would declare success on code whose tests never ran.
    """
    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise EvaluationError("test", f"test command exceeded {timeout_s}s: {test_cmd!r}")
    combined = f"{result.stdout}\n{result.stderr}"
    failures = parse_validator_output(STAGE_TEST, combined)
    if not failures and result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip()[-300:]
        raise EvaluationError(
            "test",
            f"test command produced no parseable result (rc={result.returncode}): {tail}",
        )
    return failures


def evaluate(worktree: Path, base_repo: Path, spec: Dict[str, Any]) -> List[ParsedFailure]:
    """The real ``EvaluateFn``: stage-ordered evaluation, first failing stage wins (P2-D8).

    Compile runs only when the target exists in the worktree (at C0 the deliverable is absent,
    so evaluation goes straight to the test stage, which surfaces the import/undefined failure).
    """
    target = (spec.get("deliverable") or {}).get("target")
    acceptance = spec.get("acceptance") or {}
    timeout_s = (spec.get("budgets") or {}).get("wall_clock_s") or _STAGE_TIMEOUT_S

    if target:
        rel = os.path.relpath(os.path.realpath(target), os.path.realpath(base_repo))
        target_in_worktree = Path(worktree) / rel
        if target_in_worktree.exists():
            compile_failures = _run_compile_stage(target_in_worktree, timeout_s)
            if compile_failures:
                return compile_failures

    test_cmd = acceptance.get("test_cmd")
    if not test_cmd:
        return []
    return _run_test_stage(Path(worktree), test_cmd, timeout_s)
