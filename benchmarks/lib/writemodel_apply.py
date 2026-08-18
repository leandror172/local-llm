"""Apply layer for the oficina write-model benchmark (T-104).

Three edit-apply mechanisms differing ONLY in how a model's output becomes a file change:
  A. code-anchored  — locate the function span (ast), replace it with the model's function text.
                      Apply cannot fail once the span is located (the anchor came from disk).
  B. whole-file     — the model returns the complete file; overwrite.
  C. model-anchored — the model returns aider SEARCH/REPLACE blocks; apply by exact match.
                      Apply fails LOUDLY when the model's search text is not present verbatim.

Pure functions, no model calls, no I/O — unit-tested in test_writemodel_apply.py.
Design: `ref:oficina-write-model-benchmark`.
"""

from __future__ import annotations

import ast
import textwrap
from typing import Optional


def strip_code_fences(text: str) -> str:
    """Remove a single ```lang ... ``` wrapper when the whole response is fenced.

    ollama_chat returns raw text (unlike the generate_code MCP tool, which strips fences
    server-side), so every arm must defence the model's output before applying it.
    """
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    lines = stripped.splitlines()
    lines = lines[1:]  # drop the opening ```lang line
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]  # drop the closing ```
    return "\n".join(lines)


def locate_function(source: str, name: str) -> Optional[tuple[int, int]]:
    """1-based inclusive line span of a top-level function, or None.

    span start = the first decorator's line if decorated, else the ``def`` line; span end =
    ``end_lineno``. Only top-level functions (not methods). None if absent or ``source`` won't
    parse. (Local-model generated, my-python-q25c14, verdict 2 — used as-is.)
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start_line = node.decorator_list[0].lineno if node.decorator_list else node.lineno
            end_line = node.end_lineno or start_line
            return (start_line, end_line)
    return None


# --- Dotted unit addressing (P3-T0) -----------------------------------------
#
# `locate_function` above is frozen: it produced arm A's published numbers and its contract
# is a measurement instrument. This is the second implementation beside it, not a widening
# of the first (`ref:patterns-refactoring-duplicate-first`).

KINDS = ("Function", "Method", "Class")

_UNIT_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _kind_of(node: ast.AST, parent: ast.AST) -> str:
    """Kind of a unit node given its parent. Position is the ONLY discriminator.

    ``ast.FunctionDef`` is a ``Function`` at module level and a ``Method`` inside a class —
    the node class is identical in both cases, so the parent is what decides.
    """
    if isinstance(node, ast.ClassDef):
        return "Class"
    return "Method" if isinstance(parent, ast.ClassDef) else "Function"


def _span_of(node: ast.AST) -> tuple[int, int]:
    """1-based inclusive span, starting at the first decorator when the node is decorated.

    The unit is whatever the language's parser ATTACHES to the node: decorators in Python
    (they carry earlier linenos), ``decl.Doc`` in Go. A ``#`` comment above a ``def`` is
    therefore outside the unit here, because ``ast`` does not model comments at all.
    """
    decorators = getattr(node, "decorator_list", None)
    start = decorators[0].lineno if decorators else node.lineno
    return (start, node.end_lineno or start)


def _walk(source: str, path: list[str]) -> list[tuple[tuple[int, int], str]]:
    """Every ``(span, kind)`` whose dotted path matches. Raises ``SyntaxError`` if unparseable.

    Descends into CLASS bodies only. A name reachable solely through a function body (a
    closure) or through an ``if``/``try`` block is in the refusal region — no grammar
    addresses those stably — so it is simply not found, and the caller gets a loud no-match
    rather than a confidently wrong span. Whole-file is the recorded fallback for them.
    """
    if not path:
        return []
    found: list[tuple[tuple[int, int], str]] = []

    def descend(parent: ast.AST, remaining: list[str]) -> None:
        name, rest = remaining[0], remaining[1:]
        for child in parent.body:
            if not isinstance(child, _UNIT_NODES) or child.name != name:
                continue
            if not rest:
                found.append((_span_of(child), _kind_of(child, parent)))
            elif isinstance(child, ast.ClassDef):
                descend(child, rest)

    descend(ast.parse(source), path)
    return found


def find_units(source: str, path: list[str]) -> list[tuple[int, int]]:
    """Every 1-based inclusive line span matching a dotted path, in source order.

    ``[]`` means ABSENT and nothing else: an unparseable source RAISES rather than being
    folded into the same value, so a caller can never confuse the two. Returns ALL matches —
    never "first match wins", which is what a hard resolve error exists to prevent.
    """
    return [span for span, _ in _walk(source, path)]


def resolve_unit(
    source: str, path: list[str], kind: Optional[str] = None
) -> tuple[Optional[tuple[int, int]], Optional[str]]:
    """Resolve a dotted path to EXACTLY ONE span, or say why not.

    Returns ``(span, None)`` on success and ``(None, reason)`` otherwise, where reason is one
    of ``unknown_kind``, ``parse_error``, ``no_match``, ``multi_match``, ``kind_mismatch``.
    Each is a distinct remedy, which is why they are distinct values: an unknown kind is
    fixed in the prompt, a no-match is fixed in the address, a multi-match is not fixable at
    all and must refuse.

    ``kind`` is a CHECK, never a selector — it never narrows a multi-match. An ABSENT kind
    means no restriction, never "matches nothing".
    """
    if kind is not None and kind not in KINDS:
        # A defect in the REQUEST, not a result of resolution — report it without pretending
        # to have resolved anything.
        return (None, "unknown_kind")
    try:
        matches = _walk(source, path)
    except SyntaxError:
        return (None, "parse_error")
    if not matches:
        return (None, "no_match")
    if len(matches) > 1:
        return (None, "multi_match")
    span, actual_kind = matches[0]
    if kind is not None and actual_kind != kind:
        return (None, "kind_mismatch")
    return (span, None)


def parse_search_replace_blocks(text: str) -> list[tuple[str, str]]:
    """Parse aider-style edit blocks; content between markers is preserved verbatim.

        <<<<<<< SEARCH
        ...search...
        =======
        ...replace...
        >>>>>>> REPLACE

    Returns (search, replace) tuples in order; [] if none. Prose outside blocks is ignored.
    (Rewritten from the local-model draft, which mis-matched the ``=======`` divider as
    ``======= REPLACE`` and dropped edge lines via ``[1:-1]``.)
    """
    blocks: list[tuple[str, str]] = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if not lines[i].startswith("<<<<<<< SEARCH"):
            i += 1
            continue
        i += 1
        search: list[str] = []
        while i < n and not lines[i].startswith("======="):
            search.append(lines[i])
            i += 1
        i += 1  # skip the ======= divider
        replace: list[str] = []
        while i < n and not lines[i].startswith(">>>>>>> REPLACE"):
            replace.append(lines[i])
            i += 1
        i += 1  # skip the >>>>>>> REPLACE marker
        blocks.append(("\n".join(search), "\n".join(replace)))
    return blocks


def apply_code_anchored(source: str, name: str, new_function_text: str) -> Optional[str]:
    """Arm A: locate the function and replace its span with the model's function text.

    Returns the new source, or None if the function could not be located (the only failure
    mode — once located, application is deterministic and always succeeds).
    """
    span = locate_function(source, name)
    if span is None:
        return None
    start, end = span  # 1-based inclusive
    lines = source.splitlines(keepends=True)
    block = new_function_text if new_function_text.endswith("\n") else new_function_text + "\n"
    return "".join(lines[: start - 1]) + block + "".join(lines[end:])


def apply_unit(
    source: str, path: list[str], new_text: str, kind: Optional[str] = None
) -> Optional[str]:
    """Replace the unit at ``path`` with ``new_text``; None if it does not resolve uniquely.

    THE HARNESS OWNS INDENTATION. ``apply_code_anchored`` splices verbatim, which is right for
    a top-level function at column 0 and produces broken Python for a method. Requiring the
    model to emit correctly-indented text would put enclosing-indentation tracking back on its
    plate — anchor burden under another name — so instead the text is dedented to column 0 and
    re-indented to the span that was actually resolved. First principle 1: harness code does
    the mechanics, models decide content.

    Refuses rather than guesses: a duplicate path, an absent path, an unaddressable closure
    and a kind mismatch all return None instead of landing the edit somewhere plausible.
    """
    span, _reason = resolve_unit(source, path, kind)
    if span is None:
        return None
    start, end = span  # 1-based inclusive
    lines = source.splitlines(keepends=True)

    first_line = next((ln for ln in lines[start - 1 : end] if ln.strip()), "")
    indent = first_line[: len(first_line) - len(first_line.lstrip())]

    # Blank lines stay blank — indenting them would leave trailing whitespace.
    block = "".join(
        f"{indent}{ln}" if ln.strip() else ln
        for ln in textwrap.dedent(new_text).splitlines(keepends=True)
    )
    if not block.endswith("\n"):
        block += "\n"
    return "".join(lines[: start - 1]) + block + "".join(lines[end:])


def apply_whole_file(model_output: str) -> str:
    """Arm B: the model's output IS the new file."""
    return model_output


def _strip_fence_lines(text: str) -> str:
    """Drop whole-line ``` / ```lang fences from inside a block.

    14B models routinely fence the SEARCH/REPLACE *contents*. A real applier (aider) strips these
    before matching — doing so here is fair robustness, NOT code-anchoring: whitespace-exactness of
    the remaining lines is still required (that is arm C's genuine fragility, kept intact).
    """
    return "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith("```"))


def apply_search_replace(source: str, model_output: str) -> Optional[str]:
    """Arm C: apply each SEARCH/REPLACE block by exact match; None if any search is absent.

    The None return is the LOUD failure mode the benchmark measures: the model's anchor text
    did not appear verbatim in the file, so the edit cannot be placed.
    """
    blocks = parse_search_replace_blocks(model_output)
    if not blocks:
        return None
    result = source
    for search, replace in blocks:
        search = _strip_fence_lines(search)
        replace = _strip_fence_lines(replace)
        if search not in result:
            return None
        result = result.replace(search, replace, 1)
    return result
