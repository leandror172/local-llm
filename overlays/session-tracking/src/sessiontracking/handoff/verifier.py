# verifier.py

import re
from typing import List, Tuple

class VerifyError(Exception):
    """Exception raised for verification errors."""
    def __init__(self, message, *, kind="internal"):
        super().__init__(message)
        self.kind = kind


def _first_diff(expected: str, actual: str, ctx: int = 40) -> str:
    """Return 'at byte N: expected <…> | actual <…>' for the first differing byte."""
    n = min(len(expected), len(actual))
    i = 0
    while i < n and expected[i] == actual[i]:
        i += 1
    e = expected[max(0, i - ctx): i + ctx].replace("\n", "\\n")
    a = actual[max(0, i - ctx): i + ctx].replace("\n", "\\n")
    return f"at byte {i}: expected «{e}» | actual «{a}»"


def _edits_label(original, edits) -> str:
    files = sorted({getattr(r, "file", "") for r, _ in edits if getattr(r, "file", "")})
    roles = [getattr(r, "role", "") for r, _ in edits if getattr(r, "role", "")]
    return f"file(s) {files} after applying roles {roles}"


def _region_label(original: str, region) -> str:
    """Build a human-readable label for a region: role(target)@file:line[-line]."""
    lo = original[:region.start].count("\n") + 1
    hi = original[:region.end].count("\n") + 1
    loc = str(lo) if lo == hi else f"{lo}-{hi}"
    role = getattr(region, "role", "") or ""
    target = getattr(region, "target", "") or ""
    file_ = getattr(region, "file", "") or ""
    if role or target or file_:
        return f"{role}({target})@{file_}:{loc}"
    return f"@byte{region.start}-{region.end}"


def _overlap_message(original: str, a, b) -> str:
    return f"{_region_label(original, a)} overlaps {_region_label(original, b)}"


def _segment(region, content) -> str:
    """Generate the segment based on the region's mode and content."""
    if region.mode == "replace" or region.mode == "nomodel":
        return content
    elif region.mode == "prepend":
        return content + region.interior
    elif region.mode == "append":
        return region.interior + content
    elif region.mode == "checkoff":
        return region.interior.replace("[ ]", "[x]", 1)
    else:
        raise VerifyError(f"unsupported mode '{region.mode}' for role '{getattr(region,'role','?')}' — TOOL BUG")


def _effective_range(region, mode: str, content: str) -> Tuple[int, int]:
    """(lo, hi) byte range of original text actually mutated by this edit."""
    if mode == "replace" or mode == "nomodel":
        return (region.start, region.end)
    elif mode == "prepend":
        return (region.start, region.start)
    elif mode == "append":
        return (region.end, region.end)
    elif mode == "checkoff":
        offset = region.interior.find("[ ]")
        if offset != -1:
            return (region.start + offset, region.start + offset + 3)
        else:
            return (region.start, region.end)
    else:
        raise VerifyError(f"unsupported mode '{mode}' for role '{getattr(region,'role','?')}' — TOOL BUG")


def verify(original: str, modified: str, edits: List[Tuple[object, str]]) -> None:
    """Verify that the modified text matches the expected text derived from edits."""

    # Overlap guard
    effective_ranges = [(region, _effective_range(region, region.mode, content)) for region, content in edits]
    sorted_edits = sorted(effective_ranges, key=lambda e: e[1][0])
    for i in range(1, len(sorted_edits)):
        if sorted_edits[i][1][0] < sorted_edits[i - 1][1][1]:
            a = sorted_edits[i - 1][0]
            b = sorted_edits[i][0]
            raise VerifyError(
                f"two payload edits target overlapping bytes: {_overlap_message(original, a, b)}",
                kind="payload")

    # Independently re-derive the expected text — use descending sort (matching applier order)
    # so equal-start regions apply in the same sequence the applier uses.
    expected = original
    for region, content in sorted(edits, key=lambda e: e[0].start, reverse=True):
        if region.mode == "append":
            # Insertion at region.end — DO NOT overwrite the interior, which may
            # carry a nested edit (e.g. a checkoff flip) applied earlier in this loop.
            expected = expected[:region.end] + content + expected[region.end:]
        elif region.mode == "prepend":
            # Insertion at region.start — same reasoning.
            expected = expected[:region.start] + content + expected[region.start:]
        else:
            segment = _segment(region, content)
            expected = expected[:region.start] + segment + expected[region.end:]

    # Check if expected matches modified
    if expected != modified:
        raise VerifyError(
            "internal verification mismatch — this is likely a TOOL BUG, not your payload. "
            "Please report it with the run's input.md. "
            f"verify failed on {_edits_label(original, edits)}; "
            f"diff {_first_diff(expected, modified)}",
            kind="internal",
        )

    # Marker check
    def _collect_markers(text: str) -> List[str]:
        return re.findall(r"<!-- ref:[^>]+ -->|<!-- /ref:[^>]+ -->", text)

    original_markers = _collect_markers(original)
    modified_markers = _collect_markers(modified)

    if sorted(original_markers) != sorted(modified_markers):
        lost = sorted(set(original_markers) - set(modified_markers))
        gained = sorted(set(modified_markers) - set(original_markers))
        raise VerifyError(
            "internal verification mismatch (ref-marker set changed) — likely a TOOL BUG; "
            f"report with input.md. on {_edits_label(original, edits)}; "
            f"lost={lost} gained={gained}",
            kind="internal",
        )
