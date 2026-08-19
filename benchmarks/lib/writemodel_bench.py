#!/usr/bin/env python3
"""oficina write-model benchmark harness (T-104).

Per (task, arm, run): build the arm's prompt, call the model once, apply the output via the arm's
mechanism, run the tests split into target vs regression, record a row. Aggregated BY SIZE BUCKET
per the pre-registered decision rule (`ref:oficina-write-model-benchmark`).

Invoke via the wrapper: benchmarks/lib/run-write-model-bench.sh  (do not call directly).

Arms:
  A code-anchored  — model returns only the function; code locates the span and applies it.
  B whole-file     — model returns the complete file; overwrite.
  C model-anchored — model returns SEARCH/REPLACE blocks; apply by exact match (loud fail on miss).
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_chat  # noqa: E402

from writemodel_apply import (  # noqa: E402
    KINDS,
    apply_code_anchored,
    apply_search_replace,
    apply_unit,
    apply_whole_file,
    locate_function,
    resolve_unit,
    strip_code_fences,
)
from writemodel_corpus import (  # noqa: E402
    Task,
    generate_class_task,
    generate_corpus,
    generate_import_task,
)

ARMS = ("code_anchored", "whole_file", "model_anchored", "symbol_addressed")

# Arm D's response schema (P3-T0). `path` and `body` are grammar-constrained because their
# SHAPE is not what is under test — but `kind` is a FREE STRING on purpose. Constraining it to
# an enum would make `unknown_kind` unobservable, and "the model used the wrong vocabulary"
# and "the model named the wrong unit" have opposite remedies. A probe must not use a grammar
# to hide the failure it exists to measure.
_UNIT_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "array", "items": {"type": "string"}},
        "kind": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["path", "kind", "body"],
}

_SYSTEM = "You are a precise Python engineer. Output only what is asked — no explanation."


def _function_source(task: Task) -> str:
    """The current source text of the task's target function (for the code-anchored prompt)."""
    span = locate_function(task.source, task.target_fn)
    if span is None:
        return ""
    start, end = span
    return "".join(task.source.splitlines(keepends=True)[start - 1 : end])


def build_prompt(task: Task, arm: str) -> str:
    """The arm's prompt. Each arm gets the minimal ask its mechanism needs (deliberately not
    controlled — 'which ask yields better code' is part of the write-model question)."""
    if arm == "code_anchored":
        return (
            f"{task.behavior}\n\nHere is the current function:\n\n"
            f"```python\n{_function_source(task)}```\n\n"
            "Return ONLY the complete rewritten function definition. No other text, no fences."
        )
    if arm == "whole_file":
        return (
            f"{task.behavior}\n\nHere is the complete file:\n\n"
            f"```python\n{task.source}```\n\n"
            "Return the COMPLETE modified file, with every other function unchanged. "
            "No other text, no fences."
        )
    if arm == "model_anchored":
        return (
            f"{task.behavior}\n\nHere is the complete file:\n\n"
            f"```python\n{task.source}```\n\n"
            "Return one or more edit blocks in this EXACT format (verbatim search text):\n"
            "<<<<<<< SEARCH\n<lines to find>\n=======\n<replacement lines>\n>>>>>>> REPLACE"
        )
    if arm == "symbol_addressed":
        return (
            f"{task.behavior}\n\nHere is the complete file:\n\n"
            f"```python\n{task.source}```\n\n"
            "Name the ONE unit to replace and give its new source. Reply as JSON:\n"
            '  "path": the dotted address as a list, e.g. ["ClassName", "method_name"] '
            'for a method or ["function_name"] for a top-level function\n'
            '  "kind": "Function", "Method" or "Class"\n'
            '  "body": the complete new source of THAT UNIT ONLY — no other functions, '
            "no surrounding code, no fences"
        )
    raise ValueError(f"unknown arm: {arm}")


# Recorded per cell. `load_duration_ms` separates "slow because cold" from "slow
# because contended" — the discriminator T-131 needs and the one a wall-clock
# figure cannot supply.
_STATS_KEYS = (
    "eval_count",
    "eval_duration_ms",
    "prompt_eval_duration_ms",
    "load_duration_ms",
)


def call_model(
    prompt: str, model: str, timeout: int, schema: dict | None = None
) -> tuple[str, dict]:
    """One model call; single retry on a cold-start timeout.

    Returns (content, stats). `stats` carries Ollama's own timings, so a cell's
    generation rate is READ rather than bounded by wall clock — the `ms` field
    below also contains apply + test time, which is why s137 could only report
    "at least" a figure (T-137).
    """
    for attempt in (1, 2):
        try:
            resp = ollama_chat(prompt, model=model, system=_SYSTEM, timeout=timeout,
                               keep_alive="10m", format_schema=schema)
            return resp["content"], {k: resp.get(k) or 0 for k in _STATS_KEYS}
        except TimeoutError:
            if attempt == 2:
                raise
            time.sleep(3)
    return "", {k: 0 for k in _STATS_KEYS}


def apply_output(task: Task, arm: str, content: str) -> str | None:
    """Apply the (defenced) model output via the arm's mechanism. None = apply failed."""
    text = strip_code_fences(content)
    if arm == "code_anchored":
        return apply_code_anchored(task.source, task.target_fn, text)
    if arm == "whole_file":
        return apply_whole_file(text)
    if arm == "model_anchored":
        return apply_search_replace(task.source, text)
    if arm == "symbol_addressed":
        emitted = _parse_unit(content)
        if emitted is None:
            return None
        return apply_unit(task.source, emitted["path"], emitted["body"], kind=emitted["kind"])
    raise ValueError(f"unknown arm: {arm}")


def _parse_unit(content: str) -> dict | None:
    """The arm's JSON reply, or None if it is not usable. Grammar-constrained, so a miss here
    is itself a finding rather than routine parsing noise."""
    try:
        obj = json.loads(strip_code_fences(content))
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    path, kind, body = obj.get("path"), obj.get("kind"), obj.get("body")
    if not isinstance(path, list) or not all(isinstance(p, str) for p in path):
        return None
    if not isinstance(kind, str) or not isinstance(body, str):
        return None
    return {"path": path, "kind": kind, "body": body}


def _symbol_metrics(task: Task, content: str) -> dict:
    """Criteria 1, 2, 4 and 5 of P3-T0, measured per attempt.

    These are recorded whether or not the edit applied: a run that fails is exactly where the
    distribution of FAILURE MODES matters, and collapsing them into `applied: False` is what
    the distinct resolve reasons exist to prevent.
    """
    m = {
        "emitted_path": None, "emitted_kind": None,
        "resolve_reason": "unparseable_reply",      # criterion 1
        "span_ratio": None, "body_ratio": None,     # criterion 2
        "body_fenced": None, "body_units": None, "body_parses": None,   # criterion 4
        # Criterion 5a. Three outcomes, derivable from these two plus the task's own module:
        #   has_import                      -> function-local import (the PREDICTED tell)
        #   references and not has_import   -> used the module, never imported it anywhere
        #   not references                  -> avoided it (hand-rolled); a counted outcome
        "body_has_import": None,
        "body_references_module": None,
        "required_module": task.required_module,
    }
    emitted = _parse_unit(content)
    if emitted is None:
        return m

    file_lines = len(task.source.splitlines()) or 1
    body = emitted["body"]
    m["emitted_path"] = emitted["path"]
    m["emitted_kind"] = emitted["kind"]
    m["body_ratio"] = round(len(body.splitlines()) / file_lines, 3)
    m["body_fenced"] = "```" in body

    # Parse the DEFENCED body: a fence would otherwise make the body unparseable and take the
    # neighbouring-code count down with it, so one criterion-4 defect would silently hide the
    # other. `body_fenced` above already recorded the raw observation, independently.
    try:
        tree = ast.parse(textwrap.dedent(strip_code_fences(body)))
    except SyntaxError:
        m["body_parses"] = False
    else:
        m["body_parses"] = True
        # >1 top-level unit means it emitted NEIGHBOURING code, not just the one asked for.
        m["body_units"] = sum(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in tree.body
        )
        # Criterion 5: a function-local import is the predicted tell that the model needed a
        # top-level statement it had no way to address. Legal Python, passes tests, invisible
        # to every other criterion.
        m["body_has_import"] = any(
            isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree)
        )
        # Whether the body reaches for the module at all. Matched on ast.Name ids, NOT on
        # text: `aftermath_of(x)` contains "math" and is not a use of it, and inflating the
        # most interesting outcome with substring hits would be undetectable in the results.
        if task.required_module is not None:
            m["body_references_module"] = any(
                isinstance(n, ast.Name) and n.id == task.required_module
                for n in ast.walk(tree)
            )

    span, reason = resolve_unit(task.source, emitted["path"], emitted["kind"])
    m["resolve_reason"] = reason or "ok"
    if span is not None:
        m["span_ratio"] = round((span[1] - span[0] + 1) / file_lines, 3)
    return m


def _pytest(tmp: Path, *node_args: str) -> bool:
    """Run pytest in tmp; True iff exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", *node_args],
        cwd=str(tmp),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def run_tests(new_source: str, task: Task) -> tuple[bool, bool]:
    """Write the edited module + tests to a temp dir; return (target_pass, no_regression)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "module_under_test.py").write_text(new_source, encoding="utf-8")
        (tmp / "test_gen.py").write_text(task.tests, encoding="utf-8")
        target_pass = _pytest(tmp, f"test_gen.py::{task.target_test}")
        no_regression = _pytest(tmp, "test_gen.py", "--deselect", f"test_gen.py::{task.target_test}")
        return target_pass, no_regression


def run_cell(task: Task, arm: str, model: str, run_idx: int, timeout: int) -> dict:
    """One (task, arm, run) → a record row."""
    t0 = time.perf_counter()
    error = None
    applied = False
    target_pass = no_regression = False
    stats: dict = {k: 0 for k in _STATS_KEYS}
    metrics: dict = {}
    try:
        content, stats = call_model(
            build_prompt(task, arm), model, timeout,
            schema=_UNIT_SCHEMA if arm == "symbol_addressed" else None,
        )
        if arm == "symbol_addressed":
            # Recorded BEFORE the apply, so a failed apply still reports its failure mode.
            metrics = _symbol_metrics(task, content)
        new_source = apply_output(task, arm, content)
        applied = new_source is not None
        if applied:
            target_pass, no_regression = run_tests(new_source, task)
    except Exception as exc:  # noqa: BLE001 — a failed cell must not abort the run
        error = f"{type(exc).__name__}: {exc}"
    return {
        "task": task.name,
        "bucket": task.bucket,
        "arm": arm,
        "run": run_idx,
        "applied": applied,
        "target_pass": target_pass,
        "no_regression": no_regression,
        "combined": applied and target_pass and no_regression,
        **stats,
        # Wall clock for the WHOLE cell (generate + apply + run tests), which is
        # why it is not a generation-rate denominator. Use eval_duration_ms.
        "ms": round((time.perf_counter() - t0) * 1000),
        "error": error,
        **metrics,
    }


def run_all(tasks, arms, model, runs, timeout, out_path):
    """Serial sweep (VRAM ceiling). Append each record to JSONL as it lands (crash-survivable)."""
    records = []
    total = len(tasks) * len(arms) * runs
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for task in tasks:
            for arm in arms:
                for run_idx in range(runs):
                    n += 1
                    rec = run_cell(task, arm, model, run_idx, timeout)
                    records.append(rec)
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    flag = "OK " if rec["combined"] else ("app" if rec["applied"] else "FAIL")
                    print(f"[{n:>3}/{total}] {task.name:<18} {arm:<15} {flag} "
                          f"tgt={int(rec['target_pass'])} reg={int(rec['no_regression'])} "
                          f"{rec['ms']}ms", flush=True)
    return records


def _rate(rows, key):
    return round(100 * sum(r[key] for r in rows) / len(rows)) if rows else 0


def report(records):
    """Print rates BY SIZE BUCKET × arm (never aggregate — the pre-registered rule)."""
    print("\n" + "=" * 78)
    print("WRITE-MODEL BENCHMARK — rates by size bucket (higher = better)")
    print("=" * 78)
    for bucket in ("small", "medium", "large"):
        brows = [r for r in records if r["bucket"] == bucket]
        if not brows:
            continue
        # Divide by the arms actually PRESENT, not by every arm that exists — a subset run
        # otherwise reports "n=0 tasks" above real numbers.
        n_arms = len({r["arm"] for r in brows}) or 1
        print(f"\n{bucket.upper()}  (n={len(brows) // n_arms} rows per arm)")
        print(f"  {'arm':<15} {'applied':>8} {'target':>8} {'no-reg':>8} {'COMBINED':>9} {'toks':>7}")
        for arm in ARMS:
            rows = [r for r in brows if r["arm"] == arm]
            if not rows:
                continue
            toks = round(sum(r["eval_count"] for r in rows) / len(rows))
            print(f"  {arm:<15} {_rate(rows,'applied'):>7}% {_rate(rows,'target_pass'):>7}% "
                  f"{_rate(rows,'no_regression'):>7}% {_rate(rows,'combined'):>8}% {toks:>7}")
    _symbol_report(records)
    errs = [r for r in records if r["error"]]
    if errs:
        print(f"\n{len(errs)} cell error(s); first: {errs[0]['error']}")


def _symbol_report(records):
    """P3-T0's criteria for the symbol-addressed arm. Failure MODES, not just a pass rate —
    the outcome table branches differently on each, so collapsing them decides nothing."""
    rows = [r for r in records if r["arm"] == "symbol_addressed"]
    if not rows:
        return
    print("\n" + "=" * 78)
    print("P3-T0 — symbol-addressed arm: criteria")
    print("=" * 78)

    print("\n  criterion 1 — address fidelity (resolve reason)")
    reasons: dict[str, int] = {}
    for r in rows:
        reasons[r.get("resolve_reason") or "?"] = reasons.get(r.get("resolve_reason") or "?", 0) + 1
    for reason, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"    {reason:<22} {n:>4}  ({round(100 * n / len(rows))}%)")

    resolved = [r for r in rows if r.get("span_ratio") is not None]
    if resolved:
        spans = sorted(r["span_ratio"] for r in resolved)
        bodies = sorted(r["body_ratio"] for r in resolved if r.get("body_ratio") is not None)
        print("\n  criterion 2 — degeneration to a coarse unit (fraction of the file)")
        print(f"    span  median {spans[len(spans) // 2]:.3f}   max {spans[-1]:.3f}")
        if bodies:
            print(f"    body  median {bodies[len(bodies) // 2]:.3f}   max {bodies[-1]:.3f}")
        coarse = sum(r["span_ratio"] > 0.5 for r in resolved)
        print(f"    addressed >50% of the file: {coarse}/{len(resolved)}"
              f"  ({round(100 * coarse / len(resolved))}%)  <- the design-killing case")

    print("\n  criterion 4 — response shape")
    parsed = [r for r in rows if r.get("body_parses") is not None]
    if parsed:
        print(f"    body fenced           {sum(bool(r.get('body_fenced')) for r in parsed):>4}/{len(parsed)}")
        print(f"    body does not parse   {sum(r.get('body_parses') is False for r in parsed):>4}/{len(parsed)}")
        multi = sum((r.get("body_units") or 0) > 1 for r in parsed)
        print(f"    >1 unit in body       {multi:>4}/{len(parsed)}  <- emitted neighbouring code")

    print("\n  criterion 5 — needed a unit it could not address")
    imports = [r for r in parsed if r.get("body_has_import")]
    print(f"    import INSIDE the body {len(imports):>3}/{len(parsed) if parsed else 0}"
          "  <- the predicted function-local-import tell")


def main():
    p = argparse.ArgumentParser(description="oficina write-model benchmark")
    p.add_argument("--model", default="my-python-q25c14")
    p.add_argument("--arms", default=",".join(ARMS), help="comma-separated subset of arms")
    p.add_argument("--per-bucket", type=int, default=4, help="tasks per size bucket")
    p.add_argument("--corpus", default="flat",
                   choices=("flat", "class", "both", "import"),
                   help="flat = top-level-function tasks (the published arm A/B/C corpus); "
                        "class = class-bearing tasks, REQUIRED for criterion 2 since a flat "
                        "corpus has no class to name coarsely; both = the union; "
                        "import = tasks whose fix REQUIRES a new top-level import, for "
                        "criterion 5a — the case s137's 0/12 never exercised")
    p.add_argument("--buckets", default="small,medium,large")
    p.add_argument("--runs", type=int, default=3, help="runs per (task, arm) cell")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--out", default=None, help="JSONL output path")
    p.add_argument("--limit", type=int, default=None, help="cap total tasks (smoke testing)")
    args = p.parse_args()

    arms = [a for a in args.arms.split(",") if a in ARMS]
    buckets = set(args.buckets.split(","))
    tasks = []
    if args.corpus in ("flat", "both"):
        tasks += generate_corpus(args.per_bucket)
    if args.corpus in ("class", "both"):
        tasks += [
            generate_class_task(b, i)
            for b in ("small", "medium", "large")
            for i in range(args.per_bucket)
        ]
    if args.corpus == "import":
        tasks += [
            generate_import_task(b, i)
            for b in ("small", "medium", "large")
            for i in range(args.per_bucket)
        ]
    tasks = [t for t in tasks if t.bucket in buckets]
    if args.limit:
        tasks = tasks[: args.limit]
    out_path = args.out or str(REPO_ROOT / "benchmarks" / "results" / "write-model-bench.jsonl")

    print(f"model={args.model} arms={arms} tasks={len(tasks)} runs={args.runs} "
          f"→ {len(tasks) * len(arms) * args.runs} generations\nout={out_path}\n")
    records = run_all(tasks, arms, args.model, args.runs, args.timeout, out_path)
    report(records)


if __name__ == "__main__":
    main()
