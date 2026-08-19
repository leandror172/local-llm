"""Tests for the criterion-5b census (T-140).

Only the two pure functions are tested; the git walk is plumbing. `top_sets` is where the
measurement can be quietly wrong, because the whole point of doing this structurally rather
than with grep is the cases a diff cannot see.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unaddressable_census import classify, top_sets


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
