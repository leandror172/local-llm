"""Retention sweep with observability (P1-D2).

Prunes prunable per-run state under two policies and appends a ``RetentionPruned``
event PER prune to the worker ledger (what / bytes freed / which policy). Silence
means nothing was pruned. ``dry_run`` computes the same records but touches
nothing and emits nothing.

Hard invariant: retention NEVER touches ``events.jsonl`` (``ledger: forever``,
P1-D2). Only ``artifacts/`` is prunable — the delivery report lives in the
``Delivered`` event payload, so ``run_result`` stays answerable after a prune.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .config import RetentionConfig
from .ledger import Ledger
from .store import Store

_SECONDS_PER_DAY = 86400


@dataclass
class PruneRecord:
    """One prune action: what class, which run, bytes freed, which policy fired."""

    what: str
    run_id: str
    bytes_freed: int
    policy: str


def _list_run_ids(store: Store) -> List[str]:
    """Return the ids of every run directory currently in the store."""
    if not store.runs_dir.exists():
        return []
    return [p.name for p in store.runs_dir.iterdir() if p.is_dir()]


def _artifacts_bytes(artifacts_dir: Path) -> int:
    """Total bytes held under an artifacts directory (0 if absent/empty)."""
    if not artifacts_dir.exists():
        return 0
    return sum(f.stat().st_size for f in artifacts_dir.rglob("*") if f.is_file())


def _has_content(artifacts_dir: Path) -> bool:
    """True if the artifacts dir exists and holds at least one file."""
    return artifacts_dir.exists() and any(f.is_file() for f in artifacts_dir.rglob("*"))


def _prune_artifacts(store: Store, run_id: str, policy: str, dry_run: bool) -> Optional[PruneRecord]:
    """Prune one run's artifacts dir under ``policy``; None if nothing to free."""
    artifacts_dir = store.artifacts_dir(run_id)
    if not _has_content(artifacts_dir):
        return None
    freed = _artifacts_bytes(artifacts_dir)
    if not dry_run:
        shutil.rmtree(artifacts_dir)
    return PruneRecord("artifacts", run_id, freed, policy)


def _runs_over_keep_limit(store: Store, keep_runs: int) -> List[str]:
    """Run ids beyond the ``keep_runs`` newest (by run-dir mtime)."""
    ids = _list_run_ids(store)
    newest_first = sorted(ids, key=lambda r: store.run_dir(r).stat().st_mtime, reverse=True)
    return newest_first[keep_runs:]


def _runs_past_ttl(store: Store, ttl_days: int, now: float, skip: set) -> List[str]:
    """Run ids whose artifacts are older than the workspace TTL."""
    ttl_seconds = ttl_days * _SECONDS_PER_DAY
    stale: List[str] = []
    for run_id in _list_run_ids(store):
        if run_id in skip:
            continue
        artifacts_dir = store.artifacts_dir(run_id)
        if not _has_content(artifacts_dir):
            continue
        if now - artifacts_dir.stat().st_mtime > ttl_seconds:
            stale.append(run_id)
    return stale


def sweep(
    store: Store,
    worker_ledger: Ledger,
    config: RetentionConfig,
    now: Optional[float] = None,
    dry_run: bool = False,
) -> List[PruneRecord]:
    """Run both retention policies; emit RetentionPruned per prune unless dry-run."""
    now = time.time() if now is None else now
    records: List[PruneRecord] = []
    pruned: set = set()
    for run_id in _runs_over_keep_limit(store, config.artifacts_keep_runs):
        record = _prune_artifacts(store, run_id, "artifacts_keep_runs", dry_run)
        if record:
            records.append(record)
            pruned.add(run_id)
    for run_id in _runs_past_ttl(store, config.workspaces_ttl_days, now, pruned):
        record = _prune_artifacts(store, run_id, "workspaces_ttl_days", dry_run)
        if record:
            records.append(record)
            pruned.add(run_id)
    if not dry_run:
        for record in records:
            worker_ledger.retention_pruned(
                {
                    "what": record.what,
                    "run_id": record.run_id,
                    "bytes_freed": record.bytes_freed,
                    "policy": record.policy,
                }
            )
    return records
