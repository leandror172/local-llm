"""LTG Phase 3 — anchor integration.

Ingest every ``<!-- ref:KEY -->`` marker in tracked ``*.md`` files, create one
**anchor node** per unique key, embed its description, link it to semantically-near
topic rows via ``alias_of``, and rebuild the LanceDB ``topics`` table with both
surfaces present (dual-path retrieval — anchors and topics co-exist, neither merges).

Design: ``ref:ltg-phase3-decisions`` (frozen) + ``ref:ltg-phase3-discussion`` (why).
Plan:   ``docs/plans/ltg-phase3-anchors-implementation.md`` (how).

This module is the CONTRACT skeleton (task #1). Bodies are filled by later TDD
slices (SA-1..SA-4). Every signature below is the seam another slice builds against —
do not change a signature without updating its consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Merge threshold for anchor<->topic aliasing, expressed as cosine similarity.
# Vectors are unit-normalized (qwen3-embedding:8b), so cosine == dot product and
# the L2 equivalent is sqrt(2*(1-0.85)) = 0.5477 (valid ONLY for unit vectors).
# Provisional: derived from a 3-anchor LTG-self-referential probe (session 82).
# TODO Phase 5: move to config.yaml; recalibrate from full distribution at Phase 2.5.
COSINE_THRESHOLD: float = 0.85

# Description methods (D3). "mechanical+key" is the validated default; the key name
# is hyphenated and NEVER space-normalized (qwen3-embedding:8b treats hyphenated
# identifiers as meaningful compound units — probe session 82).
METHOD_MECHANICAL_KEY = "mechanical+key"
METHOD_KEY_ONLY = "key_only"
METHOD_MECHANICAL = "mechanical"
DEFAULT_METHOD = METHOD_MECHANICAL_KEY

# Near-miss diagnostic band: top match in [LOW, COSINE_THRESHOLD) is the interesting
# signal (just-below-threshold, e.g. graph_exploitation at 0.836), not 0.6 orphans.
NEARMISS_LOW: float = 0.80

# Schema field values for anchor rows that have no extraction provenance.
# rows_to_arrow_table uses r.get(name) -> a missing key becomes None, which a
# non-nullable column rejects. Every row dict MUST carry all fields explicitly.
ANCHOR_SOURCE_CLASS = "anchor_ref"
TOPIC_SOURCE_CLASS = "topic_extracted"
ANCHOR_CONFIDENCE: float = 1.0   # structural authority (explicit ref:KEY convention)
TOPIC_CONFIDENCE: float = 0.7    # LLM-extracted default; NOT changed by aliasing


# ---------------------------------------------------------------------------
# Data model — the unit that flows ingestion -> description -> matching -> rows
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Anchor:
    """One ``<!-- ref:KEY -->`` marker, resolved to its source context."""

    key: str          # full key with prefix, e.g. "ref:concept-ltg"
    bare_key: str     # "concept-ltg" — hyphenated, NEVER space-normalized (D3)
    file_path: str    # repo-relative, e.g. "docs/research/latent-topic-graph.md"
    start_line: int   # 1-based line of the marker (from git grep)
    heading: str      # nearest enclosing markdown heading text ("" if none)
    first_prose: str  # parse_first_prose_line output ("" if none)


@dataclass(frozen=True)
class RebuildReport:
    """Outcome of a full index rebuild (returned by rebuild_index)."""

    index_path: str
    anchors_ingested: int
    topics_read: int
    aliases_created: int                       # count of topic rows that gained an alias_of
    method: str
    staleness: list[str] = field(default_factory=list)
    nearmiss: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Ingestion + parsing (SA-1)
# ---------------------------------------------------------------------------

def ingest_anchors(repo_root: Path) -> list[Anchor]:
    """Find every unique ``<!-- ref:KEY -->`` in tracked ``*.md`` and resolve each
    to an Anchor. Uses ``git grep`` (tracked-only => .claude/local/ + gitignored
    excluded for free, D2 safety filter). Dedup by key (first occurrence wins)."""
    raise NotImplementedError


def parse_first_prose_line(body: str) -> str:
    """First meaningful prose line of a ref block body, or "" if none.
    Skips: blank lines, italic-only metadata (``*...*``), sub-headings (``#``+),
    horizontal rules (``---``), and HTML comment markers."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Description methods (SA-1, D3) — named-intent public fns + private dispatch
# (ref:patterns-code-named-methods)
# ---------------------------------------------------------------------------

def describe_mechanical_key(anchor: Anchor) -> str:
    """Default: ``f"{bare_key}: {heading} — {first_prose}"`` (hyphenated key)."""
    raise NotImplementedError


def describe_key_only(anchor: Anchor) -> str:
    """Fast fallback: the hyphenated bare key alone (no body)."""
    raise NotImplementedError


def describe_mechanical(anchor: Anchor) -> str:
    """Body-only: heading + first_prose, no key. Validates the D3 failure mode
    (plan-type anchors opening with operational metadata fail to merge)."""
    raise NotImplementedError


def describe(anchor: Anchor, method: str = DEFAULT_METHOD) -> str:
    """Generic dispatch over the named describe_* methods by method string."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Matching (SA-2) — exact in-memory cosine, NOT LanceDB ANN
# ---------------------------------------------------------------------------

def match_anchors(
    anchor_vectors: dict[str, list[float]],
    topic_rows: list[dict],
    threshold: float = COSINE_THRESHOLD,
) -> dict[str, list[str]]:
    """Exact cosine match of anchors against topics over unit-normalized vectors.

    THE M:N SEAM (SA-2 produces, SA-3 consumes):
      returns ``{topic_id: [anchor_key, ...]}`` — every topic above threshold for
      an anchor, both directions of multiplicity preserved. Topics with no match
      are absent from the dict.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Row construction (SA-3) — field table §4 / ref:ltg-phase2-schema
# ---------------------------------------------------------------------------

def build_anchor_rows(
    anchors: list[Anchor],
    vectors: dict[str, list[float]],
) -> list[dict]:
    """One full row dict per anchor (all 22 schema fields explicit; "" for
    non-nullable provenance fields, "[]" scope_tags, null anchor_key->set/alias_of)."""
    raise NotImplementedError


def apply_aliases(topic_rows: list[dict], matches: dict[str, list[str]]) -> list[dict]:
    """Return topic rows with the Phase-3 fields backfilled on ALL rows
    (source_class=topic_extracted, confidence=0.7, anchor_key=null) and ``alias_of``
    set to the JSON list of anchor keys on matched rows. Aliasing does NOT change
    confidence (D1)."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Diagnostics (SA-4)
# ---------------------------------------------------------------------------

def staleness_warnings(topic_rows: list[dict], repo_root: Path) -> list[str]:
    """One warning per topic whose source file mtime is newer than its
    extraction_timestamp (index may be stale vs current files; D6 #4)."""
    raise NotImplementedError


def nearmiss_report(anchors: list[Anchor], topic_rows: list[dict]) -> list[dict]:
    """Anchors whose top match sits in [NEARMISS_LOW, COSINE_THRESHOLD) — the
    just-below-threshold band. Inert until Phase 2.5 corpus expansion (most of the
    143 keys are legitimate orphans). Each entry: {anchor_key, top_topic, top_cosine}."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Orchestration (SA-4)
# ---------------------------------------------------------------------------

def rebuild_index(
    repo_root: Path,
    index_path: Path,
    method: str = DEFAULT_METHOD,
) -> RebuildReport:
    """Full rebuild: ingest anchors -> read topics (reuse stored vectors) -> embed
    anchor descriptions -> match -> apply aliases -> build anchor rows -> write
    topics+anchors via store.py overwrite path (auto-backup). Returns a RebuildReport
    carrying counts + staleness + near-miss diagnostics."""
    raise NotImplementedError
