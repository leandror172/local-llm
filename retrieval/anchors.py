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

import re
import subprocess
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
# Ingestion helpers (SA-1)
# ---------------------------------------------------------------------------

def _parse_grep_line(line: str) -> tuple[str, int, str] | None:
    """Parse one git grep output line into (file_path, start_line, bare_key).

    git grep --line-number -oE produces lines like:
      path/to/file.md:42:<!-- ref:my-key -->
    Returns None if the line doesn't match the expected format.
    """
    m = re.match(r'^(.+?):(\d+):<!-- ref:([a-z0-9-]+) -->$', line)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3)


def _read_block_lines(file_path: Path, start_line: int, bare_key: str) -> list[str]:
    """Return lines of the ref block body (exclusive of opening and closing markers)."""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    closing = f"<!-- /ref:{bare_key} -->"
    # start_line is 1-based; the marker is at index start_line-1
    body_lines = []
    for line in lines[start_line:]:   # start_line-1+1 = start_line (0-based after marker)
        if line.strip() == closing:
            break
        body_lines.append(line)
    return body_lines


def _find_heading_in_lines(lines: list[str]) -> str:
    """Return the text of the first heading line (``# ...``) in the block, or ''."""
    for line in lines:
        if re.match(r'^#{1,6}\s', line):
            return re.sub(r'^#{1,6}\s+', '', line).strip()
    return ""


def _prose_body_lines(block_lines: list[str]) -> str:
    """Join block lines into a string for parse_first_prose_line."""
    return "\n".join(block_lines)


# ---------------------------------------------------------------------------
# Ingestion + parsing (SA-1)
# ---------------------------------------------------------------------------

def ingest_anchors(repo_root: Path) -> list[Anchor]:
    """Find every unique ``<!-- ref:KEY -->`` in tracked ``*.md`` and resolve each
    to an Anchor. Uses ``git grep`` (tracked-only => .claude/local/ + gitignored
    excluded for free, D2 safety filter). Dedup by key (first occurrence wins)."""
    result = subprocess.run(
        ["git", "grep", "--line-number", "-oE", "<!-- ref:[a-z0-9-]+ -->", "--", "*.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    seen: dict[str, Anchor] = {}
    for line in result.stdout.splitlines():
        parsed = _parse_grep_line(line)
        if parsed is None:
            continue
        rel_path, start_line, bare_key = parsed
        if bare_key in seen:
            continue
        block_lines = _read_block_lines(repo_root / rel_path, start_line, bare_key)
        heading = _find_heading_in_lines(block_lines)
        first_prose = parse_first_prose_line(_prose_body_lines(block_lines))
        seen[bare_key] = Anchor(
            key=f"ref:{bare_key}",
            bare_key=bare_key,
            file_path=rel_path,
            start_line=start_line,
            heading=heading,
            first_prose=first_prose,
        )
    return list(seen.values())


def parse_first_prose_line(body: str) -> str:
    """First meaningful prose line of a ref block body, or "" if none.
    Skips: blank lines, italic-only metadata (``*...*``), sub-headings (``#``+),
    horizontal rules (``---``), and HTML comment markers."""
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line == "---":
            continue
        if line.startswith("<!--"):
            continue
        # italic-only: entire line is *...* (single asterisks wrapping the whole content)
        if re.match(r'^\*[^*]+\*$', line):
            continue
        return line
    return ""


# ---------------------------------------------------------------------------
# Description methods (SA-1, D3) — named-intent public fns + private dispatch
# (ref:patterns-code-named-methods)
# ---------------------------------------------------------------------------

def describe_mechanical_key(anchor: Anchor) -> str:
    """Default: ``f"{bare_key}: {heading} — {first_prose}"`` (hyphenated key)."""
    return f"{anchor.bare_key}: {anchor.heading} — {anchor.first_prose}"


def describe_key_only(anchor: Anchor) -> str:
    """Fast fallback: the hyphenated bare key alone (no body)."""
    return anchor.bare_key


def describe_mechanical(anchor: Anchor) -> str:
    """Body-only: heading + first_prose, no key. Validates the D3 failure mode
    (plan-type anchors opening with operational metadata fail to merge)."""
    return f"{anchor.heading} — {anchor.first_prose}"


def describe(anchor: Anchor, method: str = DEFAULT_METHOD) -> str:
    """Generic dispatch over the named describe_* methods by method string."""
    if method == METHOD_MECHANICAL_KEY:
        return describe_mechanical_key(anchor)
    if method == METHOD_KEY_ONLY:
        return describe_key_only(anchor)
    if method == METHOD_MECHANICAL:
        return describe_mechanical(anchor)
    raise ValueError(f"Unknown describe method: {method!r}")


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
    result = {}
    for topic_row in topic_rows:
        topic_id = topic_row["id"]
        vector = topic_row["vector"]
        matches = []
        for anchor_key, anchor_vector in anchor_vectors.items():
            dot_product = sum(a * b for a, b in zip(vector, anchor_vector))
            if dot_product >= threshold:
                matches.append(anchor_key)
        if matches:
            result[topic_id] = sorted(matches)
    return result


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
