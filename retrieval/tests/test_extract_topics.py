import json
import sys
import httpx
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import extract_topics  # noqa: E402
import model_client  # noqa: E402
import embed  # noqa: E402

@pytest.fixture(autouse=True)
def set_repo_root(tmp_path):
    extract_topics.REPO_ROOT = tmp_path

@pytest.fixture
def mock_client():
    return MagicMock(spec=model_client.ModelClient)

VALID_TOPICS_JSON = json.dumps({"topics": [{"name": "t", "description": "d", "spans": [[1, 2]]}]})
FAKE_RESULT_PROSE = model_client.ChatResult(content=VALID_TOPICS_JSON, model="qwen3:14b", prompt_tokens=10, eval_count=20)
FAKE_RESULT_CODE  = model_client.ChatResult(content=VALID_TOPICS_JSON, model="qwen2.5-coder:14b", prompt_tokens=10, eval_count=20)

# GROUP 1 — route_file
def test_route_file_py_returns_extraction_code():
    assert extract_topics.route_file("src/main.py") == "extraction_code"

def test_route_file_md_returns_extraction_prose():
    assert extract_topics.route_file("docs/design.md") == "extraction_prose"

def test_route_file_go_returns_extraction_code():
    assert extract_topics.route_file("lib/util.go") == "extraction_code"

# GROUP 2 — run_file dispatch
# Each test creates the corpus file in tmp_path (REPO_ROOT is redirected there by autouse fixture).

def _make_file(tmp_path, rel: str, content: str = "sample") -> str:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return rel


@patch('extract_topics.route')
def test_run_file_prose_calls_extract_prose(mock_route, tmp_path, mock_client):
    mock_route.return_value = "extraction_prose"
    mock_client.extract_prose.return_value = FAKE_RESULT_PROSE
    record = extract_topics.run_file(_make_file(tmp_path, "docs/design.md"), "role", "template", mock_client)
    assert mock_client.extract_prose.called

@patch('extract_topics.route')
def test_run_file_code_calls_extract_code(mock_route, tmp_path, mock_client):
    mock_route.return_value = "extraction_code"
    mock_client.extract_code.return_value = FAKE_RESULT_CODE
    record = extract_topics.run_file(_make_file(tmp_path, "src/main.py"), "role", "template", mock_client)
    assert mock_client.extract_code.called

@patch('extract_topics.route')
def test_run_file_model_field_matches_result_model(mock_route, tmp_path, mock_client):
    mock_route.return_value = "extraction_prose"
    mock_client.extract_prose.return_value = FAKE_RESULT_PROSE
    record = extract_topics.run_file(_make_file(tmp_path, "docs/design.md"), "role", "template", mock_client)
    assert record["model"] == "qwen3:14b"

@patch('extract_topics.route')
def test_run_file_returns_ok_status(mock_route, tmp_path, mock_client):
    mock_route.return_value = "extraction_prose"
    mock_client.extract_prose.return_value = FAKE_RESULT_PROSE
    record = extract_topics.run_file(_make_file(tmp_path, "docs/design.md"), "role", "template", mock_client)
    assert record["status"] == "ok"

@patch('extract_topics.route')
def test_run_file_timeout_sets_status_timeout(mock_route, tmp_path, mock_client):
    mock_route.return_value = "extraction_prose"
    mock_client.extract_prose.side_effect = httpx.TimeoutException("t")
    record = extract_topics.run_file(_make_file(tmp_path, "docs/design.md"), "role", "template", mock_client)
    assert record["status"] == "timeout"

@patch('extract_topics.route')
def test_run_file_record_has_contract_fields(mock_route, tmp_path, mock_client):
    mock_route.return_value = "extraction_prose"
    mock_client.extract_prose.return_value = FAKE_RESULT_PROSE
    record = extract_topics.run_file(_make_file(tmp_path, "docs/design.md"), "role", "template", mock_client)
    assert all(field in record for field in ["run_id","timestamp","model","file","file_role","status","parsed_topics"])

# GROUP 3 — parse_topics
def test_parse_topics_valid_json_returns_list():
    topics = extract_topics.parse_topics(VALID_TOPICS_JSON)
    assert isinstance(topics, list)

def test_parse_topics_invalid_json_returns_none():
    topics = extract_topics.parse_topics("not json")
    assert topics is None
