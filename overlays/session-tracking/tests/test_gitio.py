# test_gitio.py

import shutil
import subprocess
import pytest
from pathlib import Path
from sessiontracking.handoff.gitio import SubprocessGit


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_log_messages_returns_subject_lines(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root)
    subprocess.run(["git", "config", "--local", "user.name", "test"], cwd=repo_root)
    subprocess.run(["git", "config", "--local", "user.email", "test@example.com"], cwd=repo_root)

    (repo_root / "file1.txt").write_text("content 1")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_root)
    subprocess.run(["git", "commit", "-m", "Commit 1"], cwd=repo_root)

    (repo_root / "file2.txt").write_text("content 2")
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_root)
    subprocess.run(["git", "commit", "-m", "Commit 2"], cwd=repo_root)

    git = SubprocessGit(repo_root)
    messages = git.log_messages(2)
    assert messages == ["Commit 2", "Commit 1"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_log_messages_default_n_returns_up_to_five(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root)
    subprocess.run(["git", "config", "--local", "user.name", "test"], cwd=repo_root)
    subprocess.run(["git", "config", "--local", "user.email", "test@example.com"], cwd=repo_root)

    for i in range(3):
        (repo_root / f"file{i}.txt").write_text(f"content {i}")
        subprocess.run(["git", "add", f"file{i}.txt"], cwd=repo_root)
        subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=repo_root)

    git = SubprocessGit(repo_root)
    messages = git.log_messages()
    assert len(messages) == 3
    assert messages == ["Commit 2", "Commit 1", "Commit 0"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_log_messages_n_limits_output(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root)
    subprocess.run(["git", "config", "--local", "user.name", "test"], cwd=repo_root)
    subprocess.run(["git", "config", "--local", "user.email", "test@example.com"], cwd=repo_root)

    for i in range(3):
        (repo_root / f"file{i}.txt").write_text(f"content {i}")
        subprocess.run(["git", "add", f"file{i}.txt"], cwd=repo_root)
        subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=repo_root)

    git = SubprocessGit(repo_root)
    messages = git.log_messages(1)
    assert len(messages) == 1
    assert messages == ["Commit 2"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_log_messages_empty_repo_raises(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root)

    git = SubprocessGit(repo_root)
    with pytest.raises(subprocess.CalledProcessError):
        git.log_messages()
