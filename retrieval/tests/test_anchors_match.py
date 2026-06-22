"""Tests for match_anchors (SA-2 slice).

Vector math convention
----------------------
All vectors here are 2-D unit vectors for readability. Production vectors are
4096-D but match_anchors is dimension-agnostic (pure dot-product). Cosines are
computed by hand and annotated inline so the assertions document behavior, not
just re-implement the function under test.

Threshold used in all tests: 0.85 (COSINE_THRESHOLD default).

Key unit vectors used
---------------------
  e1 = [1.0, 0.0]
  e2 = [0.0, 1.0]
  at_threshold  = [0.85, 0.526783]   dot(e1, at_threshold)  == 0.85  (== threshold)
  just_below    = [0.849473, 0.527632] dot(e1, just_below) ≈ 0.849473 (< threshold)

These are all unit vectors: norm == 1.0, so cosine == dot product.

Ordering contract
-----------------
match_anchors returns anchor keys in SORTED order within each topic's list.
This is the stable-order guarantee SA-3 can depend on.
"""

import math

import pytest

from retrieval.anchors import match_anchors, COSINE_THRESHOLD

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

E1 = [1.0, 0.0]
E2 = [0.0, 1.0]
# dot(E1, AT_THRESHOLD) == 0.85 exactly
AT_THRESHOLD = [0.85, math.sqrt(1 - 0.85 ** 2)]
# dot(E1, JUST_BELOW) ≈ 0.849473 — falls just under 0.85
_theta_below = math.acos(0.85) + 0.001
JUST_BELOW = [math.cos(_theta_below), math.sin(_theta_below)]


def _topic(id_: str, vector: list[float]) -> dict:
    return {"id": id_, "vector": vector}


# ---------------------------------------------------------------------------
# Sanity: our hand-computed dot products are correct
# ---------------------------------------------------------------------------

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def test_vector_math_at_threshold():
    """Verify AT_THRESHOLD dot E1 == 0.85 (no floating-point surprises)."""
    assert abs(_dot(E1, AT_THRESHOLD) - 0.85) < 1e-9


def test_vector_math_just_below():
    """Verify JUST_BELOW dot E1 < 0.85."""
    assert _dot(E1, JUST_BELOW) < 0.85


# ---------------------------------------------------------------------------
# Core behaviours
# ---------------------------------------------------------------------------

class TestOneAnchorManyTopics:
    """One anchor whose vector matches multiple topics above threshold."""

    def test_anchor_matches_two_topics(self):
        # anchor "ref:a" has vector E1 = [1, 0]
        # t1 vector is also E1 → dot = 1.0 ≥ 0.85 ✓
        # t2 vector is E1   → dot = 1.0 ≥ 0.85 ✓
        anchor_vectors = {"ref:a": E1}
        topics = [_topic("t1", E1), _topic("t2", E1)]
        result = match_anchors(anchor_vectors, topics)
        assert set(result.keys()) == {"t1", "t2"}
        assert "ref:a" in result["t1"]
        assert "ref:a" in result["t2"]

    def test_near_miss_topic_absent(self):
        # t3 has JUST_BELOW vs E1 → dot < 0.85 → should NOT appear
        anchor_vectors = {"ref:a": E1}
        topics = [_topic("t1", E1), _topic("t3", JUST_BELOW)]
        result = match_anchors(anchor_vectors, topics)
        assert "t1" in result
        assert "t3" not in result


class TestOneTopicManyAnchors:
    """A single topic that matches more than one anchor (the M:N seam)."""

    def test_topic_lists_both_anchor_keys(self):
        # t1 = E1; anchor "ref:alpha" = E1, anchor "ref:beta" = E1
        # Both dot products == 1.0 ≥ 0.85
        anchor_vectors = {"ref:alpha": E1, "ref:beta": E1}
        topics = [_topic("t1", E1)]
        result = match_anchors(anchor_vectors, topics)
        assert "t1" in result
        assert set(result["t1"]) == {"ref:alpha", "ref:beta"}

    def test_only_passing_anchor_in_list(self):
        # "ref:good" matches (E1·E1=1.0), "ref:bad" doesn't (E1·E2=0.0)
        anchor_vectors = {"ref:good": E1, "ref:bad": E2}
        topics = [_topic("t1", E1)]
        result = match_anchors(anchor_vectors, topics)
        assert result["t1"] == ["ref:good"]


class TestThresholdBoundary:
    """Exact-at-threshold is included; just-below is excluded."""

    def test_exactly_at_threshold_included(self):
        # dot(E1, AT_THRESHOLD) == 0.85 == COSINE_THRESHOLD → included
        anchor_vectors = {"ref:a": E1}
        topics = [_topic("t1", AT_THRESHOLD)]
        result = match_anchors(anchor_vectors, topics)
        assert "t1" in result

    def test_just_below_threshold_excluded(self):
        # dot(E1, JUST_BELOW) ≈ 0.849473 < 0.85 → excluded
        anchor_vectors = {"ref:a": E1}
        topics = [_topic("t1", JUST_BELOW)]
        result = match_anchors(anchor_vectors, topics)
        assert "t1" not in result

    def test_custom_threshold_respected(self):
        # With threshold=0.9, AT_THRESHOLD (0.85) should NOT match
        anchor_vectors = {"ref:a": E1}
        topics = [_topic("t1", AT_THRESHOLD)]
        result = match_anchors(anchor_vectors, topics, threshold=0.9)
        assert "t1" not in result


class TestOrphans:
    """Anchor that matches nothing / topic that matches nothing → absent."""

    def test_orphan_anchor_produces_no_entries(self):
        # "ref:orphan" = E2; topic has E1 → dot = 0.0 → no match
        anchor_vectors = {"ref:orphan": E2}
        topics = [_topic("t1", E1)]
        result = match_anchors(anchor_vectors, topics)
        assert result == {}

    def test_orphan_topic_absent_from_result(self):
        # "ref:a" = E1; "t_orphan" = E2 → dot = 0.0 → absent
        anchor_vectors = {"ref:a": E1}
        topics = [_topic("t_match", E1), _topic("t_orphan", E2)]
        result = match_anchors(anchor_vectors, topics)
        assert "t_match" in result
        assert "t_orphan" not in result

    def test_empty_inputs_return_empty_dict(self):
        assert match_anchors({}, []) == {}
        assert match_anchors({"ref:a": E1}, []) == {}
        assert match_anchors({}, [_topic("t1", E1)]) == {}


class TestStableOrdering:
    """Anchor keys within each topic's list are in sorted (lexicographic) order."""

    def test_keys_sorted_lexicographically(self):
        # Ensure the order is deterministic regardless of dict insertion order
        anchor_vectors = {
            "ref:zebra": E1,
            "ref:alpha": E1,
            "ref:middle": E1,
        }
        topics = [_topic("t1", E1)]
        result = match_anchors(anchor_vectors, topics)
        assert result["t1"] == sorted(result["t1"])

    def test_single_key_list_is_trivially_sorted(self):
        anchor_vectors = {"ref:only": E1}
        topics = [_topic("t1", E1)]
        result = match_anchors(anchor_vectors, topics)
        assert result["t1"] == ["ref:only"]

    def test_ordering_independent_of_input_order(self):
        # Two different insertion orders must produce identical sorted output
        av1 = {"ref:b": E1, "ref:a": E1}
        av2 = {"ref:a": E1, "ref:b": E1}
        topics = [_topic("t1", E1)]
        r1 = match_anchors(av1, topics)
        r2 = match_anchors(av2, topics)
        assert r1["t1"] == r2["t1"]
