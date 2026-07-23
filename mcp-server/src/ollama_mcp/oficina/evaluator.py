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
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List

from .errors import TriadError
from .intake import resolve_language
from .parser import (
    SCOPE_OUT,
    STAGE_COMPILE,
    STAGE_TEST,
    ParsedFailure,
    _parse_go_build,
    _parse_gotest,
    parse_validator_output,
    scope_of,
)
from .workspace import target_relpath


class EvaluationError(TriadError):
    """An evaluation failure (validator tooling / hung stage); ``whose`` defaults to system."""


# --- delta-scoped attribution (P2-D12) --------------------------------------


def attributable_failures(
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
    normalized worktree-relative path (T-98): git emits that spelling, and declared
    test_files use it — basename matching made a target named like a test file
    (``src/test_utils.py`` vs ``tests/test_utils.py``) fire anti-cheat on its own writes.
    """
    if not test_files:
        return []  # nothing declared → nothing to diff; skip the subprocess entirely
    result = subprocess.run(
        ["git", "-C", str(worktree), "diff", "--name-only", from_ref, to_ref],
        capture_output=True,
        text=True,
    )
    changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    declared = {os.path.normpath(t) for t in test_files}
    return [path for path in changed if os.path.normpath(path) in declared]


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


def _run_compile_stage(
    target_in_worktree: Path, target_rel: str, timeout_s: int
) -> List[ParsedFailure]:
    """Run the compile validator on the target and parse its JSON (T1).

    Failures are stamped with ``target_rel`` (T-98): only the target is ever
    compiled, so the worktree-relative spelling is known here — the validator's
    own ``file`` field is not canonical.
    """
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
    failures = parse_validator_output(STAGE_COMPILE, payload)
    return [replace(failure, file=target_rel) for failure in failures]


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


# --- Go stages (T-92 Phase 3): duplicated beside the Python stages on purpose —
# the LanguagePack extraction is Phase 4. Signatures + contracts are pinned here;
# bodies are filled by the evaluator edit run against the test_evaluator.py twins.


def _go_binary() -> str:
    """Resolve the go binary: ``OFICINA_GO`` env override, else PATH lookup, else the
    literal ``go`` (the ``_validate_code_script`` env-override pattern — the detached
    worker's PATH may lack the login shell's ``/usr/local/go/bin``)."""
    return os.environ.get("OFICINA_GO") or shutil.which("go") or "go"


def _read_go_module(worktree: Path) -> str:
    """The module path from the worktree's ``go.mod`` — the line starting ``module ``."""
    go_mod_path = worktree / "go.mod"
    if not go_mod_path.exists():
        raise EvaluationError("test", "go.mod not found in worktree")
    for line in go_mod_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("module "):
            return line[len("module "):]
    raise EvaluationError("test", "no module line found in go.mod")


def _run_go_compile_stage(worktree: Path, timeout_s: int) -> List[ParsedFailure]:
    """R3: run ``go build ./...`` with ``cwd=worktree``, capturing output.

    Exit 0 → ``[]``; nonzero → ``_parse_go_build(stderr)`` (the path in each error
    line is already worktree-relative — compile is self-attributing, R4). A timeout
    raises ``EvaluationError("compile", ...)`` exactly like the Python stage.
    """
    try:
        result = subprocess.run(
            [_go_binary(), "build", "./..."],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise EvaluationError("compile", f"go build exceeded {timeout_s}s")
    if result.returncode != 0:
        return _parse_go_build(result.stderr)
    return []


def _run_go_test_stage(worktree: Path, timeout_s: int) -> List[ParsedFailure]:
    """A2: ALWAYS run ``go test -json ./...`` with ``cwd=worktree`` — the caller's
    ``test_cmd`` is deliberately not consulted, because Package-field attribution
    depends on ``-json`` and honoring a plain ``go test`` would silently degrade
    into the P2-D12 masking hole.

    Exit 0 → ``[]``; nonzero → ``_parse_gotest(stdout, module)`` with the module
    from ``_read_go_module``; nonzero with ZERO parsed failures raises
    ``EvaluationError("test", ...)`` (tests-never-ran must not read as passed —
    the same guard as the Python test stage). A timeout raises ``EvaluationError``.
    """
    try:
        result = subprocess.run(
            [_go_binary(), "test", "-json", "./..."],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise EvaluationError("test", f"go test exceeded {timeout_s}s")
    if result.returncode == 0:
        return []
    failures = _parse_gotest(result.stdout, _read_go_module(worktree))
    if not failures:
        # go <1.24: a build failure under `go test -json` emits NO fail events —
        # the compiler errors go to stderr in `go build` shape (banner + error
        # lines). This is every greenfield C0 (test file references the absent
        # target), so surface them as failures before declaring "no parseable
        # result"; an EvaluationError here would kill greenfield Go assembly.
        failures = _parse_go_build(result.stderr)
    if not failures:
        tail = (result.stderr or result.stdout or "").strip()[-300:]
        raise EvaluationError(
            "test",
            f"go test produced no parseable result (rc={result.returncode}): {tail}",
        )
    return failures


def evaluate(worktree: Path, base_repo: Path, spec: Dict[str, Any]) -> List[ParsedFailure]:
    """The real ``EvaluateFn``: stage-ordered evaluation, first failing stage wins (P2-D8).

    Compile runs only when the target exists in the worktree (at C0 the deliverable is absent,
    so evaluation goes straight to the test stage, which surfaces the import/undefined failure).
    The stages are language-dispatched (T-92 Phase 3): the resolved deliverable language picks
    the Go twins or the Python originals; the flow (presence rule, first-failing-stage) is
    invariant.
    """
    target = (spec.get("deliverable") or {}).get("target")
    acceptance = spec.get("acceptance") or {}
    timeout_s = (spec.get("budgets") or {}).get("wall_clock_s") or _STAGE_TIMEOUT_S
    language = resolve_language(spec.get("deliverable") or {}) or "python"

    if language == "go":
        if target:
            rel = target_relpath(target, base_repo)
            if (Path(worktree) / rel).exists():
                compile_failures = _run_go_compile_stage(Path(worktree), timeout_s)
                if compile_failures:
                    return compile_failures
        return _run_go_test_stage(Path(worktree), timeout_s)

    if target:
        rel = target_relpath(target, base_repo)
        target_in_worktree = Path(worktree) / rel
        if target_in_worktree.exists():
            compile_failures = _run_compile_stage(target_in_worktree, rel, timeout_s)
            if compile_failures:
                return compile_failures

    test_cmd = acceptance.get("test_cmd")
    if not test_cmd:
        return []
    return _run_test_stage(Path(worktree), test_cmd, timeout_s)
