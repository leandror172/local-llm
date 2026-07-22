"""Monotonic-prefix prompt assembly for the evaluated loop (P2 build step T2; P2-D2/D3).

Ollama exposes *implicit prefix reuse only* (`ref:ollama-explicit-cache-api`): llama.cpp
reuses the longest matching prompt prefix and recomputes from the first differing byte.
So every loop iteration lays its prompt out **stable-first, variable-last** — run-constant
content (system · constraints · context · tests · objective) then iteration-varying content
(repair feedback · previous attempt). One early byte change would invalidate all downstream
KV, so the ordering is a hard invariant (P2-D2).

The order lives in ONE swappable definition — the ``SEGMENTS`` tuple, each segment carrying
``stable: bool`` — and ``build_prompt`` is a fold over it (P2-D3). Changing the cache strategy
is a one-tuple edit; the ordering-guard test travels with it and trips if a variable segment
is ever placed above a stable one. **Config-field promotion is deferred** (house rule: config
over code-patching seams) until the order must vary without a code edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Segment:
    """One ordered slot in the prompt.

    Attributes:
        key: the key looked up in the ``parts`` mapping passed to ``build_prompt``.
        header: a label prepended to the segment's content (``""`` for no header).
        stable: True if this segment is run-constant (byte-identical every iteration,
            so it belongs in the reused KV prefix); False if it varies per iteration.
    """

    key: str
    header: str
    stable: bool


# The layout contract (P2-D2). Stable-first, variable-last. Reorder WITHIN the stable
# block freely; never move a variable segment above a stable one (the guard test enforces).
SEGMENTS: tuple[Segment, ...] = (
    Segment("system", "", True),
    Segment("constraints", "CONSTRAINTS:", True),
    Segment("context", "CONTEXT:", True),
    # Edit mode (T-110/E-D3): the target's committed content, run-constant → stable prefix.
    # Placed before `tests` so the model reads what it is modifying, then the acceptance tests.
    # Reorder-within-stable is allowed by P2-D2; omitted entirely in greenfield (blank part).
    Segment("current_file", "CURRENT FILE (you are modifying this file):", True),
    Segment("tests", "TESTS (implement against these — they are the acceptance criteria):", True),
    Segment("objective", "OBJECTIVE:", True),
    Segment("repair_feedback", "REPAIR FEEDBACK (from the previous attempt):", False),
    Segment("previous_attempt", "PREVIOUS ATTEMPT:", False),
)


def build_prompt(parts: Mapping[str, str]) -> str:
    """Fold ``parts`` into a single prompt in ``SEGMENTS`` order.

    A segment whose ``parts`` value is missing or blank is omitted entirely (so
    iteration 1, with no repair feedback or previous attempt, ends at the objective).
    Non-empty segments are joined with a blank line; a segment's header (when present)
    precedes its content. Because stable segments come first, the stable prefix is
    byte-identical whenever the stable parts are unchanged — the P2-D2 cache win.
    """
    chunks: list[str] = []
    for segment in SEGMENTS:
        content = (parts.get(segment.key) or "").strip()
        if not content:
            continue
        chunks.append(f"{segment.header}\n{content}" if segment.header else content)
    return "\n\n".join(chunks)
