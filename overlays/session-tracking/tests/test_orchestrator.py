# test_orchestrator.py
#
# Contract tests for F6 (orchestrator): the atomic stage -> apply -> verify ->
# commit-or-rollback transaction. Unit tests drive a FakeGit + fake rotate so the
# orchestration logic is hermetic; two integration tests use real git in a tmp repo.
#
# Flat imports — run from inside the handoff dir or pass absolute file paths.

import datetime
import shutil
import subprocess
import types

import pytest

from sessiontracking.handoff import orchestrator
from sessiontracking.handoff.orchestrator import run_handoff, stage_and_apply, HandoffPayload
from sessiontracking.handoff.gitio import SubprocessGit
from sessiontracking.handoff.verifier import VerifyError
from sessiontracking.handoff.mechanics import LogEntry


CLOCK = lambda: datetime.datetime(2026, 6, 5, 14, 30, 0)

REGISTER = {
    "log-entry": {
        "file": ".claude/session-log.md",
        "locator": {"type": "structural", "pattern": "^---$", "occurrence": 1, "position": "after"},
        "write_mode": "prepend",
    },
    "header-current-session": {
        "file": ".claude/session-log.md",
        "locator": {"type": "field", "label": "Current Session"},
        "write_mode": "nomodel",
    },
    "header-current-layer": {
        "file": ".claude/session-log.md",
        "locator": {"type": "field", "label": "Current Layer"},
        "write_mode": "nomodel",
    },
    "current-status": {
        "file": ".claude/session-context.md",
        "locator": {"type": "ref_block", "key": "current-status"},
        "write_mode": "replace",
    },
    "tasks-checkoff": {
        "file": ".claude/tasks.md",
        "locator": {"type": "checklist", "scope": "file"},
        "write_mode": "checkoff",
    },
}

SESSION_LOG = (
    "# Session Log\n"
    "\n"
    "**Current Layer:** Old layer\n"
    "**Current Session:** 2026-06-01 — Session 84: Old topic\n"
    "\n"
    "---\n"
    "\n"
    "## 2026-06-01 - Session 84: prev entry\n"
    "body\n"
)

SESSION_CONTEXT = (
    "# Context\n"
    "\n"
    "<!-- ref:current-status -->\n"
    "old status\n"
    "<!-- /ref:current-status -->\n"
)

TASKS = (
    "# Tasks\n"
    "\n"
    "- [ ] (T-99) Foo bar baz\n"
)


def _payload():
    return HandoffPayload(
        session_title="F6 test",
        current_layer="New layer text",
        blocks={
            "current-status": "\nnew status here\n",
        },
        log_entry=LogEntry(
            context="resumed from B4 test",
            what_was_done=["tested the F6 orchestrator"],
            next=["do B4.2"],
        ),
        checkoffs=["T-99"],
        raw="verbatim payload text",
    )


def _setup(root):
    claude = root / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "session-log.md").write_text(SESSION_LOG)
    (claude / "session-context.md").write_text(SESSION_CONTEXT)
    (claude / "tasks.md").write_text(TASKS)
    return root


def _make_run_dir(root, session_number=85):
    """Create a pre-staged run dir with input.md (caller's responsibility in new design)."""
    run_dir = root / ".claude" / "local" / "handoff-runs" / f"session-{session_number}-20260605-143000-pending"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "input.md").write_text("verbatim payload text")
    return run_dir


class FakeGit:
    def __init__(self, clean=True, fail_commit=False):
        self._clean = clean
        self.fail_commit = fail_commit
        self.added = None
        self.committed = None
        self.checked_out = None

    def is_clean(self, paths):
        return self._clean

    def add(self, paths):
        self.added = list(paths)

    def commit(self, message):
        if self.fail_commit:
            raise RuntimeError("commit boom")
        self.committed = message

    def checkout(self, paths):
        self.checked_out = list(paths)

    def status_short(self):
        return ""

    def log_messages(self, n=5):
        return []


def fake_rotate(repo_root, keep=3):
    return types.SimpleNamespace(returncode=0, stdout="", stderr="")


def boom_rotate(repo_root, keep=3):
    raise RuntimeError("rotate boom")


# ---- unit: happy path -------------------------------------------------------

def test_happy_path_applies_commits_and_logs(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=True)
    run_dir = _make_run_dir(root)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate,
                         clock=CLOCK, run_dir=run_dir)

    assert report.committed and not report.rolled_back and report.verify_ok
    assert git.committed is not None and git.checked_out is None

    log = (root / ".claude/session-log.md").read_text()
    assert "**Current Session:** 2026-06-05 — Session 85: F6 test" in log
    assert "**Current Layer:** New layer text" in log
    assert "tested the F6 orchestrator" in log  # rendered from LogEntry.what_was_done

    ctx = (root / ".claude/session-context.md").read_text()
    assert "new status here" in ctx and "old status" not in ctx

    tasks = (root / ".claude/tasks.md").read_text()
    assert "- [x] (T-99)" in tasks

    assert (run_dir / "input.md").read_text() == "verbatim payload text"
    assert "Session 85" in (run_dir / "report.md").read_text()


# ---- unit: run_handoff writes report to provided run_dir --------------------

def test_run_handoff_writes_report_to_provided_run_dir(tmp_path):
    """report.md is written to the run_dir the caller passed in, not one created internally."""
    root = _setup(tmp_path)
    run_dir = _make_run_dir(root)

    report = run_handoff(root, REGISTER, _payload(), git=FakeGit(clean=True),
                         rotate=fake_rotate, clock=CLOCK, run_dir=run_dir)

    assert (run_dir / "report.md").exists()
    assert report.committed


# ---- unit: dirty tree precondition ------------------------------------------

def test_dirty_tree_aborts_before_any_change(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=False)
    run_dir = _make_run_dir(root)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate,
                         clock=CLOCK, run_dir=run_dir)

    assert not report.committed and not report.rolled_back
    assert "precondition" in report.reason.lower()
    assert git.committed is None
    assert "old status" in (root / ".claude/session-context.md").read_text()


# ---- unit: verify failure (in-memory, nothing written) ----------------------

def test_verify_failure_rolls_back_without_writing(tmp_path, monkeypatch):
    root = _setup(tmp_path)
    git = FakeGit(clean=True)
    run_dir = _make_run_dir(root)

    def boom_verify(*a, **k):
        raise VerifyError("marker mismatch")

    monkeypatch.setattr(orchestrator, "verify", boom_verify)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate,
                         clock=CLOCK, run_dir=run_dir)

    assert report.rolled_back and not report.committed and not report.verify_ok
    assert "verify failed" in report.reason.lower()
    assert git.committed is None
    assert "old status" in (root / ".claude/session-context.md").read_text()
    assert "verify failed" in (run_dir / "report.md").read_text().lower()


# ---- unit: block content is newline-normalized before splicing --------------

def test_append_block_without_trailing_newline_keeps_marker_on_its_line(tmp_path):
    """Regression (dog-food, session 86): a payload block whose content lacks a
    trailing newline must NOT glue the closing ref marker onto the appended line.
    """
    root = _setup(tmp_path)
    (root / ".claude/tasks.md").write_text(
        "# Tasks\n\n"
        "<!-- ref:deferred-infra -->\n"
        "- [ ] (T-10) existing\n"
        "<!-- /ref:deferred-infra -->\n"
    )
    register = dict(REGISTER)
    register["tasks-append"] = {
        "file": ".claude/tasks.md",
        "locator": {"type": "ref_block", "key": "deferred-infra"},
        "write_mode": "append",
    }
    payload = HandoffPayload(
        session_title="append test",
        current_layer="L",
        blocks={"tasks-append": "- [ ] (T-11) new task"},  # NO trailing newline
        log_entry=None,
        checkoffs=[],
        raw="x",
    )
    run_dir = _make_run_dir(root)

    report = run_handoff(root, register, payload, git=FakeGit(clean=True),
                         rotate=fake_rotate, clock=CLOCK, run_dir=run_dir)

    assert report.committed and report.verify_ok
    tasks = (root / ".claude/tasks.md").read_text()
    assert "- [ ] (T-11) new task\n<!-- /ref:deferred-infra -->" in tasks
    assert "new task<!-- /ref:deferred-infra -->" not in tasks


# ---- unit: stage_and_apply is public and callable ---------------------------

def test_stage_and_apply_is_callable(tmp_path):
    """stage_and_apply is importable and returns (modified_by_file, region_edits)."""
    root = _setup(tmp_path)
    modified, edits = stage_and_apply(root, REGISTER, _payload(), clock=CLOCK)
    assert ".claude/session-log.md" in modified
    assert any(e.role == "current-status" for e in edits)


# ---- unit: commit failure triggers git rollback -----------------------------

def test_commit_failure_invokes_checkout(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=True, fail_commit=True)
    run_dir = _make_run_dir(root)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate,
                         clock=CLOCK, run_dir=run_dir)

    assert report.rolled_back and report.verify_ok and not report.committed
    assert git.committed is None
    assert git.checked_out is not None


# ---- integration: real git happy path + real rollback -----------------------

def _git_init(root):
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    (root / ".claude" / "archive").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)


def _porcelain(root, paths):
    return subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=root, capture_output=True, text=True,
    ).stdout.strip()


TRACKING = [".claude/session-log.md", ".claude/session-context.md", ".claude/tasks.md"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_integration_real_git_commits(tmp_path):
    root = _setup(tmp_path)
    _git_init(root)
    run_dir = _make_run_dir(root)

    report = run_handoff(root, REGISTER, _payload(), git=SubprocessGit(root),
                         rotate=fake_rotate, clock=CLOCK, run_dir=run_dir)

    assert report.committed
    log = subprocess.run(["git", "log", "--oneline"], cwd=root,
                         capture_output=True, text=True).stdout
    assert "session 85" in log.lower()
    assert _porcelain(root, TRACKING) == ""


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_integration_real_git_rollback_restores_files(tmp_path):
    root = _setup(tmp_path)
    _git_init(root)
    run_dir = _make_run_dir(root)

    report = run_handoff(root, REGISTER, _payload(), git=SubprocessGit(root),
                         rotate=boom_rotate, clock=CLOCK, run_dir=run_dir)

    assert report.rolled_back and not report.committed
    assert _porcelain(root, TRACKING) == ""
    count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    assert count == "1"
