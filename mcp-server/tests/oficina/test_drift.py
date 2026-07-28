"""Contract for `oficina/drift.py` — the mechanical half of the T-119 split (P4-D3).

The free layer SURFACES magnitude; the judge CLASSIFIES scope. Nothing here gates: these
metrics never block an iteration, they make drift legible to whoever reads the delivery
report — and they make the deferred detector's trigger ("a second leak in any run")
countable, which it is not while nobody measures.

Pure-function SUT, so per `ref:test-executable-spec` rule 5 the given/when/then scaffold
COLLAPSES: intent-named builder constants plus one verdict assertion per behaviour. No
mutation mini-language, no parametrize table — each behaviour keeps its own story.

Vocabulary note: the DELIVERED file is production source; a TEST SOURCE is its acceptance
test, a different file. `max_verbatim_run_vs_tests` exists to catch the second leaking into
the first (T-119: 77 consecutive lines, against a legitimate baseline of 4 measured across
all 14 real oficina source/test pairs).
"""

from ollama_mcp.oficina.drift import measure

AN_AREA_MODULE = "def area(w, h):\n    return w * h\n"
THE_SAME_MODULE_WITH_ONE_LINE_CHANGED = "def area(w, h):\n    return w + h\n"

_TWENTY_LINES = [f"line {i}\n" for i in range(1, 21)]
A_TWENTY_LINE_MODULE = "".join(_TWENTY_LINES)


def _with_lines_replaced(**replacements):
    """A copy of the 20-line module with the given 1-based lines replaced."""
    lines = list(_TWENTY_LINES)
    for number, text in replacements.items():
        lines[int(number.lstrip("line_")) - 1] = text
    return "".join(lines)


THE_SAME_MODULE_EDITED_AT_BOTH_ENDS = _with_lines_replaced(line_3="line 3 EDITED\n",
                                                           line_18="line 18 EDITED\n")

A_SHARED_IMPORT_HEADER = "import os\nimport sys\n\n"
A_MODULE_SHARING_ONLY_ITS_HEADER = A_SHARED_IMPORT_HEADER + AN_AREA_MODULE
A_TEST_SHARING_ONLY_THAT_HEADER = A_SHARED_IMPORT_HEADER + "def test_area():\n    assert area(2, 3) == 6\n"

# A block long enough that no legitimate source/test pair could share it by coincidence.
A_PASTED_BLOCK = "".join(f"    assert helper({i}) == {i}\n" for i in range(20))
A_TEST_CONTAINING_THAT_BLOCK = "def test_helper():\n" + A_PASTED_BLOCK
A_MODULE_WITH_THE_TESTS_PASTED_IN = "def helper(x):\n    return x\n" + A_PASTED_BLOCK

A_MODULE_WHOSE_ONLY_SHARED_LINES_ARE_BLANK = "def a():\n\n\n    return 1\n"
A_TEST_WHOSE_ONLY_SHARED_LINES_ARE_BLANK = "def test_a():\n\n\n    assert True\n"


def test_an_unchanged_file_shows_no_drift():
    """The negative control. First principle 6: a signal that fires unconditionally carries
    zero bits, so the metrics must be silent when nothing changed."""
    assert measure(AN_AREA_MODULE, AN_AREA_MODULE, []) == {
        "hunks": [],
        "lines_added": 0,
        "lines_removed": 0,
        "max_verbatim_run_vs_tests": 0,
    }


def test_one_changed_line_is_one_hunk():
    """A single edit reports exactly the line it touched, in delivered-file coordinates."""
    result = measure(AN_AREA_MODULE, THE_SAME_MODULE_WITH_ONE_LINE_CHANGED, [])

    assert result["hunks"] == [[2, 2]]
    assert result["lines_added"] == 1
    assert result["lines_removed"] == 1


def test_edits_far_apart_stay_two_hunks():
    """Separate regions are not merged into one span — the count and the locations are the
    signal a reader acts on."""
    result = measure(A_TWENTY_LINE_MODULE, THE_SAME_MODULE_EDITED_AT_BOTH_ENDS, [])

    assert result["hunks"] == [[3, 3], [18, 18]]
    assert result["lines_added"] == 2
    assert result["lines_removed"] == 2


def test_greenfield_counts_the_whole_file_as_added():
    """No baseline means nothing was removed — a greenfield run is all addition."""
    result = measure(None, AN_AREA_MODULE, [])

    assert result["hunks"] == [[1, 2]]
    assert result["lines_added"] == 2
    assert result["lines_removed"] == 0


def test_a_shared_import_header_scores_low():
    """The legitimate case. Real source/test pairs share short headers; the measured worst
    case across 14 oficina pairs was 4 consecutive lines."""
    result = measure(None, A_MODULE_SHARING_ONLY_ITS_HEADER, [A_TEST_SHARING_ONLY_THAT_HEADER])

    assert result["max_verbatim_run_vs_tests"] == 2


def test_a_pasted_test_block_scores_high():
    """The T-119 leak: acceptance tests copied verbatim into the production module. The
    separation from the legitimate case is what makes this detectable at all — ~20x."""
    result = measure(None, A_MODULE_WITH_THE_TESTS_PASTED_IN, [A_TEST_CONTAINING_THAT_BLOCK])

    assert result["max_verbatim_run_vs_tests"] >= 20


def test_blank_lines_never_build_a_run():
    """Two unrelated files share blank lines constantly; counting them would make every run
    look like a leak."""
    result = measure(
        None,
        A_MODULE_WHOSE_ONLY_SHARED_LINES_ARE_BLANK,
        [A_TEST_WHOSE_ONLY_SHARED_LINES_ARE_BLANK],
    )

    assert result["max_verbatim_run_vs_tests"] == 0


def test_no_declared_tests_means_nothing_to_compare():
    """A run with no declared test_files cannot leak from them — and the metric must say 0
    rather than guess."""
    result = measure(AN_AREA_MODULE, THE_SAME_MODULE_WITH_ONE_LINE_CHANGED, [])

    assert result["max_verbatim_run_vs_tests"] == 0


def test_a_deletion_at_end_of_file_points_inside_the_delivered_file():
    """A deletion produced no delivered lines, so it is reported as a marker at the line that
    now FOLLOWS the removal — but at EOF there is no following line, and the marker pointed one
    line past the end, naming somewhere the reader cannot open. These ranges are read by a human
    scanning the report AND inlined into the judge's prompt, so a range must be addressable in
    the file it claims to describe."""
    result = measure("a\nb\nc\nd\n", "a\nb\n", [])

    assert result["lines_removed"] == 2
    assert result["hunks"] == [[2, 2]]  # the last delivered line, not the phantom line 3
