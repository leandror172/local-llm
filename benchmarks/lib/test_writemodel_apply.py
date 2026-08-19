"""Unit tests for the write-model benchmark apply layer (T-104). Model-free, deterministic."""

import pytest

from writemodel_apply import (
    KINDS,
    apply_code_anchored,
    apply_search_replace,
    apply_unit,
    apply_whole_file,
    find_units,
    locate_function,
    parse_search_replace_blocks,
    resolve_unit,
    strip_code_fences,
)

SRC = '''\
import math


def area(w, h):
    return w * h


@staticmethod
def perimeter(w, h):
    return 2 * (w + h)


async def volume(w, h, d):
    return w * h * d
'''


# --- locate_function --------------------------------------------------------


def test_locate_plain_function():
    assert locate_function(SRC, "area") == (4, 5)


def test_locate_includes_decorator():
    # span starts at the @staticmethod line, not the def line
    assert locate_function(SRC, "perimeter") == (8, 10)


def test_locate_async_function():
    assert locate_function(SRC, "volume") == (13, 14)


def test_locate_missing_returns_none():
    assert locate_function(SRC, "nope") is None


def test_locate_syntax_error_returns_none():
    assert locate_function("def broken(:\n    pass", "broken") is None


# --- parse_search_replace_blocks --------------------------------------------

ONE_BLOCK = """\
some prose
<<<<<<< SEARCH
    return w * h
=======
    return w * h * 2
>>>>>>> REPLACE
trailing prose
"""


def test_parse_one_block():
    assert parse_search_replace_blocks(ONE_BLOCK) == [("    return w * h", "    return w * h * 2")]


def test_parse_preserves_interior_lines():
    # first and last content lines must survive (the local-model draft dropped them)
    text = "<<<<<<< SEARCH\nfirst\nmiddle\nlast\n=======\nnew\n>>>>>>> REPLACE\n"
    assert parse_search_replace_blocks(text) == [("first\nmiddle\nlast", "new")]


def test_parse_multiple_blocks():
    text = (
        "<<<<<<< SEARCH\na\n=======\nA\n>>>>>>> REPLACE\n"
        "<<<<<<< SEARCH\nb\n=======\nB\n>>>>>>> REPLACE\n"
    )
    assert parse_search_replace_blocks(text) == [("a", "A"), ("b", "B")]


def test_parse_no_blocks():
    assert parse_search_replace_blocks("just prose, no markers") == []


# --- strip_code_fences ------------------------------------------------------


def test_strip_fenced():
    assert strip_code_fences("```python\ndef f(): pass\n```") == "def f(): pass"


def test_strip_unfenced_passthrough():
    assert strip_code_fences("def f(): pass") == "def f(): pass"


# --- apply_code_anchored (arm A) --------------------------------------------


def test_apply_code_anchored_replaces_span():
    new = apply_code_anchored(SRC, "area", "def area(w, h):\n    return w * h * 2")
    assert "return w * h * 2" in new
    # untouched functions survive verbatim
    assert "async def volume(w, h, d):" in new
    assert "def perimeter(w, h):" in new


def test_apply_code_anchored_locate_miss_returns_none():
    assert apply_code_anchored(SRC, "nope", "def nope(): pass") is None


def test_apply_code_anchored_result_parses():
    import ast

    new = apply_code_anchored(SRC, "area", "def area(w, h):\n    return w + h")
    ast.parse(new)  # must remain valid Python


# --- apply_whole_file (arm B) -----------------------------------------------


def test_apply_whole_file_is_output():
    assert apply_whole_file("whatever the model returned") == "whatever the model returned"


# --- apply_search_replace (arm C) -------------------------------------------


def test_apply_search_replace_success():
    out = apply_search_replace(SRC, ONE_BLOCK)
    assert out is not None and "return w * h * 2" in out


def test_apply_search_replace_no_match_is_loud_none():
    # the model's search text is not present verbatim -> loud failure
    bad = "<<<<<<< SEARCH\n    return NONEXISTENT\n=======\n    return 0\n>>>>>>> REPLACE\n"
    assert apply_search_replace(SRC, bad) is None


def test_apply_search_replace_no_blocks_is_none():
    assert apply_search_replace(SRC, "no blocks here") is None


def test_apply_search_replace_strips_interior_fences():
    # the model fenced the block contents (common 14B behavior) — fair appliers strip them
    fenced = (
        "<<<<<<< SEARCH\n```python\n    return w * h\n```\n=======\n"
        "```python\n    return w * h * 2\n```\n>>>>>>> REPLACE\n"
    )
    out = apply_search_replace(SRC, fenced)
    assert out is not None and "return w * h * 2" in out


# --- find_units / resolve_unit — dotted addressing (P3-T0) -------------------
#
# `locate_function` above resolves ONLY top-level functions, which is 69% of loop.py by line
# and 10% by addressable unit (ref:unit-addressing-census). Dotted `Class.method` addressing is
# what P3-D1 option (B) actually needs, so it is built ALONGSIDE rather than folded in —
# locate_function is the instrument that produced arm A's published numbers.
#
# Fixture hazards are deliberate (census Finding 3 + the P3-T0 method):
#   - a decorated function AND a decorated method — the span must start at the decorator
#   - a docstring'd method — in Python the docstring is INSIDE the span (this test can only
#     pass; it is here to pin the boundary, not to discriminate)
#   - a `#` comment above a def — OUTSIDE the span, because `ast` does not model comments.
#     The rule is "the unit is whatever the language's parser attaches to the node", which
#     yields decorators in Python and `decl.Doc` in Go, by construction rather than by a
#     hand-authored per-language list. This is the one span test that CAN fail.
#   - duplicate definitions at module AND class level — multi-match, never first-match-wins
#   - a closure and a conditionally-defined function — the refusal region (survey § 5)
#   - module-level statements with no name (import, module docstring) — unaddressable BY
#     CONSTRUCTION. This is the complement of the census's 89.1%, and it is the bound on
#     what option (B) can express at all.
#   - a module CONSTANT is a different case and this comment used to get it wrong (fixed
#     s139): it BINDS A NAME, and the census counts `assign` as `named`. It is unresolvable
#     here only because `_UNIT_NODES` does not index assignments — our resolver's gap, not
#     Python's. Criterion 5b measured it as the LARGEST unaddressable class (30.4% of
#     oficina's own edits), so filing it under "by construction" had hidden the biggest and
#     most fixable slice of the problem.

UNITS_SRC = '''\
"""Module docstring — not an addressable unit."""

import ast
from typing import Optional

CONSTANT = 42


def plain():
    return 1


# a leading comment, deliberately NOT part of the unit below
def commented():
    return 2


@staticmethod
def decorated():
    return 3


def duplicated():
    return "first"


def duplicated():
    return "second"


class Shape:
    """A documented class."""

    KIND = "shape"

    def area(self):
        """Docstring is INSIDE the span."""
        return 0

    @property
    def name(self):
        return "shape"

    async def render(self):
        return None

    def dup(self):
        return 1

    def dup(self):
        return 2

    class Inner:
        def deep(self):
            return 9


def outer():
    def local():
        return "unaddressable"
    return local


if True:
    def conditional():
        return "also unaddressable"
'''


# --- find_units: resolution ---------------------------------------------------


def test_find_plain_top_level_function():
    assert find_units(UNITS_SRC, ["plain"]) == [(9, 10)]


def test_find_dotted_method():
    assert find_units(UNITS_SRC, ["Shape", "area"]) == [(36, 38)]


def test_find_async_method():
    assert find_units(UNITS_SRC, ["Shape", "render"]) == [(44, 45)]


def test_find_nested_class():
    assert find_units(UNITS_SRC, ["Shape", "Inner"]) == [(53, 55)]


def test_find_method_of_nested_class():
    assert find_units(UNITS_SRC, ["Shape", "Inner", "deep"]) == [(54, 55)]


def test_find_class_resolves_to_the_whole_class():
    # Naming the class instead of the method is criterion 2's design-killing failure
    # (EvaluatedLoop is 69% of loop.py), so a class MUST resolve — and resolve to a span
    # whose size is measurable — rather than being quietly unavailable.
    assert find_units(UNITS_SRC, ["Shape"]) == [(31, 55)]


# --- find_units: span boundaries (census Finding 3) ---------------------------


def test_find_decorated_function_span_starts_at_decorator():
    assert find_units(UNITS_SRC, ["decorated"]) == [(18, 20)]


def test_find_decorated_method_span_starts_at_decorator():
    assert find_units(UNITS_SRC, ["Shape", "name"]) == [(40, 42)]


def test_find_method_docstring_is_inside_the_span():
    (start, end), = find_units(UNITS_SRC, ["Shape", "area"])
    body = "\n".join(UNITS_SRC.splitlines()[start - 1 : end])
    assert "Docstring is INSIDE the span." in body


def test_find_comment_above_def_is_outside_the_span():
    # The decision, made explicit: `ast` does not attach comments, so they are not the unit.
    # In Go the parser DOES attach decl.Doc, so the same rule includes it there.
    assert find_units(UNITS_SRC, ["commented"]) == [(14, 15)]


# --- find_units: multi-match, never first-match-wins (survey § 3) -------------


def test_find_duplicate_top_level_defs_returns_both():
    assert find_units(UNITS_SRC, ["duplicated"]) == [(23, 24), (27, 28)]


def test_find_duplicate_methods_returns_both():
    assert find_units(UNITS_SRC, ["Shape", "dup"]) == [(47, 48), (50, 51)]


# --- find_units: the refusal region (survey § 5) ------------------------------


def test_find_does_not_descend_into_function_bodies():
    # A closure has no stable address; whole-file is the recorded fallback, and refusing
    # here surfaces as a loud no_match rather than a wrong span.
    assert find_units(UNITS_SRC, ["outer", "local"]) == []


def test_find_does_not_descend_into_conditional_blocks():
    # `def` under if/try — the optional-import fallback shape. Also refused.
    assert find_units(UNITS_SRC, ["conditional"]) == []


def test_find_module_constant_is_not_addressable():
    # NOT "a statement with no name" — that was this comment's error until s139, and it was
    # copied from P3-D1 item 6, which had itself corrupted the census. `CONSTANT = 42` binds a
    # name; the census counts `assign` as `named`. This returns [] because `_UNIT_NODES` covers
    # only FunctionDef/AsyncFunctionDef/ClassDef, so the resolver never indexes assignments.
    # A RESOLVER GAP, closable by extending _UNIT_NODES + adding a kind — not a language bound.
    assert find_units(UNITS_SRC, ["CONSTANT"]) == []


def test_find_import_is_not_addressable():
    # Consequence worth stating in a test rather than a doc: an edit that needs a NEW import
    # cannot be expressed as replace_unit. "Import merging" was named as an unpriced cost of
    # the code-anchored design and it is still unpriced.
    assert find_units(UNITS_SRC, ["ast"]) == []


def test_find_absent_path_is_empty():
    assert find_units(UNITS_SRC, ["nope"]) == []


# --- find_units: [] has exactly ONE meaning -----------------------------------


def test_find_raises_on_unparseable_source():
    # Absent is []. Unparseable travels on a different channel, so the two can never be
    # confused by a caller — which is what locate_function's Optional could not do.
    with pytest.raises(SyntaxError):
        find_units("def broken(:\n    pass", ["broken"])


# --- resolve_unit: the four resolution outcomes -------------------------------


def test_resolve_unique_returns_span_and_no_reason():
    assert resolve_unit(UNITS_SRC, ["Shape", "area"]) == ((36, 38), None)


def test_resolve_absent_is_no_match():
    assert resolve_unit(UNITS_SRC, ["nope"]) == (None, "no_match")


def test_resolve_duplicate_is_multi_match():
    # NEGATIVE CONTROL: a path resolving to two units fails loud. A silent no-op or a
    # first-match win is what this asserts cannot happen.
    assert resolve_unit(UNITS_SRC, ["duplicated"]) == (None, "multi_match")


def test_resolve_unparseable_is_parse_error():
    # NEGATIVE CONTROL: distinguishable from no_match, so the probe can tally it separately.
    assert resolve_unit("def broken(:\n    pass", ["broken"]) == (None, "parse_error")


# --- resolve_unit: kind is a CHECK, never a selector --------------------------


def test_resolve_accepts_matching_kind():
    assert resolve_unit(UNITS_SRC, ["plain"], kind="Function") == ((9, 10), None)


def test_resolve_accepts_class_kind():
    assert resolve_unit(UNITS_SRC, ["Shape"], kind="Class") == ((31, 55), None)


def test_resolve_kind_is_derived_from_position_not_node_type():
    # ast.FunctionDef is a Function at module level and a Method inside a class — the SAME
    # node class. Position is the only thing that distinguishes them.
    assert resolve_unit(UNITS_SRC, ["Shape", "area"], kind="Method") == ((36, 38), None)
    assert resolve_unit(UNITS_SRC, ["plain"], kind="Method") == (None, "kind_mismatch")


def test_resolve_method_of_nested_class_is_a_method():
    assert resolve_unit(UNITS_SRC, ["Shape", "Inner", "deep"], kind="Method") == ((54, 55), None)


def test_resolve_class_named_where_method_meant_is_loud():
    # Criterion 2's failure mode made DETECTABLE: the model said Method and named a class
    # that is most of the file. This narrows the silent region; it does not close it — a
    # model that says Class and means it is self-consistent and still coarse.
    assert resolve_unit(UNITS_SRC, ["Shape"], kind="Method") == (None, "kind_mismatch")


# --- resolve_unit: the kind vocabulary is a CLOSED set ------------------------


def test_resolve_kind_vocabulary_is_closed():
    assert KINDS == ("Function", "Method", "Class")


def test_resolve_unknown_kind_is_its_own_reason():
    # "your vocabulary is wrong" and "you named the wrong unit" have OPPOSITE remedies — a
    # prompt fix vs. abandoning the design — so they must not share a bucket.
    assert resolve_unit(UNITS_SRC, ["plain"], kind="function") == (None, "unknown_kind")
    assert resolve_unit(UNITS_SRC, ["plain"], kind="func") == (None, "unknown_kind")


def test_resolve_validates_kind_before_resolving():
    # An unknown kind is a defect in the REQUEST. Report it as such rather than reporting
    # the result of a resolution that was never meaningful.
    assert resolve_unit(UNITS_SRC, ["nope"], kind="banana") == (None, "unknown_kind")


def test_resolve_without_kind_is_permissive():
    # ABSENT means "no restriction", never "matches nothing". Asserted in the PERMISSIVE
    # direction on purpose: a delegated model inverted exactly this check on applies_to,
    # with the case spelled out in its brief.
    assert resolve_unit(UNITS_SRC, ["plain"]) == ((9, 10), None)
    assert resolve_unit(UNITS_SRC, ["Shape"]) == ((31, 55), None)
    assert resolve_unit(UNITS_SRC, ["Shape", "area"]) == ((36, 38), None)


# --- apply_unit: the dotted-path applier (P3-T0) ------------------------------
#
# apply_code_anchored splices at column 0, which is correct for a top-level function and
# WRONG for a method. Under symbol addressing the harness owns indentation, per first
# principle 1 ("harness code does all mechanics ... models only decide content") — asking a
# 14B to track enclosing indentation is anchor burden wearing a different hat.


def test_apply_unit_replaces_a_top_level_function():
    out = apply_unit(UNITS_SRC, ["plain"], "def plain():\n    return 99")
    assert out is not None
    assert "return 99" in out
    assert "def commented():" in out          # siblings survive
    assert "class Shape:" in out


def test_apply_unit_reindents_a_method_to_its_span():
    # The model emits the unit at column 0; the harness places it at the span's indentation.
    out = apply_unit(UNITS_SRC, ["Shape", "area"], "def area(self):\n    return 99")
    assert out is not None
    assert "    def area(self):\n        return 99\n" in out
    import ast
    ast.parse(out)                            # the whole point: it must still parse


def test_apply_unit_accepts_already_indented_input():
    # A model that DID indent correctly must not be double-indented.
    out = apply_unit(UNITS_SRC, ["Shape", "area"], "    def area(self):\n        return 99")
    assert out is not None
    assert "    def area(self):\n        return 99\n" in out
    assert "        def area" not in out
    import ast
    ast.parse(out)


def test_apply_unit_replaces_a_method_of_a_nested_class():
    out = apply_unit(UNITS_SRC, ["Shape", "Inner", "deep"], "def deep(self):\n    return 99")
    assert out is not None
    assert "        def deep(self):\n            return 99\n" in out
    import ast
    ast.parse(out)


def test_apply_unit_replaces_the_decorated_span_including_its_decorator():
    out = apply_unit(UNITS_SRC, ["Shape", "name"], "def name(self):\n    return 'x'")
    assert out is not None
    assert "@property" not in out             # the decorator was INSIDE the replaced span
    import ast
    ast.parse(out)


def test_apply_unit_refuses_a_path_that_does_not_resolve_uniquely():
    # Both failure directions are LOUD — the applier never guesses which duplicate was meant,
    # and never silently no-ops on an absent path.
    assert apply_unit(UNITS_SRC, ["duplicated"], "def duplicated():\n    return 0") is None
    assert apply_unit(UNITS_SRC, ["nope"], "def nope():\n    return 0") is None


def test_apply_unit_refuses_an_unaddressable_target():
    # A closure has no address, so an edit aimed at one must fail rather than land somewhere.
    assert apply_unit(UNITS_SRC, ["outer", "local"], "def local():\n    return 0") is None


def test_apply_unit_honours_a_kind_check():
    assert apply_unit(UNITS_SRC, ["Shape"], "def Shape():\n    pass", kind="Method") is None
    out = apply_unit(UNITS_SRC, ["Shape", "area"], "def area(self):\n    return 1", kind="Method")
    assert out is not None
