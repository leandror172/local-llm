"""Shared exception shape for oficina stages.

The where/whose/what triad is the single failure spelling (unified in P2): every stage
error that should become a ``Failed`` event carries it, and the worker forwards
``exc.triad`` verbatim instead of re-deriving a generic one.
"""

from __future__ import annotations

from typing import Dict


class TriadError(Exception):
    """A stage failure carrying the where/whose/what triad for a Failed event.

    Subclasses pick the stage-appropriate ``whose`` default; a raise site may
    override it (e.g. a payload-caused failure inside a system-owned stage).
    """

    def __init__(self, where: str, what: str, whose: str = "system") -> None:
        super().__init__(what)
        self.triad: Dict[str, str] = {"where": where, "whose": whose, "what": what}
