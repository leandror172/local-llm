#!/usr/bin/env python3
"""Measure what fraction of the estate fits a model's context window (T-122, P4-D2).

Two questions, one arithmetic. A whole-file task pays for its target file TWICE — once
inbound, once outbound — so the reachable set is bounded by `(ceiling - overhead)/2`:

  * **coder** (T-122): inbound `current_file` + outbound generated file + tests.
  * **judge** (P4-D2): inbound baseline + inbound delivered file + rubric criterion.

The estimate matches the shipped guard verbatim (`loop.py:_context_overflow`):
`ceil(len(prompt)/4) + num_predict <= context_limit`, so a file this reports as
unreachable is one the guard would actually refuse.

Ceilings are read live from `/api/show` rather than from `models.yaml`, because the
recorded numbers drifted (T-113: 32K@14B recorded 9.5 GiB, measures 14.2 GiB live).

Usage:
  .claude/tools/judge-window-sweep.py --models my-codegen-q3 my-python-q25c14-16k
  .claude/tools/judge-window-sweep.py --paths 'mcp-server/src/**/*.py' --overhead 600
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import statistics
import sys
import urllib.error
import urllib.request

DEFAULT_HOST = "http://localhost:11435"
DEFAULT_PATHS = [
    "mcp-server/src/ollama_mcp/**/*.py",
    "evaluator/lib/*.py",
]
# Rubric criterion + system framing. One criterion per call is the rubric's own design.
DEFAULT_OVERHEAD = 600
# A judge emits a score plus a short reason; a coder emits a file. Caller sets this.
DEFAULT_NUM_PREDICT = 512


def context_limit(host: str, model: str) -> int | None:
    """The model's live num_ctx, or None when it cannot be resolved (guard-disabling case)."""
    req = urllib.request.Request(
        f"{host}/api/show",
        data=json.dumps({"model": model}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"  ! {model}: cannot reach /api/show ({exc})", file=sys.stderr)
        return None
    for line in (payload.get("parameters") or "").splitlines():
        if line.startswith("num_ctx"):
            return int(line.split()[1])
    return None


def estimate_tokens(path: str) -> int:
    """chars/4, the same estimate the shipped guard applies to its assembled prompt."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return math.ceil(len(fh.read()) / 4)


def collect(patterns: list[str]) -> list[tuple[str, int]]:
    files: dict[str, int] = {}
    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            if "/.venv/" in path or "/__pycache__/" in path:
                continue
            files[path] = estimate_tokens(path)
    return sorted(files.items(), key=lambda kv: kv[1])


def paired_test_tokens(path: str, test_roots: list[str]) -> tuple[str | None, int]:
    """The declared test file an edit run would carry, and its cost.

    A coder edit run's second term is the acceptance tests, not a rubric criterion — the
    T-122 band is `(num_ctx - tests - overhead)/2`. Omitting the tests term reports a band
    the coder does not actually have.
    """
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    for root in test_roots:
        for candidate in glob.glob(f"{root}/**/test_{stem}.py", recursive=True):
            return candidate, estimate_tokens(candidate)
    return None, 0


def report(
    model: str,
    ceiling: int,
    files: list[tuple[str, int]],
    overhead: int,
    num_predict: int,
    test_roots: list[str] | None = None,
) -> None:
    print(f"\n=== {model} — ceiling {ceiling} tokens ===")
    if test_roots:
        print(f"  mode: PAIRED-TESTS (per-file budget = ceiling - tests - {overhead} - {num_predict})")
    else:
        print(f"  budget after overhead({overhead}) + num_predict({num_predict}): "
              f"{ceiling - overhead - num_predict}")
        print(f"  largest reachable file: {(ceiling - overhead - num_predict) // 2} tokens")

    reachable, blocked, unpaired = [], [], 0
    for path, tok in files:
        tests_tok = 0
        if test_roots:
            test_path, tests_tok = paired_test_tokens(path, test_roots)
            if test_path is None:
                unpaired += 1
        budget = ceiling - overhead - num_predict - tests_tok
        (reachable if 2 * tok <= budget else blocked).append((path, tok, tests_tok))

    pct = 100.0 * len(reachable) / len(files) if files else 0.0
    print(f"  REACHABLE: {len(reachable)}/{len(files)} files ({pct:.1f}%)")
    if test_roots and unpaired:
        print(f"  ({unpaired} files have no paired test — counted with a zero tests term, i.e. optimistically)")
    if blocked:
        print(f"  blocked ({len(blocked)}):")
        for path, tok, tests_tok in reversed(blocked):
            suffix = f" + tests {tests_tok}" if tests_tok else ""
            print(f"    {tok:>6} tok{suffix:>14}  {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--paths", nargs="+", default=DEFAULT_PATHS)
    ap.add_argument("--overhead", type=int, default=DEFAULT_OVERHEAD)
    ap.add_argument("--num-predict", type=int, default=DEFAULT_NUM_PREDICT)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument(
        "--pair-tests",
        nargs="+",
        metavar="ROOT",
        help="coder mode: charge each file its paired test_<stem>.py found under these roots",
    )
    args = ap.parse_args()

    files = collect(args.paths)
    if not files:
        print("no files matched", file=sys.stderr)
        return 1

    sizes = [t for _, t in files]
    print(f"estate: {len(files)} files")
    print(f"  tokens  min {min(sizes)}  median {int(statistics.median(sizes))}  max {max(sizes)}")

    for model in args.models:
        ceiling = context_limit(args.host, model)
        if ceiling is None:
            print(f"\n=== {model} — ceiling UNRESOLVED (guard would run unguarded) ===")
            continue
        report(model, ceiling, files, args.overhead, args.num_predict, args.pair_tests)
    return 0


if __name__ == "__main__":
    sys.exit(main())
