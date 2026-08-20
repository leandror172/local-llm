"""Tests for the criterion-5b cut definitions (s140).

The CUTS are the measurement -- the headline rate moves ~2x between them -- so a wrong cut is
a wrong published number, not a cosmetic problem. This file exists because the first draft of
`census_report.py` filtered on the substring `"oficina/"`, which also matches
`mcp-server/tests/oficina/`, silently adding 45 test-file edits to a 69-edit cut and moving the
constant share from 30.4% to 21.1% -- i.e. it would have "corrected" a correct number.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from census_report import CUTS, rows_for, tally


def _row(path, churn=1, bare=(), units=(), before=()):
    return {"path": path, "churn": churn, "bare_added": list(bare),
            "units_added": list(units), "before_bound": list(before)}


class TestCuts:
    def test_the_oficina_cut_excludes_oficina_TESTS(self):
        """THE defect this file was written for. A test file's edits are not the population
        s139 measured, and including them halves the constant share."""
        rows = [_row("mcp-server/src/ollama_mcp/oficina/loop.py"),
                _row("mcp-server/tests/oficina/test_loop.py")]
        label, sub, churn = next(c for c in CUTS if c[0].startswith("oficina/"))
        got = rows_for(rows, sub, churn)
        assert [r["path"] for r in got] == ["mcp-server/src/ollama_mcp/oficina/loop.py"]

    def test_churn_bound_is_inclusive(self):
        """s139's rows are labelled '<=10' and '<=40'. An exclusive bound would drop every edit
        sitting exactly on the boundary and quietly shrink each population."""
        rows = [_row("a.py", churn=10), _row("b.py", churn=11)]
        assert [r["path"] for r in rows_for(rows, None, 10)] == ["a.py"]

    def test_all_edits_cut_filters_nothing(self):
        rows = [_row("anything.py", churn=9999)]
        assert rows_for(rows, None, None) == rows


class TestTally:
    def test_a_pre_s140_census_reports_constants_as_ADDED_not_as_zero(self):
        """An older census file has no `before_bound`. It recorded nothing about the before
        names, so every constant reads as ADDED -- which is the honest reading of a run that
        could not tell. Defaulting to a zero in BOTH halves would look like a measurement."""
        rows = [_row("a.py", bare=["X = 1"])]          # note: no `before_bound` key at all
        del rows[0]["before_bound"]
        t = tally(rows)
        assert t["other_bare"] == 100.0
        assert t["other_bare_added"] == 100.0
        assert t["other_bare_changed"] == 0.0

    def test_changed_and_added_are_counted_from_before_bound(self):
        rows = [_row("a.py", bare=["X = 2"], before=["X"]),
                _row("b.py", bare=["Y = 2"], before=["X"])]
        t = tally(rows)
        assert t["other_bare_changed"] == 50.0
        assert t["other_bare_added"] == 50.0
        assert t["other_bare"] == 100.0, "the split must not move the s139 bucket"

    def test_an_empty_cut_returns_empty_rather_than_dividing_by_zero(self):
        assert tally([]) == {}


class TestConvertible:
    def test_an_edit_that_also_ADDS_a_constant_is_not_convertible(self):
        """THE distinction the whole s140 measurement exists to make. Changing `X` is
        addressable once assignments are indexed; adding `Y` in the same edit is not, so the
        edit still needs `insert_top_level` and must not be counted as converted."""
        rows = [_row("a.py", bare=["X = 2", "Y = 3"], before=["X"])]
        t = tally(rows)
        assert t["other_bare_changed"] == 100.0, "it does contain a change"
        assert t["other_bare_added"] == 100.0, "and it also contains an add"
        assert t["constant_convertible"] == 0.0, "so it is NOT converted"

    def test_an_edit_that_only_changes_constants_is_convertible(self):
        rows = [_row("a.py", bare=["X = 2"], before=["X"])]
        assert tally(rows)["constant_convertible"] == 100.0

    def test_convertible_never_exceeds_the_published_constant_share(self):
        """A guard on the direction of the correction: the split may only ever shrink the
        30.4%, never inflate it. If CONVERT could exceed `const`, the instrument would be
        manufacturing addressable edits rather than partitioning them."""
        rows = [_row("a.py", bare=["X = 2"], before=["X"]),
                _row("b.py", bare=["import os"], before=[]),
                _row("c.py", bare=["Y = 1", "Z = 2"], before=["Y"])]
        t = tally(rows)
        assert t["constant_convertible"] <= t["other_bare"]
