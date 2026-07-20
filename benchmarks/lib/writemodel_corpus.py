"""Corpus generator for the oficina write-model benchmark (T-104).

Programmatic, not hand-authored — which makes it MORE controlled: every filler function carries a
passing test, so the regression surface scales with file size automatically. That operationalizes
the core hypothesis (whole-file degrades with size): a larger file = more filler = more chances an
arm silently drops one, which its test catches. Ground truth is exact — the original always fails
the target test and passes all filler tests.

A Task is a self-contained edit problem:
  - source:      a valid .py file with N filler functions + one DEFECTIVE target function
  - tests:       one target test (fails on the original) + one test per filler (all pass)
  - target_fn:   the function to fix
  - target_test: the test node that must pass after the fix
  - behavior:    the natural-language change spec handed to the model

Buckets vary file size (the discriminator); edit-type variety is carried by the defect kind.
Design: `ref:oficina-write-model-benchmark`.
"""

from __future__ import annotations

from dataclasses import dataclass

BUCKET_FILLER = {"small": 1, "medium": 8, "large": 20}

# Four target defects (modify-body edits) — vary the task within a bucket without changing size.
# Each: (fn_name, bad_body, behavior, test_expr, expected). The bad body fails test_expr.
DEFECTS = [
    ("scale", "return x + factor", "return x MULTIPLIED by factor (it currently adds them)",
     "scale(3, 4)", 12),
    ("clamp", "return value", "clamp `value` to the inclusive range [lo, hi] (it currently ignores lo/hi)",
     "clamp(15, 0, 10)", 10),
    ("nth_even", "return n", "return the nth even number counting from 0 (0,2,4,...); it currently returns n",
     "nth_even(3)", 6),
    ("weighted", "return a + b", "return a*wa + b*wb (it currently ignores the weights and adds a+b)",
     "weighted(2, 3, 4, 5)", 23),
]

TARGET_SIG = {
    "scale": "def scale(x, factor):",
    "clamp": "def clamp(value, lo, hi):",
    "nth_even": "def nth_even(n):",
    "weighted": "def weighted(a, b, wa, wb):",
}


@dataclass
class Task:
    name: str
    bucket: str
    target_fn: str
    target_test: str          # pytest node name, e.g. "test_target"
    behavior: str
    source: str               # the .py file to edit
    tests: str                # the pytest file (target + filler tests)


def _filler(k: int) -> tuple[str, str]:
    """A trivially-correct function and its passing test (a regression tripwire)."""
    fn = f"def op_{k}(x):\n    return x + {k}\n"
    test = f"def test_op_{k}():\n    assert op_{k}(100) == {100 + k}\n"
    return fn, test


def generate_task(bucket: str, idx: int) -> Task:
    """Build one Task for a size bucket. ``idx`` selects the defect (mod 4) for within-bucket variety."""
    n_filler = BUCKET_FILLER[bucket]
    fn_name, bad_body, behavior_tail, test_expr, expected = DEFECTS[idx % len(DEFECTS)]
    sig = TARGET_SIG[fn_name]

    # Assemble the source: half the filler, then the defective target, then the rest — so the
    # target sits *inside* the file (not at an edge), which is where whole-file omission bites.
    fillers = [_filler(k) for k in range(n_filler)]
    half = n_filler // 2
    before = "\n".join(f for f, _ in fillers[:half])
    after = "\n".join(f for f, _ in fillers[half:])
    target_src = f"{sig}\n    {bad_body}\n"

    parts = ['"""Generated benchmark module."""', ""]
    if before:
        parts += [before]
    parts += [target_src.rstrip()]
    if after:
        parts += ["", after]
    source = "\n".join(parts).rstrip() + "\n"

    # Tests: the target test (fails on the defective original) + one test per filler (all pass).
    target_test_src = f"def test_target():\n    assert {test_expr} == {expected}\n"
    filler_tests = "\n".join(t for _, t in fillers)
    tests = f"from module_under_test import *\n\n\n{target_test_src}\n{filler_tests}".rstrip() + "\n"

    return Task(
        name=f"{bucket}-{idx:02d}-{fn_name}",
        bucket=bucket,
        target_fn=fn_name,
        target_test="test_target",
        behavior=f"Modify the function `{fn_name}` so that it will {behavior_tail}.",
        source=source,
        tests=tests,
    )


def generate_corpus(per_bucket: int = 4) -> list[Task]:
    """The full corpus: ``per_bucket`` tasks in each of small/medium/large."""
    return [
        generate_task(bucket, idx)
        for bucket in ("small", "medium", "large")
        for idx in range(per_bucket)
    ]
