"""Retention sweep with observability (P1-D2).

Prunes prunable per-run state under two policies and appends a ``RetentionPruned``
event PER prune to the worker ledger (what / bytes freed / which policy / git_pruned).
Silence means nothing was pruned. ``dry_run`` computes the same records but touches
nothing and emits nothing.

Hard invariant: retention NEVER touches ``events.jsonl`` (``ledger: forever``,
P1-D2). Only ``artifacts/`` and ``workspace/`` are prunable — the delivery report
lives in the ``Delivered`` event payload, so ``run_result`` stays answerable after a prune.

Prunable state is artifacts/ AND workspace/ (crashed-run worktrees); staleness for
the TTL policy is run-dir mtime.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

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
    git_pruned: Optional[bool] = None


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


def _prune_workspace(
    store: Store,
    run_id: str,
    policy: str,
    dry_run: bool,
) -> Optional[PruneRecord]:
    """Prune one run's workspace dir under ``policy``; None if nothing to free.

    The workspace tree is ALWAYS reclaimed; the git worktree registration is
    deregistered only when the target repo is still resolvable (``git_pruned``
    records which case fired — T-97's decided rule).
    """
    workspace_dir = store.run_dir(run_id) / "workspace"
    if not workspace_dir.exists():
        return None
    freed = _workspace_bytes(workspace_dir)
    if dry_run:
        return PruneRecord("workspace", run_id, freed, policy, git_pruned=None)
    base_repo = _base_repo_of(store, run_id)
    if base_repo is not None:
        _deregister_worktree(base_repo, workspace_dir / "worktree")
    shutil.rmtree(workspace_dir, ignore_errors=True)
    return PruneRecord("workspace", run_id, freed, policy, git_pruned=base_repo is not None)


def _base_repo_of(store: Store, run_id: str) -> Optional[Path]:
    """The git top-level of the run's deliverable target; None if unresolvable."""
    try:
        target = (store.load_spec(run_id).get("deliverable") or {}).get("target")
    except Exception:  # noqa: BLE001 — spec unreadable == repo unresolvable, still reclaim disk
        return None
    if not target:
        return None
    return _resolve_git_repo(Path(target).parent)


def _deregister_worktree(base_repo: Path, worktree: Path) -> None:
    """Best-effort ``git worktree remove --force`` + ``prune`` (mirrors Workspace.teardown)."""
    for args in (("worktree", "remove", "--force", str(worktree)), ("worktree", "prune")):
        subprocess.run(
            ["git", "-C", str(base_repo), *args], capture_output=True, text=True, check=False
        )


def _workspace_bytes(workspace_dir: Path) -> int:
    """Total bytes held under a workspace directory (0 if absent/empty)."""
    if not workspace_dir.exists():
        return 0
    return sum(f.stat().st_size for f in workspace_dir.rglob("*") if f.is_file())


def _runs_over_keep_limit(store: Store, keep_runs: int) -> List[str]:
    """Run ids beyond the ``keep_runs`` newest (by run-dir mtime)."""
    ids = _list_run_ids(store)
    newest_first = sorted(ids, key=lambda r: store.run_dir(r).stat().st_mtime, reverse=True)
    return newest_first[keep_runs:]


def _runs_past_ttl(
    store: Store,
    ttl_days: int,
    now: float,
) -> List[str]:
    """Run ids whose run dir is older than the workspace TTL."""
    ttl_seconds = ttl_days * _SECONDS_PER_DAY
    stale: List[str] = []
    for run_id in _list_run_ids(store):
        run_dir = store.run_dir(run_id)
        if now - run_dir.stat().st_mtime > ttl_seconds:
            stale.append(run_id)
    return stale


def _prune_over_keep_limit(
    store: Store, config: RetentionConfig, dry_run: bool
) -> Tuple[Set[str], List[PruneRecord]]:
    """Keep-limit policy: prune artifacts of runs beyond ``artifacts_keep_runs``.

    Returns the set of run ids whose artifacts were pruned — the TTL policy consumes
    this as ``skip`` so it never re-prunes the same artifacts under a second policy.
    ``artifacts_keep_runs`` never touches workspaces.
    """
    records: List[PruneRecord] = []
    pruned: Set[str] = set()
    for run_id in _runs_over_keep_limit(store, config.artifacts_keep_runs):
        record = _prune_artifacts(store, run_id, "artifacts_keep_runs", dry_run)
        if record:
            records.append(record)
            pruned.add(run_id)
    return pruned, records


def _prune_past_ttl(
    store: Store, config: RetentionConfig, now: float, skip: Set[str], dry_run: bool
) -> List[PruneRecord]:
    """TTL policy: prune artifacts + workspace of runs past ``workspaces_ttl_days``.

    ``skip`` names runs whose artifacts the keep-limit policy already pruned; their
    artifacts are left alone here, but their workspace is ALWAYS reclaimed.
    """
    records: List[PruneRecord] = []
    for run_id in _runs_past_ttl(store, config.workspaces_ttl_days, now):
        if run_id not in skip:
            record = _prune_artifacts(store, run_id, "workspaces_ttl_days", dry_run)
            if record:
                records.append(record)
        workspace_record = _prune_workspace(store, run_id, "workspaces_ttl_days", dry_run)
        if workspace_record:
            records.append(workspace_record)
    return records


def _emit_records(worker_ledger: Ledger, records: List[PruneRecord]) -> None:
    """Replay collected prune records into the worker ledger as RetentionPruned events."""
    for record in records:
        payload = {
            "what": record.what,
            "run_id": record.run_id,
            "bytes_freed": record.bytes_freed,
            "policy": record.policy,
        }
        if record.what == "workspace":
            payload["git_pruned"] = record.git_pruned
        worker_ledger.retention_pruned(payload)


def sweep(
    store: Store,
    worker_ledger: Ledger,
    config: RetentionConfig,
    now: Optional[float] = None,
    dry_run: bool = False,
) -> List[PruneRecord]:
    """Run both retention policies; emit RetentionPruned per prune unless dry-run."""
    now = time.time() if now is None else now
    pruned, records = _prune_over_keep_limit(store, config, dry_run)
    records += _prune_past_ttl(store, config, now, skip=pruned, dry_run=dry_run)
    if not dry_run:
        _emit_records(worker_ledger, records)
    return records


def _resolve_git_repo(start: Path) -> Optional[Path]:
    """Resolve the git repo containing the target path."""
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return None
