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

import orchestrator
from orchestrator import run_handoff, HandoffPayload
from gitio import SubprocessGit
from verifier import VerifyError


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
            "log-entry": "\n## 2026-06-05 - Session 85: F6 test\n\nnew entry body\n\n---\n",
            "current-status": "\nnew status here\n",
        },
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


def fake_rotate(repo_root, keep=3):
    return types.SimpleNamespace(returncode=0, stdout="", stderr="")


def boom_rotate(repo_root, keep=3):
    raise RuntimeError("rotate boom")


# ---- unit: happy path -------------------------------------------------------

def test_happy_path_applies_commits_and_logs(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=True)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate, clock=CLOCK)

    assert report.committed and not report.rolled_back and report.verify_ok
    assert git.committed is not None and git.checked_out is None

    log = (root / ".claude/session-log.md").read_text()
    assert "**Current Session:** 2026-06-05 — Session 85: F6 test" in log
    assert "**Current Layer:** New layer text" in log
    assert "new entry body" in log

    ctx = (root / ".claude/session-context.md").read_text()
    assert "new status here" in ctx and "old status" not in ctx

    tasks = (root / ".claude/tasks.md").read_text()
    assert "- [x] (T-99)" in tasks

    runs = list((root / ".claude/local/handoff-runs").iterdir())
    assert len(runs) == 1
    assert (runs[0] / "input.md").read_text() == "verbatim payload text"
    assert "Session 85" in (runs[0] / "report.md").read_text()


# ---- unit: dirty tree precondition ------------------------------------------

def test_dirty_tree_aborts_before_any_change(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=False)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate, clock=CLOCK)

    assert not report.committed and not report.rolled_back
    assert "precondition" in report.reason.lower()
    assert git.committed is None
    assert "old status" in (root / ".claude/session-context.md").read_text()
    assert not (root / ".claude/local/handoff-runs").exists()


# ---- unit: verify failure (in-memory, nothing written) ----------------------

def test_verify_failure_rolls_back_without_writing(tmp_path, monkeypatch):
    root = _setup(tmp_path)
    git = FakeGit(clean=True)

    def boom_verify(*a, **k):
        raise VerifyError("marker mismatch")

    monkeypatch.setattr(orchestrator, "verify", boom_verify)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate, clock=CLOCK)

    assert report.rolled_back and not report.committed and not report.verify_ok
    assert "verify failed" in report.reason.lower()
    assert git.committed is None
    assert "old status" in (root / ".claude/session-context.md").read_text()  # untouched
    runs = list((root / ".claude/local/handoff-runs").iterdir())
    assert "verify failed" in (runs[0] / "report.md").read_text().lower()


# ---- unit: dry-run stages + verifies but writes nothing ---------------------

def test_dry_run_validates_without_writing(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=True)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate,
                         clock=CLOCK, dry_run=True)

    assert not report.committed and not report.rolled_back and report.verify_ok
    assert "dry-run" in report.reason.lower()
    assert report.edits  # populated so the caller can print a before->after preview
    assert git.committed is None and git.added is None  # no side effects at all
    assert "old status" in (root / ".claude/session-context.md").read_text()  # untouched
    assert "Session 84: Old topic" in (root / ".claude/session-log.md").read_text()
    assert not (root / ".claude/local/handoff-runs").exists()  # no run dir on dry-run


def test_dry_run_on_verify_failure_returns_reason_no_artifacts(tmp_path, monkeypatch):
    root = _setup(tmp_path)
    git = FakeGit(clean=True)

    def boom_verify(*a, **k):
        raise VerifyError("marker mismatch")

    monkeypatch.setattr(orchestrator, "verify", boom_verify)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate,
                         clock=CLOCK, dry_run=True)

    assert not report.committed and not report.verify_ok
    assert "verify" in report.reason.lower()
    assert not (root / ".claude/local/handoff-runs").exists()  # no artifacts on dry-run
    assert "old status" in (root / ".claude/session-context.md").read_text()


# ---- unit: commit failure triggers git rollback -----------------------------

def test_commit_failure_invokes_checkout(tmp_path):
    root = _setup(tmp_path)
    git = FakeGit(clean=True, fail_commit=True)

    report = run_handoff(root, REGISTER, _payload(), git=git, rotate=fake_rotate, clock=CLOCK)

    assert report.rolled_back and report.verify_ok and not report.committed
    assert git.committed is None
    assert git.checked_out is not None  # rollback path taken


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

    report = run_handoff(root, REGISTER, _payload(), git=SubprocessGit(root),
                         rotate=fake_rotate, clock=CLOCK)

    assert report.committed
    log = subprocess.run(["git", "log", "--oneline"], cwd=root,
                         capture_output=True, text=True).stdout
    assert "session 85" in log.lower()
    assert _porcelain(root, TRACKING) == ""  # tracking files committed, tree clean


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_integration_real_git_rollback_restores_files(tmp_path):
    root = _setup(tmp_path)
    _git_init(root)

    # rotate raises AFTER files are written -> exercises real git checkout restore
    report = run_handoff(root, REGISTER, _payload(), git=SubprocessGit(root),
                         rotate=boom_rotate, clock=CLOCK)

    assert report.rolled_back and not report.committed
    assert _porcelain(root, TRACKING) == ""  # files restored to HEAD
    count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    assert count == "1"  # no new commit
