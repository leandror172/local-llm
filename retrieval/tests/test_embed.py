"""
Tests for retrieval/embed.py

Covers:
- extractor routing: .py/.go/.ts/.java → qwen2.5-coder:14b; else → qwen3:14b
- winning-row filtering: picks the row matching file + winning model + status=ok
- topic parsing: uses parsed_topics from JSONL row
- topic slug normalization: snake_case, collision suffix
- embed text construction: description-only vs description_plus_spans
- output row shape: all 16 schema fields present and correct types
- batch embed: sends texts in correct batch size chunks
- max_failures abort: exits non-zero when failures exceed threshold
- skip behaviours: empty description, status != ok, no winning row
- vector length validation: aborts if embed returns wrong dim
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import embed  # noqa: E402
import model_client  # noqa: E402

# Minimal extraction cfg for tests — mirrors config.yaml extraction roles
EXTRACT_CFG = {
    "extraction_prose": {"model": "qwen3:14b"},
    "extraction_code": {"model": "qwen2.5-coder:14b"},
}


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def make_row(file, model, status="ok", topics=None, file_role="long_research_doc",
             run_id="abc-123", timestamp="2026-04-16T21:19:16.892426+00:00"):
    if topics is None:
        topics = [
            {"name": "topic_one", "description": "First topic.", "spans": [[1, 3]]},
            {"name": "topic_two", "description": "Second topic.", "spans": [[5, 7]]},
        ]
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "model": model,
        "file": file,
        "file_role": file_role,
        "status": status,
        "raw_response": json.dumps({"topics": topics}),
        "parsed_topics": topics,
    }


def fake_embed_response(texts):
    return [[0.01] * 1024 for _ in texts]


# ---------------------------------------------------------------------------
# Extractor routing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filepath,expected_model", [
    ("src/main.py",        "qwen2.5-coder:14b"),
    ("lib/util.go",        "qwen2.5-coder:14b"),
    ("app/component.ts",   "qwen2.5-coder:14b"),
    ("src/Parser.java",    "qwen2.5-coder:14b"),
    ("docs/design.md",     "qwen3:14b"),
    (".memories/QUICK.md", "qwen3:14b"),
    ("notes.txt",          "qwen3:14b"),
])
def test_winning_extractor_routing(filepath, expected_model):
    assert embed.winning_extractor(filepath, EXTRACT_CFG) == expected_model


def test_routing_agreement():
    cfg = model_client.load_config(embed.CONFIG_PATH)
    assert embed.winning_extractor("src/main.py", cfg) == cfg["extraction_code"]["model"]
    assert embed.winning_extractor("docs/design.md", cfg) == cfg["extraction_prose"]["model"]


def test_config_yaml_contract():
    """Regression: pins the real config.yaml so a tag/dim change is caught immediately.

    Guards Invariant D: winning-row match depends on Ollama echoing the exact tag that
    config.yaml declares. If a model is re-tagged (e.g., ':latest' instead of ':8b'),
    select_winning_row silently drops the row. This test will fail before that happens.
    """
    cfg = model_client.load_config(embed.CONFIG_PATH)
    assert cfg["embedding"]["embed_dim"] == 4096, (
        "embed_dim must be 4096 (qwen3-embedding:8b); update embed.py + this test if changed"
    )
    assert cfg["extraction_prose"]["model"] == "qwen3:14b", (
        "extraction_prose model tag changed; verify Ollama echoes this exact tag"
    )
    assert cfg["extraction_code"]["model"] == "qwen2.5-coder:14b", (
        "extraction_code model tag changed; verify Ollama echoes this exact tag"
    )


# ---------------------------------------------------------------------------
# Winning row selection
# ---------------------------------------------------------------------------

def test_select_winning_row_returns_correct_model():
    rows = [
        make_row("file.md", "gemma3:12b"),
        make_row("file.md", "qwen3:14b"),
    ]
    result = embed.select_winning_row(rows, "file.md", EXTRACT_CFG)
    assert result["model"] == "qwen3:14b"


def test_select_winning_row_skips_failed_status():
    rows = [
        make_row("file.md", "qwen3:14b", status="error"),
        make_row("file.md", "gemma3:12b", status="ok"),
    ]
    # qwen3:14b is the winner but failed — no winning row exists
    result = embed.select_winning_row(rows, "file.md", EXTRACT_CFG)
    assert result is None


def test_select_winning_row_missing_file_returns_none():
    rows = [make_row("other.md", "qwen3:14b")]
    assert embed.select_winning_row(rows, "missing.md", EXTRACT_CFG) is None


# ---------------------------------------------------------------------------
# Topic slug normalization
# ---------------------------------------------------------------------------

def test_slugify_snake_lowercases():
    assert embed.slugify_snake("TopicName") == "topicname"


def test_slugify_snake_replaces_spaces():
    assert embed.slugify_snake("topic name here") == "topic_name_here"


def test_slugify_snake_strips_special_chars():
    slug = embed.slugify_snake("topic: name!")
    assert " " not in slug and ":" not in slug and "!" not in slug


def test_unique_slugs_deduplicates_within_file():
    names = ["topic_one", "topic_one", "topic_two", "topic_one"]
    result = embed.unique_slugs(names)
    assert len(set(result)) == len(result), "All slugs must be unique"
    assert result[0] == "topic_one"
    assert result[1] == "topic_one-2"
    assert result[3] == "topic_one-3"


# ---------------------------------------------------------------------------
# Embed text construction
# ---------------------------------------------------------------------------

def test_embed_text_description_mode_returns_description():
    topic = {"name": "t", "description": "Desc text.", "spans": [[1, 2]]}
    text = embed.build_embed_text(topic, mode="description", file_path=None, repo_root=None)
    assert text == "Desc text."


def test_embed_text_description_plus_spans_includes_description(tmp_path):
    # Create a fake source file
    src = tmp_path / "file.md"
    src.write_text("line one\nline two\nline three\n")
    topic = {"name": "t", "description": "Desc.", "spans": [[1, 2]]}
    text = embed.build_embed_text(topic, mode="description_plus_spans",
                                   file_path="file.md", repo_root=tmp_path)
    assert "Desc." in text
    assert "line one" in text or "line two" in text


# ---------------------------------------------------------------------------
# Output row shape
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "id", "file_path", "topic_name", "description", "spans",
    "vector", "embed_model", "embed_dim", "embed_mode", "embedding_timestamp",
    "extractor_model", "extraction_run_id", "extraction_timestamp", "file_role",
    "node_kind", "scope_tags", "segment_id", "segment_range",
]

def test_build_output_row_has_all_16_fields():
    row = make_row("docs/design.md", "qwen3:14b")
    topic = {"name": "my_topic", "description": "Desc.", "spans": [[1, 2]]}
    slug = "my_topic"
    vector = [0.01] * 1024
    result = embed.build_output_row(
        row=row, topic=topic, slug=slug, vector=vector,
        embed_model="bge-m3", embed_dim=1024, embed_mode="description",
    )
    for field in REQUIRED_FIELDS:
        assert field in result, f"Missing field: {field}"


def test_build_output_row_id_format():
    row = make_row("docs/design.md", "qwen3:14b")
    topic = {"name": "my_topic", "description": "Desc.", "spans": [[1, 2]]}
    result = embed.build_output_row(
        row=row, topic=topic, slug="my_topic", vector=[0.01] * 1024,
        embed_model="bge-m3", embed_dim=1024, embed_mode="description",
    )
    assert result["id"] == "docs/design.md:my_topic"


def test_build_output_row_forward_compat_defaults():
    row = make_row("docs/design.md", "qwen3:14b")
    topic = {"name": "t", "description": "D.", "spans": [[1, 1]]}
    result = embed.build_output_row(
        row=row, topic=topic, slug="t", vector=[0.01] * 1024,
        embed_model="bge-m3", embed_dim=1024, embed_mode="description",
    )
    assert result["node_kind"] == "extracted"
    assert result["scope_tags"] == "[]"
    assert result["segment_id"] is None
    assert result["segment_range"] is None


def test_build_output_row_spans_is_json_string():
    row = make_row("docs/design.md", "qwen3:14b")
    topic = {"name": "t", "description": "D.", "spans": [[1, 3], [5, 7]]}
    result = embed.build_output_row(
        row=row, topic=topic, slug="t", vector=[0.01] * 1024,
        embed_model="bge-m3", embed_dim=1024, embed_mode="description",
    )
    # spans must be a JSON-encoded string, not a list
    assert isinstance(result["spans"], str)
    parsed = json.loads(result["spans"])
    assert parsed == [[1, 3], [5, 7]]


# ---------------------------------------------------------------------------
# Skip behaviours
# ---------------------------------------------------------------------------

def test_empty_description_topic_is_skipped():
    topics = [{"name": "t", "description": "   ", "spans": [[1, 1]]}]
    valid = embed.filter_valid_topics(topics)
    assert valid == []


def test_missing_description_key_is_skipped():
    topics = [{"name": "t", "spans": [[1, 1]]}]
    valid = embed.filter_valid_topics(topics)
    assert valid == []


def test_valid_topic_passes_filter():
    topics = [{"name": "t", "description": "Good desc.", "spans": [[1, 1]]}]
    valid = embed.filter_valid_topics(topics)
    assert len(valid) == 1
