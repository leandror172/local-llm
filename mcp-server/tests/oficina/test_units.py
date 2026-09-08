"""Unit addressing for production edits (P3-D1(B), build step 1).

Pure-function SUT: `(source, path) -> span` and `(source, path, body) -> (old, new)`. No
sequence, no state, so per `ref:test-executable-spec` rule 5 the given/when/then scaffold
COLLAPSES — the vocabulary here is builder-nouns plus verdict predicates and nothing more.
Resisting a mutation mini-language is deliberate: over-DSLing a pure-function family is the
most common way to violate that doc's rule 3.

The copied resolver surface (`find_units`/`resolve_unit`) is characterized by the benchmark's
own suite; what is asserted here is that the COPY is faithful on each distinct reason, plus
the full behaviour of the one genuinely new function, `render_unit_replacement`.
"""

import ast

import pytest

from ollama_mcp.oficina.units import (
    KINDS,
    find_units,
    render_unit_replacement,
    resolve_unit,
)

# --- vocabulary ------------------------------------------------------------------------

# Two classes declare a BYTE-IDENTICAL one-line constant. Both resolve uniquely by path and
# their span text occurs twice, which is the case `patch_file`'s uniqueness check refuses.
# Measured on the real corpus (s141): 5 of 899 uniquely-resolved units collide this way, and
# all five are `model_config` lines in `intake.py` -- a file in T-122's blocked set and a
# named criterion 3 target, so this is reachable exactly where the first real run lands.
UNITS_SRC = '''\
"""Module docstring."""
import ast

TIMEOUT = 30


def plain():
    return 1


class Alpha:
    LIMIT = 5

    def area(self):
        return 2


class Beta:
    LIMIT = 5

    def area(self):
        return 3
'''

SHARED_BINDING_SRC = "A, B = 1, 2\n"
UNPARSEABLE_SRC = "def broken(:\n"

A_NEW_BODY = "def plain():\n    return 99\n"
A_NEW_METHOD_AT_COLUMN_ZERO = "def area(self):\n    return 42\n"
A_NEW_CONSTANT = "LIMIT = 7"


def pair_for(path, body, kind=None, source=UNITS_SRC):
    """The (old_string, new_string) pair, asserting the render succeeded."""
    pair, reason = render_unit_replacement(source, path, body, kind)
    assert reason is None, f"expected a pair, got reason {reason!r}"
    return pair


def refuses(path, body, with_reason, kind=None, source=UNITS_SRC):
    pair, reason = render_unit_replacement(source, path, body, kind)
    assert pair is None
    assert reason == with_reason


def applied(pair, source=UNITS_SRC):
    """The source as `patch_file` would leave it -- exact replace, first occurrence."""
    old, new = pair
    assert source.count(old) == 1, "patch_file would REFUSE: old_string is not unique"
    return source.replace(old, new, 1)


# --- the copied resolver: one assertion per distinct reason ----------------------------


def test_a_top_level_function_resolves_to_exactly_one_span():
    assert len(find_units(UNITS_SRC, ["plain"])) == 1


def test_a_method_resolves_through_its_class():
    span, reason = resolve_unit(UNITS_SRC, ["Alpha", "area"], "Method")
    assert reason is None and span is not None


def test_a_module_constant_is_addressable():
    span, reason = resolve_unit(UNITS_SRC, ["TIMEOUT"], "Constant")
    assert reason is None and span is not None


def test_an_absent_name_is_no_match_not_an_empty_success():
    assert resolve_unit(UNITS_SRC, ["nope"]) == (None, "no_match")


def test_a_kind_that_does_not_exist_is_a_request_defect():
    assert resolve_unit(UNITS_SRC, ["plain"], "Widget") == (None, "unknown_kind")


def test_a_wrong_kind_is_reported_rather_than_ignored():
    assert resolve_unit(UNITS_SRC, ["plain"], "Class") == (None, "kind_mismatch")


def test_an_unparseable_source_raises_rather_than_reading_as_absent():
    assert resolve_unit(UNPARSEABLE_SRC, ["broken"]) == (None, "parse_error")


def test_a_shared_binding_refuses_rather_than_rewriting_its_sibling():
    assert resolve_unit(SHARED_BINDING_SRC, ["A"]) == (None, "shared_binding")


def test_the_prompt_facing_kind_list_is_the_one_the_resolver_enforces():
    # s140's instrument trap, pinned in this copy too: a vocabulary the code owns must be
    # RENDERED from it. If `KINDS` grows and a prompt restates the old list, the new
    # capability is unreachable by the model and the arm reports a clean zero for a case it
    # never offered.
    assert "Constant" in KINDS and "ClassConstant" in KINDS


# --- render_unit_replacement: the new function -----------------------------------------


def test_it_returns_an_exact_pair_that_reproduces_the_edit():
    out = applied(pair_for(["plain"], A_NEW_BODY))
    assert "return 99" in out and "return 1" not in out
    assert ast.parse(out)


def test_the_harness_owns_indentation_for_a_method():
    # s137's finding, and the reason `apply_unit`'s contract had to graduate alongside the
    # locator: the model emits at column 0, the class body needs column 4. `patch_file` is an
    # exact-string replace and would splice the model's text verbatim.
    out = applied(pair_for(["Alpha", "area"], A_NEW_METHOD_AT_COLUMN_ZERO))
    assert "    def area(self):\n        return 42" in out
    assert ast.parse(out)


def test_a_colliding_span_is_widened_until_patch_file_can_apply_it():
    # THE NEGATIVE CONTROL FOR THE WIDENING. `Alpha.LIMIT` and `Beta.LIMIT` are byte-identical
    # lines: the SPAN is unique, the TEXT is not. A renderer handing back the bare span text
    # makes `patch_file` refuse with `old_string found 2 times` on an edit that is perfectly
    # addressable. Remove the widening and `applied`'s uniqueness assertion fails here.
    pair = pair_for(["Alpha", "LIMIT"], A_NEW_CONSTANT)
    old, _new = pair
    assert UNITS_SRC.count(old) == 1
    out = applied(pair)
    assert "class Alpha:\n    LIMIT = 7" in out
    assert "class Beta:\n    LIMIT = 5" in out, "the sibling must be untouched"
    assert ast.parse(out)


def test_widening_edits_the_addressed_unit_and_not_its_twin():
    # The claim above, stated as the property rather than as string containment: exactly one
    # of the two identical constants changed.
    out = applied(pair_for(["Beta", "LIMIT"], A_NEW_CONSTANT))
    assert out.count("LIMIT = 5") == 1 and out.count("LIMIT = 7") == 1


@pytest.mark.parametrize(
    "path, source, expected",
    [
        (["nope"], UNITS_SRC, "no_match"),
        (["plain"], UNPARSEABLE_SRC, "parse_error"),
        (["A"], SHARED_BINDING_SRC, "shared_binding"),
    ],
)
def test_the_refusal_reason_survives_into_the_pair_channel(path, source, expected):
    # `patterns-code-value-or-error`: the benchmark's `apply_unit` collapses every failure to
    # None, which is right for an A/B harness that only counts applies. Production ROUTES on
    # the reason -- a `no_match` is a prompt problem, a `shared_binding` is a whole-file
    # fallback -- so the reason must not be thrown away at this seam.
    refuses(path, "X = 1", with_reason=expected, source=source)


def test_a_kind_mismatch_refuses_instead_of_landing_the_edit_somewhere_plausible():
    refuses(["plain"], A_NEW_BODY, kind="Class", with_reason="kind_mismatch")


def test_a_body_already_indented_is_not_double_indented():
    # The model sometimes emits a method already indented. Dedent-then-reindent must be
    # idempotent, or the harness owning indentation becomes the harness corrupting it.
    out = applied(pair_for(["Alpha", "area"], "    def area(self):\n        return 42\n"))
    assert "        def area" not in out
    assert ast.parse(out)


# --- LanguagePack member #5: which languages can be symbol-addressed --------------------
# These live here rather than beside the other pack tests because the property under test is
# unit addressing, surfaced THROUGH the pack. The pack is only the place the answer is kept,
# so that no `language == "python"` conditional is needed at the call site.


def test_python_declares_a_unit_renderer():
    from ollama_mcp.oficina.evaluator import PYTHON

    assert PYTHON.unit_renderer is render_unit_replacement


def test_go_declares_none_because_no_go_locator_exists():
    # P3-D10 (s141): "a shape that cannot be derived is whole_file". A missing locator is read
    # exactly as a missing context ceiling -- decline to act, keep today's behaviour. Asserting
    # None is asserting that Go runs are UNCHANGED, which is the actual claim.
    from ollama_mcp.oficina.evaluator import GO

    assert GO.unit_renderer is None


def test_the_pack_answers_the_capability_question_for_a_resolved_spec():
    from ollama_mcp.oficina.evaluator import language_pack

    assert language_pack({"deliverable": {"language": "python"}}).unit_renderer is not None
    assert language_pack({"deliverable": {"language": "go"}}).unit_renderer is None
