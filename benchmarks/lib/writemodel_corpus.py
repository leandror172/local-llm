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
# Each: (fn_name, bad_body, behavior_tail, test_expr, expected). The bad body fails test_expr.
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
    target_path: list[str] | None = None   # dotted address; defaults to the bare name
    # Set only by generate_import_task: the module whose import the fix requires, and which
    # has NO dotted address (P3-D1 item 6). None for every other generator, so existing
    # constructions are untouched.
    required_module: str | None = None

    def __post_init__(self) -> None:
        # A flat task addresses itself as ["scale"]; a class task as ["Ops", "scale"]. Deriving
        # the default means no existing caller changes and there is no second field to drift.
        if self.target_path is None:
            self.target_path = [self.target_fn]


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


CLASS_NAME = "Ops"


def _method_sig(sig: str) -> str:
    """``def f(a, b):`` -> ``def f(self, a, b):`` — the flat target becomes a method."""
    head, params = sig.split("(", 1)
    return f"{head}(self, {params}"


def _sibling_method(k: int) -> tuple[str, str]:
    """A trivially-correct method and its passing test — the CLASS's regression surface.

    Siblings are what make a coarse address cost something. If the class were only its target
    method, naming the class instead of the method would be free and the benchmark could not
    detect the failure it exists to detect.
    """
    method = f"    def m_{k}(self, x):\n        return x - {k}\n"
    test = f"def test_m_{k}():\n    assert {CLASS_NAME}().m_{k}(100) == {100 - k}\n"
    return method, test


def generate_class_task(bucket: str, idx: int) -> Task:
    """Like ``generate_task``, but the defective target is a METHOD of a class.

    This exists because a corpus of flat top-level functions **cannot express criterion 2** of
    P3-T0 — "does the model name the CLASS instead of the METHOD". With no classes there is
    nothing to name coarsely, so a symbol-addressed arm would score a clean pass that means
    nothing. The file stays heterogeneous (a class AND plain top-level functions), which is
    also the direction E-D1's prescribed hardening asks for.
    """
    n_filler = BUCKET_FILLER[bucket]
    fn_name, bad_body, behavior_tail, test_expr, expected = DEFECTS[idx % len(DEFECTS)]

    n_methods = max(4, n_filler // 2)
    siblings = [_sibling_method(k) for k in range(n_methods)]
    mid = n_methods // 2
    target_method = f"    {_method_sig(TARGET_SIG[fn_name])}\n        {bad_body}\n"

    # The target sits INSIDE the class, not at either edge — same reason generate_task puts it
    # inside the file: an edge is the easy case for anything that drops content.
    class_lines = [f"class {CLASS_NAME}:", '    """Operations."""', ""]
    for method, _ in siblings[:mid]:
        class_lines += [method.rstrip(), ""]
    class_lines += [target_method.rstrip(), ""]
    for method, _ in siblings[mid:]:
        class_lines += [method.rstrip(), ""]
    class_src = "\n".join(class_lines).rstrip()

    fillers = [_filler(k) for k in range(n_filler)]
    half = n_filler // 2
    before = "\n".join(f for f, _ in fillers[:half])
    after = "\n".join(f for f, _ in fillers[half:])

    parts = ['"""Generated benchmark module (class-bearing)."""', ""]
    if before:
        parts += [before]
    parts += [class_src]
    if after:
        parts += ["", after]
    source = "\n".join(parts).rstrip() + "\n"

    # test_expr comes from DEFECTS and differs per defect — clamp/nth_even/weighted do not take
    # scale's arguments, so hardcoding any one signature breaks three tasks in four.
    target_test_src = f"def test_target():\n    assert {CLASS_NAME}().{test_expr} == {expected}\n"
    sibling_tests = "\n".join(t for _, t in siblings)
    filler_tests = "\n".join(t for _, t in fillers)
    tests = (
        f"from module_under_test import *\n\n\n{target_test_src}\n{sibling_tests}\n{filler_tests}"
    ).rstrip() + "\n"

    return Task(
        name=f"{bucket}-cls-{idx:02d}-{fn_name}",
        bucket=bucket,
        target_fn=fn_name,
        target_test="test_target",
        behavior=f"Modify the method `{CLASS_NAME}.{fn_name}` so that it will {behavior_tail}.",
        source=source,
        tests=tests,
        target_path=[CLASS_NAME, fn_name],
    )


IMPORT_DEFECTS = [
    (
        "gcd_ratio",
        "def gcd_ratio(a, b):",
        "return (a, b)",
        "math",
        "g = math.gcd(a, b)\n    return (a // g, b // g)",
        "reduce the fraction a/b to lowest terms using `math.gcd`, returning the tuple (a//g, b//g); it currently returns the inputs unchanged",
        "gcd_ratio(6, 8)",
        (3, 4),
    ),
    (
        "running_total",
        "def running_total(xs):",
        "return list(xs)",
        "itertools",
        "return list(itertools.accumulate(xs))",
        "return the running cumulative sums of `xs` using `itertools.accumulate`; it currently returns the list unchanged",
        "running_total([1, 2, 3])",
        [1, 3, 6],
    ),
]


def generate_import_task(bucket: str, idx: int) -> Task:
    """Build one import-requiring Task for a size bucket."""
    n_filler = BUCKET_FILLER[bucket]
    fn_name, sig, bad_body, module, fixed_body, behavior_tail, test_expr, expected = IMPORT_DEFECTS[idx % len(IMPORT_DEFECTS)]

    fillers = [_filler(k) for k in range(n_filler)]
    half = n_filler // 2
    before = "\n".join(f for f, _ in fillers[:half])
    after = "\n".join(f for f, _ in fillers[half:])
    target_src = f"{sig}\n    {bad_body}\n"

    parts = ['"""Generated benchmark module (import-requiring)."""', ""]
    if before:
        parts += [before]
    parts += [target_src.rstrip()]
    if after:
        parts += ["", after]
    source = "\n".join(parts).rstrip() + "\n"

    # Tests: the target test (fails on the defective original) + one test per filler (all pass).
    target_test_src = f"def test_target():\n    assert {test_expr} == {expected}\n"
    filler_tests = "\n".join(t for _, t in fillers)
    tests = (
        f"from module_under_test import *\n\n\n{target_test_src}\n{filler_tests}"
    ).rstrip() + "\n"

    return Task(
        name=f"{bucket}-{idx:02d}-{fn_name}-import",
        bucket=bucket,
        target_fn=fn_name,
        target_test="test_target",
        behavior=f"Modify the function `{fn_name}` so that it will {behavior_tail}.",
        source=source,
        tests=tests,
        required_module=module,
    )


def reference_solution(task: Task) -> str:
    """The task's source, correctly repaired: the required module imported at TOP LEVEL and the
    target body replaced.

    This is the probe's negative control, not a convenience. If it does not go green, a zero
    from the live run would be measuring an impossible task while looking exactly like the
    finding (s133: "a check that can only pass teaches nothing", inverted).

    The import is placed after the module docstring deliberately — that position is the one a
    `replace_unit` operation cannot express, which is the whole point of criterion 5.
    """
    for fn_name, sig, _bad, module, fixed_body, _tail, _expr, _exp in IMPORT_DEFECTS:
        if task.target_fn != fn_name:
            continue
        lines = task.source.splitlines()
        try:
            at = next(i for i, l in enumerate(lines) if l.strip() == sig.strip())
        except StopIteration:  # pragma: no cover — generator and table would have to disagree
            raise ValueError(f"{task.name}: signature {sig!r} not found in source") from None

        # Body replacement first, so the index `at` is still valid.
        body = ["    " + b for b in fixed_body.split("\n    ")]
        lines[at + 1:at + 2] = body

        # Then the top-level import, immediately after the module docstring.
        insert_at = 1 if lines and lines[0].lstrip().startswith('"""') else 0
        lines[insert_at:insert_at] = ["", f"import {module}"]
        return "\n".join(lines).rstrip() + "\n"

    raise ValueError(f"{task.name}: target_fn {task.target_fn!r} not in IMPORT_DEFECTS")


# --- Constant-requiring tasks (P3-D1 remedy 2, s140) ---------------------------
#
# The constant is read by THREE functions and the target test asserts all three, so editing any
# ONE function body leaves two assertions failing. That is the point: it turns "the model
# repaired a consumer instead of the constant" into a visible test failure instead of a silent
# pass. Every consumer is STRICTLY PROPORTIONAL to the constant, so the behaviour text is true
# of all three -- a squared or cubed consumer (the local model's first draft) makes the prompt's
# own description wrong for two thirds of the assertions it has to satisfy.
#
# `behavior_tail` never names the constant and never says which unit to edit. Naming the
# address would hand the model the answer to the one question this corpus exists to ask.
CONSTANT_DEFECTS = [
    (
        "SCALE_FACTOR",
        "SCALE_FACTOR = 2",
        "SCALE_FACTOR = 10",
        [
            ("def scale_value(x):\n    return x * SCALE_FACTOR", "scale_value(5)", 50),
            ("def scaled_total(xs):\n    return sum(x * SCALE_FACTOR for x in xs)",
             "scaled_total([1, 2])", 30),
            ("def half_scaled(x):\n    return (x * SCALE_FACTOR) // 2", "half_scaled(4)", 20),
        ],
        "every scaled result is five times larger than it currently is",
    ),
    (
        "MAX_RETRIES",
        "MAX_RETRIES = 1",
        "MAX_RETRIES = 4",
        [
            ("def should_retry(attempt):\n    return attempt < MAX_RETRIES", "should_retry(2)", True),
            ("def retry_countdown(start):\n    return list(range(start, -1, -1))[:MAX_RETRIES]",
             "retry_countdown(5)", [5, 4, 3, 2]),
            ("def max_attempts_reached(attempts):\n    return attempts >= MAX_RETRIES",
             "max_attempts_reached(3)", False),
        ],
        "four attempts are allowed rather than the one it currently permits",
    ),
]


def generate_constant_task(bucket: str, idx: int) -> Task:
    """Build one constant-requiring Task for a size bucket.

    ``target_fn`` is the CONSTANT's name, so ``target_path`` defaults to it and the
    symbol-addressed arm is asked for an address only the s140 resolver extension can resolve.
    """
    n_filler = BUCKET_FILLER[bucket]
    const_name, bad_stmt, _good, consumers, tail = CONSTANT_DEFECTS[idx % len(CONSTANT_DEFECTS)]

    fillers = [_filler(k) for k in range(n_filler)]
    half = n_filler // 2
    before = "\n".join(f for f, _ in fillers[:half])
    after = "\n".join(f for f, _ in fillers[half:])

    parts = ['"""Generated benchmark module (constant-requiring)."""', "", bad_stmt, ""]
    if before:
        parts += [before]
    parts += [f"{fn_src}\n" for fn_src, _, _ in consumers]
    if after:
        parts += ["", after]
    source = "\n".join(parts).rstrip() + "\n"

    asserts = "".join(f"    assert {expr} == {expected!r}\n" for _, expr, expected in consumers)
    filler_tests = "\n".join(t for _, t in fillers)
    tests = (
        f"from module_under_test import *\n\n\ndef test_target():\n{asserts}\n{filler_tests}"
    ).rstrip() + "\n"

    return Task(
        name=f"{bucket}-{idx:02d}-{const_name.lower()}-constant",
        bucket=bucket,
        target_fn=const_name,
        target_test="test_target",
        behavior=f"Fix the module so that {tail}.",
        source=source,
        tests=tests,
    )


def constant_reference_solution(task: Task) -> str:
    """The task's source with ONLY the defective constant statement corrected.

    The probe's negative control, not a convenience. If it does not go green, a zero from the
    live run would be measuring an impossible task while looking exactly like the finding
    (s133: "a check that can only pass teaches nothing", inverted).
    """
    for const_name, bad_stmt, good_stmt, _consumers, _tail in CONSTANT_DEFECTS:
        if task.target_fn != const_name:
            continue
        lines = task.source.splitlines()
        try:
            at = next(i for i, l in enumerate(lines) if l.strip() == bad_stmt)
        except StopIteration:  # pragma: no cover — generator and table would have to disagree
            raise ValueError(f"{task.name}: {bad_stmt!r} not found in source") from None
        lines[at] = good_stmt
        return "\n".join(lines).rstrip() + "\n"

    raise ValueError(f"{task.name}: target_fn {task.target_fn!r} not in CONSTANT_DEFECTS")
