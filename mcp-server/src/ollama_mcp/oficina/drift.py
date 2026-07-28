"""Mechanical drift metrics for a delivered file (P4-D3).

**The free layer surfaces; the judging layer classifies** (T-119, session 130). Magnitude is
reference-checkable and costs nothing, so it belongs in Phase-1 territory — deterministic, no
model required. Whether a change was *in scope* has no reference to check against and is
genuinely a judgment, so it belongs to the judge.

Nothing here gates. These numbers block no iteration; they exist so a reader of the delivery
report sees drift they would otherwise have to hunt for in a diff, and so the deliberately
deferred leak-detector has a countable trigger ("a second leak in any run") instead of an
uncounted one. The motivating incident pasted ~110 lines of acceptance tests into a production
module and reported success: 77 consecutive shared lines, against a legitimate worst case of 4
measured across all 14 real oficina source/test pairs.
"""

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Tuple


def measure(
    baseline: Optional[str], delivered: str, test_sources: Sequence[str]
) -> Dict[str, Any]:
    """Drift metrics for one delivered file.

    ``baseline`` is None for a greenfield run — there is no prior file, so everything the
    model wrote is an addition. ``test_sources`` are the contents of the run's declared
    acceptance tests; they are compared against, never modified.
    """
    baseline_lines = [] if baseline is None else baseline.splitlines()
    delivered_lines = delivered.splitlines()

    hunks, lines_added, lines_removed = _changed_regions(baseline_lines, delivered_lines)
    return {
        "hunks": hunks,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "max_verbatim_run_vs_tests": _longest_run_shared_with_tests(
            delivered_lines, test_sources
        ),
    }


def _changed_regions(
    baseline_lines: List[str], delivered_lines: List[str]
) -> Tuple[List[List[int]], int, int]:
    """Every changed region as a 1-based inclusive range in the DELIVERED file, plus totals.

    A replacement or insertion spans the delivered lines it produced. A **deletion produced no
    delivered lines**, so it is reported as a single-line marker at the line that now follows
    the removal — a range must never come out empty or inverted, and this is the case that
    surfaces E-D6 (a whole-file edit dropping the module docstring), where the reader needs to
    know *where* something vanished, not merely that the count fell.
    """
    hunks: List[List[int]] = []
    lines_added = 0
    lines_removed = 0

    for tag, i1, i2, j1, j2 in SequenceMatcher(None, baseline_lines, delivered_lines).get_opcodes():
        if tag == "equal":
            continue
        hunks.append([j1 + 1, j2 if j2 > j1 else j1 + 1])
        lines_added += j2 - j1
        lines_removed += i2 - i1

    return hunks, lines_added, lines_removed


def _longest_run_shared_with_tests(
    delivered_lines: List[str], test_sources: Sequence[str]
) -> int:
    """The longest run of consecutive NON-BLANK lines shared with any one test file.

    Runs are measured in non-blank lines, matching how the motivating leak was measured (78
    non-trivial lines, longest contiguous run 77). Consequence worth knowing: a pasted block
    interrupted by blank lines still reads as ONE run, which is the useful reading — the
    blank lines are not what makes it a leak.
    """
    delivered_content = _content_lines(delivered_lines)
    return max(
        (
            _longest_shared_run(delivered_content, _content_lines(source.splitlines()))
            for source in test_sources
        ),
        default=0,
    )


def _content_lines(lines: List[str]) -> List[str]:
    """The lines that could evidence a leak — blank and whitespace-only ones cannot.

    Dropping them BEFORE matching rather than marking them junk is deliberate:
    ``SequenceMatcher``'s ``isjunk`` stops junk from anchoring a match but still lets the
    winning block absorb adjacent junk, so a two-line import header followed by a blank line
    scored 3. Junk is excluded from the anchor, not from the count.
    """
    return [line for line in lines if line.strip()]


def _longest_shared_run(delivered_lines: List[str], test_lines: List[str]) -> int:
    """Size of the largest contiguous block common to both sequences."""
    matcher = SequenceMatcher(None, delivered_lines, test_lines)
    return matcher.find_longest_match(0, len(delivered_lines), 0, len(test_lines)).size
