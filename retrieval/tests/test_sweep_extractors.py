import json
import sys
import httpx
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY
import pytest

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import sweep_extractors  # noqa: E402
from schemas import TOPIC_FORMAT_SCHEMA  # noqa: E402
import model_client  # noqa: E402

# TEST GROUP 1 — _build_benchmark_config(model)

def test_build_benchmark_config_qwen3_14b_has_think_false():
    result = sweep_extractors._build_benchmark_config("qwen3:14b")
    assert result["think"] is False

def test_build_benchmark_config_qwen3_8b_has_think_false():
    result = sweep_extractors._build_benchmark_config("qwen3:8b")
    assert result["think"] is False

def test_build_benchmark_config_coder_has_no_think():
    result = sweep_extractors._build_benchmark_config("qwen2.5-coder:14b")
    assert "think" not in result

def test_build_benchmark_config_gemma_has_no_think():
    result = sweep_extractors._build_benchmark_config("gemma3:12b")
    assert "think" not in result

def test_build_benchmark_config_sets_model_name():
    result = sweep_extractors._build_benchmark_config("qwen3:14b")
    assert result["model"] == "qwen3:14b"

def test_build_benchmark_config_has_address():
    result = sweep_extractors._build_benchmark_config("qwen3:14b")
    assert result["address"].startswith("http")

def test_build_benchmark_config_has_options_with_num_ctx():
    result = sweep_extractors._build_benchmark_config("qwen3:14b")
    assert result["options"]["num_ctx"] is not None

# TEST GROUP 2 — run_single(model, rel_path, role, template, client)

VALID_TOPICS_JSON = json.dumps({"topics": [{"name": "t", "description": "d", "spans": [[1, 2]]}]})

@pytest.fixture
def mock_client():
    return MagicMock(spec=model_client.ModelClient)

@pytest.fixture(autouse=True)
def setup_repo_root(tmp_path):
    sweep_extractors.REPO_ROOT = tmp_path

def test_run_single_calls_client_call_with_schema(tmp_path, mock_client):
    file_content = "Sample content"
    file_path = tmp_path / "sample.md"
    file_path.write_text(file_content)
    
    rel_path = str(file_path.relative_to(sweep_extractors.REPO_ROOT))
    model = "qwen3:14b"
    role = "test_role"
    template = "test_template"
    
    mock_client.call.return_value = model_client.ChatResult(content=VALID_TOPICS_JSON, model=model, prompt_tokens=10, eval_count=20)
    
    record = sweep_extractors.run_single(model, rel_path, role, template, mock_client)
    
    mock_client.call.assert_called_once_with(
        ANY,
        ANY,
        schema=TOPIC_FORMAT_SCHEMA,
        timeout=sweep_extractors.TIMEOUT_S
    )

def test_run_single_calls_client_call_with_timeout(tmp_path, mock_client):
    file_path = tmp_path / "sample.md"
    file_path.write_text("Sample content")
    rel_path = str(file_path.relative_to(sweep_extractors.REPO_ROOT))

    mock_client.call.return_value = model_client.ChatResult(
        content=VALID_TOPICS_JSON, model="qwen3:14b", prompt_tokens=10, eval_count=20
    )

    sweep_extractors.run_single("qwen3:14b", rel_path, "test_role", "test_template", mock_client)

    _, kwargs = mock_client.call.call_args
    assert kwargs["timeout"] == sweep_extractors.TIMEOUT_S

def test_run_single_model_config_matches_build_benchmark_config(tmp_path, mock_client):
    file_content = "Sample content"
    file_path = tmp_path / "sample.md"
    file_path.write_text(file_content)
    
    rel_path = str(file_path.relative_to(sweep_extractors.REPO_ROOT))
    model = "qwen3:14b"
    role = "test_role"
    template = "test_template"
    
    mock_client.call.return_value = model_client.ChatResult(content=VALID_TOPICS_JSON, model=model, prompt_tokens=10, eval_count=20)
    
    record = sweep_extractors.run_single(model, rel_path, role, template, mock_client)
    
    expected_config = sweep_extractors._build_benchmark_config(model)
    positional_args = mock_client.call.call_args[0]
    actual_model_config = positional_args[1]  # (prompt, model_config) positional
    assert actual_model_config == expected_config

def test_run_single_returns_ok_status_on_valid_response(tmp_path, mock_client):
    file_content = "Sample content"
    file_path = tmp_path / "sample.md"
    file_path.write_text(file_content)
    
    rel_path = str(file_path.relative_to(sweep_extractors.REPO_ROOT))
    model = "qwen3:14b"
    role = "test_role"
    template = "test_template"
    
    mock_client.call.return_value = model_client.ChatResult(content=VALID_TOPICS_JSON, model=model, prompt_tokens=10, eval_count=20)
    
    record = sweep_extractors.run_single(model, rel_path, role, template, mock_client)
    
    assert record["status"] == "ok"

def test_run_single_returns_timeout_status_on_timeout_exception(tmp_path, mock_client):
    file_content = "Sample content"
    file_path = tmp_path / "sample.md"
    file_path.write_text(file_content)
    
    rel_path = str(file_path.relative_to(sweep_extractors.REPO_ROOT))
    model = "qwen3:14b"
    role = "test_role"
    template = "test_template"
    
    mock_client.call.side_effect = httpx.TimeoutException("t")
    
    record = sweep_extractors.run_single(model, rel_path, role, template, mock_client)
    
    assert record["status"] == "timeout"

def test_run_single_record_has_contract_fields(tmp_path, mock_client):
    file_content = "Sample content"
    file_path = tmp_path / "sample.md"
    file_path.write_text(file_content)
    
    rel_path = str(file_path.relative_to(sweep_extractors.REPO_ROOT))
    model = "qwen3:14b"
    role = "test_role"
    template = "test_template"
    
    mock_client.call.return_value = model_client.ChatResult(content=VALID_TOPICS_JSON, model=model, prompt_tokens=10, eval_count=20)
    
    record = sweep_extractors.run_single(model, rel_path, role, template, mock_client)
    
    required_fields = ["run_id", "timestamp", "model", "file", "file_role", "status", "parsed_topics"]
    assert all(field in record for field in required_fields)
