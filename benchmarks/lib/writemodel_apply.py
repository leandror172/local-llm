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
