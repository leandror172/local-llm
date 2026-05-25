import pathlib

import pytest

from ollama_mcp.server import patch_file


async def test_basic_replacement_unique_match(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    return 1\n", encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 1", new_string="return 42")
    assert "1 replacement" in result
    assert file_path.read_text(encoding="utf-8") == "def foo():\n    return 42\n"


async def test_basic_replacement_return_includes_count(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    return 1\n", encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 1", new_string="return 42")
    assert "1 replacement" in result


async def test_old_string_not_found_returns_error(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    return 1\n", encoding="utf-8")
    original_content = file_path.read_text(encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 99", new_string="return 42")
    assert result.startswith("Error:")
    assert file_path.read_text(encoding="utf-8") == original_content


async def test_non_unique_old_string_returns_error_with_count(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    return 1\ndef bar():\n    return 1\n", encoding="utf-8")
    original_content = file_path.read_text(encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 1", new_string="return 42", replace_all=False)
    assert result.startswith("Error:")
    assert "found 2 times" in result
    assert file_path.read_text(encoding="utf-8") == original_content


async def test_replace_all_replaces_every_occurrence(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    return 1\ndef bar():\n    return 1\n", encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 1", new_string="return 99", replace_all=True)
    assert "2 replacement" in result
    content = file_path.read_text(encoding="utf-8")
    assert "return 1" not in content
    assert content.count("return 99") == 2


async def test_replace_all_with_single_occurrence_succeeds(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    return 1\n", encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 1", new_string="return 99", replace_all=True)
    assert not result.startswith("Error:")
    assert "1 replacement" in result


async def test_multiline_old_string(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("    x = 1\n    return x\n", encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="    x = 1\n    return x", new_string="    return 42")
    content = file_path.read_text(encoding="utf-8")
    assert "x = 1" not in content
    assert "return 42" in content


async def test_file_not_found_returns_error_not_exception(tmp_path):
    result = await patch_file(path=str(tmp_path / "nonexistent.py"), old_string="x", new_string="y")
    assert result.startswith("Error:")


async def test_relative_path_resolved_from_repo_root(tmp_path, monkeypatch):
    file_path = tmp_path / "r.py"
    file_path.write_text("x = 1\n", encoding="utf-8")

    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(tmp_path))
    result = await patch_file(path="r.py", old_string="x = 1", new_string="x = 2")
    assert "1 replacement" in result
    assert file_path.read_text(encoding="utf-8") == "x = 2\n"


async def test_tilde_in_path_expands_to_home(tmp_path, monkeypatch):
    """`~/foo` must resolve to $HOME/foo, not be treated as a literal directory.

    Regression: prior to expanduser() in _resolve_output_path, both output_file
    and patch_file would join the literal "~" onto REPO_ROOT, silently writing
    to `<repo>/~/foo` instead of the user's home directory.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    file_path = tmp_path / "foo.py"
    file_path.write_text("return 1\n", encoding="utf-8")

    result = await patch_file(path="~/foo.py", old_string="return 1", new_string="return 42")

    assert "1 replacement" in result
    assert file_path.read_text(encoding="utf-8") == "return 42\n"
    # Confirm we didn't write to a literal "~" directory anywhere.
    assert not (tmp_path / "~").exists()


async def test_utf8_round_trip(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("# café\nreturn 1\n", encoding="utf-8")

    result = await patch_file(path=str(file_path), old_string="return 1", new_string="return 42")
    content = file_path.read_text(encoding="utf-8")
    assert "café" in content
    assert "return 42" in content
