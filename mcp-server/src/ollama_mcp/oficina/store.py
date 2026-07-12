"""Run-dir layout and spec persistence (P1-D7).

Storage root is machine-global (``~/.local/share/oficina/`` by default) but is
ALWAYS injected as a parameter — tests use tmp_path, the default is wired later.
Layout per run: ``runs/<run_id>/{spec.json, events.jsonl, artifacts/}``.

``spec.json`` is write-once and immutable after creation (P1-D6 ownership table),
written atomically via tmp + ``os.replace``. ``events.jsonl`` is owned by the
ledger; the store only creates it empty so the first append counts offset 0.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from . import ids


class UnknownRunError(Exception):
    """Raised when a run_id does not resolve to a run directory."""


class Store:
    """Filesystem layout for oficina runs, rooted at ``root``."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)

    @property
    def runs_dir(self) -> Path:
        """The parent directory holding every run's subdirectory."""
        return self.root / "runs"

    def run_dir(self, run_id: str) -> Path:
        """The directory for a single run (may not exist yet)."""
        return self.runs_dir / run_id

    def events_path(self, run_id: str) -> Path:
        """Path to a run's append-only event ledger."""
        return self.run_dir(run_id) / "events.jsonl"

    def artifacts_dir(self, run_id: str) -> Path:
        """Path to a run's artifacts subdirectory."""
        return self.run_dir(run_id) / "artifacts"

    def create_run(self, spec: Dict[str, Any]) -> str:
        """Mint an ID, build the run dir + artifacts, persist spec.json; return id."""
        run_id = ids.mint_run_id()
        run_directory = self.run_dir(run_id)
        run_directory.mkdir(parents=True, exist_ok=True)
        self.events_path(run_id).touch(exist_ok=True)
        self.artifacts_dir(run_id).mkdir(parents=True, exist_ok=True)
        _atomic_write_json(run_directory / "spec.json", spec)
        return run_id

    def load_spec(self, run_id: str) -> Dict[str, Any]:
        """Load a run's persisted spec; raise UnknownRunError if absent."""
        spec_path = self.run_dir(run_id) / "spec.json"
        if not spec_path.exists():
            raise UnknownRunError(run_id)
        return json.loads(spec_path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON to ``path`` atomically via a same-dir temp + os.replace."""
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temp_path, path)
