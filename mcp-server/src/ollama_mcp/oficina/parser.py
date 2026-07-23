from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

# Evaluation stages (P2-D8). The FIRST failing stage names the category.
STAGE_COMPILE = "compile"
STAGE_TEST = "test"
STAGE_STRUCTURAL = "structural"

# Failure categories (P2-D8 / the verdict-data taxonomy).
CATEGORY_MECHANICAL = "mechanical"
CATEGORY_STRUCTURAL = "structural"

# Scope buckets (P2-D12).
SCOPE_TARGET = "target"
SCOPE_TEST = "test"
SCOPE_OUT = "out"


@dataclass(frozen=True)
class ParsedFailure:
    """One normalized failure extracted from a validator/evaluation stage.

    Attributes:
        stage: which evaluation stage produced it — one of ``STAGE_*``.
        file: basename of the faulting file, or ``None`` when the stage output
            does not attribute the failure to a file.
        error_key: the defect's stable identity as ``(kind, detail)`` with all
            volatile coordinates stripped — e.g. ``("py-syntax_error",
            "invalid-syntax-...")`` or ``("pytest-failed:test_area.py::test_x",
            "assert-...")``.
        raw: the original unmodified message text, for the diff report/forensics.
    """

    stage: str
    file: Optional[str]
    error_key: tuple[str, str]
    raw: str


# --- normalization (P2-D7): strip volatile coordinates ----------------------


def _basename(path: str) -> str:
    """The final path component, slash-agnostic."""
    return os.path.basename(path)


def _normalize(text: str) -> str:
    """Reduce a message to its location-invariant identity.

    Order matters: paths collapse to basenames first, then line/column numbers
    and hex addresses are removed, then whitespace is collapsed to a
    deterministic hyphenated lowercase slug. The same defect at different lines
    (or under different temp dirs) yields an identical result.
    """
    # Path/temp-dir fragments (anything containing a slash) collapse to basename.
    text = re.sub(r"\S*/\S+", lambda m: _basename(m.group(0)), text)
    # Line/column coordinates.
    text = re.sub(r"\bline\s+\d+|:\d+:\d+|:\d+", "", text)
    # Hex addresses.
    text = re.sub(r"0x[0-9a-fA-F]+", "", text)
    # Deterministic slug.
    return "-".join(text.split()).lower()


# --- per-stage parsers ------------------------------------------------------


# error_key prefix per R1 language identifier. The "py-" spelling predates the
# language field and is pinned by every recorded repetition signature, so
# "python" maps down to it rather than renaming the key space.
_ERROR_KEY_PREFIX = {"python": "py", "go": "go"}


def _parse_compile(payload: list, language: str) -> list[ParsedFailure]:
    """One ParsedFailure per error across every failing file in the JSON array."""
    prefix = _ERROR_KEY_PREFIX.get(language, language)
    failures: list[ParsedFailure] = []
    for result in payload:
        if result.get("status") != "fail":
            continue
        for error in result.get("errors", []):
            text = error["text"]
            error_key = (f"{prefix}-{error['type']}", _normalize(text))
            failures.append(
                ParsedFailure(
                    stage=STAGE_COMPILE,
                    file=result.get("file"),
                    error_key=error_key,
                    raw=text,
                )
            )
    return failures


_SUMMARY_HEADER = "short test summary info"


def _summary_section(payload: str) -> Optional[list[str]]:
    """The lines of pytest's 'short test summary info' block, or None if absent.

    The block opens at the ``=== short test summary info ===`` banner and closes
    at the next ``=``-ruled banner (the final ``=== N failed, M passed ===`` line).
    Restricting the FAILED/ERROR scan to this block is what keeps *application*
    output — a test that logs ``ERROR ...`` under ``log_cli``/``-s``, or any stderr
    line beginning ``ERROR ``/``FAILED `` — from being misread as a test failure
    (the phantom-failure hole). ``None`` means pytest emitted no summary at all,
    which the caller distinguishes from "summary present, zero failures".
    """
    lines = payload.splitlines()
    start = None
    for index, raw in enumerate(lines):
        if _SUMMARY_HEADER in raw and raw.lstrip().startswith("="):
            start = index + 1
            break
    if start is None:
        return None
    section: list[str] = []
    for raw in lines[start:]:
        if raw.startswith("="):  # the trailing summary banner closes the block
            break
        section.append(raw)
    return section


def _parse_pytest(payload: str) -> list[ParsedFailure]:
    """Scan the pytest short-summary FAILED/ERROR lines into failures.

    ERROR (collection/import) keys under ``pytest-error:`` (mechanical), FAILED
    (assertion) under ``pytest-failed:`` (structural) — so the category split
    survives into the repetition signature. The ``- <reason>`` tail is optional.
    Only the short-summary block is scanned (``_summary_section``); no summary
    block → no parsed failures (the caller reads the exit code to tell "passed"
    from "the test command never ran").
    """
    section = _summary_section(payload)
    if section is None:
        return []
    failures: list[ParsedFailure] = []
    for raw_line in section:
        line = raw_line.strip()
        if line.startswith("FAILED "):
            keyword, prefix = "FAILED ", "pytest-failed:"
        elif line.startswith("ERROR "):
            keyword, prefix = "ERROR ", "pytest-error:"
        else:
            continue

        body = line[len(keyword):]
        nodeid, _, reason = body.partition(" - ")
        nodeid = nodeid.strip()
        file_part = nodeid.split("::", 1)[0]
        error_key = (prefix + _normalize(nodeid), _normalize(reason))
        failures.append(
            ParsedFailure(
                stage=STAGE_TEST,
                file=file_part,
                error_key=error_key,
                raw=line,
            )
        )
    return failures


# --- public surface ---------------------------------------------------------


def parse_validator_output(stage: str, payload: Any, language: str = "python") -> list[ParsedFailure]:
    """Parse one stage's raw output into zero or more ``ParsedFailure``.

    Args:
        stage: ``STAGE_COMPILE`` (payload = the JSON array from
            ``validate-code.py``) or ``STAGE_TEST`` (payload = pytest stdout
            text). The caller always knows which stage it just ran, so the
            stage is explicit — never sniffed from the payload.
        payload: a ``list[dict]`` for the compile stage, a ``str`` for the test
            stage.
        language: the R1 language identifier ("python" / "go") the caller resolved
            via ``resolve_language`` — never a prefix spelling. The compile
            error_key prefix derives from it through ``_ERROR_KEY_PREFIX``.

    Returns:
        A list of failures (empty when the stage passed).
    """
    if stage == STAGE_COMPILE:
        return _parse_compile(payload, language)
    if stage == STAGE_TEST:
        return _parse_pytest(payload)
    raise ValueError(f"unknown stage: {stage!r}")


def category_for(failure: ParsedFailure) -> str:
    """Map a failure to its category (P2-D8).

    ``compile`` and ``structural`` stages are ``mechanical`` and ``structural``
    respectively. The ``test`` stage is split by the Python caveat: a pytest
    collection/import **ERROR** is ``mechanical`` (undefined-name/import defects
    that ``py_compile`` cannot see), a pytest assertion **FAILED** is
    ``structural``.
    """
    if failure.stage == STAGE_COMPILE:
        return CATEGORY_MECHANICAL
    if failure.stage == STAGE_STRUCTURAL:
        return CATEGORY_STRUCTURAL
    if failure.stage == STAGE_TEST:
        if failure.error_key[0].startswith("pytest-error"):
            return CATEGORY_MECHANICAL
        if failure.error_key[0].startswith("pytest-failed"):
            return CATEGORY_STRUCTURAL
    if failure.error_key[0].startswith("go-test-failed:"):
        return CATEGORY_STRUCTURAL
    raise ValueError(f"uncategorizable failure: {failure!r}")


def scope_of(
    file: Optional[str],
    target_files: "list[str] | set[str]",
    test_files: "list[str] | set[str]",
) -> str:
    """Classify a failure's file as ``target`` / ``test`` / ``out`` (P2-D12).

    Comparison is by normalized worktree-relative path (T-98): basename matching
    silently flipped scope on collisions (``lib/util.py`` vs target ``src/util.py``
    → permanent false-exhaustion). Every producer already speaks worktree-relative
    — pytest nodeids and ``git diff --name-only`` emit it, and the evaluator stamps
    compile failures with the target relpath — so callers pass that spelling.
    A ``None`` file (unattributable) is ``out``.
    """
    if file is None:
        return SCOPE_OUT
    path = os.path.normpath(file)
    if any(os.path.normpath(f) == path for f in target_files):
        return SCOPE_TARGET
    if any(os.path.normpath(f) == path for f in test_files):
        return SCOPE_TEST
    return SCOPE_OUT

# --- go test -json event stream parser (T-92 Phase 3) ------------------------


def _parse_gotest(payload: str, module: str) -> list[ParsedFailure]:
    """Parse the stdout of `go test -json ./...` into zero or more ``ParsedFailure``.

    Args:
        payload: The JSON Lines output from `go test -json`.
        module: The module path to strip from package paths.

    Returns:
        A list of failures (empty when no tests failed).
    """
    failures: list[ParsedFailure] = []
    events = [json.loads(line) for line in payload.splitlines() if line.strip()]

    test_outputs: dict[str, list[str]] = {}
    for event in events:
        if event.get("Action") == "output" and event.get("Test"):
            test_outputs.setdefault(event["Test"], []).append(event["Output"])

    for event in events:
        if event.get("Action") != "fail" or not event.get("Test"):
            continue  # package-level fail events (no Test) summarize, never count
        test = event["Test"]
        # The detail line is the Output carrying the file:line fragment — keying on
        # it (not the join of all outputs) keeps error_key invariant to volatile
        # output composition ('=== RUN' banners, extra logs), per P2-D7.
        detail_line = next(
            (o for o in test_outputs.get(test, []) if re.search(r"\S+_test\.go:\d+", o)),
            None,
        )
        file_part = None
        if detail_line is not None:
            file_name = re.search(r"(\S+_test\.go):\d+", detail_line).group(1)
            package_dir = (
                "" if event["Package"] == module
                else event["Package"].removeprefix(module + "/")
            )
            file_part = f"{package_dir}/{file_name}" if package_dir else file_name
        raw = (detail_line or "\n".join(test_outputs.get(test, []))).strip()
        failures.append(
            ParsedFailure(
                stage=STAGE_TEST,
                file=file_part,
                error_key=("go-test-failed:" + _normalize(test), _normalize(raw)),
                raw=raw,
            )
        )

    return failures

# --- go build stderr parser (T-92 Phase 3) ------------------------


def _parse_go_build(payload: str) -> list[ParsedFailure]:
    """Parse the stderr of `go build ./...` into zero or more ``ParsedFailure``.

    Args:
        payload: The stderr output from `go build`.

    Returns:
        A list of failures (empty when no errors occurred).
    """
    failures: list[ParsedFailure] = []
    lines = payload.splitlines()
    for line in lines:
        if line.startswith("#"):
            continue  # Skip package banner lines
        match = re.match(r"\./(\S+):(\d+):(\d+): (.*)", line)
        if not match:
            continue  # Skip non-error lines
        file, line_num, col_num, message = match.groups()
        kind = _classify_go_error(message)
        error_key = (f"go-{kind}", _normalize(message))
        failures.append(
            ParsedFailure(
                stage=STAGE_COMPILE,
                file=file[2:],  # Strip leading './'
                error_key=error_key,
                raw=line,
            )
        )
    return failures


def _classify_go_error(message: str) -> str:
    """Classify a Go compiler error message into a kind."""
    if "undefined:" in message or "undefined name" in message:
        return "undefined_reference"
    elif "syntax error" in message or "expected" in message:
        return "syntax_error"
    elif "cannot use" in message or "type " in message or "cannot convert" in message:
        return "type_error"
    elif "imported and not used" in message:
        return "unused_import"
    else:
        return "compile_error"

