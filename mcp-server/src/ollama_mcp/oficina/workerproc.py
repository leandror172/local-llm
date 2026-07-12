"""Worker process arbitration + detached spawn (P1-D9).

Exactly one worker owns the store at a time. Ownership is a pidfile
(``<root>/worker.pid``) created with ``O_CREAT|O_EXCL`` — the loser of a
double-spawn race fails the exclusive create and backs off. The pidfile stores
the PID **and** the process start-time: a bare PID is not enough because the OS
recycles PIDs, so a stale pidfile whose PID now belongs to an unrelated process
must be distinguishable from a live owner. Liveness = ``kill(pid, 0)`` succeeds
AND the recorded start-time matches the live process's start-time.

The start-time lookup is injectable so the PID-reuse case is testable without an
actual reuse (feed a wrong start-time against a real, alive PID).

The spawn target (argv) is a PARAMETER — this module owns process mechanics, not
the worker's body (``worker.py`` is a later task).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def _proc_start_time(pid: int) -> Optional[str]:
    """Return a stable start-time token for ``pid`` from /proc, or None.

    Uses field 22 (starttime, jiffies since boot) of ``/proc/<pid>/stat``. The
    comm field (2) is parenthesized and may contain spaces/parens, so fields are
    parsed from after the LAST ``)`` (state is field 3 = index 0 there, so
    starttime field 22 is index 19).
    """
    try:
        text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        rest = text[text.rindex(")") + 1:].split()
        return rest[19]
    except (OSError, IndexError, ValueError):
        return None


class WorkerProc:
    """Pidfile arbitration and detached worker spawn, rooted at ``root``."""

    def __init__(
        self,
        root: str | os.PathLike,
        start_time_reader: Callable[[int], Optional[str]] = _proc_start_time,
    ) -> None:
        self.root = Path(root)
        self._start_time_reader = start_time_reader

    @property
    def pidfile(self) -> Path:
        """Path to the exclusive worker pidfile."""
        return self.root / "worker.pid"

    @property
    def log_path(self) -> Path:
        """Path the detached worker's stdout/stderr are redirected to."""
        return self.root / "worker.log"

    def is_alive(self, pid: int) -> bool:
        """True if a process with ``pid`` currently exists."""
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def read_pidfile(self) -> Optional[Dict[str, Any]]:
        """Return the parsed pidfile ({pid, start}) or None if absent/unreadable."""
        if not self.pidfile.exists():
            return None
        try:
            return json.loads(self.pidfile.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def owner_is_live(self) -> bool:
        """True iff the pidfile names a live process with a matching start-time."""
        data = self.read_pidfile()
        if not data:
            return False
        pid = data["pid"]
        if not self.is_alive(pid):
            return False
        return data.get("start") == self._start_time_reader(pid)

    def _exclusive_write(self, pid: int, start: Optional[str]) -> bool:
        """Create the pidfile with O_CREAT|O_EXCL; False if it already exists."""
        try:
            fd = os.open(self.pidfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": pid, "start": start}, f)
        return True

    def claim_pidfile(self, pid: Optional[int] = None, start: Optional[str] = None) -> bool:
        """Try to become the worker; recover a stale pidfile; return success."""
        if pid is None:
            pid = os.getpid()
        if start is None:
            start = self._start_time_reader(pid)
        self.root.mkdir(parents=True, exist_ok=True)
        if self._exclusive_write(pid, start):
            return True
        if self.owner_is_live():
            return False
        self.pidfile.unlink(missing_ok=True)
        return self._exclusive_write(pid, start)

    def spawn_detached(self, argv: List[str]) -> int:
        """Spawn ``argv`` fully detached (new session, stdio→worker.log); return pid."""
        self.root.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "ab") as log:
            proc = subprocess.Popen(
                argv,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        return proc.pid

    def ensure_worker(self, argv: List[str]) -> int:
        """If no live owner, spawn one detached; return the live/new worker pid."""
        if self.owner_is_live():
            return self.read_pidfile()["pid"]
        return self.spawn_detached(argv)
