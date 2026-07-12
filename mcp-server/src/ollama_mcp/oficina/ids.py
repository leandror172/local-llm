"""Run-ID minting (P1-D8).

Run IDs are unguessable bearer-like handles — ``secrets.token_urlsafe(16)`` —
not sequential. Possession of the ID is the authorization to read/cancel a run
(single-user infra; revisit if the store ever becomes multi-user).
"""

from __future__ import annotations

import secrets


def mint_run_id() -> str:
    """Return a fresh, URL-safe, unguessable run identifier."""
    return secrets.token_urlsafe(16)
