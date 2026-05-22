import pathlib

import pytest

from ollama_mcp.server import (
    ContextFile,
    _build_refs_block,
    _resolve_ref_key,
    ask_ollama,
    generate_code,
)


async def test_resolve_ref_key_returns_block_content(monkeypatch, repo_root, ref_dir):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _resolve_ref_key("test-key", str(ref_dir))
    assert "ref content here" in result
    assert not result.startswith("Error:")


async def test_resolve_ref_key_missing_key_returns_error(monkeypatch, repo_root, ref_dir):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _resolve_ref_key("nonexistent-key-xyz", str(ref_dir))
    assert result.startswith("Error:") or "not found" in result.lower()


async def test_resolve_ref_key_root_is_respected(monkeypatch, repo_root, tmp_path):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _resolve_ref_key("test-key", str(tmp_path))
    assert result.startswith("Error:")


async def test_build_refs_block_wraps_in_refs_tags(monkeypatch, repo_root, ref_dir):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _build_refs_block(["test-key"], str(ref_dir))
    assert result.strip().startswith("<refs>")
    assert result.strip().endswith("</refs>")


async def test_build_refs_block_labels_each_key(monkeypatch, repo_root, ref_dir):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _build_refs_block(["test-key"], str(ref_dir))
    assert "<!-- ref:test-key -->" in result


async def test_build_refs_block_all_keys_present(monkeypatch, repo_root, ref_dir):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _build_refs_block(["test-key", "other-key"], str(ref_dir))
    assert "ref content here" in result
    assert "other content" in result


async def test_build_refs_block_fails_fast_on_missing_key(monkeypatch, repo_root, ref_dir):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    result = await _build_refs_block(["test-key", "missing-xyz"], str(ref_dir))
    assert result.startswith("Error:")
    assert "ref content here" not in result


async def test_refs_appear_before_user_prompt_in_ollama_call(monkeypatch, repo_root, ref_dir, mock_ollama):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    await ask_ollama(prompt="MY_SENTINEL_PROMPT", refs=["test-key"], refs_root=str(ref_dir))
    prompt_sent = mock_ollama.chat.call_args.kwargs["prompt"]
    pos_refs = prompt_sent.find("<refs>")
    pos_sentinel = prompt_sent.find("MY_SENTINEL_PROMPT")
    assert pos_refs >= 0
    assert pos_sentinel >= 0
    assert pos_refs < pos_sentinel


async def test_refs_appear_before_context_when_both_provided(monkeypatch, repo_root, ref_dir, mock_ollama):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    context_files = [ContextFile(path=str(repo_root / "CLAUDE.md"))]
    await ask_ollama(
        prompt="sentinel",
        refs=["test-key"],
        refs_root=str(ref_dir),
        context_files=context_files,
    )
    prompt_sent = mock_ollama.chat.call_args.kwargs["prompt"]
    pos_refs = prompt_sent.find("<refs>")
    pos_context = prompt_sent.find("<context>")
    assert pos_refs >= 0
    assert pos_context >= 0
    assert pos_refs < pos_context


async def test_generate_code_refs_appear_before_prompt(monkeypatch, repo_root, ref_dir, mock_ollama):
    monkeypatch.setattr("ollama_mcp.server.REPO_ROOT", str(repo_root))
    await generate_code(prompt="GC_SENTINEL_PROMPT", refs=["test-key"], refs_root=str(ref_dir))
    prompt_sent = mock_ollama.chat.call_args.kwargs["prompt"]
    pos_refs = prompt_sent.find("<refs>")
    pos_sentinel = prompt_sent.find("GC_SENTINEL_PROMPT")
    assert pos_refs >= 0
    assert pos_sentinel >= 0
    assert pos_refs < pos_sentinel
