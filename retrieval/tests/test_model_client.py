"""
Tests for retrieval/model_client.py

Covers:
- load_config: reads Phase 2 interim flat config.yaml shape
- load_config: raises on missing file
- ModelClient.embed_dim: returns correct dimension from config
- ModelClient.embed_texts: calls POST /api/embed, returns embeddings list
- ModelClient.embed_texts: raises on connection refused
- ModelClient.embed_texts: validates returned vector length matches embed_dim
- ModelClient.embed_query: thin delegate to embed_texts(texts, role="embedding")
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

# Add retrieval/ dir to path so we can import model_client as a module
RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import model_client  # noqa: E402
from schemas import TOPIC_FORMAT_SCHEMA  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CONFIG_YAML = """\
models:
  ollama-bge-m3-dim-1024:
    provider: ollama
    model: bge-m3
    address: http://localhost:11434
    embed_dim: 1024
roles:
  embedding: ollama-bge-m3-dim-1024
"""


@pytest.fixture
def config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(VALID_CONFIG_YAML, encoding="utf-8")
    return p


@pytest.fixture
def client(config_file):
    cfg = model_client.load_config(config_file)
    return model_client.ModelClient(cfg)


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_returns_embedding_role(config_file):
    cfg = model_client.load_config(config_file)
    assert "embedding" in cfg


def test_load_config_embedding_has_model(config_file):
    cfg = model_client.load_config(config_file)
    assert cfg["embedding"]["model"] == "bge-m3"


def test_load_config_embedding_has_address(config_file):
    cfg = model_client.load_config(config_file)
    assert cfg["embedding"]["address"] == "http://localhost:11434"


def test_load_config_embedding_has_embed_dim(config_file):
    cfg = model_client.load_config(config_file)
    assert cfg["embedding"]["embed_dim"] == 1024


def test_load_config_missing_file_raises():
    with pytest.raises((FileNotFoundError, OSError)):
        model_client.load_config(Path("/nonexistent/config.yaml"))


# ---------------------------------------------------------------------------
# ModelClient.embed_dim
# ---------------------------------------------------------------------------

def test_embed_dim_returns_1024(client):
    assert client.embed_dim("embedding") == 1024


def test_embed_dim_unknown_role_raises(client):
    with pytest.raises((KeyError, ValueError)):
        client.embed_dim("nonexistent_role")


# ---------------------------------------------------------------------------
# ModelClient.embed_texts — success path
# ---------------------------------------------------------------------------

def _fake_embeddings(texts):
    """Return a unit vector per text (dim=1024)."""
    return [[0.01] * 1024 for _ in texts]


def test_embed_texts_returns_one_vector_per_text(client):
    texts = ["hello world", "latent topic graph"]
    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {"embeddings": _fake_embeddings(texts)}

    with patch("httpx.post", return_value=fake_resp) as mock_post:
        result = client.embed_texts(texts, role="embedding")

    assert len(result) == 2


def test_embed_texts_calls_correct_endpoint(client):
    texts = ["test"]
    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {"embeddings": _fake_embeddings(texts)}

    with patch("httpx.post", return_value=fake_resp) as mock_post:
        client.embed_texts(texts, role="embedding")

    call_url = mock_post.call_args[0][0]
    assert "/api/embed" in call_url


def test_embed_texts_sends_model_and_input(client):
    texts = ["topic one", "topic two"]
    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {"embeddings": _fake_embeddings(texts)}

    with patch("httpx.post", return_value=fake_resp) as mock_post:
        client.embed_texts(texts, role="embedding")

    payload = mock_post.call_args[1]["json"]
    assert payload["model"] == "bge-m3"
    assert payload["input"] == texts


def test_embed_texts_vector_length_matches_embed_dim(client):
    texts = ["check dimension"]
    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {"embeddings": _fake_embeddings(texts)}

    with patch("httpx.post", return_value=fake_resp):
        result = client.embed_texts(texts, role="embedding")

    assert len(result[0]) == 1024


# ---------------------------------------------------------------------------
# ModelClient.embed_texts — error paths
# ---------------------------------------------------------------------------

def test_embed_texts_connection_refused_raises(client):
    import httpx as _httpx
    with patch("httpx.post", side_effect=_httpx.ConnectError("connection refused")):
        with pytest.raises((_httpx.ConnectError, SystemExit, ConnectionError)):
            client.embed_texts(["text"], role="embedding")


def test_embed_texts_wrong_vector_length_raises(client):
    texts = ["test"]
    bad_resp = MagicMock()
    bad_resp.raise_for_status = MagicMock()
    bad_resp.json.return_value = {"embeddings": [[0.01] * 512]}  # wrong dim

    with patch("httpx.post", return_value=bad_resp):
        with pytest.raises((ValueError, AssertionError)):
            client.embed_texts(texts, role="embedding")


# ---------------------------------------------------------------------------
# Two-level config fixtures
# ---------------------------------------------------------------------------

VALID_TWO_LEVEL_CONFIG_YAML = """\
models:
  ollama-qwen3-14b-no-think:
    provider: ollama
    model: qwen3:14b
    address: http://localhost:11434
    think: false
    timeout_s: 600
    options:
      num_ctx: 32768
      temperature: 0.1
  ollama-qwen25coder-14b:
    provider: ollama
    model: qwen2.5-coder:14b
    address: http://localhost:11434
    timeout_s: 600
    options:
      num_ctx: 32768
      temperature: 0.1
roles:
  extraction_prose: ollama-qwen3-14b-no-think
  extraction_code: ollama-qwen25coder-14b
"""


@pytest.fixture
def two_level_config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(VALID_TWO_LEVEL_CONFIG_YAML, encoding="utf-8")
    return p


@pytest.fixture
def client_with_extraction(two_level_config_file):
    cfg = model_client.load_config(two_level_config_file)
    return model_client.ModelClient(cfg)


# ---------------------------------------------------------------------------
# ChatResult NamedTuple
# ---------------------------------------------------------------------------

def test_chat_result_is_namedtuple():
    result = model_client.ChatResult(content="x", model="m", prompt_tokens=1, eval_count=2)
    assert isinstance(result, tuple)


def test_chat_result_has_content_field():
    result = model_client.ChatResult(content="x", model="m", prompt_tokens=1, eval_count=2)
    assert result.content == "x"


def test_chat_result_has_model_field():
    result = model_client.ChatResult(content="x", model="m", prompt_tokens=1, eval_count=2)
    assert result.model == "m"


def test_chat_result_has_prompt_tokens_field():
    result = model_client.ChatResult(content="x", model="m", prompt_tokens=1, eval_count=2)
    assert result.prompt_tokens == 1


def test_chat_result_has_eval_count_field():
    result = model_client.ChatResult(content="x", model="m", prompt_tokens=1, eval_count=2)
    assert result.eval_count == 2


# ---------------------------------------------------------------------------
# load_config — two-level resolution
# ---------------------------------------------------------------------------

def test_load_config_two_level_returns_extraction_prose(two_level_config_file):
    cfg = model_client.load_config(two_level_config_file)
    assert "extraction_prose" in cfg


def test_load_config_two_level_prose_model(two_level_config_file):
    cfg = model_client.load_config(two_level_config_file)
    assert cfg["extraction_prose"]["model"] == "qwen3:14b"


def test_load_config_two_level_code_model(two_level_config_file):
    cfg = model_client.load_config(two_level_config_file)
    assert cfg["extraction_code"]["model"] == "qwen2.5-coder:14b"


def test_load_config_undefined_model_raises(tmp_path):
    invalid_yaml = "models: {}\nroles:\n  prose: nonexistent\n"
    p = tmp_path / "config.yaml"
    p.write_text(invalid_yaml, encoding="utf-8")
    with pytest.raises(KeyError):
        model_client.load_config(p)


# ---------------------------------------------------------------------------
# call() — payload shape
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_ollama_resp():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "message": {"content": "topics..."},
        "model": "qwen3:14b",
        "prompt_eval_count": 10,
        "eval_count": 50,
    }
    return resp


def test_call_payload_has_stream_false(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config)
    payload = mock_post.call_args[1]["json"]
    assert payload["stream"] == False


def test_call_payload_has_messages(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config)
    payload = mock_post.call_args[1]["json"]
    assert payload["messages"] == [{"role": "user", "content": "test prompt"}]


def test_call_injects_format_when_schema_passed(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config, schema={"type": "object"})
    payload = mock_post.call_args[1]["json"]
    assert "format" in payload


def test_call_omits_format_when_no_schema(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config)
    payload = mock_post.call_args[1]["json"]
    assert "format" not in payload


def test_call_injects_think_when_in_config(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config)
    payload = mock_post.call_args[1]["json"]
    assert payload["think"] == False


def test_call_omits_think_when_not_in_config(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_code"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config)
    payload = mock_post.call_args[1]["json"]
    assert "think" not in payload


def test_call_passes_options_from_config(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config)
    payload = mock_post.call_args[1]["json"]
    assert payload["options"] == model_config["options"]


def test_call_timeout_override_beats_config(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp) as mock_post:
        client_with_extraction.call("test prompt", model_config, timeout=999)
    assert mock_post.call_args[1]["timeout"] == 999


def test_call_returns_chat_result(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp):
        result = client_with_extraction.call("test prompt", model_config)
    assert isinstance(result, model_client.ChatResult)


def test_call_populates_content(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp):
        result = client_with_extraction.call("test prompt", model_config)
    assert result.content == "topics..."


def test_call_populates_model(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp):
        result = client_with_extraction.call("test prompt", model_config)
    assert result.model == "qwen3:14b"


def test_call_populates_prompt_tokens(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp):
        result = client_with_extraction.call("test prompt", model_config)
    assert result.prompt_tokens == 10


def test_call_populates_eval_count(client_with_extraction, fake_ollama_resp):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", return_value=fake_ollama_resp):
        result = client_with_extraction.call("test prompt", model_config)
    assert result.eval_count == 50


# ---------------------------------------------------------------------------
# call() — error propagation
# ---------------------------------------------------------------------------

def test_call_timeout_exception_propagates(client_with_extraction):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", side_effect=httpx.TimeoutException("t")):
        with pytest.raises(httpx.TimeoutException):
            client_with_extraction.call("test prompt", model_config)


def test_call_connect_error_propagates(client_with_extraction):
    model_config = client_with_extraction.config["extraction_prose"]
    with patch("httpx.post", side_effect=httpx.ConnectError("c")):
        with pytest.raises(httpx.ConnectError):
            client_with_extraction.call("test prompt", model_config)


# ---------------------------------------------------------------------------
# Named methods — dispatch to _chat with correct config + schema
# ---------------------------------------------------------------------------

def test_extract_prose_calls_chat_with_extraction_prose_config(client_with_extraction):
    with patch.object(client_with_extraction, "_chat", return_value=MagicMock()) as mock_chat:
        client_with_extraction.extract_prose("my prompt")
        assert mock_chat.call_args[0][1] == client_with_extraction.config["extraction_prose"]


def test_extract_code_calls_chat_with_extraction_code_config(client_with_extraction):
    with patch.object(client_with_extraction, "_chat", return_value=MagicMock()) as mock_chat:
        client_with_extraction.extract_code("my prompt")
        assert mock_chat.call_args[0][1] == client_with_extraction.config["extraction_code"]


def test_extract_prose_passes_topic_schema(client_with_extraction):
    with patch.object(client_with_extraction, "_chat", return_value=MagicMock()) as mock_chat:
        client_with_extraction.extract_prose("my prompt")
        assert mock_chat.call_args[1].get("schema") == TOPIC_FORMAT_SCHEMA


# ---------------------------------------------------------------------------
# Named method — embed_query delegates to embed_texts(texts, role="embedding")
# ---------------------------------------------------------------------------

def test_embed_query_delegates_to_embed_texts_with_embedding_role(client):
    texts = ["test query"]
    with patch.object(client, "embed_texts", return_value=[[0.01] * 1024]) as mock_embed:
        client.embed_query(texts)
    mock_embed.assert_called_once_with(texts, role="embedding")


def test_embed_query_returns_embed_texts_result(client):
    texts = ["sentinel query"]
    sentinel = [[0.99] * 1024]
    with patch.object(client, "embed_texts", return_value=sentinel):
        result = client.embed_query(texts)
    assert result is sentinel


def test_embed_query_end_to_end_returns_vectors(client):
    texts = ["end to end query"]
    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {"embeddings": _fake_embeddings(texts)}

    with patch("httpx.post", return_value=fake_resp):
        result = client.embed_query(texts)

    assert len(result) == 1
    assert len(result[0]) == 1024
