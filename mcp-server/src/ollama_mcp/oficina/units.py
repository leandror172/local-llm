"""Unit addressing for production edits — P3-D1(B) build step 1.

Resolves a dotted symbol path to exactly one span, and renders that span plus a model-supplied
body into the exact ``(old_string, new_string)`` pair ``patch_file`` applies. First principle 1:
harness code does all the mechanics, models only decide content.

**This is a DUPLICATE of ``benchmarks/lib/writemodel_apply.py``'s resolver, deliberately, and
the original is untouched.** ``patterns-refactoring-duplicate-first``: the benchmark owns the
published arm-A/arm-D numbers, `benchmarks/` and `mcp-server/` are independent test suites
(verified s141 — benchmarks references mcp-server only as path STRINGS in census cuts, never as
an import), and moving the code would create the first import edge between them, running through
the module whose measurements T-140 already flags as taken under a superseded prompt. Convergence
trigger: a second production consumer, or T-140's re-run, whichever lands first.

**What is NOT copied.** ``apply_unit`` spliced bytes itself; production splices through
``patch_file`` for its uniqueness check and atomic tmp+rename (P3-D1 rider (a)). Only its
harness-owns-indentation *contract* graduates, into ``render_unit_replacement`` — the rider names
"the applier" at module altitude while the property lives at function altitude, so taken
literally it would have dropped s137's own finding and spliced method bodies at column 0.
``apply_whole_file``/``apply_search_replace``/``strip_code_fences`` are benchmark-arm machinery
and stay there; fence stripping belongs at the parse step (E-D5), not here.

**Prediction recorded at duplication time** (``patterns-refactoring-duplicate-first`` rule 3, so
the delta is measurable rather than remembered): ``LanguagePack``'s fifth member is predicted to
be exactly one callable, ``unit_renderer``, with this module's signature. Go's locator does not
exist; when it does, rule 1 says this signature is an *accident* rather than a spec — ``go/parser``
attaches ``decl.Doc`` where ``ast`` attaches decorators, and Go has no module-level docstring at
all. Expect the member to survive and its *signature* to move.
"""

from __future__ import annotations

import ast
import textwrap
from typing import Optional

KINDS = ("Function", "Method", "Class", "Constant", "ClassConstant")

_ASSIGNMENT_NODES = (ast.Assign, ast.AnnAssign)

# There is deliberately NO `_UNIT_NODES` membership tuple. The plan predicted one ("extend
# `_UNIT_NODES` + a `Constant` kind") and s140 wrote it, then MEASURED it as redundant: with
# `_addressable_names` returning an empty set for anything it does not handle, a pre-filter
# blocks nothing the dispatch does not already block. Worse than harmless — it made the rule
# UNTESTABLE. Two mutations, `ast.AugAssign` added to the dispatch and `ast.Import` added to
# the tuple, BOTH left the whole suite green, each neutralised by the other mechanism. One
# rule needs one enforcement point or no single-point mutation can reach it.


class SharedBinding(Exception):
    """One statement answers to several names, so no single name addresses its span.

    ``A, B = 1, 2`` and ``A = B = 5`` are ONE statement occupying ONE span while binding two
    names. Replacing the unit at ``["A"]`` would rewrite ``B`` along with it, silently and
    correctly-looking. Refusing is the only safe answer.

    It is deliberately neither of the two reasons that already exist. ``no_match`` says *fix
    the address* — but the name IS present, so that would send a caller looking for a typo
    that is not there. ``multi_match`` means two SEPARATE units answer to one path, which is
    nearly the inverse situation and has a different remedy again.
    """


def _target_names(target: ast.AST) -> set[str]:
    """Plain names bound by ONE assignment target, descending through unpacking.

    ``A, B = 1, 2`` is a single ``ast.Tuple`` target holding two names, and ``A, *rest = xs``
    wraps one of them in ``ast.Starred``. A matcher that only understood ``ast.Name`` would
    report such a statement as binding NOTHING, and it would then be skipped as unaddressable
    rather than refused as ambiguous — the failure hidden instead of raised.

    An attribute or subscript target (``obj.a = 1``, ``d["k"] = 1``) mutates something that
    already exists and binds no module-level name, so it contributes nothing.
    """
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for elt in target.elts for name in _target_names(elt)}
    return set()


def _addressable_names(node: ast.AST) -> set[str]:
    """Every name this unit node answers to; empty when nothing addresses it.

    ONE function for ALL indexed node types, because ``_walk`` dispatches on the answer. A
    def or a class answers to its own declared name; an assignment answers to what it binds.

    **Empty means "not addressable by any name", never an error.** Writing this to handle only
    assignments returns empty for every function and class, and a caller that reads empty as a
    failure then refuses every ordinary lookup.

    Imports are absent by construction and that is the trap this function must not fall into:
    ``import ast`` binds ``ast`` and ``from typing import Optional`` binds ``Optional``, so a
    resolver widened by "does it bind a name" would swallow both. An import is not a
    replaceable unit — it is routed to a separate insert operation — so it is simply not an
    indexed node type and never reaches here.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.Assign):
        return {name for target in node.targets for name in _target_names(target)}
    if isinstance(node, ast.AnnAssign):
        return _target_names(node.target)
    # Everything else answers to nothing, and two cases are worth naming because a reader will
    # wonder about both. ``ast.AugAssign``: ``X += 1`` at module level REBINDS a name that must
    # already exist, so it is not the statement that DEFINES the unit — were it to answer to
    # ``X``, an ordinary lookup would become a multi_match against the increment. Imports: they
    # bind names but are not replaceable units, and they are routed to a separate insert
    # operation.
    #
    # This function is the SINGLE enforcement point for both, which is a deliberate property
    # and not an accident — see the note above the assignment-node tuple.
    return set()


def _kind_of(node: ast.AST, parent: ast.AST) -> str:
    """Kind of a unit node given its parent. Position is the ONLY discriminator.

    ``ast.FunctionDef`` is a ``Function`` at module level and a ``Method`` inside a class —
    the node class is identical in both cases, so the parent is what decides. An assignment
    follows the same rule rather than becoming the one exception to it: ``Constant`` at module
    level, ``ClassConstant`` inside a class.
    """
    if isinstance(node, ast.ClassDef):
        return "Class"
    if isinstance(node, _ASSIGNMENT_NODES):
        return "ClassConstant" if isinstance(parent, ast.ClassDef) else "Constant"
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
            names = _addressable_names(child)
            if name not in names:
                continue
            # Only ambiguous once someone ASKS for one of the shared names. A tuple assignment
            # elsewhere in the file is irrelevant and must not make the whole source unwalkable.
            if len(names) > 1:
                raise SharedBinding(f"{name!r} shares one span with {sorted(names - {name})}")
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
    of ``unknown_kind``, ``parse_error``, ``no_match``, ``multi_match``, ``kind_mismatch``,
    ``shared_binding``. Each is a distinct remedy, which is why they are distinct values: an
    unknown kind is fixed in the prompt, a no-match is fixed in the address, a multi-match is
    not fixable at all and must refuse.

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
    except SharedBinding:
        return (None, "shared_binding")
    if not matches:
        return (None, "no_match")
    if len(matches) > 1:
        return (None, "multi_match")
    span, actual_kind = matches[0]
    if kind is not None and actual_kind != kind:
        return (None, "kind_mismatch")
    return (span, None)


def _reindented(body: str, to_match: str) -> str:
    """``body`` dedented to column 0 and re-indented to the indentation of ``to_match``.

    THE HARNESS OWNS INDENTATION (s137). ``patch_file`` is an exact-string replace and splices
    verbatim, which is right for a top-level function at column 0 and produces broken Python
    for a method. Requiring the model to emit correctly-indented text would put
    enclosing-indentation tracking back on its plate — anchor burden under another name — so
    the text is normalised here instead. Dedent-then-reindent is what makes it idempotent: a
    body the model already indented correctly comes back unchanged.
    """
    indent = to_match[: len(to_match) - len(to_match.lstrip())]
    # Blank lines stay blank — indenting them would leave trailing whitespace.
    block = "".join(
        f"{indent}{line}" if line.strip() else line
        for line in textwrap.dedent(body).splitlines(keepends=True)
    )
    return block if block.endswith("\n") else block + "\n"


def render_unit_replacement(
    source: str, path: list[str], body: str, kind: Optional[str] = None
) -> tuple[Optional[tuple[str, str]], Optional[str]]:
    """The exact ``(old_string, new_string)`` pair ``patch_file`` needs, or why not.

    Returns ``((old, new), None)`` or ``(None, reason)`` — ``patterns-code-value-or-error``.
    The benchmark's ``apply_unit`` collapsed every failure into ``None``, which is right for an
    A/B harness that only counts applies; production ROUTES on the reason (a ``no_match`` is a
    prompt problem, a ``shared_binding`` is a whole-file fallback), so it is carried on its own
    channel rather than recovered by inspecting the value.

    **``old_string`` is widened past the span when the span's TEXT is not unique.** Resolution
    guarantees a unique SPAN and says nothing about the bytes in it: two classes declaring a
    byte-identical one-line constant resolve unambiguously by path while their text occurs
    twice, and ``patch_file`` would refuse an edit that is perfectly addressable. Measured on
    this repo (s141): 5 of 899 uniquely-resolved units collide, all of them ``model_config``
    lines in ``intake.py`` — a file in T-122's blocked set and a named criterion 3 target, so
    the case is reachable precisely where the first real run lands. One or two preceding lines
    resolved every one of them.

    **The widening walks to the file start and stops, with no "still not unique" branch.** For
    a window anchored at line 1 to recur, the file would have to contain its own prefix a second
    time — which would duplicate the addressed unit and make the path a ``multi_match`` before
    reaching here. Writing the branch anyway would be unreachable code asserting an unreachable
    state, and ``patch_file``'s own count check is the single enforcement point if the argument
    is ever wrong (the ``_UNIT_NODES`` lesson: one rule, one enforcement point).
    """
    span, reason = resolve_unit(source, path, kind)
    if span is None:
        return (None, reason)
    start, end = span  # 1-based inclusive
    lines = source.splitlines(keepends=True)
    first_body_line = next((ln for ln in lines[start - 1 : end] if ln.strip()), "")
    replacement = _reindented(body, first_body_line)

    for first in range(start, 0, -1):
        prefix = "".join(lines[first - 1 : start - 1])
        old = prefix + "".join(lines[start - 1 : end])
        if source.count(old) == 1 or first == 1:
            return ((old, prefix + replacement), None)
    raise AssertionError("unreachable: the loop returns at first == 1")  # pragma: no cover
