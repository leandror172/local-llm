"""Tests for SA-3 slice: build_anchor_rows and apply_aliases.

Contract notes
--------------
build_anchor_rows:
  - accepts (anchors: list[Anchor], vectors: dict[str, list[float]], descriptions: dict[str,str] | None = None)
  - returns one dict per anchor with ALL 22 schema fields explicitly present
  - when descriptions is None (default): description = describe_mechanical_key(anchor) — backward compat
  - when descriptions provided: uses descriptions[anchor.key] — enables rebuild_index to pass pre-computed
    descriptions that match the embedded text regardless of method (SA-4 contract change)

apply_aliases:
  - accepts (topic_rows: list[dict], matches: dict[str, list[str]])
  - returns NEW dicts (no mutation of originals) with Phase-3 fields backfilled on ALL rows
  - matched rows get alias_of = json.dumps(sorted list of anchor keys)
  - unmatched rows get alias_of = None
  - confidence stays 0.7 on ALL topic rows (D1: aliasing does NOT change confidence)
  - anchor_key = None on all topic rows

Cross-check
-----------
The expected field set is derived from store.build_schema at import time. Schema drift
(adding/removing a field from build_schema without updating build_anchor_rows) will
break test_build_anchor_rows_field_set, which is the intended coupling.
"""

import json
from datetime import datetime, timezone

import pytest

from retrieval.anchors import (
    ANCHOR_CONFIDENCE,
    ANCHOR_SOURCE_CLASS,
    TOPIC_CONFIDENCE,
    TOPIC_SOURCE_CLASS,
    Anchor,
    apply_aliases,
    build_anchor_rows,
    describe_mechanical_key,
)
from retrieval.store import build_schema

# ---------------------------------------------------------------------------
# Derived constants
# ---------------------------------------------------------------------------

# Field names from the live schema. 'source_group' (T-65) is excluded: it is
# DERIVED at store-time in rows_to_arrow_table from file_path, not supplied by
# the anchor-row writer, so it is intentionally absent from writer row dicts.
STORE_DERIVED_FIELDS: frozenset[str] = frozenset({"source_group"})
SCHEMA_FIELD_NAMES: frozenset[str] = frozenset(
    f.name for f in build_schema(4096)
) - STORE_DERIVED_FIELDS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BARE_KEY = "concept-latent-topic-graph"
ANCHOR_KEY = f"ref:{BARE_KEY}"

ANCHOR = Anchor(
    key=ANCHOR_KEY,
    bare_key=BARE_KEY,
    file_path="docs/research/latent-topic-graph.md",
    start_line=42,
    heading="Latent Topic Graph",
    first_prose="The core concept behind LTG retrieval.",
)

ANCHOR2 = Anchor(
    key="ref:ltg-phase2-schema",
    bare_key="ltg-phase2-schema",
    file_path="docs/plans/ltg-phase2.md",
    start_line=10,
    heading="Phase 2 Schema",
    first_prose="16-field LanceDB row definition.",
)

FAKE_DIM = 4
VECTOR_A = [0.5, 0.5, 0.5, 0.5]
VECTOR_B = [0.1, 0.9, 0.0, 0.0]

VECTORS = {
    ANCHOR_KEY: VECTOR_A,
    "ref:ltg-phase2-schema": VECTOR_B,
}

# ---------------------------------------------------------------------------
# build_anchor_rows — field presence
# ---------------------------------------------------------------------------


def test_build_anchor_rows_returns_one_dict_per_anchor():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert len(rows) == 1


def test_build_anchor_rows_field_set_matches_schema():
    """All 22 schema fields must be present — schema drift will break this test."""
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    row_keys = frozenset(rows[0].keys())
    assert row_keys == SCHEMA_FIELD_NAMES, (
        f"Row fields differ from schema.\n"
        f"  Extra in row: {row_keys - SCHEMA_FIELD_NAMES}\n"
        f"  Missing from row: {SCHEMA_FIELD_NAMES - row_keys}"
    )


def test_build_anchor_rows_id_is_anchor_key():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["id"] == ANCHOR_KEY


def test_build_anchor_rows_file_path():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["file_path"] == ANCHOR.file_path


def test_build_anchor_rows_topic_name_snake_case():
    """Hyphens in bare_key must become underscores."""
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["topic_name"] == "concept_latent_topic_graph"


def test_build_anchor_rows_topic_name_no_hyphens():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert "-" not in rows[0]["topic_name"]


def test_build_anchor_rows_description_matches_describe_mechanical_key():
    """description must equal what was embedded — describe_mechanical_key for DEFAULT_METHOD."""
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["description"] == describe_mechanical_key(ANCHOR)


def test_build_anchor_rows_spans_is_json_single_line_point():
    """spans = '[[start_line, start_line]]' — single-line point, JSON string."""
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    spans = rows[0]["spans"]
    parsed = json.loads(spans)
    assert parsed == [[ANCHOR.start_line, ANCHOR.start_line]]


def test_build_anchor_rows_vector_matches_input():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["vector"] == VECTOR_A


def test_build_anchor_rows_embed_model():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["embed_model"] == "qwen3-embedding:8b"


def test_build_anchor_rows_embed_dim():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["embed_dim"] == 4096


def test_build_anchor_rows_embed_mode():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["embed_mode"] == "description"


def test_build_anchor_rows_embedding_timestamp_is_utc_iso8601():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    ts = rows[0]["embedding_timestamp"]
    # Must parse as ISO-8601 and have timezone info
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None


def test_build_anchor_rows_provenance_fields_empty_string():
    """Non-nullable extraction provenance fields must be '' (not None)."""
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    for field in ("extractor_model", "extraction_run_id", "extraction_timestamp"):
        assert rows[0][field] == "", f"{field} should be empty string, got {rows[0][field]!r}"


def test_build_anchor_rows_file_role():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["file_role"] == "anchor"


def test_build_anchor_rows_node_kind():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["node_kind"] == "anchor"


def test_build_anchor_rows_scope_tags_empty_json_array():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["scope_tags"] == "[]"


def test_build_anchor_rows_nullable_fields_are_none():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["segment_id"] is None
    assert rows[0]["segment_range"] is None
    assert rows[0]["alias_of"] is None


def test_build_anchor_rows_source_class():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["source_class"] == ANCHOR_SOURCE_CLASS


def test_build_anchor_rows_confidence():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["confidence"] == ANCHOR_CONFIDENCE


def test_build_anchor_rows_anchor_key():
    rows = build_anchor_rows([ANCHOR], {ANCHOR_KEY: VECTOR_A})
    assert rows[0]["anchor_key"] == ANCHOR_KEY


def test_build_anchor_rows_two_anchors():
    rows = build_anchor_rows([ANCHOR, ANCHOR2], VECTORS)
    assert len(rows) == 2
    ids = {r["id"] for r in rows}
    assert ids == {ANCHOR_KEY, "ref:ltg-phase2-schema"}


# ---------------------------------------------------------------------------
# apply_aliases — Phase-3 field backfill
# ---------------------------------------------------------------------------

def _make_topic_row(topic_id: str) -> dict:
    """Minimal topic row dict (only fields relevant to apply_aliases)."""
    return {
        "id": topic_id,
        "file_path": "docs/something.md",
        "topic_name": "some_topic",
        "description": "A description.",
        "spans": "[[1,5]]",
        "vector": [0.1, 0.2, 0.3, 0.4],
        "embed_model": "qwen3-embedding:8b",
        "embed_dim": 4096,
        "embed_mode": "description",
        "embedding_timestamp": "2026-01-01T00:00:00+00:00",
        "extractor_model": "qwen3:14b",
        "extraction_run_id": "abc123",
        "extraction_timestamp": "2026-01-01T00:00:00+00:00",
        "file_role": "long_research_doc",
        "node_kind": "extracted",
        "scope_tags": "[]",
        "segment_id": None,
        "segment_range": None,
        # Phase-3 fields absent on pre-Phase-3 topic rows (apply_aliases must backfill them)
    }


def test_apply_aliases_all_rows_get_source_class():
    rows = [_make_topic_row("t1"), _make_topic_row("t2")]
    result = apply_aliases(rows, matches={"t1": [ANCHOR_KEY]})
    for r in result:
        assert r["source_class"] == TOPIC_SOURCE_CLASS


def test_apply_aliases_all_rows_get_confidence():
    rows = [_make_topic_row("t1"), _make_topic_row("t2")]
    result = apply_aliases(rows, matches={"t1": [ANCHOR_KEY]})
    for r in result:
        assert r["confidence"] == TOPIC_CONFIDENCE


def test_apply_aliases_all_rows_get_anchor_key_none():
    rows = [_make_topic_row("t1"), _make_topic_row("t2")]
    result = apply_aliases(rows, matches={"t1": [ANCHOR_KEY]})
    for r in result:
        assert r["anchor_key"] is None


def test_apply_aliases_matched_row_gets_alias_of_json_list():
    rows = [_make_topic_row("t1")]
    result = apply_aliases(rows, matches={"t1": [ANCHOR_KEY]})
    alias_of = result[0]["alias_of"]
    assert alias_of is not None
    parsed = json.loads(alias_of)
    assert isinstance(parsed, list)
    assert ANCHOR_KEY in parsed


def test_apply_aliases_matched_row_alias_of_contains_all_matched_keys():
    rows = [_make_topic_row("t1")]
    two_keys = [ANCHOR_KEY, "ref:ltg-phase2-schema"]
    result = apply_aliases(rows, matches={"t1": two_keys})
    parsed = json.loads(result[0]["alias_of"])
    assert set(parsed) == set(two_keys)


def test_apply_aliases_unmatched_row_alias_of_is_none():
    rows = [_make_topic_row("t1"), _make_topic_row("t2")]
    result = apply_aliases(rows, matches={"t1": [ANCHOR_KEY]})
    unmatched = next(r for r in result if r["id"] == "t2")
    assert unmatched["alias_of"] is None


def test_apply_aliases_confidence_unchanged_on_aliased_row():
    """D1: aliasing does NOT change confidence. Aliased topics stay at 0.7."""
    rows = [_make_topic_row("t1")]
    result = apply_aliases(rows, matches={"t1": [ANCHOR_KEY]})
    assert result[0]["confidence"] == TOPIC_CONFIDENCE


def test_apply_aliases_empty_matches_all_unmatched():
    rows = [_make_topic_row("t1"), _make_topic_row("t2")]
    result = apply_aliases(rows, matches={})
    for r in result:
        assert r["alias_of"] is None


def test_apply_aliases_does_not_mutate_input_rows():
    """apply_aliases must return NEW dicts — original row dicts must not be changed."""
    original_row = _make_topic_row("t1")
    original_snapshot = dict(original_row)
    apply_aliases([original_row], matches={"t1": [ANCHOR_KEY]})
    assert original_row == original_snapshot, "Input dict was mutated"


def test_apply_aliases_preserves_existing_fields():
    """Non-Phase-3 fields on topic rows must be preserved unchanged."""
    rows = [_make_topic_row("t1")]
    result = apply_aliases(rows, matches={})
    assert result[0]["description"] == rows[0]["description"]
    assert result[0]["embed_model"] == rows[0]["embed_model"]
    assert result[0]["topic_name"] == rows[0]["topic_name"]
