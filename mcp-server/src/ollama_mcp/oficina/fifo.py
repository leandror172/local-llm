"""Disk FIFO queue for oficina runs (P1-D9).

Markers are files named ``<epoch-ms>-<run_id>`` under ``<root>/queue/``. Many
processes may push; in P1 a single worker pops. Safety comes from the marker
names being distinct by construction (epoch-ms + unguessable run_id) and from
atomic file creation — never a lock.

Run IDs are ``secrets.token_urlsafe`` and MAY contain ``-``; the epoch-ms prefix
never does, so the run_id is recovered by splitting on the FIRST dash. FIFO
order is the numeric epoch-ms prefix (not lexicographic), tie-broken by name.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List, Optional

_SEP = "-"


class Fifo:
    """A directory-backed FIFO of run markers, rooted at ``root``."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)

    @property
    def queue_dir(self) -> Path:
        """The directory holding queue marker files."""
        return self.root / "queue"

    def _marker_name(self, run_id: str, now_ms: int) -> str:
        """Build the ``<epoch-ms>-<run_id>`` marker filename."""
        return f"{now_ms}{_SEP}{run_id}"

    def _markers(self) -> List[str]:
        """Return all marker names ordered FIFO (numeric epoch-ms prefix)."""
        if not self.queue_dir.exists():
            return []
        markers = list(self.queue_dir.iterdir())
        markers.sort(key=lambda p: (int(p.name.split(_SEP, 1)[0]), p.name))
        return [m.name for m in markers]

    def push(self, run_id: str, now_ms: Optional[int] = None) -> str:
        """Enqueue a run; create the marker atomically; return the marker name."""
        if now_ms is None:
            now_ms = int(time.time() * 1000)
        marker_name = self._marker_name(run_id, now_ms)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        temp_marker_path = self.queue_dir / f"{marker_name}.tmp"
        temp_marker_path.touch()
        os.rename(temp_marker_path, self.queue_dir / marker_name)
        return marker_name

    def pop(self) -> Optional[str]:
        """Claim and remove the FIFO-lowest marker; return its run_id or None."""
        markers = self._markers()
        if not markers:
            return None
        first_marker = markers[0]
        (self.queue_dir / first_marker).unlink()
        return first_marker.split(_SEP, 1)[1]
