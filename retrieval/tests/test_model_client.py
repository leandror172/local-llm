"""
Tests for retrieval/model_client.py

Covers:
- load_config: reads Phase 2 interim flat config.yaml shape
- load_config: raises on missing file
- ModelClient.embed_dim: returns correct dimension from config
- ModelClient.embed_texts: calls POST /api/embed, returns embeddings list
- ModelClient.embed_texts: raises on connection refused
- ModelClient.embed_texts: validates returned vector length matches embed_dim
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add retrieval/ dir to path so we can import model_client as a module
RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import model_client  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CONFIG_YAML = """\
roles:
  embedding:
    provider: ollama
    model: bge-m3
    address: http://localhost:11434
    embed_dim: 1024
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
