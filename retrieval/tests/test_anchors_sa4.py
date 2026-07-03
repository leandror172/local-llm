"""Tests for SA-4 slice: staleness_warnings, nearmiss_report, rebuild_index,
and the build_anchor_rows contract change (descriptions param).

Build-anchor-rows contract change
----------------------------------
build_anchor_rows gains an optional ``descriptions: dict[str, str] | None``
parameter. When provided, descriptions[anchor.key] is used for the ``description``
field instead of calling describe_mechanical_key(anchor). SA-3 tests remain green
because None falls back to the prior behavior.

staleness_warnings
-------------------
Pure function: one warning string per topic whose source file mtime is newer than
its extraction_timestamp. Topics with no extraction_timestamp (empty string,
anchors) are skipped. Topics whose source file doesn't exist are skipped (warn-safe).

nearmiss_report
----------------
Accepts (anchors, topic_rows, anchor_vectors) — the anchor_vectors are passed
explicitly by rebuild_index so the function doesn't re-embed. The pinned public
signature nearmiss_report(anchors, topic_rows) is flagged (raises NotImplementedError)
because it cannot compute cosines without vectors; rebuild_index calls the private
_nearmiss_with_vectors helper directly.

rebuild_index
--------------
Orchestration: ingest_anchors -> read topics -> descriptions=describe(a,method) ->
embed anchor descriptions -> match_anchors -> apply_aliases -> build_anchor_rows ->
write via store path (backup + overwrite) -> return RebuildReport.
Key invariants:
- embedder called only with anchor descriptions, never with topic text
- topic vectors reused from index (not re-embedded)
- RebuildReport counts match row and match counts
- staleness and nearmiss piped through to report
"""

import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import lancedb
import pyarrow as pa
import pytest

from retrieval.anchors import (
    COSINE_THRESHOLD,
    DEFAULT_METHOD,
    NEARMISS_LOW,
    Anchor,
    RebuildReport,
    apply_aliases,
    build_anchor_rows,
    describe,
    describe_key_only,
    describe_mechanical_key,
    nearmiss_report,
    rebuild_index,
    staleness_warnings,
)
from retrieval.store import build_schema


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

BARE_KEY_A = "concept-latent-topic-graph"
ANCHOR_A = Anchor(
    key=f"ref:{BARE_KEY_A}",
    bare_key=BARE_KEY_A,
    file_path="docs/research/latent-topic-graph.md",
    start_line=42,
    heading="Latent Topic Graph",
    first_prose="The core concept behind LTG retrieval.",
)

BARE_KEY_B = "plan-latent-topic-graph"
ANCHOR_B = Anchor(
    key=f"ref:{BARE_KEY_B}",
    bare_key=BARE_KEY_B,
    file_path="docs/plans/ltg.md",
    start_line=10,
    heading="LTG Plan",
    first_prose="**Status:** Ready for execution",
)

# Small fake dimension — tests that need Arrow table use this; rebuild_index
# tests mock the store-write path to avoid the 4096 vs 4 mismatch.
FAKE_DIM = 4

# Unit vectors for cosine math (already normalized, so cosine == dot product)
VEC_HIGH = [1.0, 0.0, 0.0, 0.0]   # cosine 1.0 against itself
VEC_MED  = [0.0, 1.0, 0.0, 0.0]   # cosine 0.0 against VEC_HIGH
VEC_NEAR = [0.9, 0.436, 0.0, 0.0] # cosine ~0.9 against VEC_HIGH (above threshold)
VEC_MISS = [0.82, 0.572, 0.0, 0.0]  # cosine ~0.82 (in nearmiss band)

# Topic rows as bare dicts (only fields needed by each function)
def _make_topic_row(topic_id: str, file_path: str, vector: list,
                    extraction_ts: str = "2026-01-01T00:00:00+00:00") -> dict:
    """Minimal full-schema topic row for rebuild tests."""
    return {
        "id": topic_id,
        "file_path": file_path,
        "topic_name": topic_id.replace("-", "_"),
        "description": f"Description of {topic_id}",
        "spans": "[[1,5]]",
        "vector": vector,
        "embed_model": "qwen3-embedding:8b",
        "embed_dim": 4096,
        "embed_mode": "description",
        "embedding_timestamp": "2026-01-01T00:00:00+00:00",
        "extractor_model": "qwen3:14b",
        "extraction_run_id": "run-abc",
        "extraction_timestamp": extraction_ts,
        "file_role": "long_research_doc",
        "node_kind": "extracted",
        "scope_tags": "[]",
        "segment_id": None,
        "segment_range": None,
    }


# ---------------------------------------------------------------------------
# build_anchor_rows — contract change: descriptions param
# ---------------------------------------------------------------------------

class TestBuildAnchorRowsDescriptionsParam:
    """Tests for the new optional descriptions parameter."""

    def test_descriptions_none_falls_back_to_describe_mechanical_key(self):
        """None (default) must produce the same description as SA-3 — backward compat."""
        rows = build_anchor_rows([ANCHOR_A], {ANCHOR_A.key: VEC_HIGH}, descriptions=None)
        assert rows[0]["description"] == describe_mechanical_key(ANCHOR_A)

    def test_descriptions_provided_overrides_describe_mechanical_key(self):
        """Non-default method description must appear in row — the key contract change."""
        key_only_desc = describe_key_only(ANCHOR_A)
        descriptions = {ANCHOR_A.key: key_only_desc}
        rows = build_anchor_rows([ANCHOR_A], {ANCHOR_A.key: VEC_HIGH}, descriptions=descriptions)
        assert rows[0]["description"] == key_only_desc
        # Verify it differs from mechanical+key so the test is non-trivial
        assert rows[0]["description"] != describe_mechanical_key(ANCHOR_A)

    def test_descriptions_stored_description_matches_embedded_text(self):
        """Proves the embedded text and stored description are the same when descriptions is passed.

        This is the one test mandated by the contract change: pass descriptions built
        from key_only, assert row['description'] == what was embedded.
        """
        embedded_text = describe(ANCHOR_B, "key_only")
        descriptions = {ANCHOR_B.key: embedded_text}
        rows = build_anchor_rows([ANCHOR_B], {ANCHOR_B.key: VEC_MED}, descriptions=descriptions)
        assert rows[0]["description"] == embedded_text

    def test_descriptions_dict_used_per_anchor_key(self):
        """With two anchors, each gets its own description from the dict."""
        descs = {
            ANCHOR_A.key: "custom-a",
            ANCHOR_B.key: "custom-b",
        }
        rows = build_anchor_rows(
            [ANCHOR_A, ANCHOR_B],
            {ANCHOR_A.key: VEC_HIGH, ANCHOR_B.key: VEC_MED},
            descriptions=descs,
        )
        by_id = {r["id"]: r for r in rows}
        assert by_id[ANCHOR_A.key]["description"] == "custom-a"
        assert by_id[ANCHOR_B.key]["description"] == "custom-b"


# ---------------------------------------------------------------------------
# staleness_warnings
# ---------------------------------------------------------------------------

class TestStalenessWarnings:
    """staleness_warnings returns one string per topic whose source file
    mtime is newer than extraction_timestamp. Skips empty-ts and missing files."""

    def test_no_warnings_when_file_older_than_extraction(self, tmp_path):
        """File mtime before extraction_timestamp → no warning."""
        src = tmp_path / "docs" / "something.md"
        src.parent.mkdir()
        src.write_text("content")
        # Set mtime to 2025 (before extraction 2026)
        old_time = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()
        os.utime(src, (old_time, old_time))

        row = _make_topic_row("t1", "docs/something.md", VEC_HIGH,
                               extraction_ts="2026-01-01T00:00:00+00:00")
        warnings = staleness_warnings([row], tmp_path)
        assert warnings == []

    def test_warning_when_file_newer_than_extraction(self, tmp_path):
        """File mtime after extraction_timestamp → one warning string."""
        src = tmp_path / "docs" / "something.md"
        src.parent.mkdir()
        src.write_text("updated content")
        # mtime = now (definitely newer than 2020 extraction)
        row = _make_topic_row("t1", "docs/something.md", VEC_HIGH,
                               extraction_ts="2020-01-01T00:00:00+00:00")
        warnings = staleness_warnings([row], tmp_path)
        assert len(warnings) == 1
        assert "something.md" in warnings[0]

    def test_warning_message_contains_topic_id(self, tmp_path):
        src = tmp_path / "docs" / "something.md"
        src.parent.mkdir()
        src.write_text("x")
        row = _make_topic_row("my-topic-id", "docs/something.md", VEC_HIGH,
                               extraction_ts="2020-01-01T00:00:00+00:00")
        warnings = staleness_warnings([row], tmp_path)
        assert any("my-topic-id" in w for w in warnings)

    def test_skips_topic_with_empty_extraction_timestamp(self, tmp_path):
        """Anchor rows have extraction_timestamp=''; must not produce warnings."""
        row = _make_topic_row("anchor-row", "docs/something.md", VEC_HIGH,
                               extraction_ts="")
        warnings = staleness_warnings([row], tmp_path)
        assert warnings == []

    def test_skips_topic_when_source_file_missing(self, tmp_path):
        """Missing source file → skip (don't crash)."""
        row = _make_topic_row("t-missing", "does/not/exist.md", VEC_HIGH,
                               extraction_ts="2020-01-01T00:00:00+00:00")
        warnings = staleness_warnings([row], tmp_path)
        assert warnings == []

    def test_multiple_topics_only_stale_ones_warned(self, tmp_path):
        src_old = tmp_path / "old.md"
        src_new = tmp_path / "new.md"
        src_old.write_text("unchanged")
        src_new.write_text("changed")
        # Set old file to 2025, keep new file at current mtime (now)
        os.utime(src_old, (datetime(2025, 6, 1).timestamp(),) * 2)

        row_fresh = _make_topic_row("t-fresh", "old.md", VEC_HIGH,
                                    extraction_ts="2026-01-01T00:00:00+00:00")
        row_stale = _make_topic_row("t-stale", "new.md", VEC_HIGH,
                                    extraction_ts="2020-01-01T00:00:00+00:00")
        warnings = staleness_warnings([row_fresh, row_stale], tmp_path)
        assert len(warnings) == 1
        assert "new.md" in warnings[0]


# ---------------------------------------------------------------------------
# nearmiss_report (private helper + public pinned sig)
# ---------------------------------------------------------------------------

class TestNearmissWithVectors:
    """_nearmiss_with_vectors(anchors, topic_rows, anchor_vectors) — private helper
    that rebuild_index calls once vectors are in hand."""

    def _call(self, anchors, topic_rows, anchor_vectors):
        from retrieval.anchors import _nearmiss_with_vectors
        return _nearmiss_with_vectors(anchors, topic_rows, anchor_vectors)

    def test_anchor_above_threshold_not_in_report(self):
        """Top match ≥ COSINE_THRESHOLD → not a near-miss."""
        topic = _make_topic_row("t1", "f.md", VEC_HIGH)
        # anchor vector matches topic at cosine 1.0 (above 0.85)
        entries = self._call([ANCHOR_A], [topic], {ANCHOR_A.key: VEC_HIGH})
        assert entries == []

    def test_anchor_in_nearmiss_band_appears(self):
        """Top match in [NEARMISS_LOW, COSINE_THRESHOLD) → appears in report."""
        # VEC_MISS · VEC_HIGH = 0.82 which is in [0.80, 0.85)
        topic = _make_topic_row("t1", "f.md", VEC_HIGH)
        entries = self._call([ANCHOR_A], [topic], {ANCHOR_A.key: VEC_MISS})
        assert len(entries) == 1
        entry = entries[0]
        assert entry["anchor_key"] == ANCHOR_A.key
        assert entry["top_topic"] == "t1"
        assert NEARMISS_LOW <= entry["top_cosine"] < COSINE_THRESHOLD

    def test_anchor_below_nearmiss_low_not_in_report(self):
        """Top match < NEARMISS_LOW → pure orphan, not reported."""
        # VEC_MED · VEC_HIGH = 0.0 — completely orthogonal
        topic = _make_topic_row("t1", "f.md", VEC_HIGH)
        entries = self._call([ANCHOR_A], [topic], {ANCHOR_A.key: VEC_MED})
        assert entries == []

    def test_report_uses_top_match_only(self):
        """Entry top_cosine is the max cosine across all topics for that anchor."""
        topic_low  = _make_topic_row("t-low",  "a.md", VEC_MED)
        topic_miss = _make_topic_row("t-miss", "b.md", VEC_HIGH)
        # ANCHOR_A key VEC_MISS: cosine with VEC_HIGH=0.82, with VEC_MED=0.0
        entries = self._call([ANCHOR_A], [topic_low, topic_miss], {ANCHOR_A.key: VEC_MISS})
        assert len(entries) == 1
        assert entries[0]["top_topic"] == "t-miss"
        assert abs(entries[0]["top_cosine"] - 0.82) < 0.01

    def test_multiple_anchors_each_evaluated_independently(self):
        topic = _make_topic_row("t1", "f.md", VEC_HIGH)
        # ANCHOR_A → nearmiss (VEC_MISS cosine 0.82), ANCHOR_B → above threshold (cosine 1.0)
        entries = self._call(
            [ANCHOR_A, ANCHOR_B],
            [topic],
            {ANCHOR_A.key: VEC_MISS, ANCHOR_B.key: VEC_HIGH},
        )
        keys = {e["anchor_key"] for e in entries}
        assert ANCHOR_A.key in keys
        assert ANCHOR_B.key not in keys


class TestNearmissReportPinnedSignature:
    """The public pinned signature nearmiss_report(anchors, topic_rows) must raise
    NotImplementedError to signal that vectors are required (SA-4 design flag)."""

    def test_pinned_signature_raises_not_implemented(self):
        topic = _make_topic_row("t1", "f.md", VEC_HIGH)
        with pytest.raises(NotImplementedError):
            nearmiss_report([ANCHOR_A], [topic])


# ---------------------------------------------------------------------------
# rebuild_index — orchestration (mocked embedder + tmp LanceDB)
# ---------------------------------------------------------------------------

def _build_tmp_index(tmp_path: Path, topic_rows: list[dict]) -> Path:
    """Write topic rows to a temporary LanceDB index and return its path.
    Uses schema from store.build_schema with 4096 embed_dim (anchor rows use 4096).
    We pad fake 4-dim vectors to 4096 with zeros for this helper.
    """
    index_path = tmp_path / "index"
    schema = build_schema(4096)
    # Pad all row vectors to 4096 dims
    padded_rows = []
    for row in topic_rows:
        r = dict(row)
        r["vector"] = (r["vector"] + [0.0] * 4096)[:4096]
        r.setdefault("source_class", "topic_extracted")
        r.setdefault("confidence", 0.7)
        r.setdefault("anchor_key", None)
        r.setdefault("alias_of", None)
        padded_rows.append(r)

    vectors = pa.array(
        [pa.array(r["vector"], type=pa.float32()) for r in padded_rows],
        type=pa.list_(pa.float32(), 4096),
    )
    scalar_fields = [f.name for f in schema if f.name != "vector"]
    col_data = {name: [r.get(name) for r in padded_rows] for name in scalar_fields}
    col_data["vector"] = vectors
    arrow_table = pa.table(col_data, schema=schema)

    db = lancedb.connect(str(index_path))
    db.create_table("topics", data=arrow_table, mode="overwrite")
    return index_path


class TestRebuildIndex:
    """rebuild_index orchestration tests — embedder and store.write mocked."""

    def _fake_embed(self, descriptions: list[str]) -> list[list[float]]:
        """Returns a 4096-dim unit vector for each description (1.0 in first slot)."""
        return [[1.0] + [0.0] * 4095 for _ in descriptions]

    def test_rebuild_returns_rebuild_report(self, tmp_path):
        """rebuild_index must return a RebuildReport instance."""
        topic_row = _make_topic_row("t1", "docs/something.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}
            mock_write.return_value = None

            report = rebuild_index(tmp_path, index_path)

        assert isinstance(report, RebuildReport)

    def test_rebuild_report_anchors_ingested_count(self, tmp_path):
        topic_row = _make_topic_row("t1", "docs/something.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write:
            mock_ingest.return_value = [ANCHOR_A, ANCHOR_B]
            mock_embed.return_value = {
                ANCHOR_A.key: [1.0] + [0.0] * 4095,
                ANCHOR_B.key: [0.0, 1.0] + [0.0] * 4094,
            }
            mock_write.return_value = None

            report = rebuild_index(tmp_path, index_path)

        assert report.anchors_ingested == 2

    def test_rebuild_report_topics_read_count(self, tmp_path):
        rows = [
            _make_topic_row("t1", "a.md", [1.0] + [0.0] * 3),
            _make_topic_row("t2", "b.md", [0.0, 1.0] + [0.0] * 2),
        ]
        index_path = _build_tmp_index(tmp_path, rows)

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}
            mock_write.return_value = None

            report = rebuild_index(tmp_path, index_path)

        assert report.topics_read == 2

    def test_embed_called_only_with_anchor_descriptions_not_topic_text(self, tmp_path):
        """Core invariant: embedder sees anchor descriptions, never topic text."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])
        expected_desc = describe_mechanical_key(ANCHOR_A)

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}
            mock_write.return_value = None

            rebuild_index(tmp_path, index_path)

        # _embed_anchor_descriptions must be called with descriptions dict
        mock_embed.assert_called_once()
        passed_descs = mock_embed.call_args[0][0]
        # The dict value for ANCHOR_A.key must be the expected description
        assert ANCHOR_A.key in passed_descs
        assert passed_descs[ANCHOR_A.key] == expected_desc
        # Topic description ("Description of t1") must NOT appear
        topic_desc = topic_row["description"]
        assert topic_desc not in passed_descs.values()

    def test_embed_called_with_method_key_only(self, tmp_path):
        """When method='key_only', embed receives key_only descriptions."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])
        expected_desc = describe_key_only(ANCHOR_A)

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}
            mock_write.return_value = None

            rebuild_index(tmp_path, index_path, method="key_only")

        passed_descs = mock_embed.call_args[0][0]
        assert passed_descs[ANCHOR_A.key] == expected_desc

    def test_topic_vectors_read_from_index_not_re_embedded(self, tmp_path):
        """Topic rows must be read with their stored vectors — no re-embedding of topics."""
        topic_row = _make_topic_row("t1", "docs/x.md", [0.5] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        written_rows = []

        def capture_write(all_rows, index_path, backup_path):
            written_rows.extend(all_rows)

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index", side_effect=capture_write):
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}

            rebuild_index(tmp_path, index_path)

        # Find the topic row in written rows (node_kind != "anchor")
        topic_written = [r for r in written_rows if r.get("node_kind") != "anchor"]
        assert len(topic_written) == 1
        # Vector must start with 0.5 (original stored value), padded to 4096
        assert topic_written[0]["vector"][0] == pytest.approx(0.5)

    def test_report_method_matches_argument(self, tmp_path):
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index"):
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}

            report = rebuild_index(tmp_path, index_path, method="key_only")

        assert report.method == "key_only"

    def test_report_aliases_created_counts_matched_topics(self, tmp_path):
        """aliases_created counts topics that gained alias_of (matched ≥1 anchor)."""
        # Two topics: one will match the anchor, one won't
        row_match  = _make_topic_row("t-match",  "a.md", [1.0] + [0.0] * 3)
        row_orphan = _make_topic_row("t-orphan", "b.md", [0.0, 1.0] + [0.0] * 2)
        index_path = _build_tmp_index(tmp_path, [row_match, row_orphan])

        # Anchor vector = [1,0,...] → cosine 1.0 with row_match, 0.0 with row_orphan
        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index"):
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}

            report = rebuild_index(tmp_path, index_path)

        assert report.aliases_created == 1

    def test_staleness_piped_to_report(self, tmp_path):
        """staleness_warnings result appears in report.staleness."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index"), \
             patch("retrieval.anchors.staleness_warnings") as mock_stale:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}
            mock_stale.return_value = ["STALE: t1 docs/x.md"]

            report = rebuild_index(tmp_path, index_path)

        assert "STALE: t1 docs/x.md" in report.staleness

    def test_nearmiss_piped_to_report(self, tmp_path):
        """nearmiss diagnostic result appears in report.nearmiss."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])
        fake_nearmiss = [{"anchor_key": "ref:x", "top_topic": "t1", "top_cosine": 0.82}]

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index"), \
             patch("retrieval.anchors._nearmiss_with_vectors") as mock_nm:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}
            mock_nm.return_value = fake_nearmiss

            report = rebuild_index(tmp_path, index_path)

        assert report.nearmiss == fake_nearmiss


# ---------------------------------------------------------------------------
# T-71 — backup-chain hardening: stage-suffixed default slot + backup=False routing
# ---------------------------------------------------------------------------

class TestRebuildIndexBackupRouting:
    def test_default_backup_uses_stage_suffixed_slot(self, tmp_path):
        """backup=True (default) must write to {index}.bak-anchors, not the
        shared {index}.bak slot (T-71)."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}

            rebuild_index(tmp_path, index_path)

        _, _, backup_path = mock_write.call_args[0]
        assert backup_path.name == "index.bak-anchors"

    def test_backup_false_skips_backup_entirely(self, tmp_path):
        """backup=False (run-rebuild-all.sh's --no-backup) must route to
        _write_index_no_backup, never touching any .bak* slot."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        with patch("retrieval.anchors.ingest_anchors") as mock_ingest, \
             patch("retrieval.anchors._embed_anchor_descriptions") as mock_embed, \
             patch("retrieval.anchors._write_index") as mock_write, \
             patch("retrieval.anchors._write_index_no_backup") as mock_write_nb:
            mock_ingest.return_value = [ANCHOR_A]
            mock_embed.return_value = {ANCHOR_A.key: [1.0] + [0.0] * 4095}

            rebuild_index(tmp_path, index_path, backup=False)

        mock_write.assert_not_called()
        mock_write_nb.assert_called_once()

    def test_write_index_no_backup_does_not_create_bak(self, tmp_path):
        """_write_index_no_backup must overwrite topics without creating any
        backup directory."""
        topic_row = _make_topic_row("t1", "docs/x.md", [1.0] + [0.0] * 3)
        index_path = _build_tmp_index(tmp_path, [topic_row])

        from retrieval.anchors import _write_index_no_backup
        row = dict(topic_row, source_class="topic_extracted", confidence=0.7,
                   anchor_key=None, alias_of=None)
        row["vector"] = (row["vector"] + [0.0] * 4096)[:4096]
        _write_index_no_backup([row], index_path)

        assert not (index_path.parent / "index.bak").exists()
        assert not (index_path.parent / "index.bak-anchors").exists()
