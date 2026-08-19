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
from writemodel_corpus import (
    DEFECTS,
    IMPORT_DEFECTS,
    TARGET_SIG,
    generate_class_task,
    generate_corpus,
    generate_import_task,
    generate_task,
    reference_solution,
)

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


# --- import-requiring tasks (P3-T0 criterion 5a) ------------------------------
#
# These exist because criterion 5's s137 result was 0/12 and MEANINGLESS: no task in the
# corpus needed a statement the model cannot address, so "no function-local imports" reported
# that the case never arose. A designed task is the only way to exercise it.
#
# The validity bar here is higher than for the other generators. A task that can be repaired
# WITHOUT the new import does not exercise the criterion at all -- it would return another
# clean zero wearing a different mask, which is the precise failure being corrected.


def test_import_task_source_has_no_imports_at_all():
    """The forcing property. If the module already imports something, a model can reuse it and
    never faces the unaddressable case; and `find_units` has no dotted address for an import,
    so adding one cannot be expressed as replace_unit (P3-D1 item 6)."""
    for bucket in BUCKETS:
        for idx in range(2):
            task = generate_import_task(bucket, idx)
            tree = ast.parse(task.source)
            imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            assert imports == [], f"{task.name}: source already imports something"


def test_import_task_behavior_names_the_module_it_needs():
    """`no addressable repair exists` is enforced by the BRIEF naming the module, not by
    semantic impossibility -- pure Python can hand-roll gcd or accumulate. A model that
    hand-rolls instead is a COUNTED OUTCOME of 5a ("avoided the unaddressable statement"),
    not a broken task, and this assertion is what makes that reading legitimate."""
    for bucket in BUCKETS:
        for idx in range(2):
            task = generate_import_task(bucket, idx)
            assert task.required_module in task.behavior, (
                f"{task.name}: brief must name {task.required_module!r} explicitly, else a "
                "hand-rolled fix is indistinguishable from a model dodging the import"
            )


def test_import_task_ground_truth_holds():
    """Same bar as every other generator: a real defect, and a sound regression surface."""
    for bucket in BUCKETS:
        task = generate_import_task(bucket, 0)
        target_fails, fillers_pass = _ground_truth(task)
        assert target_fails, f"{task.name}: target test PASSES on the original — no defect"
        assert fillers_pass, f"{task.name}: a filler test fails on the original"


def test_import_task_is_actually_solvable():
    """The negative control for the whole probe. If the reference fix does not go green, a
    zero from the live run would measure an impossible task, not model behaviour -- and would
    look exactly like the finding."""
    for bucket in BUCKETS:
        task = generate_import_task(bucket, 0)
        fixed = reference_solution(task)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "module_under_test.py").write_text(fixed, encoding="utf-8")
            (tmp / "test_gen.py").write_text(task.tests, encoding="utf-8")
            rc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--no-header", "test_gen.py"],
                cwd=str(tmp), capture_output=True, text=True,
            )
        assert rc.returncode == 0, (
            f"{task.name}: reference solution does not pass:\n{rc.stdout[-800:]}"
        )


def test_import_task_reference_solution_adds_a_top_level_import():
    """Pins what 'solved' means here: the fix is not merely green, it is green BY adding the
    statement the schema cannot express. Without this the reference could hand-roll and the
    task would silently stop testing what it exists to test."""
    task = generate_import_task("small", 0)
    tree = ast.parse(reference_solution(task))
    top_level_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert top_level_imports, "reference solution must add a module-level import"


def test_import_task_target_function_IS_dotted_addressable():
    """Isolates the variable. The function body is perfectly addressable; ONLY the import is
    not. If the target itself were unaddressable, a failure would have two candidate causes."""
    for bucket in BUCKETS:
        task = generate_import_task(bucket, 0)
        spans = find_units(task.source, task.target_path)
        assert len(spans) == 1, f"{task.name}: target resolved to {len(spans)} units, want 1"


# --- the brief and the signature must agree (s139) -----------------------------
#
# FOUND BY ACCIDENT, WHICH IS THE POINT. A delegated edit silently changed
# TARGET_SIG["clamp"] from `def clamp(value, lo, hi)` to `... lo, hhi`, and the whole suite
# stayed green: the target test calls `clamp(15, 0, 10)` POSITIONALLY, so a renamed parameter
# changes nothing observable. The ground-truth tests verify the corpus's BEHAVIOUR while its
# consumer -- the model -- reads its TEXT, and nothing compared the two
# (ref:corpus-divergence-pattern).
#
# The invariant that makes the text checkable: every parameter must be referred to in the
# brief. A parameter the brief never mentions is one the model was never told what to do with,
# which is a defective task independently of any typo.

import re


def _params(sig: str) -> list[str]:
    """Parameter names of a `def f(...):` signature line, `self` excluded."""
    fn = ast.parse(sig + "\n    pass\n").body[0]
    return [a.arg for a in fn.args.args if a.arg != "self"]


def test_every_defect_brief_mentions_every_parameter():
    checked = 0
    for fn_name, _bad, behavior_tail, test_expr, _expected in DEFECTS:
        for param in _params(TARGET_SIG[fn_name]):
            haystack = f"{behavior_tail} {test_expr}"
            assert re.search(rf"\b{re.escape(param)}\b", haystack), (
                f"DEFECTS[{fn_name}]: parameter {param!r} is never mentioned in the brief "
                f"({behavior_tail!r}) — the model is not told what it is for, and a typo in "
                f"the signature would be invisible to every behavioural test"
            )
            checked += 1
    assert checked, "table empty — this check would pass vacuously"


def test_every_import_defect_brief_mentions_every_parameter():
    checked = 0
    for fn_name, sig, _bad, _mod, _fixed, behavior_tail, test_expr, _exp in IMPORT_DEFECTS:
        for param in _params(sig):
            haystack = f"{behavior_tail} {test_expr}"
            assert re.search(rf"\b{re.escape(param)}\b", haystack), (
                f"IMPORT_DEFECTS[{fn_name}]: parameter {param!r} never mentioned in the brief"
            )
            checked += 1
    assert checked, "table empty — this check would pass vacuously"


def test_target_signature_in_source_matches_the_table():
    """The generated file must contain the signature the table declares — the two drifting is
    exactly how a corrupted brief would reach a live run unnoticed."""
    for bucket in BUCKETS:
        for idx in range(len(DEFECTS)):
            task = generate_task(bucket, idx)
            assert TARGET_SIG[task.target_fn] in task.source, (
                f"{task.name}: source does not contain {TARGET_SIG[task.target_fn]!r}"
            )
