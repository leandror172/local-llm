import pathlib

import pytest

from ollama_mcp.server import ask_ollama, generate_code


async def test_file_is_written_when_output_file_set(tmp_path, mock_ollama):
    output_file = tmp_path / "output.txt"
    await ask_ollama(prompt="test", output_file=str(output_file))
    assert output_file.exists()


async def test_returned_content_equals_file_content(tmp_path, mock_ollama):
    output_file = tmp_path / "output.txt"
    result = await ask_ollama(prompt="test", output_file=str(output_file))
    assert result == "mocked-model-output"
    assert result == output_file.read_text(encoding="utf-8")


async def test_output_only_returns_status_not_content(tmp_path, mock_ollama):
    output_file = tmp_path / "output.txt"
    result = await ask_ollama(prompt="test", output_file=str(output_file), output_only=True)
    assert "Written" in result
    assert "mocked-model-output" not in result
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == "mocked-model-output"


async def test_output_only_status_contains_byte_count_and_path(tmp_path, mock_ollama):
    output_file = tmp_path / "output.txt"
    result = await ask_ollama(prompt="test", output_file=str(output_file), output_only=True)
    assert "Written" in result
    assert str(output_file) in result
    assert str(len("mocked-model-output".encode())) in result


async def test_output_only_without_output_file_returns_full_content(mock_ollama):
    result = await ask_ollama(prompt="test", output_only=True)
    assert result == "mocked-model-output"


async def test_relative_path_resolved_from_repo_root(tmp_path, monkeypatch, mock_ollama):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(tmp_path))
    await ask_ollama(prompt="test", output_file="subdir/out.py")
    assert (tmp_path / "subdir" / "out.py").exists()


async def test_parent_directories_created_automatically(tmp_path, mock_ollama):
    output_file = tmp_path / "a" / "b" / "c" / "out.py"
    await ask_ollama(prompt="test", output_file=str(output_file))
    assert output_file.exists()


async def test_relative_path_without_repo_root_returns_error(monkeypatch, mock_ollama):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", None)
    result = await ask_ollama(prompt="test", output_file="relative/path.py")
    assert result.startswith("Error:")


async def test_generate_code_file_written_and_content_returned(tmp_path, mock_ollama):
    output_file = tmp_path / "output.py"
    result = await generate_code(prompt="test", language="python", output_file=str(output_file))
    assert output_file.exists()
    assert result == output_file.read_text(encoding="utf-8")
    assert "[Language: python]" in mock_ollama.chat.call_args.kwargs["prompt"]
