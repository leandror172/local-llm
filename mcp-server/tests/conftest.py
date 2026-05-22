import pathlib
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent.parent


@pytest.fixture
def ref_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    test_file = tmp_path / "test.md"
    test_file.write_text(
        "<!-- ref:test-key -->\nref content here\n<!-- /ref:test-key -->\n"
        "<!-- ref:other-key -->\nother content\n<!-- /ref:other-key -->\n"
    )
    return tmp_path


@pytest.fixture
def mock_ollama(monkeypatch) -> AsyncMock:
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "mocked-model-output"
    mock_client.chat.return_value = mock_response
    monkeypatch.setattr("ollama_mcp.server._client", mock_client)
    return mock_client
