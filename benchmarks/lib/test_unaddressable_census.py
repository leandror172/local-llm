"""Tests for the criterion-5b census (T-140).

Only the two pure functions are tested; the git walk is plumbing. `top_sets` is where the
measurement can be quietly wrong, because the whole point of doing this structurally rather
than with grep is the cases a diff cannot see.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unaddressable_census import bound_names, classify, top_sets


class TestTopSets:
    def test_function_local_import_is_not_a_top_level_statement(self):
        """The case that makes a textual `+import` grep wrong in the EXPENSIVE direction: it
        would count a function-local import as needing a top-level statement, when a
        function-local import is exactly what the model emits INSTEAD of one."""
        bare, names = top_sets("def f():\n    import math\n    return math.pi\n")
        assert bare == set()
        assert names == {"f"}

    def test_module_level_import_is_counted(self):
        bare, _ = top_sets("import math\n\ndef f():\n    return 1\n")
        assert bare == {"import math"}

    def test_reordering_imports_is_not_a_change(self):
        """Set-of-unparsed-statements, so a reorder is a no-op. A line-based diff would call
        this two removals and two additions."""
        a, _ = top_sets("import os\nimport sys\n")
        b, _ = top_sets("import sys\nimport os\n")
        assert a == b

    def test_editing_a_module_constant_registers_as_a_delta(self):
        """`replace_unit` cannot address a module constant whether you ADD or EDIT it, so the
        after-minus-before difference is the right instrument — and this is why the reported
        figure is 'added or changed', not 'added'."""
        before, _ = top_sets("X = (1, 2)\n")
        after, _ = top_sets("X = (1, 2, 3)\n")
        assert after - before

    def test_editing_a_function_body_is_NOT_a_delta(self):
        """The negative control. A pure body edit is exactly what (B) handles well, and if it
        registered here the whole rate would be meaningless."""
        before = top_sets("import os\n\ndef f():\n    return 1\n")
        after = top_sets("import os\n\ndef f():\n    return 2\n")
        assert after[0] - before[0] == set()
        assert after[1] - before[1] == set()

    def test_adding_a_method_to_a_class_is_not_a_new_top_level_unit(self):
        """A method is addressable by a dotted path, so it must not land in either bucket."""
        before = top_sets("class C:\n    def a(self):\n        pass\n")
        after = top_sets("class C:\n    def a(self):\n        pass\n\n    def b(self):\n        pass\n")
        assert after[0] - before[0] == set()
        assert after[1] - before[1] == set()

    def test_unparseable_source_returns_none_rather_than_guessing(self):
        assert top_sets("def f(\n") is None


class TestClassify:
    def test_import_and_new_unit_are_separate_classes(self):
        """A new top-level def HAS a name and is still not expressible by replace_unit, but it
        needs a different operation than an import does. Merging them would overstate item 6's
        bound and hide the second gap."""
        c = classify(["import math"], ["helper"])
        assert c["import"] is True and c["new_unit"] is True
        assert c["other_bare"] is False

    def test_module_docstring_is_not_counted_as_other_bare(self):
        c = classify(['"""A module."""'], [])
        assert c["module_docstring"] is True
        assert c["other_bare"] is False
        assert c["import"] is False

    def test_module_constant_is_other_bare(self):
        c = classify(["TIMEOUT = 30"], [])
        assert c["other_bare"] is True
        assert c["import"] is False

    def test_a_pure_body_edit_is_unaddressable_by_nothing(self):
        c = classify([], [])
        assert not any(c.values())

    def test_module_docstring_is_detected_despite_ast_unparse_quoting(self):
        """FOUND BY A ZERO THAT SHOULD NOT HAVE BEEN ZERO. The census reported
        `docstring 0.0%` across every cut while the sample visibly contained module-docstring
        edits. `ast.unparse` renders a docstring as an ordinary SINGLE-quoted string literal,
        never as a triple-quoted one, so a `startswith(('\"\"\"', \"'''\"))` prefix test cannot
        ever match it and the whole category silently emptied into `other_bare`.

        The headline rate was unaffected -- a docstring IS unaddressable either way -- which is
        exactly why this could sit there looking like a real measurement of zero.
        """
        import ast
        rendered = ast.unparse(ast.parse('"""A module."""').body[0])
        assert not rendered.startswith('"""'), "the premise: unparse does not keep the triples"
        c = classify([rendered], [])
        assert c["module_docstring"] is True
        assert c["other_bare"] is False


class TestBoundNames:
    """`bound_names` exists because `bare_added` is a set difference over unparsed STRINGS,
    which cannot distinguish `X = 1` -> `X = 2` (a change) from a brand-new `X = 2` (an add).
    Only the first is convertible by giving the resolver a `Constant` kind."""

    def test_plain_assignment_binds_its_name(self):
        assert bound_names("TIMEOUT = 30") == {"TIMEOUT"}

    def test_annotated_assignment_binds_its_name(self):
        """`ast.AnnAssign` carries `.target` (singular), NOT `.targets`. Measured: no
        assignment node has `.name` at all, so the resolver's `child.name != name` matcher
        raises AttributeError on the first one it meets. This is that case."""
        assert bound_names("TIMEOUT: int = 30") == {"TIMEOUT"}

    def test_augmented_assignment_binds_nothing_because_it_mutates(self):
        """`X += 1` at module level REBINDS an existing name; it never creates one. Counting it
        as a binding would report a name as 'already present before' on the strength of a
        statement that presupposes it."""
        assert bound_names("COUNTER += 1") == set()

    def test_tuple_unpacking_binds_every_name(self):
        """ONE node, TWO names, ONE span. This is the correctness hazard for the resolver
        extension: `["A"]` and `["B"]` would resolve to the SAME span, so replacing one
        rewrites both. The census must at least SEE both names."""
        assert bound_names("A, B = 1, 2") == {"A", "B"}

    def test_chained_assignment_binds_every_name(self):
        assert bound_names("A = B = 5") == {"A", "B"}

    def test_attribute_and_subscript_targets_bind_no_top_level_name(self):
        """`obj.attr = 1` binds nothing at module scope — there is no top-level name for a
        resolver to address, so it must not be mistaken for a constant."""
        assert bound_names("obj.attr = 1") == set()
        assert bound_names("d['k'] = 1") == set()

    def test_imports_and_docstrings_bind_no_name_here(self):
        """They have their own buckets. If they leaked a name into `before_bound`, an
        unrelated constant sharing that name would be misreported as 'changed'."""
        assert bound_names("import math") == set()
        assert bound_names("'A module.'") == set()

    def test_unparseable_statement_returns_empty_rather_than_raising(self):
        assert bound_names("A = (") == set()

    def test_starred_unpacking_binds_every_name(self):
        """`ast.Starred` wraps one element of the tuple target, so a matcher that only knows
        `Name` and `Tuple` silently drops `rest`."""
        assert bound_names("HEAD, *REST = xs") == {"HEAD", "REST"}

    def test_empty_statement_returns_empty_rather_than_raising(self):
        """`ast.parse("")` succeeds and yields a module with an EMPTY body, so indexing
        `body[0]` raises IndexError -- which `except SyntaxError` does not catch. A blank
        entry must be a no-op, never a crash mid-census."""
        assert bound_names("") == set()
        assert bound_names("   \n  ") == set()


class TestClassifyAddedVsChanged:
    """The split the s139 census could not make. Its `classify` docstring argued the
    conflation was right -- "a module constant has no path whether you are adding it or
    editing it" -- which is TRUE of today's resolver and FALSE the moment a `Constant` kind
    lands. That is the whole point of measuring this."""

    def test_changed_constant_is_marked_changed_not_added(self):
        """THE headline case. `DEFAULT = 1` -> `DEFAULT = 2`: the name was already bound, so a
        resolver that indexes assignments can address and replace it."""
        c = classify(["DEFAULT = 2"], [], {"DEFAULT"})
        assert c["other_bare_changed"] is True
        assert c["other_bare_added"] is False

    def test_added_constant_is_marked_added_not_changed(self):
        """Nothing to replace. Needs `insert_top_level`, exactly like an import does."""
        c = classify(["NEW_THING = 2"], [], {"DEFAULT"})
        assert c["other_bare_added"] is True
        assert c["other_bare_changed"] is False

    def test_one_edit_can_be_both(self):
        """Per-edit booleans, so an edit that changes one constant and adds another is not
        forced into a single bucket. Such an edit still needs `insert_top_level`."""
        c = classify(["DEFAULT = 2", "NEW_THING = 3"], [], {"DEFAULT"})
        assert c["other_bare_changed"] is True
        assert c["other_bare_added"] is True

    def test_a_nameless_bare_statement_counts_as_added(self):
        """An `if`/`try` block or a bare call binds no addressable top-level name, so there is
        nothing a resolver could replace. It belongs on the `insert`/fallback side, never on
        the converted side."""
        c = classify(["if TYPE_CHECKING:\n    pass"], [], set())
        assert c["other_bare_added"] is True
        assert c["other_bare_changed"] is False

    def test_the_split_ignores_imports_and_docstrings(self):
        """An import binds a name (`import math` binds `math`), but imports go to
        `insert_top_level` regardless of whether they changed. If the split counted them, the
        resolver extension's share would be inflated by a class it cannot convert."""
        c = classify(["import math", "'A module.'"], [], {"math"})
        assert c["other_bare_changed"] is False
        assert c["other_bare_added"] is False
        assert c["import"] is True and c["module_docstring"] is True

    def test_the_conflated_headline_is_UNCHANGED_by_the_split(self):
        """NEGATIVE CONTROL, and the one that protects the published 5b figure. The split adds
        information; it must not redefine `unaddressable` or `other_bare`. If either moved,
        23-48% would silently become a different number and every consumer citing it would be
        wrong without any of them changing."""
        for before in (set(), {"DEFAULT"}):
            c = classify(["DEFAULT = 2"], [], before)
            assert c["unaddressable"] is True, "headline must not move with the split"
            assert c["other_bare"] is True, "bucket must not move with the split"

    def test_existing_two_argument_callers_still_work(self):
        """`before_bound` defaults, so the 5b instrument's own prior tests keep passing and the
        saved s139 output stays recomputable."""
        c = classify(["TIMEOUT = 30"], [])
        assert c["other_bare"] is True
        assert c["other_bare_added"] is True
