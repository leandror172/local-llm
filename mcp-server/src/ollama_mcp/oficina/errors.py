"""Shared exception shape for oficina stages.

The where/whose/what triad is the single failure spelling (unified in P2): every stage
error that should become a ``Failed`` event carries it, and the worker forwards
``exc.triad`` verbatim instead of re-deriving a generic one.
"""

from __future__ import annotations

from typing import Dict

# --- the `whose` vocabulary: who owns the remedy -----------------------------
# One list, in the module that owns the triad. A triad built anywhere else invents its own
# spelling, and the vocabularies then drift with nothing comparing them — which had already
# happened: the worker's classifier knew only model/system while the loop's knew four values.
WHOSE_MODEL = "model"              # the coder had what it needed and did not deliver
WHOSE_PAYLOAD = "payload"          # the request cannot succeed as written; the caller must change it
WHOSE_ENVIRONMENT = "environment"  # something around the run ran out (wall clock, resources)
WHOSE_SYSTEM = "system"            # oficina's own fault, or unclassifiable

# Which budget limit attributes to whom. `context_budget` is here AND is what
# `ContextBudgetError` fixes, because they are the SAME condition observed at two points in one
# run — iteration 1 raises, a later iteration exhausts — so both read this one mapping and
# cannot disagree. They previously stated it independently, one line apart, in two modules.
WHOSE_BY_LIMIT: Dict[str, str] = {
    "exhausted": WHOSE_MODEL,
    "timeout": WHOSE_ENVIRONMENT,
    "context_budget": WHOSE_PAYLOAD,
}


def triad(where: str, what: str, whose: str = WHOSE_SYSTEM) -> Dict[str, str]:
    """The triad as a plain dict, for the paths that REPORT a failure without raising one.

    Same shape and same vocabulary as ``TriadError.triad``: the exhausted terminal and the
    worker's exception classifier both need the dict with no exception to carry it.
    """
    return {"where": where, "whose": whose, "what": what}


class TriadError(Exception):
    """A stage failure carrying the where/whose/what triad for a Failed event.

    Subclasses pick the stage-appropriate ``whose`` default; a raise site may
    override it (e.g. a payload-caused failure inside a system-owned stage).
    """

    def __init__(self, where: str, what: str, whose: str = WHOSE_SYSTEM) -> None:
        super().__init__(what)
        self.triad: Dict[str, str] = triad(where, what, whose)


class ContextBudgetError(TriadError):
    """The prompt plus the resolved generation budget cannot fit the model's window (T-112).

    ``whose="payload"`` because the remedy belongs to the caller: a smaller target, an
    explicit smaller ``budgets.num_predict``, or a model with a larger window. Raised only
    when the FIRST iteration cannot fit — a later overflow ends the run ``exhausted``
    carrying the best attempt, because by then one exists.
    """

    def __init__(self, what: str) -> None:
        super().__init__("generation", what, whose=WHOSE_BY_LIMIT["context_budget"])
