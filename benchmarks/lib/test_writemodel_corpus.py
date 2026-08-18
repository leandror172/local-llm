"""Ground-truth tests for the write-model benchmark corpus generator (P3-T0).

The benchmark's validity rests on one property that nothing checked until now: **the generated
original must FAIL its target test and PASS every filler test.** If that ever inverts, each arm
scores against a task with no real defect (or an unfixable one) and the whole run is noise
wearing the shape of data — the corpus-divergence failure at its most expensive, since the
numbers still print.

`generate_class_task` exists because a corpus of flat top-level functions **cannot express
criterion 2** — "does the model name the CLASS instead of the METHOD". With no classes there is
nothing to name coarsely, so the symbol-addressed arm would report a clean pass that means
nothing: a check that can only pass.
"""

import ast
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writemodel_apply import find_units, resolve_unit
from writemodel_corpus import generate_class_task, generate_corpus, generate_task

BUCKETS = ("small", "medium", "large")


def _ground_truth(task) -> tuple[bool, bool]:
    """(target_test_fails, filler_tests_pass) for the UNEDITED source. The benchmark is only
    meaningful when this is (True, True) — a real defect, and a sound regression surface."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "module_under_test.py").write_text(task.source, encoding="utf-8")
        (tmp / "test_gen.py").write_text(task.tests, encoding="utf-8")

        def run(*args):
            return subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--no-header", *args],
                cwd=str(tmp), capture_output=True, text=True,
            ).returncode

        target_fails = run(f"test_gen.py::{task.target_test}") != 0
        fillers_pass = run("test_gen.py", "--deselect", f"test_gen.py::{task.target_test}") == 0
        return target_fails, fillers_pass


# --- structural validity, across the whole corpus ----------------------------


def test_every_generated_source_and_test_file_parses():
    for task in generate_corpus(per_bucket=2):
        ast.parse(task.source)
        ast.parse(task.tests)


def test_every_class_task_source_and_test_file_parses():
    for bucket in BUCKETS:
        for idx in range(2):
            task = generate_class_task(bucket, idx)
            ast.parse(task.source)
            ast.parse(task.tests)


# --- ground truth: the property the whole benchmark rests on -----------------


def test_flat_task_original_fails_target_and_passes_fillers():
    assert _ground_truth(generate_task("small", 0)) == (True, True)


def test_class_task_original_fails_target_and_passes_fillers():
    assert _ground_truth(generate_class_task("small", 0)) == (True, True)


# --- addressing: what the class task exists to make measurable ---------------


def test_flat_task_target_path_defaults_to_the_bare_name():
    task = generate_task("small", 0)
    assert task.target_path == [task.target_fn]


def test_class_task_target_path_is_DOTTED():
    task = generate_class_task("small", 0)
    assert len(task.target_path) == 2
    assert task.target_path[1] == task.target_fn


def test_class_task_target_resolves_to_exactly_one_method():
    for bucket in BUCKETS:
        task = generate_class_task(bucket, 0)
        span, reason = resolve_unit(task.source, task.target_path, kind="Method")
        assert reason is None, f"{bucket}: {reason}"
        assert span is not None


def test_class_task_makes_criterion_2_measurable():
    """Naming the CLASS must be meaningfully coarser than naming the METHOD.

    If the class were only its target method, a coarse address would cost nothing and the
    criterion could not discriminate — the same defect as having no classes at all, one
    level subtler.
    """
    for bucket in BUCKETS:
        task = generate_class_task(bucket, 0)
        (class_span,) = find_units(task.source, task.target_path[:1])
        (method_span,) = find_units(task.source, task.target_path)
        class_lines = class_span[1] - class_span[0] + 1
        method_lines = method_span[1] - method_span[0] + 1
        assert class_lines >= 3 * method_lines, (
            f"{bucket}: class {class_lines} lines vs method {method_lines} — too close to "
            "discriminate a coarse address"
        )


def test_class_task_source_contains_top_level_functions_too():
    """Heterogeneous by construction: the file holds BOTH a class and plain functions, so a
    run measures addressing across both, not just the easy uniform case E-D1 warned about."""
    task = generate_class_task("medium", 0)
    tree = ast.parse(task.source)
    assert any(isinstance(n, ast.ClassDef) for n in tree.body)
    assert any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in tree.body)
