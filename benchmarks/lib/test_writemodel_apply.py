"""Unit tests for the write-model benchmark apply layer (T-104). Model-free, deterministic."""

from writemodel_apply import (
    apply_code_anchored,
    apply_search_replace,
    apply_whole_file,
    locate_function,
    parse_search_replace_blocks,
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
